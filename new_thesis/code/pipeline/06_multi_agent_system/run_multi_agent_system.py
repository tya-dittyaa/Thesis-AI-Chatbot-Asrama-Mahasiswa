"""
Pipeline Stage 6: Multi-Agent System (MAS) Evaluation
Evaluates the 3-Agent Architecture on the Golden Benchmark (500 tickets):
1. Agen 1: Reception & Handbook RAG Retrieval
2. Agen 2: Triage & Classification via LLM Native Function Calling
3. Agen 3: Empathetic Official Staff Response Generator

Features:
- Built-in TF-IDF Handbook RAG retriever (46 semantic chunks)
- Native Function Calling with triage_tool_schema.json
- Resumable checkpoints (skips processed tickets in results/mas_predictions.csv)
- Mock mode (--mock) for dry-run verification without API quota
- Exports detailed predictions CSV and comparative summary JSON metrics
"""

import os
import sys
import time
import json
import re
import argparse
import threading
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from datetime import datetime

warnings.filterwarnings("ignore", message=".*automatic function calling.*")
warnings.filterwarnings("ignore", category=UserWarning, module="google.genai")

import pandas as pd
from tqdm import tqdm
from dotenv import load_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Try importing google.genai
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

# Add project root to sys.path to enable importing pipeline modules
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from pipeline.api_key_manager import ApiKeyManager
except ImportError:
    ApiKeyManager = None

try:
    from pipeline.clario_client import call_clario_completion
except ImportError:
    call_clario_completion = None

# Mapping of department codes to canonical names
DEPT_CODE_TO_NAME = {
    "ED": "Estate Department",
    "OP": "Operations",
    "FN": "Finance",
    "MR": "Marketing",
    "SO": "Student Support Office",
}

DEPT_NAME_TO_CODE = {v.lower(): k for k, v in DEPT_CODE_TO_NAME.items()}


def normalize_dept_name(val: str) -> str:
    """Normalize department code or full name to canonical full name."""
    if not val or not isinstance(val, str):
        return "Unknown"
    val_clean = val.strip()
    val_upper = val_clean.upper()
    if val_upper in DEPT_CODE_TO_NAME:
        return DEPT_CODE_TO_NAME[val_upper]
    val_lower = val_clean.lower()
    for code, name in DEPT_CODE_TO_NAME.items():
        if val_lower == name.lower():
            return name
        if code.lower() in val_lower or val_lower in name.lower():
            return name
    return val_clean


def extract_json_from_text(text: str) -> dict:
    """Safely extract and parse JSON from model response text."""
    if not text:
        return {}
    text_clean = text.strip()
    try:
        return json.loads(text_clean)
    except json.JSONDecodeError:
        pass
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text_clean, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    start = text_clean.find("{")
    end = text_clean.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = text_clean[start:end+1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass
    return {}


class HandbookRetriever:
    """Fast TF-IDF semantic chunk retriever for Boarder Handbook."""
    def __init__(self, chunks_path: Path):
        with open(chunks_path, "r", encoding="utf-8") as f:
            self.chunks = json.load(f)
        docs = [c.get("section_title", "") + " " + c.get("text_content", "") for c in self.chunks]
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=5000)
        self.doc_vectors = self.vectorizer.fit_transform(docs)

    def retrieve(self, query: str, top_k: int = 2, min_score: float = 0.08) -> list[dict]:
        if not query or not query.strip():
            return []
        q_vec = self.vectorizer.transform([query])
        similarities = cosine_similarity(q_vec, self.doc_vectors)[0]
        top_indices = similarities.argsort()[-top_k:][::-1]
        results = []
        for idx in top_indices:
            score = float(similarities[idx])
            if score >= min_score:
                chunk = self.chunks[idx].copy()
                chunk["relevance_score"] = round(score, 3)
                results.append(chunk)
        return results


def simulate_mock_mas(row: pd.Series, retriever: HandbookRetriever) -> dict:
    """Simulate MAS 3-agent pipeline for dry-run testing."""
    complaint = str(row.get("CleanedComplaint", "")).lower()
    initial_dept = str(row.get("InitialDepartmentName", "Estate Department"))
    
    # 1. Agen 1 Retrieval & Intent
    relevant_chunks = retriever.retrieve(complaint, top_k=2)
    top_chunk_title = relevant_chunks[0]["section_title"] if relevant_chunks else "General Facilities"
    
    # 2. Agen 2 Triage Tool Call
    if any(k in complaint for k in ["ac", "bocor", "lampu", "kran", "pintu", "kasur", "lemari", "kunci kamar", "plafon"]):
        dept_code = "ED"
        category = "Air Conditioner (AC)" if "ac" in complaint else "Room Maintenance"
        urgency = "High" if "bocor" in complaint or "mati total" in complaint else "Medium"
        item = "AC / Perabot Kamar"
    elif any(k in complaint for k in ["wifi", "internet", "paket", "koneksi", "resepsionis", "tamu", "pindah kamar"]):
        dept_code = "OP"
        category = "Internet" if ("wifi" in complaint or "internet" in complaint) else "Front Desk"
        urgency = "Medium"
        item = "WiFi / Jaringan / Paket"
    elif any(k in complaint for k in ["listrik berlebih", "deposit", "tagihan", "biaya sewa", "refund", "pembayaran"]):
        dept_code = "FN"
        category = "Electricity Usage" if "listrik" in complaint else "Room Payment and Due Date"
        urgency = "Medium"
        item = "Tagihan / Administrasi Keuangan"
    elif any(k in complaint for k in ["renewal", "perpanjangan", "check out", "checkout", "booking", "sewa kamar"]):
        dept_code = "MR"
        category = "Room Renewal" if "renewal" in complaint or "perpanjangan" in complaint else "Check Out Procedure"
        urgency = "Low"
        item = "Kontrak Sewa Hunian"
    elif any(k in complaint for k in ["bising", "berisik", "teman sekamar", "tata tertib", "rokok", "konseling"]):
        dept_code = "SO"
        category = "Roommate Conflict" if "teman" in complaint else "Noise Disturbance"
        urgency = "Medium"
        item = "Tata Tertib Penghuni"
    else:
        dept_code = DEPT_NAME_TO_CODE.get(initial_dept.lower(), "ED")
        category = str(row.get("SubjectCategory", "General Inquiry"))
        urgency = "Low"
        item = "Fasilitas Umum"

    dept_name = DEPT_CODE_TO_NAME[dept_code]
    
    # 3. Agen 3 Response
    official_resp = (
        f"Dear Penghuni Binus Square,\n\n"
        f"Terima kasih atas laporan Anda mengenai {category}. Laporan Anda telah berhasil "
        f"diteruskan ke tim {dept_name} untuk ditindaklanjuti dengan prioritas {urgency}.\n\n"
        f"Mohon pastikan Anda dapat dihubungi melalui portal atau nomor telepon terdaftar jika tim teknisi kami memerlukan akses kamar.\n\n"
        f"Salam hangat,\nTim Layanan Hunian Binus Square"
    )
    
    return {
        "agent1_intent": "COMPLAINT",
        "agent1_is_valid": True,
        "agent1_retrieved_policy": top_chunk_title,
        "agent2_tool_called": "route_and_classify_complaint",
        "agent2_target_dept_code": dept_code,
        "agent2_target_dept_name": dept_name,
        "agent2_category": category,
        "agent2_urgency": urgency,
        "agent2_item": item,
        "agent2_confidence": 0.92 if urgency in ["High", "Emergency"] else 0.78,
        "agent2_reasoning": f"Berdasarkan analisis keluhan '{complaint[:40]}...', penanganan berada di ranah wewenang {dept_name}.",
        "agent3_confirmed": True,
        "agent3_response": official_resp,
        "agent1_latency": 0.02,
        "agent2_latency": 0.04,
        "agent3_latency": 0.03,
        "total_latency": 0.09,
        "total_tokens": 420
    }


def call_with_retry(client, model_name: str, contents: str, config, max_retries: int = 8, key_manager = None):
    for attempt in range(max_retries):
        key_idx = None
        try:
            if key_manager:
                key_idx, curr_client = key_manager.acquire_client_with_index()
            else:
                curr_client = client
            t0 = time.time()
            resp = curr_client.models.generate_content(
                model=model_name,
                contents=contents,
                config=config
            )
            pure_lat = time.time() - t0
            return resp, pure_lat
        except Exception as e:
            err_str = str(e).lower()
            is_daily_quota = ("generaterequestsperday" in err_str or "requests per day limit" in err_str or "limit: 500" in err_str or "retry in 20h" in err_str or "retry in 2" in err_str)
            if is_daily_quota and key_manager:
                key_manager.mark_daily_exhausted(key_idx)
                continue
            is_invalid = ("api_key_invalid" in err_str or "api key not valid" in err_str or "400" in err_str or "403" in err_str or "permission_denied" in err_str or "unauthenticated" in err_str or "401" in err_str)
            if is_invalid and key_manager:
                key_manager.mark_invalid(key_idx)
                continue
            is_rate = ("503" in err_str or "429" in err_str or "demand" in err_str or "quota" in err_str or "resource_exhausted" in err_str or "disconnected" in err_str)
            if attempt < max_retries - 1 and is_rate:
                if ("429" in err_str or "quota" in err_str or "resource_exhausted" in err_str) and key_manager and len(key_manager.keys) > 1:
                    key_manager.rotate(wait_sec=1, idx=key_idx)
                else:
                    sleep_dur = 8 * (attempt + 1)
                    print(f"[RateLimit] Menunggu {sleep_dur}s sebelum retry ke-{attempt+1}...")
                    time.sleep(sleep_dur)
            else:
                raise e


def call_agent1_reception(client, model_name: str, system_prompt: str, complaint: str, chunks_text: str, subject_category: str = "", initial_dept: str = "", key_manager = None):
    """Agen 1: Receptionist & Handbook RAG validator."""
    # Portal metadata (subject category, initial department) is deliberately not sent: it leaks the label.
    rag_block = chunks_text if chunks_text else "(Tidak ada pasal Handbook yang relevan langsung)"
    user_content = (
        f"PESAN PENGHUNI:\n{complaint}\n\n"
        f"POTONGAN ATURAN HANDBOOK ASRAMA (RAG CONTEXT):\n{rag_block}\n\n"
        f"Keluarkan analisis niat, distilasi aturan Handbook, dan ringkasan keluhan dalam format JSON sesuai panduan."
    )

    clario_key = os.getenv("CLARIO_API_KEY", "").strip()
    if call_clario_completion and clario_key and "YOUR_API_KEY" not in clario_key:
        clario_model = os.getenv("CLARIO_MODEL", "clario/gemini-3.7-flash")
        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_content}]
        p, raw, lat, p_tok, r_tok = call_clario_completion(messages=messages, model=clario_model, response_format={"type": "json_object"})
        return p, lat, p_tok + r_tok

    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        temperature=0.1,
        response_mime_type="application/json"
    )
    resp, lat = call_with_retry(client, model_name, user_content, config, key_manager=key_manager)
    parsed = extract_json_from_text(resp.text or "")
    usage = getattr(resp, "usage_metadata", None)
    tokens = (getattr(usage, "prompt_token_count", 0) or 0) + (getattr(usage, "candidates_token_count", 0) or 0)
    return parsed, lat, tokens


def call_agent2_triage(client, model_name: str, system_prompt: str, tool_schema: dict, complaint: str, agent1_summary: str, initial_dept: str, subject_category: str = "", agent1_policy: str = "", key_manager = None):
    """Agen 2: Triage Specialist invoking native function calling."""
    policy_line = f"- Intisari Regulasi Handbook (Distilasi Agen 1): {agent1_policy}\n" if agent1_policy else ""
    user_content = (
        f"LAPORAN KELUHAN MAHASISWA:\n"
        f"- Isi Keluhan Asli: {complaint}\n"
        f"- Ringkasan Validasi Agen 1: {agent1_summary}\n"
        f"{policy_line}\n"
        f"Silakan analisis dan panggil fungsi tool `route_and_classify_complaint`."
    )

    clario_key = os.getenv("CLARIO_API_KEY", "").strip()
    if call_clario_completion and clario_key and "YOUR_API_KEY" not in clario_key:
        clario_model = os.getenv("CLARIO_MODEL", "clario/gemini-3.7-flash")
        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_content}]
        tool_args, fn_name, lat, p_tok, r_tok = call_clario_completion(messages=messages, model=clario_model, tools=[tool_schema])
        return fn_name, tool_args, lat, p_tok + r_tok
    
    tool = types.Tool(function_declarations=[
        types.FunctionDeclaration(
            name=tool_schema["name"],
            description=tool_schema["description"],
            parameters=tool_schema["parameters"]
        )
    ])
    
    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        temperature=0.1,
        tools=[tool]
    )
    
    resp, lat = call_with_retry(client, model_name, user_content, config, key_manager=key_manager)
    usage = getattr(resp, "usage_metadata", None)
    tokens = (getattr(usage, "prompt_token_count", 0) or 0) + (getattr(usage, "candidates_token_count", 0) or 0)
    
    tool_args = {}
    func_name = ""
    # Check direct function_calls helper in google-genai
    if hasattr(resp, "function_calls") and resp.function_calls:
        fc = resp.function_calls[0]
        func_name = getattr(fc, "name", "")
        tool_args = dict(fc.args) if hasattr(fc, "args") and fc.args else {}
    elif resp.candidates and resp.candidates[0].content and resp.candidates[0].content.parts:
        for part in resp.candidates[0].content.parts:
            if hasattr(part, "function_call") and part.function_call:
                func_name = part.function_call.name
                tool_args = dict(part.function_call.args) if part.function_call.args else {}
                break
                
    return func_name, tool_args, lat, tokens


def call_agent3_response(client, model_name: str, system_prompt: str, complaint: str, triage_data: dict, key_manager = None):
    """Agen 3: Empathetic Official Staff Response Generator."""
    user_content = (
        f"KELUHAN MAHASISWA:\n{complaint}\n\n"
        f"HASIL TRIASE TERSTRUKTUR (AGEN 2):\n{json.dumps(triage_data, ensure_ascii=False, indent=2)}\n\n"
        f"Susun draf balasan resmi staf sesuai panduan format JSON."
    )

    clario_key = os.getenv("CLARIO_API_KEY", "").strip()
    if call_clario_completion and clario_key and "YOUR_API_KEY" not in clario_key:
        clario_model = os.getenv("CLARIO_MODEL", "clario/gemini-3.7-flash")
        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_content}]
        p, raw, lat, p_tok, r_tok = call_clario_completion(messages=messages, model=clario_model, response_format={"type": "json_object"})
        return p, lat, p_tok + r_tok

    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        temperature=0.2,
        response_mime_type="application/json"
    )
    resp, lat = call_with_retry(client, model_name, user_content, config, key_manager=key_manager)
    parsed = extract_json_from_text(resp.text or "")
    usage = getattr(resp, "usage_metadata", None)
    tokens = (getattr(usage, "prompt_token_count", 0) or 0) + (getattr(usage, "candidates_token_count", 0) or 0)
    return parsed, lat, tokens


def main():
    parser = argparse.ArgumentParser(description="Run Multi-Agent System (MAS) Evaluation on Golden Benchmark")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of tickets to evaluate")
    parser.add_argument("--sample-per-dept", type=int, default=None, help="Sample N tickets per department (e.g. 1 or 2)")
    parser.add_argument("--model", type=str, default=None, help="Gemini model name (default: gemini-2.5-flash)")
    parser.add_argument("--mock", action="store_true", help="Run with simulated mock responses (no API calls)")
    parser.add_argument("--resume", action="store_true", default=True, help="Resume from existing predictions file")
    parser.add_argument("--no-resume", dest="resume", action="store_false", help="Overwrite existing predictions file")
    # NOTE: --cleaned flag dihapus. Benchmark sudah selalu bersih sejak tahap 02a.
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent
    workspace_root = base_dir.parent.parent

    # Load .env
    env_path = workspace_root / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    else:
        load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    clario_key = os.getenv("CLARIO_API_KEY", "").strip()
    is_clario = bool(clario_key and "YOUR_API_KEY" not in clario_key)
    model_name = os.getenv("CLARIO_MODEL", "clario/gemini-3.7-flash") if is_clario else (args.model or os.getenv("GEMINI_MODEL") or "gemini-2.5-flash")

    key_manager = None
    client = None
    if not args.mock and not is_clario:
        if ApiKeyManager is not None:
            try:
                key_manager = ApiKeyManager(env_path=str(env_path) if env_path.exists() else None)
                client = key_manager.get_client()
            except Exception as e:
                print(f"[ApiKeyManager] Inisialisasi multi-key gagal ({e}), fallback ke single key.")
        
        if client is None:
            if not api_key or api_key.strip() == "your_gemini_api_key_here":
                print("\n" + "="*70)
                print("WARNING: GEMINI_API_KEY belum disetel!")
                print(f"Silakan buat file: {workspace_root / '.env'}")
                print("Isi dengan: GEMINI_API_KEY=AIzaSy...")
                print("Atau jalankan dengan flag --mock untuk testing dry-run:")
                print("  python run_multi_agent_system.py --mock --limit 10")
                print("="*70 + "\n")
                sys.exit(1)
            if not GENAI_AVAILABLE:
                print("ERROR: Paket google-genai belum terinstal.")
                sys.exit(1)
            client = genai.Client(api_key=api_key)

    # Load data (selalu bersih - label noise sudah dihapus di tahap 02a)
    splitting_data_dir = base_dir.parent / "02_data_splitting" / "data"
    data_path = splitting_data_dir / "test_golden_benchmark_500.csv"
    if not data_path.exists():
        print(f"ERROR: Dataset benchmark tidak ditemukan di {data_path}")
        print("Jalankan dulu: python pipeline/02_data_splitting/split_data.py")
        sys.exit(1)

    df = pd.read_csv(data_path)
    print(f"Loaded Golden Benchmark: {len(df)} tiket bersih (label noise telah dibersihkan di tahap 02a)")

    # Load Handbook & Retriever
    chunks_path = base_dir / "data" / "handbook_chunks.json"
    retriever = HandbookRetriever(chunks_path)
    print(f"Initialized Handbook RAG Retriever ({len(retriever.chunks)} chunks)")

    # Load Prompts & Schema
    prompts_dir = base_dir.parent / "04_agent_schemas_and_prompts" / "prompts"
    schema_path = base_dir.parent / "04_agent_schemas_and_prompts" / "schemas" / "triage_tool_schema.json"
    
    with open(prompts_dir / "agent1_reception_rag.txt", "r", encoding="utf-8") as f:
        p1 = f.read()
    with open(prompts_dir / "agent2_triage_specialist.txt", "r", encoding="utf-8") as f:
        p2 = f.read()
    with open(prompts_dir / "agent3_response_generator.txt", "r", encoding="utf-8") as f:
        p3 = f.read()
    with open(schema_path, "r", encoding="utf-8") as f:
        tool_schema = json.load(f)

    results_dir = base_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    predictions_csv = results_dir / "mas_predictions.csv"
    summary_json = results_dir / "mas_summary.json"

    existing_preds = {}
    if args.resume and predictions_csv.exists():
        try:
            df_exist = pd.read_csv(predictions_csv)
            if "FeedbackHeaderID" in df_exist.columns:
                for _, row in df_exist.iterrows():
                    err = str(row.get("ErrorMessage", "")).strip()
                    pred = str(row.get("PredictedDepartmentName", "")).strip()
                    if pred and pred != "Unknown" and (not err or err == "nan"):
                        existing_preds[row["FeedbackHeaderID"]] = row.to_dict()
                print(f"Resuming: Ditemukan {len(existing_preds)} tiket valid tersimpan. Sisa/error ({len(df_exist) - len(existing_preds)}) akan dievaluasi.")
        except Exception as e:
            print(f"Resume warning: {e}")

    if args.sample_per_dept:
        df_eval = df.groupby("HandledDepartmentName").head(args.sample_per_dept)
        print(f"Evaluating stratified subset: {len(df_eval)} tickets ({args.sample_per_dept} per department, Mode: {'MOCK' if args.mock else model_name})")
    elif args.limit:
        df_eval = df.head(args.limit)
        print(f"Evaluating subset: {len(df_eval)} tickets (limit={args.limit}, Mode: {'MOCK' if args.mock else model_name})")
    else:
        df_eval = df
        print(f"Evaluating full benchmark: {len(df_eval)} tickets (Mode: {'MOCK' if args.mock else model_name})")

    results = list(existing_preds.values())
    processed_ids = set(existing_preds.keys())
    pending_rows = [row for _, row in df_eval.iterrows() if str(row["FeedbackHeaderID"]) not in processed_ids]
    res_lock = threading.Lock()

    def eval_one(row):
        ticket_id = str(row["FeedbackHeaderID"])
        complaint = str(row.get("CleanedComplaint", "")).strip()
        initial_dept = str(row.get("InitialDepartmentName", "")).strip()
        handled_dept = str(row.get("HandledDepartmentName", "")).strip()
        subject_category = str(row.get("SubjectCategory", "")).strip()
        is_rerouted = int(row.get("IsRerouted", 0))

        if args.mock:
            time.sleep(0.02)
            mas_res = simulate_mock_mas(row, retriever)
            pred_dept_code = mas_res["agent2_target_dept_code"]
            pred_dept_name = mas_res["agent2_target_dept_name"]
            pred_category = mas_res["agent2_category"]
            urgency = mas_res["agent2_urgency"]
            facility_item = mas_res["agent2_item"]
            confidence = mas_res["agent2_confidence"]
            reasoning = mas_res["agent2_reasoning"]
            official_resp = mas_res["agent3_response"]
            fn_success = 1
            lat1, lat2, lat3 = mas_res["agent1_latency"], mas_res["agent2_latency"], mas_res["agent3_latency"]
            tot_tokens = mas_res["total_tokens"]
            err_msg = ""
        else:
            try:
                # 1. RAG Retrieval & Agen 1
                top_chunks = retriever.retrieve(complaint, top_k=2)
                chunks_context = "\n\n".join([f"[{c['section_title']} (Hal. {c['page_start']})]\n{c['text_content']}" for c in top_chunks])
                a1_json, lat1, tok1 = call_agent1_reception(client, model_name, p1, complaint, chunks_context, key_manager=key_manager)
                
                # 2. Agen 2 Triage with Function Calling
                a1_summary = a1_json.get("complaint_summary") or complaint
                a1_policy = a1_json.get("extracted_handbook_policy") or ""
                fn_name, tool_args, lat2, tok2 = call_agent2_triage(client, model_name, p2, tool_schema, complaint, a1_summary, "", agent1_policy=a1_policy, key_manager=key_manager)
                
                fn_success = int(bool(tool_args and "target_department" in tool_args))
                pred_dept_code = tool_args.get("target_department", "")
                pred_dept_name = normalize_dept_name(tool_args.get("target_department_name") or pred_dept_code)
                pred_category = tool_args.get("problem_category", "")
                urgency = tool_args.get("urgency_level", "")
                facility_item = tool_args.get("facility_item", "")
                confidence = float(tool_args.get("confidence_score", 0.0))
                reasoning = tool_args.get("reasoning_summary", "")

                # 3. Agen 3 Response Generator
                a3_json, lat3, tok3 = call_agent3_response(client, model_name, p3, complaint, tool_args, key_manager=key_manager)
                official_resp = a3_json.get("official_response_text", "")
                tot_tokens = tok1 + tok2 + tok3
                err_msg = ""
            except Exception as e:
                err_msg = str(e)
                print(f"\n[Warning] Error on ticket {ticket_id}: {err_msg}")
                fn_success = 0
                pred_dept_code, pred_dept_name, pred_category, urgency, facility_item, confidence, reasoning, official_resp = "", "Unknown", "", "", "", 0.0, "", ""
                lat1, lat2, lat3 = 0, 0, 0
                tot_tokens = 0

        is_correct = int(pred_dept_name.lower().strip() == handled_dept.lower().strip())
        was_reroute_fixed = int(is_rerouted == 1 and is_correct == 1 and pred_dept_name.lower().strip() != initial_dept.lower().strip())

        record = {
            "FeedbackHeaderID": ticket_id,
            "CreatedDate": row.get("CreatedDate", ""),
            "SubjectCategory": row.get("SubjectCategory", ""),
            "InitialDepartmentName": initial_dept,
            "HandledDepartmentName": handled_dept,
            "IsRerouted": is_rerouted,
            "PredictedDepartmentCode": pred_dept_code,
            "PredictedDepartmentName": pred_dept_name,
            "PredictedCategory": pred_category,
            "UrgencyLevel": urgency,
            "FacilityItem": facility_item,
            "ConfidenceScore": round(float(confidence), 3),
            "RoutingReason": reasoning,
            "OfficialStaffReply": official_resp,
            "IsCorrect": is_correct,
            "WasRerouteFixed": was_reroute_fixed,
            "FunctionCallSuccess": fn_success,
            "Latency_Agent1": round(lat1, 3),
            "Latency_Agent2": round(lat2, 3),
            "Latency_Agent3": round(lat3, 3),
            "TotalLatencySeconds": round(lat1 + lat2 + lat3, 3),
            "TotalTokens": tot_tokens,
            "ErrorMessage": err_msg
        }

        with res_lock:
            results.append(record)
            processed_ids.add(ticket_id)
            if len(results) % 10 == 0 or len(results) == len(df_eval):
                pd.DataFrame(results).to_csv(predictions_csv, index=False, encoding="utf-8")

    with ThreadPoolExecutor(max_workers=10) as ex:
        futures = [ex.submit(eval_one, r) for r in pending_rows]
        for fut in tqdm(as_completed(futures), total=len(futures), desc="Evaluating MAS Pipeline"):
            fut.result()

    order_map = {str(tid): i for i, tid in enumerate(df_eval["FeedbackHeaderID"])}
    results.sort(key=lambda r: order_map.get(str(r["FeedbackHeaderID"]), 999999))

    df_final = pd.DataFrame(results)
    df_final.to_csv(predictions_csv, index=False, encoding="utf-8")

    # Metrics
    total = len(df_final)
    correct = df_final["IsCorrect"].sum()
    overall_acc = (correct / total * 100) if total > 0 else 0.0
    fn_call_rate = (df_final["FunctionCallSuccess"].sum() / total * 100) if total > 0 else 0.0

    df_rerouted = df_final[df_final["IsRerouted"] == 1]
    reroute_total = len(df_rerouted)
    reroute_acc = (df_rerouted["IsCorrect"].sum() / reroute_total * 100) if reroute_total > 0 else 0.0
    reroute_fixed = df_rerouted["WasRerouteFixed"].sum()

    dept_metrics = {}
    for dept_name in DEPT_CODE_TO_NAME.values():
        df_dept = df_final[df_final["HandledDepartmentName"] == dept_name]
        d_tot = len(df_dept)
        d_cor = df_dept["IsCorrect"].sum() if d_tot > 0 else 0
        d_acc = (d_cor / d_tot * 100) if d_tot > 0 else 0.0
        dept_metrics[dept_name] = {
            "total_tickets": int(d_tot),
            "correct_predictions": int(d_cor),
            "accuracy_percent": round(d_acc, 2)
        }

    summary = {
        "timestamp": datetime.now().isoformat(),
        "architecture": "Multi-Agent System (3-Agent Pipeline with Native Function Calling & RAG)",
        "model_used": "MOCK" if args.mock else model_name,
        "total_evaluated": int(total),
        "overall_accuracy_percent": round(overall_acc, 2),
        "function_call_success_rate": round(fn_call_rate, 2),
        "average_latency_seconds": round(df_final["TotalLatencySeconds"].mean(), 3),
        "average_tokens_per_ticket": round(df_final["TotalTokens"].mean(), 1),
        "reroute_analysis": {
            "total_rerouted_tickets": int(reroute_total),
            "reroute_accuracy_percent": round(reroute_acc, 2),
            "reroute_successfully_corrected": int(reroute_fixed)
        },
        "per_department_metrics": dept_metrics
    }

    with open(summary_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print("\n" + "="*70)
    print("MULTI-AGENT SYSTEM (MAS) EVALUATION SUMMARY:")
    print("="*70)
    print(f"Total Evaluated: {total}")
    print(f"Overall Accuracy: {overall_acc:.2f}% ({correct}/{total})")
    print(f"Function Call Success Rate: {fn_call_rate:.2f}%")
    print(f"Avg Total Latency: {summary['average_latency_seconds']} s/ticket")
    print(f"Avg Total Tokens: {summary['average_tokens_per_ticket']} tokens/ticket")
    print(f"Reroute Recovery: {reroute_acc:.2f}% (Corrected: {reroute_fixed}/{reroute_total})")
    print("\nPer-Department Accuracy:")
    for dept, m in dept_metrics.items():
        print(f"  - {dept:25s}: {m['accuracy_percent']:6.2f}% ({m['correct_predictions']}/{m['total_tickets']})")
    print("="*70)
    print(f"Predictions saved to : {predictions_csv}")
    print(f"Summary saved to     : {summary_json}")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()

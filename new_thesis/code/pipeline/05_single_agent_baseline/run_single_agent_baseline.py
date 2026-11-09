"""
Pipeline Stage 5: Single-Agent Baseline Evaluation
Evaluates the monolithic single-agent baseline on the Golden Benchmark (500 tickets).

Features:
- Configurable model (Gemini 2.5 Flash, 2.0 Flash, 1.5 Flash, etc.)
- Resumable checkpoints (skips already-processed tickets in baseline_predictions.csv)
- Mock mode (--mock) for dry-run testing without consuming API quota
- Robust error handling and JSON parsing
- Exports detailed predictions CSV and summary JSON metrics
"""

import os
import sys
import time
import json
import re
import argparse
from pathlib import Path
from datetime import datetime
import pandas as pd
from tqdm import tqdm
from dotenv import load_dotenv

# Try importing google.genai
try:
    from google import genai
    from google.genai import types
    from google.genai.errors import APIError
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

# Mapping of department codes to canonical names
DEPT_CODE_TO_NAME = {
    "ED": "Estate Department",
    "OP": "Operations",
    "FN": "Finance",
    "MR": "Marketing",
    "SO": "Student Support Office",
}

# Reverse mapping
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
    # First try direct parsing
    text_clean = text.strip()
    try:
        return json.loads(text_clean)
    except json.JSONDecodeError:
        pass
    
    # Try finding markdown code block ```json ... ```
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text_clean, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
            
    # Try finding the first '{' and last '}'
    start = text_clean.find("{")
    end = text_clean.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = text_clean[start:end+1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass
            
    return {}


def simulate_mock_prediction(row: pd.Series) -> dict:
    """Generate a realistic mock response for dry-run testing."""
    complaint = str(row.get("CleanedComplaint", "")).lower()
    initial_dept = str(row.get("InitialDepartmentName", "Estate Department"))
    
    # Simple keyword heuristics for mock
    if any(k in complaint for k in ["ac", "bocor", "lampu", "kran", "pintu", "kasur", "lemari", "kunci kamar", "plafon"]):
        target = "ED"
    elif any(k in complaint for k in ["wifi", "internet", "paket", "koneksi", "resepsionis", "tamu", "pindah kamar"]):
        target = "OP"
    elif any(k in complaint for k in ["listrik berlebih", "deposit", "tagihan", "biaya sewa", "refund", "pembayaran"]):
        target = "FN"
    elif any(k in complaint for k in ["renewal", "perpanjangan", "check out", "checkout", "booking", "sewa kamar"]):
        target = "MR"
    elif any(k in complaint for k in ["bising", "berisik", "teman sekamar", "tata tertib", "rokok", "konseling"]):
        target = "SO"
    else:
        target = DEPT_NAME_TO_CODE.get(initial_dept.lower(), "ED")
        
    return {
        "intent": "COMPLAINT",
        "target_department": target,
        "target_department_name": DEPT_CODE_TO_NAME.get(target, target),
        "problem_category": str(row.get("SubjectCategory", "General Facility")),
        "urgency_level": "Medium",
        "facility_item": "Fasilitas Kamar/Hunian",
        "location_context": "Kamar Penghuni",
        "draft_reply": f"Halo, keluhan Anda mengenai '{row.get('SubjectCategory', 'fasilitas')}' telah kami terima dan akan diteruskan ke tim {DEPT_CODE_TO_NAME.get(target, target)}."
    }


def call_gemini_baseline(
    client: genai.Client,
    model_name: str,
    system_prompt: str,
    ticket_payload: dict,
    key_manager = None
) -> tuple[dict, str, float, int, int]:
    """
    Call Gemini API with single-agent prompt and ticket payload.
    Returns: (parsed_json, raw_text, latency_sec, prompt_tokens, response_tokens)
    """
    user_content = (
        f"DATA TIKET PENGADUAN PENGHUNI:\n"
        f"- Judul/Subjek Kategori Mahasiswa: {ticket_payload.get('SubjectCategory', '-')}\n"
        f"- Departemen Pilihan Mahasiswa: {ticket_payload.get('InitialDepartmentName', '-')}\n"
        f"- Isi Pesan Keluhan: {ticket_payload.get('CleanedComplaint', '-')}\n\n"
        f"Silakan analisis dan berikan respons JSON sesuai format panduan."
    )
    
    start_time = time.time()
    raw_text = ""
    prompt_tokens = 0
    response_tokens = 0
    
    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        temperature=0.1,
        response_mime_type="application/json"
    )
    
    response = None
    max_retries = 5
    for attempt in range(max_retries):
        try:
            curr_client = key_manager.get_client() if key_manager else client
            response = curr_client.models.generate_content(
                model=model_name,
                contents=user_content,
                config=config
            )
            break
        except Exception as e:
            err_str = str(e)
            is_rate_limit = "429" in err_str or "quota" in err_str.lower() or "rate" in err_str.lower() or "resource_exhausted" in err_str.lower()
            is_server_err = "503" in err_str or "502" in err_str or "demand" in err_str.lower()
            if attempt < max_retries - 1 and (is_rate_limit or is_server_err):
                if is_rate_limit and key_manager and len(key_manager.keys) > 1:
                    print(f"\n  [RATE LIMIT/QUOTA] Key kena limit. Auto-rotating ke API key berikutnya...")
                    key_manager.rotate(wait_sec=2)
                else:
                    # Rate limit: tunggu lebih lama (30s, 60s, 120s, 180s)
                    wait = 30 * (attempt + 1) if is_rate_limit else 5 * (2 ** attempt)
                    print(f"\n  [RATE LIMIT/ERR] attempt {attempt+1}, tunggu {wait}s...")
                    time.sleep(wait)
            else:
                raise e
    
    latency = time.time() - start_time
    raw_text = response.text or ""
    
    if hasattr(response, "usage_metadata") and response.usage_metadata:
        prompt_tokens = getattr(response.usage_metadata, "prompt_token_count", 0) or 0
        response_tokens = getattr(response.usage_metadata, "candidates_token_count", 0) or 0
        
    parsed_json = extract_json_from_text(raw_text)
    return parsed_json, raw_text, latency, prompt_tokens, response_tokens


def main():
    parser = argparse.ArgumentParser(description="Run Single-Agent Baseline on Golden Benchmark")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of tickets to evaluate (e.g. 5 or 10)")
    parser.add_argument("--sample-per-dept", type=int, default=None, help="Sample N tickets per department (e.g. 1 or 2)")
    parser.add_argument("--model", type=str, default=None, help="Gemini model name (default from GEMINI_MODEL or gemini-2.5-flash)")
    parser.add_argument("--mock", action="store_true", help="Run with simulated mock responses (no API calls)")
    parser.add_argument("--resume", action="store_true", default=True, help="Resume from existing predictions file")
    parser.add_argument("--no-resume", dest="resume", action="store_false", help="Overwrite existing predictions file")
    # NOTE: --cleaned flag dihapus. Benchmark sudah selalu bersih sejak tahap 02a.
    args = parser.parse_args()

    # Paths
    base_dir = Path(__file__).resolve().parent
    workspace_root = base_dir.parent.parent
    
    # Load .env
    env_path = workspace_root / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    else:
        load_dotenv()
        
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    model_name = args.model or os.getenv("GEMINI_MODEL") or "gemini-2.5-flash"
    
    # Check API key if not mock
    key_manager = None
    client = None
    if not args.mock:
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
                print("  python run_single_agent_baseline.py --mock --limit 10")
                print("="*70 + "\n")
                sys.exit(1)
            if not GENAI_AVAILABLE:
                print("ERROR: Paket google-genai belum terinstal.")
                sys.exit(1)
            client = genai.Client(api_key=api_key)
        
    # Input benchmark (selalu bersih — label noise sudah dihapus di tahap 02a)
    splitting_data_dir = base_dir.parent / "02_data_splitting" / "data"
    data_path = splitting_data_dir / "test_golden_benchmark_500.csv"
    if not data_path.exists():
        print(f"ERROR: Dataset benchmark tidak ditemukan di {data_path}")
        print("Jalankan dulu: python pipeline/02_data_splitting/split_data.py")
        sys.exit(1)

    df = pd.read_csv(data_path)
    print(f"Loaded Golden Benchmark: {len(df)} tiket bersih (label noise telah dibersihkan di tahap 02a)")
    
    # Prompt path
    prompt_path = base_dir.parent / "04_agent_schemas_and_prompts" / "prompts" / "single_agent_baseline.txt"
    if not prompt_path.exists():
        print(f"ERROR: Prompt tidak ditemukan di {prompt_path}")
        sys.exit(1)
    with open(prompt_path, "r", encoding="utf-8") as f:
        system_prompt = f.read()
        
    results_dir = base_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    predictions_csv = results_dir / "baseline_predictions.csv"
    summary_json = results_dir / "baseline_summary.json"
    
    # Existing predictions for resume
    existing_preds = {}
    if args.resume and predictions_csv.exists():
        try:
            df_existing = pd.read_csv(predictions_csv)
            if "FeedbackHeaderID" in df_existing.columns:
                for _, row in df_existing.iterrows():
                    err = str(row.get("ErrorMessage", "")).strip()
                    pred = str(row.get("PredictedDepartmentName", "")).strip()
                    if pred and pred != "Unknown" and (not err or err == "nan"):
                        existing_preds[row["FeedbackHeaderID"]] = row.to_dict()
                print(f"Resuming: Ditemukan {len(existing_preds)} tiket valid tersimpan. Sisa/error akan dievaluasi.")
        except Exception as e:
            print(f"Could not read existing predictions for resume: {e}")
            
    # Apply limit or stratified sampling
    if args.sample_per_dept:
        df_eval = df.groupby("HandledDepartmentName").head(args.sample_per_dept)
        print(f"Evaluating stratified subset: {len(df_eval)} tickets ({args.sample_per_dept} per department)")
    elif args.limit:
        df_eval = df.head(args.limit)
        print(f"Evaluating subset: {len(df_eval)} tickets (limit={args.limit})")
    else:
        df_eval = df
        print(f"Evaluating full benchmark: {len(df_eval)} tickets")
        
    print(f"Execution mode: {'MOCK SIMULATION' if args.mock else f'LIVE GEMINI API ({model_name})'}")
    
    results = list(existing_preds.values())
    processed_ids = set(existing_preds.keys())
    
    start_total_time = time.time()
    
    for idx, row in tqdm(df_eval.iterrows(), total=len(df_eval), desc="Evaluating Baseline"):
        ticket_id = str(row["FeedbackHeaderID"])
        if ticket_id in processed_ids:
            continue
            
        initial_dept = str(row.get("InitialDepartmentName", "")).strip()
        handled_dept = str(row.get("HandledDepartmentName", "")).strip()
        is_rerouted = int(row.get("IsRerouted", 0))
        
        ticket_payload = {
            "SubjectCategory": row.get("SubjectCategory", ""),
            "InitialDepartmentName": initial_dept,
            "CleanedComplaint": row.get("CleanedComplaint", "")
        }
        
        parsed_json = {}
        raw_text = ""
        latency = 0.0
        prompt_tokens = 0
        resp_tokens = 0
        error_msg = ""
        
        if args.mock:
            time.sleep(0.02)  # simulate fast latency
            parsed_json = simulate_mock_prediction(row)
            raw_text = json.dumps(parsed_json, indent=2)
            latency = 0.05
            prompt_tokens = 240
            resp_tokens = 110
        else:
            try:
                active_client = key_manager.get_random_client() if key_manager else client
                parsed_json, raw_text, latency, prompt_tokens, resp_tokens = call_gemini_baseline(
                    client=active_client,
                    model_name=model_name,
                    system_prompt=system_prompt,
                    ticket_payload=ticket_payload,
                    key_manager=key_manager
                )
                time.sleep(2.5)  # Dengan 3 keys acak, 2.5s pacing = ~8 RPM per key (aman di bawah 15 RPM)
            except Exception as e:
                error_msg = str(e)
                print(f"\n[Warning] Error processing ticket {ticket_id}: {error_msg}")
                time.sleep(10.0)
                
        is_valid_json = bool(parsed_json and isinstance(parsed_json, dict))
        
        pred_dept_raw = parsed_json.get("target_department_name") or parsed_json.get("target_department") or ""
        pred_dept_canonical = normalize_dept_name(pred_dept_raw)
        pred_dept_code = DEPT_NAME_TO_CODE.get(pred_dept_canonical.lower(), parsed_json.get("target_department", ""))
        
        is_correct = (pred_dept_canonical.lower().strip() == handled_dept.lower().strip())
        
        # Did it correctly fix a rerouted ticket?
        was_reroute_fixed = False
        if is_rerouted == 1:
            if is_correct and pred_dept_canonical.lower().strip() != initial_dept.lower().strip():
                was_reroute_fixed = True
                
        record = {
            "FeedbackHeaderID": ticket_id,
            "CreatedDate": row.get("CreatedDate", ""),
            "SubjectCategory": row.get("SubjectCategory", ""),
            "InitialDepartmentName": initial_dept,
            "HandledDepartmentName": handled_dept,
            "IsRerouted": is_rerouted,
            "PredictedDepartmentCode": pred_dept_code,
            "PredictedDepartmentName": pred_dept_canonical,
            "PredictedCategory": parsed_json.get("problem_category", ""),
            "UrgencyLevel": parsed_json.get("urgency_level", ""),
            "FacilityItem": parsed_json.get("facility_item", ""),
            "LocationContext": parsed_json.get("location_context", ""),
            "DraftReply": parsed_json.get("draft_reply", ""),
            "IsCorrect": int(is_correct),
            "WasRerouteFixed": int(was_reroute_fixed),
            "IsValidJson": int(is_valid_json),
            "LatencySeconds": round(latency, 3),
            "PromptTokens": prompt_tokens,
            "ResponseTokens": resp_tokens,
            "TotalTokens": prompt_tokens + resp_tokens,
            "ErrorMessage": error_msg,
            "RawOutput": raw_text
        }
        
        results.append(record)
        processed_ids.add(ticket_id)
        
        # Incremental save every 10 tickets
        if len(results) % 10 == 0 or len(results) == len(df_eval):
            df_out = pd.DataFrame(results)
            df_out.to_csv(predictions_csv, index=False, encoding="utf-8")
            
    # Final save
    df_final = pd.DataFrame(results)
    df_final.to_csv(predictions_csv, index=False, encoding="utf-8")
    
    # Compute Summary Metrics
    total = len(df_final)
    correct = df_final["IsCorrect"].sum()
    overall_acc = (correct / total * 100) if total > 0 else 0.0
    valid_json_count = df_final["IsValidJson"].sum()
    json_validity_rate = (valid_json_count / total * 100) if total > 0 else 0.0
    
    # Rerouted tickets subset
    df_rerouted = df_final[df_final["IsRerouted"] == 1]
    reroute_total = len(df_rerouted)
    reroute_acc = (df_rerouted["IsCorrect"].sum() / reroute_total * 100) if reroute_total > 0 else 0.0
    reroute_fixed = df_rerouted["WasRerouteFixed"].sum()
    
    # Per department breakdown
    dept_metrics = {}
    for dept_name in DEPT_CODE_TO_NAME.values():
        df_dept = df_final[df_final["HandledDepartmentName"] == dept_name]
        d_total = len(df_dept)
        d_correct = df_dept["IsCorrect"].sum() if d_total > 0 else 0
        d_acc = (d_correct / d_total * 100) if d_total > 0 else 0.0
        dept_metrics[dept_name] = {
            "total_tickets": int(d_total),
            "correct_predictions": int(d_correct),
            "accuracy_percent": round(d_acc, 2)
        }
        
    summary = {
        "timestamp": datetime.now().isoformat(),
        "model_used": "MOCK" if args.mock else model_name,
        "total_evaluated": int(total),
        "overall_accuracy_percent": round(overall_acc, 2),
        "json_validity_rate_percent": round(json_validity_rate, 2),
        "average_latency_seconds": round(df_final["LatencySeconds"].mean(), 3),
        "total_tokens_consumed": int(df_final["TotalTokens"].sum()),
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
    print("BASELINE EVALUATION SUMMARY:")
    print("="*70)
    print(f"Total Evaluated: {total}")
    print(f"Overall Accuracy: {overall_acc:.2f}% ({correct}/{total})")
    print(f"JSON Validity Rate: {json_validity_rate:.2f}% ({valid_json_count}/{total})")
    print(f"Avg Latency: {summary['average_latency_seconds']} s/ticket")
    print(f"Avg Tokens: {summary['average_tokens_per_ticket']} tokens/ticket")
    print(f"Reroute Accuracy: {reroute_acc:.2f}% (Corrected: {reroute_fixed}/{reroute_total})")
    print("\nPer-Department Accuracy:")
    for dept, m in dept_metrics.items():
        print(f"  - {dept:25s}: {m['accuracy_percent']:6.2f}% ({m['correct_predictions']}/{m['total_tickets']})")
    print("="*70)
    print(f"Predictions saved to : {predictions_csv}")
    print(f"Summary saved to     : {summary_json}")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()

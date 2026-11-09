"""
Pipeline Skenario 3: Single-Agent LLM + RAG Handbook (Fair Ablation Control)
Mengevaluasi model Single-Agent dengan injeksi Top-2 Chunk Handbook RAG pada Golden Benchmark (N=500)
secara paralel terukur di atas 5 API Key.
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

from google.genai import types

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.api_key_manager import ApiKeyManager
try:
    from pipeline.clario_client import call_clario_completion
except ImportError:
    call_clario_completion = None

DEPT_CODE_TO_NAME = {
    "ED": "Estate Department",
    "OP": "Operations",
    "FN": "Finance",
    "MR": "Marketing",
    "SO": "Student Support Office",
}
DEPT_NAME_TO_CODE = {v.lower(): k for k, v in DEPT_CODE_TO_NAME.items()}


def normalize_dept_name(val: str) -> str:
    if not val or not isinstance(val, str):
        return "Unknown"
    val_clean = val.strip()
    val_upper = val_clean.upper()
    if val_upper in DEPT_CODE_TO_NAME:
        return DEPT_CODE_TO_NAME[val_upper]
    val_lower = val_clean.lower()
    for code, name in DEPT_CODE_TO_NAME.items():
        if val_lower == name.lower() or code.lower() in val_lower or val_lower in name.lower():
            return name
    return val_clean


def extract_json_from_text(text: str) -> dict:
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
    start, end = text_clean.find("{"), text_clean.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text_clean[start:end + 1])
        except json.JSONDecodeError:
            pass
    return {}


class HandbookRetriever:
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


def call_gemini_single_rag(model_name: str, system_prompt: str, ticket_payload: dict, chunks_context: str, key_manager: ApiKeyManager):
    user_content = (
        f"DATA TIKET PENGADUAN PENGHUNI:\n"
        f"- Isi Pesan Keluhan: {ticket_payload.get('CleanedComplaint', '-')}\n\n"
        f"POTONGAN ATURAN HANDBOOK ASRAMA (REFERENSI TAMBAHAN RAG):\n"
        f"{chunks_context if chunks_context else '(Tidak ada pasal spesifik terkait)'}\n\n"
        f"CATATAN PENTING: Gunakan potongan Handbook di atas HANYA sebagai referensi pendukung kebijakan. "
        f"Untuk penentuan `target_department`, prioritaskan inti keluhan dan direktori departemen resmi.\n"
        f"Silakan berikan respons JSON sesuai format panduan."
    )

    clario_key = os.getenv("CLARIO_API_KEY", "").strip()
    if call_clario_completion and clario_key and "YOUR_API_KEY" not in clario_key:
        clario_model = os.getenv("CLARIO_MODEL", "clario/gemini-3.7-flash")
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        return call_clario_completion(
            messages=messages,
            model=clario_model,
            response_format={"type": "json_object"}
        )

    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        temperature=0.1,
        response_mime_type="application/json"
    )

    response = None
    latency = 0.0
    max_retries = 8
    for attempt in range(max_retries):
        key_idx = None
        try:
            key_idx, curr_client = key_manager.acquire_client_with_index()
            t0 = time.time()
            response = curr_client.models.generate_content(
                model=model_name,
                contents=user_content,
                config=config
            )
            latency = time.time() - t0
            break
        except Exception as e:
            err_str = str(e).lower()
            is_invalid = any(k in err_str for k in ["api_key_invalid", "api key not valid", "400", "403", "permission_denied", "unauthenticated", "401"])
            if is_invalid:
                key_manager.mark_invalid(key_idx)
                continue
            is_rate = any(k in err_str for k in ["429", "quota", "rate", "resource_exhausted", "503", "502", "demand", "disconnected"])
            if attempt < max_retries - 1 and is_rate:
                if "429" in err_str or "quota" in err_str or "resource_exhausted" in err_str:
                    key_manager.rotate(wait_sec=1, idx=key_idx)
                else:
                    time.sleep(6 * (attempt + 1))
            else:
                raise e

    raw_text = response.text or ""
    usage = getattr(response, "usage_metadata", None)
    prompt_tokens = (getattr(usage, "prompt_token_count", 0) or 0) if usage else 0
    response_tokens = (getattr(usage, "candidates_token_count", 0) or 0) if usage else 0
    return extract_json_from_text(raw_text), raw_text, latency, prompt_tokens, response_tokens


def main():
    parser = argparse.ArgumentParser(description="Run Skenario 3: Single-Agent + RAG on Golden Benchmark")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--model", type=str, default="gemini-3.5-flash-lite")
    parser.add_argument("--resume", action="store_true", default=True)
    parser.add_argument("--no-resume", dest="resume", action="store_false")
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent
    workspace_root = base_dir.parent.parent
    env_path = workspace_root / ".env"
    load_dotenv(dotenv_path=env_path, override=True)

    clario_key = os.getenv("CLARIO_API_KEY", "").strip()
    is_clario = bool(clario_key and "YOUR_API_KEY" not in clario_key)
    model_name = os.getenv("CLARIO_MODEL", "clario/gemini-3.7-flash") if is_clario else args.model
    key_manager = None
    if not is_clario:
        key_manager = ApiKeyManager(env_path=str(env_path), min_interval_per_key=4.15)

    data_path = base_dir.parent / "02_data_splitting" / "data" / "test_golden_benchmark_500.csv"
    df = pd.read_csv(data_path)

    chunks_path = base_dir.parent / "03_handbook_rag_prep" / "data" / "handbook_chunks.json"
    retriever = HandbookRetriever(chunks_path)

    prompt_path = base_dir.parent / "04_agent_schemas_and_prompts" / "prompts" / "single_agent_baseline.txt"
    with open(prompt_path, "r", encoding="utf-8") as f:
        system_prompt = f.read()

    results_dir = base_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    predictions_csv = results_dir / "single_agent_rag_predictions.csv"
    summary_json = results_dir / "single_agent_rag_summary.json"

    existing_preds = {}
    if args.resume and predictions_csv.exists():
        df_existing = pd.read_csv(predictions_csv)
        for _, row in df_existing.iterrows():
            err = str(row.get("ErrorMessage", "")).strip()
            pred = str(row.get("PredictedDepartmentName", "")).strip()
            if pred and pred != "Unknown" and (not err or err == "nan"):
                existing_preds[str(row["FeedbackHeaderID"])] = row.to_dict()
        print(f"[Skenario 3] Resume: {len(existing_preds)} tiket valid dipertahankan, {len(df) - len(existing_preds)} tiket dievaluasi.")

    df_eval = df.head(args.limit) if args.limit else df
    results = list(existing_preds.values())
    processed_ids = set(existing_preds.keys())
    pending_rows = [row for _, row in df_eval.iterrows() if str(row["FeedbackHeaderID"]) not in processed_ids]

    res_lock = threading.Lock()

    def eval_one(row):
        ticket_id = str(row["FeedbackHeaderID"])
        initial_dept = str(row.get("InitialDepartmentName", "")).strip()
        handled_dept = str(row.get("HandledDepartmentName", "")).strip()
        complaint = str(row.get("CleanedComplaint", "")).strip()
        is_rerouted = int(row.get("IsRerouted", 0))

        top_chunks = retriever.retrieve(complaint, top_k=2)
        chunks_context = "\n\n".join([f"[{c['section_title']} (Hal. {c['page_start']})]\n{c['text_content']}" for c in top_chunks])

        ticket_payload = {
            "SubjectCategory": row.get("SubjectCategory", ""),
            "InitialDepartmentName": initial_dept,
            "CleanedComplaint": complaint,
        }

        parsed_json, raw_text, latency, prompt_tokens, resp_tokens, error_msg = {}, "", 0.0, 0, 0, ""
        try:
            parsed_json, raw_text, latency, prompt_tokens, resp_tokens = call_gemini_single_rag(
                model_name=model_name,
                system_prompt=system_prompt,
                ticket_payload=ticket_payload,
                chunks_context=chunks_context,
                key_manager=key_manager,
            )
        except Exception as e:
            error_msg = str(e)
            print(f"\n[Warning] Error tiket {ticket_id}: {error_msg}")

        is_valid_json = bool(parsed_json and isinstance(parsed_json, dict))
        pred_dept_raw = parsed_json.get("target_department_name") or parsed_json.get("target_department") or ""
        pred_dept_canonical = normalize_dept_name(pred_dept_raw)
        pred_dept_code = DEPT_NAME_TO_CODE.get(pred_dept_canonical.lower(), parsed_json.get("target_department", ""))
        is_correct = (pred_dept_canonical.lower().strip() == handled_dept.lower().strip())
        was_reroute_fixed = (is_rerouted == 1 and is_correct and pred_dept_canonical.lower().strip() != initial_dept.lower().strip())

        rec = {
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
            "ConfidenceScore": parsed_json.get("confidence_score", None),
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
        }
        with res_lock:
            results.append(rec)
            if len(results) % 20 == 0:
                pd.DataFrame(results).to_csv(predictions_csv, index=False, encoding="utf-8")

    print(f"[Skenario 3] Mengevaluasi {len(pending_rows)} tiket dengan `{model_name}` (5 workers paralel)...")
    with ThreadPoolExecutor(max_workers=10) as ex:
        futures = [ex.submit(eval_one, r) for r in pending_rows]
        for fut in tqdm(as_completed(futures), total=len(futures), desc="Evaluating Skenario 3 (Single+RAG)"):
            fut.result()

    # Urutkan sesuai urutan asli test_golden_benchmark_500.csv
    order_map = {str(tid): i for i, tid in enumerate(df_eval["FeedbackHeaderID"])}
    results.sort(key=lambda r: order_map.get(str(r["FeedbackHeaderID"]), 999999))

    df_final = pd.DataFrame(results)
    df_final.to_csv(predictions_csv, index=False, encoding="utf-8")

    total = len(df_final)
    correct = int(df_final["IsCorrect"].sum())
    overall_acc = (correct / total * 100) if total > 0 else 0.0
    valid_json_count = int(df_final["IsValidJson"].sum())
    json_validity_rate = (valid_json_count / total * 100) if total > 0 else 0.0

    dept_metrics = {}
    for dept_name in DEPT_CODE_TO_NAME.values():
        df_dept = df_final[df_final["HandledDepartmentName"] == dept_name]
        d_total = len(df_dept)
        d_correct = int(df_dept["IsCorrect"].sum()) if d_total > 0 else 0
        dept_metrics[dept_name] = {
            "total_tickets": int(d_total),
            "correct_predictions": int(d_correct),
            "accuracy_percent": round((d_correct / d_total * 100) if d_total > 0 else 0.0, 2)
        }

    summary = {
        "timestamp": datetime.now().isoformat(),
        "scenario": "Skenario 3: Single-Agent LLM + RAG Handbook (Ablation Control)",
        "model_used": model_name,
        "total_evaluated": int(total),
        "overall_accuracy_percent": round(overall_acc, 2),
        "json_validity_rate_percent": round(json_validity_rate, 2),
        "average_latency_seconds": round(float(df_final["LatencySeconds"].mean()), 3),
        "total_tokens_consumed": int(df_final["TotalTokens"].sum()),
        "average_tokens_per_ticket": round(float(df_final["TotalTokens"].mean()), 1),
        "per_department_metrics": dept_metrics,
    }
    with open(summary_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print("=" * 70)
    print(f"SKENARIO 3 (SINGLE-AGENT + RAG) SUMMARY: {overall_acc:.2f}% ({correct}/{total})")
    for dept, m in dept_metrics.items():
        print(f"  - {dept:25s}: {m['accuracy_percent']:6.2f}% ({m['correct_predictions']}/{m['total_tickets']})")
    print("=" * 70)


if __name__ == "__main__":
    main()

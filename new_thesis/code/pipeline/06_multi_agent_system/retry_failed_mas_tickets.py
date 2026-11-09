"""
Script Perbaikan & Upgrade Evaluasi MAS (Parallel 5-Key Paced)
Mendukung:
1. Retry tiket yang gagal karena kuota/error.
2. Re-evaluasi tiket yang terdampak bug pre-upgrade (Agen 1 -> Agen 2 RAG drop & taxonomy boundary).
"""

import os
import sys
import time
import json
import argparse
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import pandas as pd
from tqdm import tqdm
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = BASE_DIR.parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from pipeline.api_key_manager import ApiKeyManager
from run_multi_agent_system import (
    HandbookRetriever,
    call_agent1_reception,
    call_agent2_triage,
    call_agent3_response,
    normalize_dept_name,
    DEPT_CODE_TO_NAME
)


def main():
    parser = argparse.ArgumentParser(description="Retry / Upgrade MAS Tickets")
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--upgrade-recheck", action="store_true", default=False,
                        help="DO NOT use for reported results: it re-runs only tickets that disagree with the portal department.")
    parser.add_argument("--model", type=str, default="gemini-3.5-flash-lite")
    args = parser.parse_args()

    results_dir = BASE_DIR / "results"
    pred_csv = results_dir / "mas_predictions.csv"
    summary_json = results_dir / "mas_summary.json"

    df = pd.read_csv(pred_csv)
    is_failed = (
        (df["ErrorMessage"].notna() & (df["ErrorMessage"].astype(str).str.strip() != "") & (df["ErrorMessage"].astype(str) != "nan"))
        | (df["FunctionCallSuccess"] == 0)
        | (df["PredictedDepartmentName"] == "Unknown")
    )
    if args.upgrade_recheck:
        # Tiket di mana prediksi lama menyimpang dari departemen awal tanpa guardrail taksonomi / kehilangan konteks Agen 1
        is_diverged = df["PredictedDepartmentName"].astype(str).str.lower().str.strip() != df["InitialDepartmentName"].astype(str).str.lower().str.strip()
        target_mask = is_failed | is_diverged
    else:
        target_mask = is_failed

    failed_df = df[target_mask]

    print("=" * 70)
    print(f"STATUS TIKET EVALUASI MULTI-AGENT SYSTEM (MAS - UPGRADED)")
    print("=" * 70)
    print(f"Total Tiket Terdaftar     : {len(df)}")
    print(f"Tiket Target Re-evaluasi  : {len(failed_df)}")
    print("=" * 70)

    if args.check_only or len(failed_df) == 0:
        return

    load_dotenv(WORKSPACE_ROOT / ".env", override=True)
    km = ApiKeyManager(env_path=str(WORKSPACE_ROOT / ".env"), min_interval_per_key=4.15)
    model_name = args.model

    chunks_path = BASE_DIR / "data" / "handbook_chunks.json"
    retriever = HandbookRetriever(chunks_path)

    prompts_dir = BASE_DIR.parent / "04_agent_schemas_and_prompts" / "prompts"
    with open(prompts_dir / "agent1_reception_rag.txt", "r", encoding="utf-8") as f:
        p1 = f.read()
    with open(prompts_dir / "agent2_triage_specialist.txt", "r", encoding="utf-8") as f:
        p2 = f.read()
    with open(prompts_dir / "agent3_response_generator.txt", "r", encoding="utf-8") as f:
        p3 = f.read()

    schema_path = BASE_DIR.parent / "04_agent_schemas_and_prompts" / "schemas" / "triage_tool_schema.json"
    with open(schema_path, "r", encoding="utf-8") as f:
        tool_schema = json.load(f)

    data_benchmark = pd.read_csv(WORKSPACE_ROOT / "pipeline" / "02_data_splitting" / "data" / "test_golden_benchmark_500.csv")
    complaint_map = dict(zip(data_benchmark["FeedbackHeaderID"].astype(str), data_benchmark["CleanedComplaint"].astype(str)))

    df_lock = threading.Lock()
    fixed_count = 0

    def process_one(idx):
        nonlocal fixed_count
        row = df.loc[idx]
        tid = str(row["FeedbackHeaderID"])
        complaint = complaint_map.get(tid, str(row.get("CleanedComplaint", "")).strip())
        initial_dept = str(row.get("InitialDepartmentName", "")).strip()
        handled_dept = str(row.get("HandledDepartmentName", "")).strip()
        subject_category = str(row.get("SubjectCategory", "")).strip()
        is_rerouted = int(row.get("IsRerouted", 0))

        top_chunks = retriever.retrieve(complaint, top_k=2, min_score=0.08)
        chunks_context = "\n\n".join([f"[{c['section_title']} (Hal. {c['page_start']})]\n{c['text_content']}" for c in top_chunks])
        a1_json, lat1, tok1 = call_agent1_reception(
            None, model_name, p1, complaint, chunks_context, key_manager=km
        )

        a1_summary = a1_json.get("complaint_summary") or a1_json.get("direct_answer") or complaint
        a1_policy = a1_json.get("extracted_handbook_policy") or a1_json.get("direct_answer") or ""
        fn_name, tool_args, lat2, tok2 = call_agent2_triage(
            None, model_name, p2, tool_schema, complaint, a1_summary, "",
            agent1_policy=a1_policy, key_manager=km
        )

        fn_success = int(bool(tool_args and "target_department" in tool_args))
        pred_dept_code = tool_args.get("target_department", "")
        pred_dept_name = normalize_dept_name(tool_args.get("target_department_name") or pred_dept_code)
        pred_category = tool_args.get("problem_category", "")
        urgency = tool_args.get("urgency_level", "")
        facility_item = tool_args.get("facility_item", "")
        confidence = float(tool_args.get("confidence_score", 0.0))
        reasoning = tool_args.get("reasoning_summary", "")

        a3_json, lat3, tok3 = call_agent3_response(None, model_name, p3, complaint, tool_args, key_manager=km)
        official_resp = a3_json.get("official_response_text", "")
        tot_tokens = tok1 + tok2 + tok3

        is_correct = int(pred_dept_name.lower().strip() == handled_dept.lower().strip())
        was_reroute_fixed = int(is_rerouted == 1 and is_correct and pred_dept_name.lower().strip() != initial_dept.lower().strip())

        with df_lock:
            df.loc[idx, "PredictedDepartmentCode"] = pred_dept_code
            df.loc[idx, "PredictedDepartmentName"] = pred_dept_name
            df.loc[idx, "PredictedCategory"] = pred_category
            df.loc[idx, "UrgencyLevel"] = urgency
            df.loc[idx, "FacilityItem"] = facility_item
            df.loc[idx, "ConfidenceScore"] = round(confidence, 3)
            df.loc[idx, "RoutingReason"] = reasoning
            df.loc[idx, "OfficialStaffReply"] = official_resp
            df.loc[idx, "IsCorrect"] = is_correct
            df.loc[idx, "WasRerouteFixed"] = was_reroute_fixed
            df.loc[idx, "FunctionCallSuccess"] = fn_success
            df.loc[idx, "Latency_Agent1"] = round(lat1, 3)
            df.loc[idx, "Latency_Agent2"] = round(lat2, 3)
            df.loc[idx, "Latency_Agent3"] = round(lat3, 3)
            df.loc[idx, "TotalLatencySeconds"] = round(lat1 + lat2 + lat3, 3)
            df.loc[idx, "TotalTokens"] = tot_tokens
            df.loc[idx, "ErrorMessage"] = ""
            fixed_count += 1
            if fixed_count % 5 == 0:
                df.to_csv(pred_csv, index=False, encoding="utf-8")

    print(f"\nMemulai evaluasi {len(failed_df)} tiket MAS dengan arsitektur Upgraded (`{model_name}`, 5 workers)...")
    with ThreadPoolExecutor(max_workers=5) as ex:
        futures = {ex.submit(process_one, idx): idx for idx in failed_df.index}
        for fut in tqdm(as_completed(futures), total=len(futures), desc="Evaluating Upgraded MAS"):
            try:
                fut.result()
            except Exception as e:
                print(f"\n[Warning] Error tiket index {futures[fut]}: {e}")

    df.to_csv(pred_csv, index=False, encoding="utf-8")

    total = len(df)
    correct = int(df["IsCorrect"].sum())
    overall_acc = (correct / total * 100) if total > 0 else 0.0
    fn_call_rate = (df["FunctionCallSuccess"].sum() / total * 100) if total > 0 else 0.0

    dept_metrics = {}
    for dept_code, dept_name in DEPT_CODE_TO_NAME.items():
        d_df = df[df["HandledDepartmentName"] == dept_name]
        d_total = len(d_df)
        d_correct = int(d_df["IsCorrect"].sum()) if d_total > 0 else 0
        dept_metrics[dept_name] = {
            "total_tickets": int(d_total),
            "correct_predictions": int(d_correct),
            "accuracy_percent": round((d_correct / d_total * 100) if d_total > 0 else 0.0, 2)
        }

    summary_data = {
        "timestamp": datetime.now().isoformat(),
        "architecture": "Multi-Agent System (3-Agent Pipeline with Distilled RAG & Native Function Calling)",
        "model_used": model_name,
        "total_evaluated": int(total),
        "overall_accuracy_percent": round(float(overall_acc), 2),
        "function_call_success_rate": round(float(fn_call_rate), 2),
        "average_latency_seconds": round(float(df["TotalLatencySeconds"].mean()), 3),
        "average_tokens_per_ticket": round(float(df["TotalTokens"].mean()), 1),
        "per_department_metrics": dept_metrics
    }
    with open(summary_json, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)

    print(f"MAS Upgraded Overall Accuracy (N={total}): {overall_acc:.2f}% ({correct}/{total})")
    for dept, m in dept_metrics.items():
        print(f"  - {dept:25s}: {m['accuracy_percent']:6.2f}% ({m['correct_predictions']}/{m['total_tickets']})")


if __name__ == "__main__":
    main()

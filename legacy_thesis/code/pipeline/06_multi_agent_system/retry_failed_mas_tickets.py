"""
Script Perbaikan Otomatis: Retry Failed Tickets di MAS
======================================================
Script ini secara cerdas:
1. Mendeteksi tiket yang gagal (misal kena 429 RESOURCE_EXHAUSTED / Unknown) di mas_predictions.csv.
2. Hanya mengeksekusi ulang tiket-tiket yang gagal tersebut (tanpa mengulang tiket yang sudah sukses).
3. Memperbarui mas_predictions.csv dan mas_summary.json secara bertahap.
4. Otomatis memicu regenerasi grafik dan tabel komparasi Bab 4 (Stage 07).

Cara pakai:
    python pipeline/06_multi_agent_system/retry_failed_mas_tickets.py
    python pipeline/06_multi_agent_system/retry_failed_mas_tickets.py --check-only
"""

import os
import sys
import time
import json
import argparse
from datetime import datetime
from pathlib import Path

# Force UTF-8 on Windows terminal
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
import pandas as pd
from tqdm import tqdm
from dotenv import load_dotenv

# Setup path
BASE_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = BASE_DIR.parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

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
    parser = argparse.ArgumentParser(description="Retry Failed MAS Tickets")
    parser.add_argument("--check-only", action="store_true", help="Hanya cek tiket yang gagal tanpa eksekusi")
    parser.add_argument("--model", type=str, default=None, help="Model name (default dari .env atau gemini-3.5-flash-lite)")
    args = parser.parse_args()

    results_dir = BASE_DIR / "results"
    pred_csv = results_dir / "mas_predictions.csv"
    summary_json = results_dir / "mas_summary.json"

    if not pred_csv.exists():
        print(f"[ERROR] File prediksi tidak ditemukan di: {pred_csv}")
        sys.exit(1)

    df = pd.read_csv(pred_csv)
    # Tiket gagal adalah yang memiliki ErrorMessage atau FunctionCallSuccess == 0 atau PredictedDepartmentName == 'Unknown'
    is_failed = (df["ErrorMessage"].notna() & (df["ErrorMessage"] != "")) | (df["FunctionCallSuccess"] == 0) | (df["PredictedDepartmentName"] == "Unknown")
    failed_df = df[is_failed]

    print("="*70)
    print(f"📊 STATUS TIKET EVALUASI MULTI-AGENT SYSTEM (MAS)")
    print("="*70)
    print(f"Total Tiket Terdaftar : {len(df)}")
    print(f"Tiket Berhasil Sukses : {len(df) - len(failed_df)}")
    print(f"Tiket Gagal / Quota   : {len(failed_df)}")
    print("\nSebaran Tiket Gagal per Departemen:")
    for dept, count in failed_df["HandledDepartmentName"].value_counts().items():
        print(f"  - {dept:25}: {count} tiket")
    print("="*70)

    if args.check_only or len(failed_df) == 0:
        if len(failed_df) == 0:
            print("🎉 Semua tiket sudah 100% sukses diproses!")
        return

    # Inisialisasi API Key Manager
    load_dotenv(WORKSPACE_ROOT / ".env")
    km = ApiKeyManager(env_path=str(WORKSPACE_ROOT / ".env"))
    model_name = args.model or os.getenv("GEMINI_MODEL") or "gemini-3.5-flash-lite"

    # Load Handbook & Prompts
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

    print(f"\n🚀 Memulai eksekusi perbaikan {len(failed_df)} tiket dengan model `{model_name}`...")
    print("Tiket diperbarui langsung ke CSV setelah setiap request sukses.\n")

    fixed_count = 0
    # Map index
    for idx in tqdm(failed_df.index, desc="Retrying Failed Tickets"):
        row = df.loc[idx]
        complaint = str(row.get("CleanedComplaint", "")).strip()
        if not complaint and "Complaint" in row:
            complaint = str(row.get("Complaint", "")).strip()

        # Jika kolom CleanedComplaint tidak ada di CSV hasil, ambil dari test_golden_benchmark_500.csv
        if not complaint or complaint == "nan":
            data_benchmark = pd.read_csv(WORKSPACE_ROOT / "pipeline" / "02_data_splitting" / "data" / "test_golden_benchmark_500.csv")
            b_row = data_benchmark[data_benchmark["FeedbackHeaderID"] == row["FeedbackHeaderID"]]
            if len(b_row) > 0:
                complaint = str(b_row.iloc[0].get("CleanedComplaint", "")).strip()

        initial_dept = str(row.get("InitialDepartmentName", "")).strip()
        handled_dept = str(row.get("HandledDepartmentName", "")).strip()
        subject_category = str(row.get("SubjectCategory", "")).strip()
        is_rerouted = int(row.get("IsRerouted", 0))

        try:
            # 1. RAG & Agen 1
            top_chunks = retriever.retrieve(complaint, top_k=2)
            chunks_context = "\n\n".join([f"[{c['section_title']} (Hal. {c['page_start']})]\n{c['text_content']}" for c in top_chunks])
            a1_json, lat1, tok1 = call_agent1_reception(None, model_name, p1, complaint, chunks_context, subject_category, key_manager=km)
            time.sleep(1.5)

            # 2. Agen 2 Triage with Function Calling
            a1_summary = a1_json.get("complaint_summary") or complaint
            fn_name, tool_args, lat2, tok2 = call_agent2_triage(None, model_name, p2, tool_schema, complaint, a1_summary, initial_dept, subject_category, key_manager=km)
            time.sleep(1.5)

            fn_success = int(bool(tool_args and "target_department" in tool_args))
            pred_dept_code = tool_args.get("target_department", "")
            pred_dept_name = normalize_dept_name(tool_args.get("target_department_name") or pred_dept_code)
            pred_category = tool_args.get("problem_category", "")
            urgency = tool_args.get("urgency_level", "")
            facility_item = tool_args.get("facility_item", "")
            confidence = float(tool_args.get("confidence_score", 0.0))
            reasoning = tool_args.get("reasoning_summary", "")

            # 3. Agen 3 Response Generator
            a3_json, lat3, tok3 = call_agent3_response(None, model_name, p3, complaint, tool_args, key_manager=km)
            official_resp = a3_json.get("official_response_text", "")
            tot_tokens = tok1 + tok2 + tok3
            err_msg = ""
            time.sleep(2.0)

            is_correct = int(pred_dept_name.lower().strip() == handled_dept.lower().strip())
            was_reroute_fixed = 0
            if is_rerouted == 1 and is_correct and pred_dept_name.lower().strip() != initial_dept.lower().strip():
                was_reroute_fixed = 1

            # Update row in dataframe
            df.loc[idx, "PredictedDepartmentCode"] = pred_dept_code
            df.loc[idx, "PredictedDepartmentName"] = pred_dept_name
            df.loc[idx, "PredictedCategory"] = pred_category
            df.loc[idx, "UrgencyLevel"] = urgency
            df.loc[idx, "FacilityItem"] = facility_item
            df.loc[idx, "ConfidenceScore"] = confidence
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
            # Save incremental
            df.to_csv(pred_csv, index=False, encoding="utf-8")

        except Exception as e:
            print(f"\n[Warning] Masih terjadi error pada tiket {row['FeedbackHeaderID']}: {e}")
            time.sleep(10.0)

    # Simpan final
    df.to_csv(pred_csv, index=False, encoding="utf-8")
    print(f"\n✅ Berhasil memperbaiki {fixed_count}/{len(failed_df)} tiket!")

    # Update summary JSON
    total = len(df)
    correct = df["IsCorrect"].sum()
    overall_acc = (correct / total * 100) if total > 0 else 0.0
    fn_call_rate = (df["FunctionCallSuccess"].sum() / total * 100) if total > 0 else 0.0

    dept_metrics = {}
    for dept_code, dept_name in DEPT_CODE_TO_NAME.items():
        d_df = df[df["HandledDepartmentName"] == dept_name]
        d_total = len(d_df)
        d_correct = d_df["IsCorrect"].sum() if d_total > 0 else 0
        d_acc = (d_correct / d_total * 100) if d_total > 0 else 0.0
        dept_metrics[dept_name] = {
            "total_tickets": int(d_total),
            "correct_predictions": int(d_correct),
            "accuracy_percent": round(d_acc, 2)
        }

    summary_data = {
        "timestamp": datetime.now().isoformat(),
        "model_used": model_name,
        "total_evaluated": total,
        "overall_accuracy_percent": round(overall_acc, 2),
        "function_call_success_rate_percent": round(fn_call_rate, 2),
        "per_department_metrics": dept_metrics
    }
    with open(summary_json, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)

    # Regenerasi Bab 4
    print("\n🔄 Memperbarui Tabel Komparasi & Gambar Grafik Bab 4 (Stage 07)...")
    comp_script = BASE_DIR.parent / "07_comparative_evaluation" / "compare_results.py"
    import subprocess
    subprocess.run([sys.executable, str(comp_script)], cwd=str(WORKSPACE_ROOT))
    print("🎉 Pembaruan Bab 4 selesai!")


if __name__ == "__main__":
    main()

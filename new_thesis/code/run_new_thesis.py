"""
Master Runner: Eksekusi Penuh 4 Skenario Eksperimen Tesis S2 (new_thesis)
========================================================================
Menjalankan secara berurutan:
1. Skenario 1: Classical Supervised ML (TF-IDF + Logistic Regression)
2. Skenario 4 Retry: Menyelesaikan 91 tiket SO pada Modular Chained MAS hingga 500/500
3. Skenario 3: Single-Agent LLM + RAG Handbook (500 tiket)
4. Stage 07: Evaluasi Komparatif 4 Skenario, Error Cascade Analysis, & Grafik Bab 4
"""

import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PIPELINE_DIR = BASE_DIR / "pipeline"


def run_step(title: str, script_rel: str):
    print("\n" + "=" * 80)
    print(f"[MASTER RUNNER] Memulai: {title}")
    print("=" * 80, flush=True)
    script_path = PIPELINE_DIR / script_rel
    res = subprocess.run([sys.executable, str(script_path)], cwd=str(BASE_DIR))
    if res.returncode != 0:
        raise RuntimeError(f"Step gagal ({res.returncode}): {script_rel}")


def main():
    run_step("Skenario 1 — Classical ML Baseline", "00_classical_ml_baseline/run_classical_ml.py")
    run_step("Skenario 4 — Retry 91 Tiket MAS (Menuju 500/500)", "06_multi_agent_system/retry_failed_mas_tickets.py")
    run_step("Skenario 3 — Single-Agent + RAG Handbook (500 Tiket)", "05b_single_agent_rag/run_single_agent_rag.py")
    run_step("Stage 07 — Comparative Evaluation & Error Cascade Analysis (4 Skenario)", "07_comparative_evaluation/compare_results.py")
    print("\nSELURUH EKSPERIMEN 4 SKENARIO TELAH SELESAI 100%!")


if __name__ == "__main__":
    main()


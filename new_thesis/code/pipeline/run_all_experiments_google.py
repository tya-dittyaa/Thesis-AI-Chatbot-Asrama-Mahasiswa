"""
Master Pipeline Runner: Skenario 1 - 4 & Comparative Evaluation
Provider: Google GenAI Direct (5 API Keys Load Balanced)
Model   : gemini-3.1-flash-lite
"""

import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime

PIPELINE_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = PIPELINE_DIR.parent
PYTHON_EXE = r"E:\Thesis\legacy_thesis\code\venv\Scripts\python.exe"

print("=" * 80)
print("GOOGLE GENAI PIPELINE RUNNER — FAST DIRECT EVALUATION")
print("=" * 80)
print(f"Timestamp   : {datetime.now().isoformat()}")
print(f"Model       : gemini-3.1-flash-lite (Google GenAI Direct)")
print(f"Python      : {PYTHON_EXE}")
print(f"Benchmark   : 500 tiket bersih (test_golden_benchmark_500.csv)")
print("=" * 80)

def run_step(step_name: str, script_path: str, args: list = None):
    print(f"\n{'#'*80}")
    print(f"MEMULAI: {step_name}")
    print(f"{'#'*80}\n", flush=True)
    cmd = [PYTHON_EXE, script_path] + (args or [])
    t0 = time.time()
    res = subprocess.run(cmd, cwd=str(WORKSPACE_ROOT))
    dur = time.time() - t0
    if res.returncode != 0:
        print(f"\n[ERROR] {step_name} gagal dengan return code {res.returncode} setelah {dur:.1f}s!", flush=True)
        sys.exit(res.returncode)
    print(f"\n[SUKSES] {step_name} selesai dalam {dur:.1f}s ({dur/60:.2f} menit).\n", flush=True)

# 1. Skenario 1: Classical ML (instan, 1 detik)
run_step("Skenario 1: Classical ML (TF-IDF + Logistic Regression)", "pipeline/00_classical_ml_baseline/run_classical_ml.py")

# 2. Skenario 2: Monolithic Single-Agent Baseline
run_step("Skenario 2: Monolithic Single-Agent Baseline (gemini-3.1-flash-lite)", "pipeline/05_single_agent_baseline/run_single_agent_baseline.py", ["--model", "gemini-3.1-flash-lite", "--no-resume"])

# 3. Skenario 3: Single-Agent + RAG Handbook
run_step("Skenario 3: Single-Agent + RAG Handbook (gemini-3.1-flash-lite)", "pipeline/05b_single_agent_rag/run_single_agent_rag.py", ["--model", "gemini-3.1-flash-lite", "--no-resume"])

# 4. Skenario 4: Modular Chained Multi-Agent System (MAS)
run_step("Skenario 4: Modular Chained MAS (gemini-3.1-flash-lite)", "pipeline/06_multi_agent_system/run_multi_agent_system.py", ["--model", "gemini-3.1-flash-lite", "--no-resume"])

# 5. Comparative Evaluation & Figures Generation
run_step("Tahap 07: Comparative Evaluation & Figures Generation", "pipeline/07_comparative_evaluation/compare_results.py")

print("\n" + "=" * 80)
print(f"SELURUH EKSPERIMEN PENELITIAN SELESAI PADA {datetime.now().isoformat()}!")
print("=" * 80)


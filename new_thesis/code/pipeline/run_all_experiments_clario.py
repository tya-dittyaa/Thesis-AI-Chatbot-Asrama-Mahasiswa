"""
Master Parallel Experiment Runner: Skenario 1 - 4 & Comparative Evaluation
Model: clario/gemini-3.7-flash (ClarioHub Gateway)
Mode: PARALLEL PROCESS EXECUTION (S2, S3, S4 jalan simultan)
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
print("PARALLEL EXPERIMENT RUNNER — SIMULTANEOUS PIPELINE EVALUATION")
print("=" * 80)
print(f"Timestamp   : {datetime.now().isoformat()}")
print(f"Model       : clario/gemini-3.7-flash")
print(f"Python      : {PYTHON_EXE}")
print(f"Benchmark   : 500 tiket bersih (test_golden_benchmark_500.csv)")
print("=" * 80)

# 1. Skenario 1: Classical ML (instan, 1 detik)
print("\n[1/3] Menjalankan Skenario 1 (Classical ML: TF-IDF + Logistic Regression)...")
t0 = time.time()
subprocess.run([PYTHON_EXE, "pipeline/00_classical_ml_baseline/run_classical_ml.py"], cwd=str(WORKSPACE_ROOT), check=True)
print(f"[SUKSES] Skenario 1 selesai dalam {time.time()-t0:.2f}s.")

# 2. Skenario 2, 3, dan 4 jalan paralel simultan!
print("\n[2/3] Memulai Skenario 2, 3, dan 4 SECARA PARALEL SIMULTAN...")
proc_s2 = subprocess.Popen([PYTHON_EXE, "pipeline/05_single_agent_baseline/run_single_agent_baseline.py", "--no-resume"], cwd=str(WORKSPACE_ROOT))
proc_s3 = subprocess.Popen([PYTHON_EXE, "pipeline/05b_single_agent_rag/run_single_agent_rag.py", "--no-resume"], cwd=str(WORKSPACE_ROOT))
proc_s4 = subprocess.Popen([PYTHON_EXE, "pipeline/06_multi_agent_system/run_multi_agent_system.py", "--no-resume"], cwd=str(WORKSPACE_ROOT))

procs = [
    ("Skenario 2 (Baseline)", proc_s2),
    ("Skenario 3 (Single+RAG)", proc_s3),
    ("Skenario 4 (MAS)", proc_s4)
]

t_start = time.time()
while any(p.poll() is None for _, p in procs):
    statuses = [f"{name}: {'Running' if p.poll() is None else ('Done' if p.returncode==0 else 'Failed')}" for name, p in procs]
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Status: " + " | ".join(statuses), flush=True)
    time.sleep(20)

for name, p in procs:
    if p.returncode != 0:
        print(f"[ERROR] {name} gagal dengan returncode {p.returncode}!")
        sys.exit(p.returncode)

print(f"\n[SUKSES] Seluruh Skenario 2, 3, dan 4 selesai secara paralel dalam {(time.time()-t_start)/60:.2f} menit!")

# 3. Comparative Evaluation & Figures Generation
print("\n[3/3] Menjalankan Tahap 07: Comparative Evaluation & Figures Generation...")
subprocess.run([PYTHON_EXE, "pipeline/07_comparative_evaluation/compare_results.py"], cwd=str(WORKSPACE_ROOT), check=True)

print("\n" + "=" * 80)
print(f"SELURUH EKSPERIMEN PENELITIAN SELESAI PADA {datetime.now().isoformat()}!")
print("=" * 80)

"""
╔======================================================================╗
║  MASTER PIPELINE RUNNER — THESIS ADITYA FAJRI (2602113205)          ║
╚======================================================================╝

Usage:
  python run_pipeline.py                  # Full pipeline, 500 tiket benchmark
  python run_pipeline.py --mock           # Dry-run tanpa API call
  python run_pipeline.py --skip-data      # Lewati tahap 1-4
  python run_pipeline.py --only-eval      # Hanya tahap 5-7
  python run_pipeline.py --limit 10       # Batasi N tiket
"""

import sys
import subprocess
import argparse
import time
from pathlib import Path
from datetime import datetime

BASE_DIR  = Path(__file__).resolve().parent
PIPE_DIR  = BASE_DIR / "pipeline"
VENV_PY   = BASE_DIR / "venv" / "Scripts" / "python.exe"
PYTHON    = str(VENV_PY) if VENV_PY.exists() else sys.executable

CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
BOLD   = "\033[1m"
RESET  = "\033[0m"


def banner():
    print(f"""
{BOLD}{CYAN}========================================================================
  THESIS PIPELINE -- Aditya Fajri (2602113205)
  MAS vs Single Agent :: LLM-based Complaint Triage Evaluation
========================================================================{RESET}
""")


def header(stage, title: str):
    print(f"\n{BOLD}{CYAN}{'-'*70}")
    print(f"  TAHAP {stage}: {title}")
    print(f"{'-'*70}{RESET}")


def run_stage(stage_num, title: str, script: Path, extra_args=None, skip: bool = False):
    if extra_args is None:
        extra_args = []
    header(stage_num, title)
    if skip:
        print(f"{YELLOW}  [SKIP] Tahap ini dilewati.{RESET}")
        return None
    if not script.exists():
        print(f"{RED}  [ERROR] Script tidak ditemukan: {script}{RESET}")
        return False

    cmd = [PYTHON, str(script)] + extra_args
    print(f"  Menjalankan: {' '.join(cmd)}\n")
    start = time.time()
    result = subprocess.run(cmd, cwd=str(script.parent))
    elapsed = time.time() - start

    if result.returncode == 0:
        print(f"\n{GREEN}  SELESAI dalam {elapsed:.1f}s{RESET}")
        return True
    else:
        print(f"\n{RED}  GAGAL (exit code {result.returncode}){RESET}")
        return False


def check_prerequisite_files() -> bool:
    required = {
        "Benchmark 500 tiket"  : PIPE_DIR / "02_data_splitting" / "data" / "test_golden_benchmark_500.csv",
        "Handbook Chunks RAG"  : PIPE_DIR / "03_handbook_rag_prep" / "data" / "handbook_chunks.json",
        "Prompt Single Agent"  : PIPE_DIR / "04_agent_schemas_and_prompts" / "prompts" / "single_agent_baseline.txt",
        "Schema Triage"        : PIPE_DIR / "04_agent_schemas_and_prompts" / "schemas" / "triage_tool_schema.json",
    }
    # Golden benchmark selalu 500 tiket bersih (pembersihan label noise dilakukan di tahap 02a)

    all_ok = True
    print(f"\n{BOLD}  Memeriksa file prerequisit:{RESET}")
    for label, path in required.items():
        exists = path.exists()
        status = f"{GREEN}OK{RESET}" if exists else f"{RED}TIDAK ADA{RESET}"
        print(f"    [{status}] {label}")
        if not exists:
            all_ok = False
    return all_ok


def main():
    parser = argparse.ArgumentParser(description="Master Pipeline Runner -- Thesis Aditya Fajri")
    parser.add_argument("--mock",      action="store_true", help="Dry-run tanpa API call")
    parser.add_argument("--skip-data", action="store_true", help="Lewati tahap 1-4")
    parser.add_argument("--only-eval", action="store_true", help="Hanya tahap 5, 6, 7")
    parser.add_argument("--limit",     type=int, default=None, help="Batasi N tiket")
    parser.add_argument("--no-resume", action="store_true", help="Mulai ulang evaluasi dari awal")
    args = parser.parse_args()

    banner()
    skip_data = args.skip_data or args.only_eval
    start_time = datetime.now()

    print(f"{BOLD}  Mode       :{RESET} {'MOCK (no API)' if args.mock else 'LIVE (Gemini API)'}")
    print(f"{BOLD}  Benchmark  :{RESET} {'500 tiket (Golden Benchmark Bersih)'}")
    if args.limit:
        print(f"{BOLD}  Limit      :{RESET} {args.limit} tiket")
    print(f"{BOLD}  Waktu mulai:{RESET} {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    results = {}

    results[1]    = run_stage(1,    "Data Filtering -- Periode 2015-2025",
                              PIPE_DIR / "01_data_filtering" / "filter_data_2015_2025.py",
                              skip=skip_data)
    results["2a"] = run_stage("2a", "Label Cleaning -- Deteksi & Hapus Label Noise (Full Dataset)",
                              PIPE_DIR / "02_data_splitting" / "clean_dataset.py",
                              skip=skip_data)
    results["2b"] = run_stage("2b", "Data Splitting -- Benchmark 500 Tiket Bersih",
                              PIPE_DIR / "02_data_splitting" / "split_data.py",
                              skip=skip_data)
    results[3]    = run_stage(3,    "Handbook RAG Preparation -- Chunking & Indexing",
                              PIPE_DIR / "03_handbook_rag_prep" / "extract_and_chunk_handbook.py",
                              skip=skip_data)
    results[4]    = run_stage(4,    "Verifikasi Schemas & Prompts",
                              PIPE_DIR / "04_agent_schemas_and_prompts" / "verify_schemas_and_prompts.py",
                              skip=skip_data)

    # Prerequisit check sebelum evaluasi
    print(f"\n{BOLD}{CYAN}{'-'*70}\n  PRE-EVALUATION CHECK\n{'-'*70}{RESET}")
    if not check_prerequisite_files():
        print(f"\n{RED}{BOLD}  Prerequisit tidak lengkap. Jalankan ulang tanpa --skip-data.{RESET}")
        sys.exit(1)
    print(f"\n{GREEN}  Semua prerequisit tersedia.{RESET}")

    eval_args = []
    
    if args.mock:      eval_args.append("--mock")
    if args.limit:     eval_args += ["--limit", str(args.limit)]
    if args.no_resume: eval_args.append("--no-resume")

    results[5] = run_stage(5, "Single Agent Baseline Evaluation",
                           PIPE_DIR / "05_single_agent_baseline" / "run_single_agent_baseline.py",
                           extra_args=eval_args)
    results[6] = run_stage(6, "Multi-Agent System (MAS) Evaluation",
                           PIPE_DIR / "06_multi_agent_system" / "run_multi_agent_system.py",
                           extra_args=eval_args)

    compare_args = []
    results[7] = run_stage(7, "Comparative Evaluation -- Generate Metrics & Figures",
                           PIPE_DIR / "07_comparative_evaluation" / "compare_results.py",
                           extra_args=compare_args)

    # Final summary
    elapsed_total = (datetime.now() - start_time).seconds
    print(f"\n{BOLD}{CYAN}{'='*70}\n  RINGKASAN PIPELINE\n{'='*70}{RESET}")

    stage_labels = {
        1: "01 Data Filtering",
        "2a": "02a Data Splitting",
        "2b": "02b Benchmark Cleaning",
        3: "03 Handbook RAG Prep",
        4: "04 Schemas & Prompts",
        5: "05 Single Agent Baseline",
        6: "06 Multi-Agent System",
        7: "07 Comparative Evaluation"
    }
    all_success = True
    for k, label in stage_labels.items():
        status = results.get(k)
        if status is True:
            icon = f"{GREEN}SELESAI{RESET}"
        elif status is False:
            icon = f"{RED}GAGAL  {RESET}"
            all_success = False
        else:
            icon = f"{YELLOW}LEWATI {RESET}"
        print(f"  [{icon}] Tahap {label}")

    print(f"\n  Total waktu  : {elapsed_total // 60}m {elapsed_total % 60}s")
    print(f"  Mode evaluasi: {'500 tiket (Golden Benchmark Bersih)'}")

    if all_success:
        out = PIPE_DIR / "07_comparative_evaluation" / "results"
        print(f"\n{GREEN}{BOLD}  Pipeline selesai! Hasil ada di:{RESET}\n  {out}")
    else:
        print(f"\n{RED}{BOLD}  Beberapa tahap gagal. Periksa error di atas.{RESET}")
        sys.exit(1)

    print(f"{CYAN}{'='*70}{RESET}\n")


if __name__ == "__main__":
    main()



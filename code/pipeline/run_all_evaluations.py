"""
Master Evaluation Runner — Thesis Aditya Fajri
================================================
Menjalankan seluruh siklus eksperimen secara otomatis:
1. Stage 05: Single-Agent Baseline (500 tiket, 4 keys load balanced)
2. Stage 06: Multi-Agent System / MAS (500 tiket, 4 keys load balanced)
3. Stage 07: Comparative Evaluation & Chart Generation (Bab 4 Thesis)

Output log dicatat langsung ke file:
    E:\\Thesis\\code\\pipeline_evaluation.log
"""

import sys
import subprocess
import time
from pathlib import Path
from datetime import datetime

PYTHON_EXE = sys.executable
BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = WORKSPACE_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "pipeline_evaluation.log"


def log_print(msg: str, lf):
    print(msg, flush=True)
    if lf:
        lf.write(msg + "\n")
        lf.flush()


def run_step(step_name: str, script_path: Path, args: list, lf):
    banner = (
        "\n" + "="*80 + "\n"
        f"🚀 [MASTER RUNNER] Memulai: {step_name}\n"
        f"⏰ Waktu Mulai: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"📄 Script: {script_path}\n"
        + "="*80 + "\n"
    )
    log_print(banner, lf)

    cmd = [PYTHON_EXE, "-u", str(script_path)] + args
    start_t = time.time()

    proc = subprocess.Popen(
        cmd,
        cwd=str(WORKSPACE_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    for line in proc.stdout:
        sys.stdout.write(line)
        sys.stdout.flush()
        if lf:
            lf.write(line)
            lf.flush()

    proc.wait()
    elapsed = time.time() - start_t

    if proc.returncode != 0:
        err_msg = f"\n❌ [MASTER RUNNER] Gagal pada {step_name} (Exit code: {proc.returncode})\n"
        log_print(err_msg, lf)
        sys.exit(proc.returncode)

    success_msg = f"\n✅ [MASTER RUNNER] Selesai: {step_name} dalam {elapsed/60:.1f} menit.\n"
    log_print(success_msg, lf)


def main():
    # Bersihkan / reset log file di awal run
    with open(LOG_FILE, "w", encoding="utf-8") as lf:
        header = (
            "="*80 + "\n"
            "🎯 BINUS SQUARE COMPLAINT TRIAGE — FULL EXPERIMENTAL EVALUATION\n"
            f"Waktu Mulai: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            "Mode: 4-Key Random Load Balancing (Active)\n"
            f"File Log: {LOG_FILE}\n"
            "="*80 + "\n"
        )
        log_print(header, lf)

        # 1. Single-Agent Baseline
        run_step(
            step_name="Stage 05 — Single-Agent Baseline (500 Tiket)",
            script_path=BASE_DIR / "05_single_agent_baseline" / "run_single_agent_baseline.py",
            args=["--no-resume"],
            lf=lf
        )

        # 2. Multi-Agent System (MAS)
        run_step(
            step_name="Stage 06 — Multi-Agent System / MAS (500 Tiket)",
            script_path=BASE_DIR / "06_multi_agent_system" / "run_multi_agent_system.py",
            args=["--no-resume"],
            lf=lf
        )

        # 3. Comparative Evaluation (Bab 4)
        run_step(
            step_name="Stage 07 — Comparative Evaluation & Figures (Bab 4)",
            script_path=BASE_DIR / "07_comparative_evaluation" / "compare_results.py",
            args=[],
            lf=lf
        )

        footer = (
            "\n" + "="*80 + "\n"
            "🎉 SEMUA EVALUASI SELESAI DENGAN SUKSES!\n"
            f"Waktu Selesai: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            "Hasil perbandingan & grafik Bab 4 tersedia di:\n"
            f"  {BASE_DIR / '07_comparative_evaluation' / 'results'}\n"
            + "="*80 + "\n"
        )
        log_print(footer, lf)


if __name__ == "__main__":
    main()

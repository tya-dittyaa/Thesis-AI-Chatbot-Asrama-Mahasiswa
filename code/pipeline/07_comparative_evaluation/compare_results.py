"""
Pipeline Stage 7: Comparative Evaluation (Single-Agent Baseline vs Multi-Agent System)
Calculates comparative performance metrics and generates high-resolution figures for Chapter 4 of the Thesis.

Metrics compared:
- Triage Accuracy (Overall & Per Department)
- Macro-F1, Weighted-F1, Precision, Recall
- Reroute Recovery Rate
- Schema / JSON Validity
- Latency (seconds per ticket)
- Token Consumption
- Confidence Score (MAS only — from Agent 2 function calling)

Outputs:
- results/comparative_metrics_table.csv
- results/comparative_metrics_table.md (Markdown format for Thesis)
- results/comparative_summary.json
- results/figures/accuracy_by_department.png
- results/figures/confusion_matrices_comparison.png
- results/figures/latency_token_tradeoff.png
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for server/script rendering
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import classification_report, confusion_matrix, precision_recall_fscore_support

DEPARTMENTS = [
    "Estate Department",
    "Operations",
    "Finance",
    "Marketing",
    "Student Support Office"
]

DEPT_SHORT = ["ED", "OP", "FN", "MR", "SO"]


def compute_metrics_for_df(df: pd.DataFrame, name: str) -> dict:
    total = len(df)
    correct = df["IsCorrect"].sum()
    overall_acc = (correct / total * 100) if total > 0 else 0.0

    y_true = df["HandledDepartmentName"].astype(str)
    y_pred = df["PredictedDepartmentName"].astype(str)

    p_macro, r_macro, f1_macro, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=DEPARTMENTS, average="macro", zero_division=0
    )
    p_weight, r_weight, f1_weight, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=DEPARTMENTS, average="weighted", zero_division=0
    )

    # Per-dept accuracy
    dept_accs = {}
    for d in DEPARTMENTS:
        d_df = df[df["HandledDepartmentName"] == d]
        d_tot = len(d_df)
        d_cor = d_df["IsCorrect"].sum() if d_tot > 0 else 0
        dept_accs[d] = round((d_cor / d_tot * 100) if d_tot > 0 else 0.0, 2)

    # Reroute recovery
    df_reroute = df[df["IsRerouted"] == 1]
    reroute_tot = len(df_reroute)
    reroute_fixed = df_reroute["WasRerouteFixed"].sum() if "WasRerouteFixed" in df_reroute.columns else 0
    reroute_acc = (df_reroute["IsCorrect"].sum() / reroute_tot * 100) if reroute_tot > 0 else 0.0

    # Validity
    if "IsValidJson" in df.columns:
        valid_rate = (df["IsValidJson"].sum() / total * 100) if total > 0 else 0.0
    elif "FunctionCallSuccess" in df.columns:
        valid_rate = (df["FunctionCallSuccess"].sum() / total * 100) if total > 0 else 0.0
    else:
        valid_rate = 100.0

    latency_col = "TotalLatencySeconds" if "TotalLatencySeconds" in df.columns else "LatencySeconds"
    valid_proc = df[df["TotalTokens"] > 0] if "TotalTokens" in df.columns and (df["TotalTokens"] > 0).any() else df
    avg_latency = float(valid_proc[latency_col].mean()) if latency_col in valid_proc.columns else 0.0
    avg_tokens = float(valid_proc["TotalTokens"].mean()) if "TotalTokens" in valid_proc.columns else 0.0

    # Confidence score (MAS only — captured from Agent 2 function call)
    if "ConfidenceScore" in df.columns:
        conf_vals = pd.to_numeric(df["ConfidenceScore"], errors="coerce").dropna()
        avg_conf = float(conf_vals.mean()) if len(conf_vals) > 0 else None
        # Calibration: mean confidence on correct vs incorrect predictions
        conf_correct = float(conf_vals[df.loc[conf_vals.index, "IsCorrect"] == 1].mean()) if len(conf_vals) > 0 else None
        conf_wrong   = float(conf_vals[df.loc[conf_vals.index, "IsCorrect"] == 0].mean()) if len(conf_vals) > 0 else None
    else:
        avg_conf = conf_correct = conf_wrong = None

    return {
        "architecture": name,
        "total_tickets": int(total),
        "overall_accuracy": round(overall_acc, 2),
        "macro_precision": round(p_macro * 100, 2),
        "macro_recall": round(r_macro * 100, 2),
        "macro_f1": round(f1_macro * 100, 2),
        "weighted_f1": round(f1_weight * 100, 2),
        "schema_validity_rate": round(valid_rate, 2),
        "reroute_tickets_count": int(reroute_tot),
        "reroute_accuracy": round(reroute_acc, 2),
        "reroute_recovered_count": int(reroute_fixed),
        "average_latency_sec": round(avg_latency, 3),
        "average_tokens_ticket": round(avg_tokens, 1),
        "per_department_accuracy": dept_accs,
        "avg_confidence_score": round(avg_conf, 3) if avg_conf is not None else None,
        "confidence_on_correct": round(conf_correct, 3) if conf_correct is not None else None,
        "confidence_on_wrong": round(conf_wrong, 3) if conf_wrong is not None else None,
    }


def generate_accuracy_bar_chart(m_base: dict, m_mas: dict, save_path: Path):
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)

    categories = ["Overall"] + DEPARTMENTS + ["Reroute Cases"]
    base_scores = [m_base["overall_accuracy"]] + [m_base["per_department_accuracy"][d] for d in DEPARTMENTS] + [m_base["reroute_accuracy"]]
    mas_scores = [m_mas["overall_accuracy"]] + [m_mas["per_department_accuracy"][d] for d in DEPARTMENTS] + [m_mas["reroute_accuracy"]]

    x = np.arange(len(categories))
    width = 0.35

    rects1 = ax.bar(x - width/2, base_scores, width, label="Single-Agent Baseline", color="#4A90E2", alpha=0.85, edgecolor="#2171B5")
    rects2 = ax.bar(x + width/2, mas_scores, width, label="Multi-Agent System (MAS)", color="#2ECC71", alpha=0.85, edgecolor="#27AE60")

    ax.set_ylabel("Akurasi (%)", fontsize=12, fontweight="bold")
    ax.set_title("Perbandingan Akurasi Triase: Baseline vs Multi-Agent System (MAS)", fontsize=14, fontweight="bold", pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(categories, rotation=25, ha="right", fontsize=10)
    ax.set_ylim(0, 110)
    ax.legend(loc="upper right", fontsize=11, frameon=True)

    # Add data labels
    for rect in rects1:
        h = rect.get_height()
        ax.annotate(f"{h:.1f}%", xy=(rect.get_x() + rect.get_width() / 2, h), xytext=(0, 3),
                    textcoords="offset points", ha="center", va="bottom", fontsize=8, color="#1C3D5A")
    for rect in rects2:
        h = rect.get_height()
        ax.annotate(f"{h:.1f}%", xy=(rect.get_x() + rect.get_width() / 2, h), xytext=(0, 3),
                    textcoords="offset points", ha="center", va="bottom", fontsize=8, color="#0E6251")

    plt.tight_layout()
    fig.savefig(save_path)
    plt.close(fig)
    print(f"Saved: {save_path.name}")


def generate_confusion_matrices(df_base: pd.DataFrame, df_mas: pd.DataFrame, save_path: Path):
    cm_base = confusion_matrix(df_base["HandledDepartmentName"], df_base["PredictedDepartmentName"], labels=DEPARTMENTS)
    cm_mas = confusion_matrix(df_mas["HandledDepartmentName"], df_mas["PredictedDepartmentName"], labels=DEPARTMENTS)

    fig, axes = plt.subplots(1, 2, figsize=(16, 7), dpi=300)

    sns.heatmap(cm_base, annot=True, fmt="d", cmap="Blues", ax=axes[0], cbar=False,
                xticklabels=DEPT_SHORT, yticklabels=DEPT_SHORT)
    axes[0].set_title("(A) Single-Agent Baseline", fontsize=13, fontweight="bold", pad=12)
    axes[0].set_xlabel("Predicted Department", fontsize=11)
    axes[0].set_ylabel("Ground Truth (Staff Handled)", fontsize=11)

    sns.heatmap(cm_mas, annot=True, fmt="d", cmap="Greens", ax=axes[1], cbar=False,
                xticklabels=DEPT_SHORT, yticklabels=DEPT_SHORT)
    axes[1].set_title("(B) Multi-Agent System (MAS)", fontsize=13, fontweight="bold", pad=12)
    axes[1].set_xlabel("Predicted Department", fontsize=11)
    axes[1].set_ylabel("Ground Truth (Staff Handled)", fontsize=11)

    dept_legend = "\n".join([f"{code} = {name}" for code, name in zip(DEPT_SHORT, DEPARTMENTS)])
    fig.text(0.5, 0.01, f"Keterangan Departemen: {', '.join([f'{c}: {n}' for c, n in zip(DEPT_SHORT, DEPARTMENTS)])}",
             ha="center", fontsize=9, style="italic")

    plt.suptitle("Perbandingan Confusion Matrix Triase Komplain (Golden Benchmark N=500)", fontsize=15, fontweight="bold", y=0.98)
    plt.tight_layout(rect=[0, 0.05, 1, 0.95])
    fig.savefig(save_path)
    plt.close(fig)
    print(f"Saved: {save_path.name}")


def generate_latency_token_chart(m_base: dict, m_mas: dict, save_path: Path):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5), dpi=300)

    # Latency
    archs = ["Baseline", "Multi-Agent"]
    lats = [m_base["average_latency_sec"], m_mas["average_latency_sec"]]
    bars1 = ax1.bar(archs, lats, color=["#4A90E2", "#2ECC71"], width=0.45)
    ax1.set_ylabel("Detik / Tiket", fontsize=11, fontweight="bold")
    ax1.set_title("Rata-rata Latensi Inferensi", fontsize=13, fontweight="bold")
    ax1.set_ylim(0, max(lats) * 1.35 if max(lats) > 0 else 1)
    for b in bars1:
        h = b.get_height()
        ax1.annotate(f"{h:.3f} s", xy=(b.get_x() + b.get_width()/2, h), xytext=(0, 4),
                     textcoords="offset points", ha="center", va="bottom", fontsize=10, fontweight="bold")

    # Tokens
    tokens = [m_base["average_tokens_ticket"], m_mas["average_tokens_ticket"]]
    bars2 = ax2.bar(archs, tokens, color=["#E67E22", "#9B59B6"], width=0.45)
    ax2.set_ylabel("Token / Tiket", fontsize=11, fontweight="bold")
    ax2.set_title("Rata-rata Konsumsi Token", fontsize=13, fontweight="bold")
    ax2.set_ylim(0, max(tokens) * 1.35 if max(tokens) > 0 else 100)
    for b in bars2:
        h = b.get_height()
        ax2.annotate(f"{h:.1f}", xy=(b.get_x() + b.get_width()/2, h), xytext=(0, 4),
                     textcoords="offset points", ha="center", va="bottom", fontsize=10, fontweight="bold")

    plt.suptitle("Analisis Trade-Off Efisiensi Operasional (Latensi & Token)", fontsize=14, fontweight="bold", y=0.98)
    plt.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(save_path)
    plt.close(fig)
    print(f"Saved: {save_path.name}")


def main():
    base_dir = Path(__file__).resolve().parent
    pipeline_dir = base_dir.parent

    base_preds_path = pipeline_dir / "05_single_agent_baseline" / "results" / "baseline_predictions.csv"
    mas_preds_path = pipeline_dir / "06_multi_agent_system" / "results" / "mas_predictions.csv"

    if not base_preds_path.exists():
        print(f"ERROR: File prediksi baseline tidak ditemukan di {base_preds_path}")
        print("Silakan jalankan tahap 05 terlebih dahulu: python pipeline/05_single_agent_baseline/run_single_agent_baseline.py")
        sys.exit(1)

    if not mas_preds_path.exists():
        print(f"ERROR: File prediksi MAS tidak ditemukan di {mas_preds_path}")
        print("Silakan jalankan tahap 06 terlebih dahulu: python pipeline/06_multi_agent_system/run_multi_agent_system.py")
        sys.exit(1)

    df_base = pd.read_csv(base_preds_path)
    df_mas = pd.read_csv(mas_preds_path)

    print(f"Loaded Baseline Predictions: {len(df_base)} tickets")
    print(f"Loaded MAS Predictions     : {len(df_mas)} tickets")

    m_base = compute_metrics_for_df(df_base, "Single-Agent Baseline")
    m_mas = compute_metrics_for_df(df_mas, "Multi-Agent System (MAS)")

    # Save metrics JSON
    results_dir = base_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    fig_dir = results_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    summary = {
        "timestamp": datetime.now().isoformat(),
        "baseline": m_base,
        "multi_agent_system": m_mas,
        "delta_mas_vs_baseline": {
            "overall_accuracy_gain": round(m_mas["overall_accuracy"] - m_base["overall_accuracy"], 2),
            "macro_f1_gain": round(m_mas["macro_f1"] - m_base["macro_f1"], 2),
            "schema_validity_gain": round(m_mas["schema_validity_rate"] - m_base["schema_validity_rate"], 2),
            "latency_delta_sec": round(m_mas["average_latency_sec"] - m_base["average_latency_sec"], 3),
            "token_overhead": round(m_mas["average_tokens_ticket"] - m_base["average_tokens_ticket"], 1)
        }
    }

    with open(results_dir / "comparative_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    # Comparative Table (DataFrame)
    table_rows = [
        {"Metrik Evaluasi": "Total Tiket Evaluasi (Golden Benchmark)", "Single-Agent Baseline": str(m_base["total_tickets"]), "Multi-Agent System (MAS)": str(m_mas["total_tickets"]), "Delta (MAS vs Base)": "-"},
        {"Metrik Evaluasi": "Akurasi Triase Keseluruhan (%)", "Single-Agent Baseline": f"{m_base['overall_accuracy']}%", "Multi-Agent System (MAS)": f"{m_mas['overall_accuracy']}%", "Delta (MAS vs Base)": f"{summary['delta_mas_vs_baseline']['overall_accuracy_gain']:+g}%"},
        {"Metrik Evaluasi": "Macro-F1 Score (%)", "Single-Agent Baseline": f"{m_base['macro_f1']}%", "Multi-Agent System (MAS)": f"{m_mas['macro_f1']}%", "Delta (MAS vs Base)": f"{summary['delta_mas_vs_baseline']['macro_f1_gain']:+g}%"},
        {"Metrik Evaluasi": "Weighted-F1 Score (%)", "Single-Agent Baseline": f"{m_base['weighted_f1']}%", "Multi-Agent System (MAS)": f"{m_mas['weighted_f1']}%", "Delta (MAS vs Base)": f"{(m_mas['weighted_f1'] - m_base['weighted_f1']):+g}%"},
        {"Metrik Evaluasi": "Validitas Format Skema/JSON (%)", "Single-Agent Baseline": f"{m_base['schema_validity_rate']}%", "Multi-Agent System (MAS)": f"{m_mas['schema_validity_rate']}%", "Delta (MAS vs Base)": f"{summary['delta_mas_vs_baseline']['schema_validity_gain']:+g}%"},
        {"Metrik Evaluasi": "Akurasi Estate Department (ED)", "Single-Agent Baseline": f"{m_base['per_department_accuracy']['Estate Department']}%", "Multi-Agent System (MAS)": f"{m_mas['per_department_accuracy']['Estate Department']}%", "Delta (MAS vs Base)": f"{(m_mas['per_department_accuracy']['Estate Department'] - m_base['per_department_accuracy']['Estate Department']):+g}%"},
        {"Metrik Evaluasi": "Akurasi Operations (OP)", "Single-Agent Baseline": f"{m_base['per_department_accuracy']['Operations']}%", "Multi-Agent System (MAS)": f"{m_mas['per_department_accuracy']['Operations']}%", "Delta (MAS vs Base)": f"{(m_mas['per_department_accuracy']['Operations'] - m_base['per_department_accuracy']['Operations']):+g}%"},
        {"Metrik Evaluasi": "Akurasi Finance (FN)", "Single-Agent Baseline": f"{m_base['per_department_accuracy']['Finance']}%", "Multi-Agent System (MAS)": f"{m_mas['per_department_accuracy']['Finance']}%", "Delta (MAS vs Base)": f"{(m_mas['per_department_accuracy']['Finance'] - m_base['per_department_accuracy']['Finance']):+g}%"},
        {"Metrik Evaluasi": "Akurasi Marketing (MR)", "Single-Agent Baseline": f"{m_base['per_department_accuracy']['Marketing']}%", "Multi-Agent System (MAS)": f"{m_mas['per_department_accuracy']['Marketing']}%", "Delta (MAS vs Base)": f"{(m_mas['per_department_accuracy']['Marketing'] - m_base['per_department_accuracy']['Marketing']):+g}%"},
        {"Metrik Evaluasi": "Akurasi Student Support (SO)", "Single-Agent Baseline": f"{m_base['per_department_accuracy']['Student Support Office']}%", "Multi-Agent System (MAS)": f"{m_mas['per_department_accuracy']['Student Support Office']}%", "Delta (MAS vs Base)": f"{(m_mas['per_department_accuracy']['Student Support Office'] - m_base['per_department_accuracy']['Student Support Office']):+g}%"},
        {"Metrik Evaluasi": "Akurasi Kasus Reroute (Salah Dept Awal)", "Single-Agent Baseline": f"{m_base['reroute_accuracy']}%", "Multi-Agent System (MAS)": f"{m_mas['reroute_accuracy']}%", "Delta (MAS vs Base)": f"{(m_mas['reroute_accuracy'] - m_base['reroute_accuracy']):+g}%"},
        {"Metrik Evaluasi": "Rata-rata Latensi (detik/tiket)", "Single-Agent Baseline": f"{m_base['average_latency_sec']} s", "Multi-Agent System (MAS)": f"{m_mas['average_latency_sec']} s", "Delta (MAS vs Base)": f"{summary['delta_mas_vs_baseline']['latency_delta_sec']:+g} s"},
        {"Metrik Evaluasi": "Rata-rata Token per Tiket", "Single-Agent Baseline": f"{m_base['average_tokens_ticket']} tokens", "Multi-Agent System (MAS)": f"{m_mas['average_tokens_ticket']} tokens", "Delta (MAS vs Base)": f"{summary['delta_mas_vs_baseline']['token_overhead']:+g} tokens"},
    ]

    df_table = pd.DataFrame(table_rows)
    df_table.to_csv(results_dir / "comparative_metrics_table.csv", index=False, encoding="utf-8")

    # Generate Markdown Table
    md_table = df_table.to_markdown(index=False)
    with open(results_dir / "comparative_metrics_table.md", "w", encoding="utf-8") as f:
        f.write("# Tabel Komparasi Hasil Eksperimen: Single-Agent Baseline vs Multi-Agent System (MAS)\n\n")
        f.write(f"Tanggal Pengujian: {datetime.now().strftime('%d %B %Y')}\n")
        f.write(f"Ukuran Data Uji : 500 Tiket Golden Benchmark (100 per departemen seimbang)\n\n")
        f.write(md_table)
        f.write("\n\n---\n*Tabel ini dapat langsung disalin ke Bab 4 Dokumen Tesis.*")

    # Generate Figures
    generate_accuracy_bar_chart(m_base, m_mas, fig_dir / "accuracy_by_department.png")
    generate_confusion_matrices(df_base, df_mas, fig_dir / "confusion_matrices_comparison.png")
    generate_latency_token_chart(m_base, m_mas, fig_dir / "latency_token_tradeoff.png")

    print("\n" + "="*75)
    print("COMPARATIVE EVALUATION SUMMARY (CHAPTER 4 THESIS):")
    print("="*75)
    print(md_table)
    print("="*75)
    print(f"Metrics table (CSV): {results_dir / 'comparative_metrics_table.csv'}")
    print(f"Metrics table (MD) : {results_dir / 'comparative_metrics_table.md'}")
    print(f"Summary JSON       : {results_dir / 'comparative_summary.json'}")
    print(f"Figures saved in   : {fig_dir}")
    print("="*75 + "\n")


if __name__ == "__main__":
    main()

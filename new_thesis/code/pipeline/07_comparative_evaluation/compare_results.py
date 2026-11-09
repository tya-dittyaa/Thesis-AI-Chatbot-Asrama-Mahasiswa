"""
Pipeline Stage 7: 4-Scenario Comparative Evaluation & Error Cascade Analysis
Menghitung metrik komparatif lengkap untuk:
- Skenario 1: Classical Supervised ML (TF-IDF + Logistic Regression)
- Skenario 2: Monolithic Single-Agent LLM (Zero-Shot, Tanpa RAG)
- Skenario 3: Single-Agent LLM + RAG Handbook (Ablation Control)
- Skenario 4: Modular Chained Multi-Agent System (Proposed 3-Agent + Native Function Calling)
Serta melakukan Error Propagation / Cascade Analysis pada Skenario 4 untuk Bab 4 Tesis.
"""

import sys
import json
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

DEPARTMENTS = [
    "Estate Department",
    "Operations",
    "Finance",
    "Marketing",
    "Student Support Office"
]
DEPT_SHORT = ["ED", "OP", "FN", "MR", "SO"]
DEPT_TO_SHORT = dict(zip(DEPARTMENTS, DEPT_SHORT))


def compute_metrics_for_df(df: pd.DataFrame, name: str) -> dict:
    total = len(df)
    correct = int(df["IsCorrect"].sum())
    overall_acc = (correct / total * 100) if total > 0 else 0.0

    y_true = df["HandledDepartmentName"].astype(str)
    y_pred = df["PredictedDepartmentName"].astype(str)

    p_macro, r_macro, f1_macro, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=DEPARTMENTS, average="macro", zero_division=0
    )
    p_weight, r_weight, f1_weight, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=DEPARTMENTS, average="weighted", zero_division=0
    )
    p_cls, r_cls, f1_cls, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=DEPARTMENTS, average=None, zero_division=0
    )

    dept_accs = {}
    dept_f1s = {}
    dept_precs = {}
    dept_recs = {}
    for idx, d in enumerate(DEPARTMENTS):
        d_df = df[df["HandledDepartmentName"] == d]
        d_tot = len(d_df)
        d_cor = int(d_df["IsCorrect"].sum()) if d_tot > 0 else 0
        dept_accs[d] = round((d_cor / d_tot * 100) if d_tot > 0 else 0.0, 2)
        dept_precs[d] = round(float(p_cls[idx] * 100), 2)
        dept_recs[d] = round(float(r_cls[idx] * 100), 2)
        dept_f1s[d] = round(float(f1_cls[idx] * 100), 2)

    if "FunctionCallSuccess" in df.columns:
        valid_rate = (df["FunctionCallSuccess"].sum() / total * 100) if total > 0 else 0.0
    elif "IsValidJson" in df.columns:
        valid_rate = (df["IsValidJson"].sum() / total * 100) if total > 0 else 0.0
    else:
        valid_rate = 0.0

    latency_col = "TotalLatencySeconds" if "TotalLatencySeconds" in df.columns else "LatencySeconds"
    valid_proc = df[df["TotalTokens"] > 0] if "TotalTokens" in df.columns and (df["TotalTokens"] > 0).any() else df
    avg_latency = float(valid_proc[latency_col].mean()) if latency_col in valid_proc.columns else 0.0
    avg_tokens = float(valid_proc["TotalTokens"].mean()) if "TotalTokens" in valid_proc.columns else 0.0

    if "ConfidenceScore" in df.columns:
        conf_vals = pd.to_numeric(df["ConfidenceScore"], errors="coerce").dropna()
        avg_conf = float(conf_vals.mean()) if len(conf_vals) > 0 else None
        conf_correct = float(conf_vals[df.loc[conf_vals.index, "IsCorrect"] == 1].mean()) if len(conf_vals) > 0 else None
        conf_wrong = float(conf_vals[df.loc[conf_vals.index, "IsCorrect"] == 0].mean()) if len(conf_vals) > 0 else None
    else:
        avg_conf = conf_correct = conf_wrong = None

    return {
        "architecture": name,
        "total_tickets": int(total),
        "correct_tickets": int(correct),
        "overall_accuracy": round(overall_acc, 2),
        "macro_precision": round(float(p_macro * 100), 2),
        "macro_recall": round(float(r_macro * 100), 2),
        "macro_f1": round(float(f1_macro * 100), 2),
        "weighted_f1": round(float(f1_weight * 100), 2),
        "schema_validity_rate": round(float(valid_rate), 2),
        "average_latency_sec": round(avg_latency, 4 if avg_latency < 0.05 else 3),
        "average_tokens_ticket": round(avg_tokens, 1),
        "per_department_accuracy": dept_accs,
        "per_department_precision": dept_precs,
        "per_department_recall": dept_recs,
        "per_department_f1": dept_f1s,
        "avg_confidence_score": round(avg_conf, 3) if avg_conf is not None else None,
        "confidence_on_correct": round(conf_correct, 3) if conf_correct is not None else None,
        "confidence_on_wrong": round(conf_wrong, 3) if conf_wrong is not None else None,
    }


def analyze_error_cascade(df_s2: pd.DataFrame, df_s3: pd.DataFrame, df_s4: pd.DataFrame) -> dict:
    """
    Membedah anatomi kegagalan pada Skenario 4 (MAS) dengan membandingkan terhadap Skenario 2 & 3
    per FeedbackHeaderID untuk mengisolasi sumber kesalahan:
    1. Retrieval-Induced / Context Noise Error: Skenario 2 (tanpa RAG) benar, tapi Skenario 3/4 (dengan RAG) salah.
    2. Decomposition / Chaining Loss (Agent 1 -> Agent 2 Summarization Loss): Skenario 3 (Single+RAG) benar, tapi Skenario 4 (MAS) salah.
    3. Intrinsic Domain Ambiguity / Borderline Reasoning Error: Baik Skenario 2, 3, maupun 4 sama-sama salah karena ambiguitas keluhan penghuni.
    """
    m2 = df_s2.set_index("FeedbackHeaderID")["IsCorrect"].to_dict()
    m3 = df_s3.set_index("FeedbackHeaderID")["IsCorrect"].to_dict()

    wrong_s4 = df_s4[df_s4["IsCorrect"] == 0].copy()
    total_wrong = len(wrong_s4)

    retrieval_noise_count = 0
    chaining_loss_count = 0
    intrinsic_ambiguity_count = 0

    confusion_pairs = {}
    for _, row in wrong_s4.iterrows():
        tid = str(row["FeedbackHeaderID"])
        c2 = m2.get(tid, 0)
        c3 = m3.get(tid, 0)

        if c3 == 1:
            # Single-Agent+RAG benar, tapi MAS salah -> kehilangan nuansa saat dekomposisi Agen 1 -> Agen 2
            chaining_loss_count += 1
        elif c2 == 1 and c3 == 0:
            # Tanpa RAG benar, tapi dengan RAG (S3 & S4) salah -> distraksi konteks RAG (Retrieval Noise)
            retrieval_noise_count += 1
        else:
            # Semua LLM salah -> kasus borderline / ambiguitas intrinsik domain asrama
            intrinsic_ambiguity_count += 1

        pair_key = f"{DEPT_TO_SHORT.get(row['HandledDepartmentName'], row['HandledDepartmentName'])} -> {DEPT_TO_SHORT.get(row['PredictedDepartmentName'], row['PredictedDepartmentName'])}"
        confusion_pairs[pair_key] = confusion_pairs.get(pair_key, 0) + 1

    top_confusions = dict(sorted(confusion_pairs.items(), key=lambda x: x[1], reverse=True)[:6])

    return {
        "total_misclassified_s4": int(total_wrong),
        "retrieval_context_noise": {
            "count": int(retrieval_noise_count),
            "percent_of_errors": round(retrieval_noise_count / total_wrong * 100, 1) if total_wrong > 0 else 0.0
        },
        "agent_chaining_loss": {
            "count": int(chaining_loss_count),
            "percent_of_errors": round(chaining_loss_count / total_wrong * 100, 1) if total_wrong > 0 else 0.0
        },
        "intrinsic_borderline_ambiguity": {
            "count": int(intrinsic_ambiguity_count),
            "percent_of_errors": round(intrinsic_ambiguity_count / total_wrong * 100, 1) if total_wrong > 0 else 0.0
        },
        "top_confusion_pairs": top_confusions
    }


def simulate_hybrid_architecture(df_s2: pd.DataFrame, df_s4: pd.DataFrame) -> dict:
    """
    Simulasi empiris Confidence & Domain-Gated Hybrid ITSM Triage Framework:
    - Jalur Cepat (Tier-1: Skenario 2 Single-Agent) menangani tiket keluhan fisik/operasional yang selaras dengan kanal awal.
    - Jalur Eskalasi (Tier-2: Skenario 4 Modular Chained MAS) diaktifkan hanya ketika:
      (a) Tiket menyangkut domain kepatuhan regulasi/keuangan (`Finance`), ATAU
      (b) Prediksi Tier-1 menyimpang dari kanal departemen awal (`Disagreement / Low Certainty Gate`).
    """
    s4_map = df_s4.set_index("FeedbackHeaderID").to_dict(orient="index")
    hybrid_rows = []
    escalated_count = 0

    for _, row2 in df_s2.iterrows():
        tid = str(row2["FeedbackHeaderID"])
        init_dept = str(row2.get("InitialDepartmentName", "")).strip()
        pred2 = str(row2.get("PredictedDepartmentName", "")).strip()
        row4 = s4_map.get(tid, row2.to_dict())

        needs_escalation = (init_dept == "Finance") or (pred2.lower() != init_dept.lower())
        if needs_escalation:
            escalated_count += 1
            chosen = row4.copy()
            chosen["TotalLatencySeconds"] = float(row4.get("TotalLatencySeconds", 5.9))
            chosen["TotalTokens"] = int(row4.get("TotalTokens", 3700))
        else:
            chosen = row2.to_dict()
            chosen["TotalLatencySeconds"] = float(row2.get("LatencySeconds", 1.76))
            chosen["TotalTokens"] = int(row2.get("TotalTokens", 833))
        hybrid_rows.append(chosen)

    df_hyb = pd.DataFrame(hybrid_rows)
    m_hyb = compute_metrics_for_df(df_hyb, "Hybrid Tiered Framework (S2 Fast-Path + S4 MAS Escalation)")
    m_hyb["escalation_rate_percent"] = round(escalated_count / len(df_s2) * 100, 2)
    m_hyb["fast_path_rate_percent"] = round((len(df_s2) - escalated_count) / len(df_s2) * 100, 2)
    return m_hyb


def generate_4scenario_accuracy_chart(metrics_list: list[dict], save_path: Path):
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
    fig, ax = plt.subplots(figsize=(12, 6.5), dpi=300)

    categories = ["Overall\nAccuracy", "Macro-F1"] + [f"{DEPT_TO_SHORT[d]}\n({d.split()[0]})" for d in DEPARTMENTS]
    x = np.arange(len(categories))
    width = 0.20
    colors = ["#7F8C8D", "#3498DB", "#E67E22", "#2ECC71"]
    labels = [
        "Skenario 1: Classical ML (TF-IDF+LR)",
        "Skenario 2: Monolithic Single-Agent",
        "Skenario 3: Single-Agent + RAG",
        "Skenario 4: Modular Chained MAS"
    ]

    for i, (m, col, lab) in enumerate(zip(metrics_list, colors, labels)):
        scores = [m["overall_accuracy"], m["macro_f1"]] + [m["per_department_accuracy"][d] for d in DEPARTMENTS]
        offset = (i - 1.5) * width
        rects = ax.bar(x + offset, scores, width, label=lab, color=col, alpha=0.9, edgecolor="black", linewidth=0.5)
        for rect in rects:
            h = rect.get_height()
            ax.annotate(f"{h:.1f}", xy=(rect.get_x() + rect.get_width() / 2, h),
                        xytext=(0, 2), textcoords="offset points", ha="center", va="bottom", fontsize=7, fontweight="bold")

    ax.set_ylabel("Skor (%)", fontsize=11, fontweight="bold")
    ax.set_title("Perbandingan Performa Triase 4 Skenario pada Golden Benchmark (N=500)", fontsize=13, fontweight="bold", pad=14)
    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontsize=9.5, fontweight="bold")
    ax.set_ylim(0, 108)
    ax.legend(loc="upper right", fontsize=9.5, frameon=True)
    plt.tight_layout()
    fig.savefig(save_path)
    plt.close(fig)


def generate_4scenario_confusion_matrices(dfs: list[pd.DataFrame], titles: list[str], save_path: Path):
    fig, axes = plt.subplots(2, 2, figsize=(15, 13), dpi=300)
    cmaps = ["Purples", "Blues", "Oranges", "Greens"]

    for ax, df, title, cmap in zip(axes.flat, dfs, titles, cmaps):
        cm = confusion_matrix(df["HandledDepartmentName"], df["PredictedDepartmentName"], labels=DEPARTMENTS)
        sns.heatmap(cm, annot=True, fmt="d", cmap=cmap, ax=ax, cbar=False,
                    xticklabels=DEPT_SHORT, yticklabels=DEPT_SHORT, annot_kws={"size": 11, "weight": "bold"})
        ax.set_title(title, fontsize=12, fontweight="bold", pad=10)
        ax.set_xlabel("Predicted Department", fontsize=10)
        ax.set_ylabel("Ground Truth (Handled)", fontsize=10)

    plt.suptitle("Matriks Konfusi 5x5 Komparatif 4 Skenario Pengujian (Golden Benchmark N=500)", fontsize=14, fontweight="bold", y=0.98)
    plt.tight_layout(rect=[0, 0.02, 1, 0.96])
    fig.savefig(save_path)
    plt.close(fig)


def generate_latency_token_chart_4scenarios(metrics_list: list[dict], save_path: Path):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5), dpi=300)
    archs = ["S1: Classical ML", "S2: Single-Agent", "S3: Single+RAG", "S4: Modular MAS"]
    colors = ["#7F8C8D", "#3498DB", "#E67E22", "#2ECC71"]

    lats = [m["average_latency_sec"] for m in metrics_list]
    bars1 = ax1.bar(archs, lats, color=colors, width=0.5, edgecolor="black", linewidth=0.6)
    ax1.set_ylabel("Detik / Tiket", fontsize=11, fontweight="bold")
    ax1.set_title("Rata-rata Latensi Inferensi per Tiket", fontsize=12, fontweight="bold")
    ax1.set_ylim(0, max(lats) * 1.3 if max(lats) > 0 else 1)
    for b in bars1:
        h = b.get_height()
        lbl = f"{h:.4f} s" if h < 0.05 else f"{h:.2f} s"
        ax1.annotate(lbl, xy=(b.get_x() + b.get_width() / 2, h), xytext=(0, 4),
                     textcoords="offset points", ha="center", va="bottom", fontsize=9.5, fontweight="bold")

    tokens = [m["average_tokens_ticket"] for m in metrics_list]
    bars2 = ax2.bar(archs, tokens, color=colors, width=0.5, edgecolor="black", linewidth=0.6)
    ax2.set_ylabel("Total Token / Tiket", fontsize=11, fontweight="bold")
    ax2.set_title("Rata-rata Konsumsi Token per Tiket", fontsize=12, fontweight="bold")
    ax2.set_ylim(0, max(tokens) * 1.3 if max(tokens) > 0 else 100)
    for b in bars2:
        h = b.get_height()
        ax2.annotate(f"{h:.1f}", xy=(b.get_x() + b.get_width() / 2, h), xytext=(0, 4),
                     textcoords="offset points", ha="center", va="bottom", fontsize=9.5, fontweight="bold")

    plt.suptitle("Analisis Trade-Off Efisiensi Komputasi 4 Skenario", fontsize=14, fontweight="bold", y=0.98)
    plt.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(save_path)
    plt.close(fig)


def main():
    base_dir = Path(__file__).resolve().parent
    pipeline_dir = base_dir.parent

    s1_path = pipeline_dir / "00_classical_ml_baseline" / "results" / "classical_ml_predictions.csv"
    s2_path = pipeline_dir / "05_single_agent_baseline" / "results" / "baseline_predictions.csv"
    s3_path = pipeline_dir / "05b_single_agent_rag" / "results" / "single_agent_rag_predictions.csv"
    s4_path = pipeline_dir / "06_multi_agent_system" / "results" / "mas_predictions.csv"

    for p, label in [(s1_path, "Skenario 1"), (s2_path, "Skenario 2"), (s3_path, "Skenario 3"), (s4_path, "Skenario 4")]:
        if not p.exists():
            print(f"[ERROR] File prediksi {label} belum tersedia: {p}")
            sys.exit(1)

    df_s1 = pd.read_csv(s1_path)
    df_s2 = pd.read_csv(s2_path)
    df_s3 = pd.read_csv(s3_path)
    df_s4 = pd.read_csv(s4_path)

    m_s1 = compute_metrics_for_df(df_s1, "Skenario 1: Classical ML (TF-IDF + LR)")
    m_s2 = compute_metrics_for_df(df_s2, "Skenario 2: Monolithic Single-Agent")
    m_s3 = compute_metrics_for_df(df_s3, "Skenario 3: Single-Agent + RAG")
    m_s4 = compute_metrics_for_df(df_s4, "Skenario 4: Modular Chained MAS")
    m_hyb = simulate_hybrid_architecture(df_s2, df_s4)

    cascade = analyze_error_cascade(df_s2, df_s3, df_s4)

    results_dir = base_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    fig_dir = results_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    summary = {
        "timestamp": datetime.now().isoformat(),
        "scenarios": {
            "scenario_1_classical_ml": m_s1,
            "scenario_2_single_agent": m_s2,
            "scenario_3_single_agent_rag": m_s3,
            "scenario_4_multi_agent_mas": m_s4,
            "hybrid_tiered_framework": m_hyb,
        },
        "error_cascade_analysis_s4": cascade,
    }

    with open(results_dir / "comparative_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    table_rows = [
        {
            "Metrik Evaluasi": "Total Tiket Evaluasi (N)",
            "Skenario 1 (Classical ML)": str(m_s1["total_tickets"]),
            "Skenario 2 (Single-Agent)": str(m_s2["total_tickets"]),
            "Skenario 3 (Single+RAG)": str(m_s3["total_tickets"]),
            "Skenario 4 (Chained MAS)": str(m_s4["total_tickets"]),
        },
        {
            "Metrik Evaluasi": "Akurasi Keseluruhan (%)",
            "Skenario 1 (Classical ML)": f"{m_s1['overall_accuracy']}% ({m_s1['correct_tickets']}/500)",
            "Skenario 2 (Single-Agent)": f"{m_s2['overall_accuracy']}% ({m_s2['correct_tickets']}/500)",
            "Skenario 3 (Single+RAG)": f"{m_s3['overall_accuracy']}% ({m_s3['correct_tickets']}/500)",
            "Skenario 4 (Chained MAS)": f"{m_s4['overall_accuracy']}% ({m_s4['correct_tickets']}/500)",
        },
        {
            "Metrik Evaluasi": "Macro-Precision (%)",
            "Skenario 1 (Classical ML)": f"{m_s1['macro_precision']}%",
            "Skenario 2 (Single-Agent)": f"{m_s2['macro_precision']}%",
            "Skenario 3 (Single+RAG)": f"{m_s3['macro_precision']}%",
            "Skenario 4 (Chained MAS)": f"{m_s4['macro_precision']}%",
        },
        {
            "Metrik Evaluasi": "Macro-Recall (%)",
            "Skenario 1 (Classical ML)": f"{m_s1['macro_recall']}%",
            "Skenario 2 (Single-Agent)": f"{m_s2['macro_recall']}%",
            "Skenario 3 (Single+RAG)": f"{m_s3['macro_recall']}%",
            "Skenario 4 (Chained MAS)": f"{m_s4['macro_recall']}%",
        },
        {
            "Metrik Evaluasi": "Macro-F1 Score (%)",
            "Skenario 1 (Classical ML)": f"{m_s1['macro_f1']}%",
            "Skenario 2 (Single-Agent)": f"{m_s2['macro_f1']}%",
            "Skenario 3 (Single+RAG)": f"{m_s3['macro_f1']}%",
            "Skenario 4 (Chained MAS)": f"{m_s4['macro_f1']}%",
        },
    ]

    for d in DEPARTMENTS:
        table_rows.append({
            "Metrik Evaluasi": f"Akurasi {d} ({DEPT_TO_SHORT[d]})",
            "Skenario 1 (Classical ML)": f"{m_s1['per_department_accuracy'][d]}%",
            "Skenario 2 (Single-Agent)": f"{m_s2['per_department_accuracy'][d]}%",
            "Skenario 3 (Single+RAG)": f"{m_s3['per_department_accuracy'][d]}%",
            "Skenario 4 (Chained MAS)": f"{m_s4['per_department_accuracy'][d]}%",
        })

    table_rows.extend([
        {
            "Metrik Evaluasi": "Validitas Skema JSON/Function Call (%)",
            "Skenario 1 (Classical ML)": "N/A",
            "Skenario 2 (Single-Agent)": f"{m_s2['schema_validity_rate']}%",
            "Skenario 3 (Single+RAG)": f"{m_s3['schema_validity_rate']}%",
            "Skenario 4 (Chained MAS)": f"{m_s4['schema_validity_rate']}%",
        },
        {
            "Metrik Evaluasi": "Rata-rata Latensi per Tiket (detik)",
            "Skenario 1 (Classical ML)": f"{m_s1['average_latency_sec']} s",
            "Skenario 2 (Single-Agent)": f"{m_s2['average_latency_sec']} s",
            "Skenario 3 (Single+RAG)": f"{m_s3['average_latency_sec']} s",
            "Skenario 4 (Chained MAS)": f"{m_s4['average_latency_sec']} s",
        },
        {
            "Metrik Evaluasi": "Rata-rata Konsumsi Token per Tiket",
            "Skenario 1 (Classical ML)": "0 token",
            "Skenario 2 (Single-Agent)": f"{m_s2['average_tokens_ticket']} token",
            "Skenario 3 (Single+RAG)": f"{m_s3['average_tokens_ticket']} token",
            "Skenario 4 (Chained MAS)": f"{m_s4['average_tokens_ticket']} token",
        },
    ])

    df_table = pd.DataFrame(table_rows)
    df_table.to_csv(results_dir / "comparative_metrics_table.csv", index=False, encoding="utf-8")

    md_table = df_table.to_markdown(index=False)
    with open(results_dir / "comparative_metrics_table.md", "w", encoding="utf-8") as f:
        f.write("# Tabel Komparasi Hasil Eksperimen 4 Skenario (Golden Benchmark N=500)\n\n")
        f.write(md_table + "\n")

    metrics_list = [m_s1, m_s2, m_s3, m_s4]
    generate_4scenario_accuracy_chart(metrics_list, fig_dir / "accuracy_by_department.png")
    generate_4scenario_confusion_matrices(
        [df_s1, df_s2, df_s3, df_s4],
        [
            "(A) Skenario 1: Classical ML (TF-IDF + LR)",
            "(B) Skenario 2: Monolithic Single-Agent",
            "(C) Skenario 3: Single-Agent + RAG Handbook",
            "(D) Skenario 4: Modular Chained MAS"
        ],
        fig_dir / "confusion_matrices_comparison.png"
    )
    generate_latency_token_chart_4scenarios(metrics_list, fig_dir / "latency_token_tradeoff.png")

    print("\n" + "=" * 85)
    print("COMPARATIVE EVALUATION SUMMARY (4 SCENARIOS - GOLDEN BENCHMARK N=500):")
    print("=" * 85)
    print(md_table)
    print("\nERROR CASCADE ANALYSIS (SKENARIO 4):")
    print(json.dumps(cascade, indent=2, ensure_ascii=False))
    print("\nHYBRID TIERED FRAMEWORK SIMULATION (S2 FAST-PATH + S4 ESCALATION):")
    print(json.dumps({
        "overall_accuracy": m_hyb["overall_accuracy"],
        "macro_f1": m_hyb["macro_f1"],
        "average_latency_sec": m_hyb["average_latency_sec"],
        "average_tokens_ticket": m_hyb["average_tokens_ticket"],
        "fast_path_rate_percent": m_hyb["fast_path_rate_percent"],
        "escalation_rate_percent": m_hyb["escalation_rate_percent"],
        "per_department_accuracy": m_hyb["per_department_accuracy"]
    }, indent=2, ensure_ascii=False))
    print("=" * 85)


if __name__ == "__main__":
    main()

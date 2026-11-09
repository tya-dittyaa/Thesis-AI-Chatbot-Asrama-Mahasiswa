"""
Pipeline Skenario 1: Classical Supervised Machine Learning Baseline (TF-IDF + Logistic Regression)
Melatih TF-IDF Vectorizer (ngram 1-2, max_features=10000) + Logistic Regression pada train_pool.csv (29.814 tiket)
dan mengevaluasi pada Golden Benchmark (test_golden_benchmark_500.csv, N=500).
"""

import time
import json
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_recall_fscore_support

DEPT_CODE_TO_NAME = {
    "ED": "Estate Department",
    "OP": "Operations",
    "FN": "Finance",
    "MR": "Marketing",
    "SO": "Student Support Office",
}
DEPT_NAME_TO_CODE = {v: k for k, v in DEPT_CODE_TO_NAME.items()}
DEPARTMENTS = list(DEPT_CODE_TO_NAME.values())


def main():
    base_dir = Path(__file__).resolve().parent
    pipeline_dir = base_dir.parent
    split_dir = pipeline_dir / "02_data_splitting" / "data"

    train_path = split_dir / "train_pool.csv"
    test_path = split_dir / "test_golden_benchmark_500.csv"

    assert train_path.exists(), f"Train pool tidak ditemukan: {train_path}"
    assert test_path.exists(), f"Test benchmark tidak ditemukan: {test_path}"

    df_train = pd.read_csv(train_path)
    df_test = pd.read_csv(test_path)

    X_train_text = df_train["CleanedComplaint"].fillna("").astype(str)
    y_train = df_train["HandledDepartmentName"].astype(str)

    X_test_text = df_test["CleanedComplaint"].fillna("").astype(str)
    y_test = df_test["HandledDepartmentName"].astype(str)

    print(f"[Skenario 1] Melatih TF-IDF + Logistic Regression pada {len(df_train)} tiket train_pool...")
    t_train_start = time.perf_counter()
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=10000, sublinear_tf=True)
    X_train_vec = vectorizer.fit_transform(X_train_text)

    clf = LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42, C=1.0)
    clf.fit(X_train_vec, y_train)
    train_time = time.perf_counter() - t_train_start
    print(f"[Skenario 1] Pelatihan selesai dalam {train_time:.3f} detik.")

    # Evaluasi inferensi per tiket pada Golden Benchmark (N=500)
    results = []
    for idx, row in df_test.iterrows():
        t0 = time.perf_counter()
        text = str(row.get("CleanedComplaint", "") or "")
        vec = vectorizer.transform([text])
        pred_dept = str(clf.predict(vec)[0])
        probs = clf.predict_proba(vec)[0]
        conf = float(np.max(probs))
        lat = time.perf_counter() - t0

        handled_dept = str(row.get("HandledDepartmentName", "")).strip()
        initial_dept = str(row.get("InitialDepartmentName", "")).strip()
        is_rerouted = int(row.get("IsRerouted", 0))
        is_correct = int(pred_dept.lower() == handled_dept.lower())
        was_reroute_fixed = int(is_rerouted == 1 and is_correct == 1 and pred_dept.lower() != initial_dept.lower())

        results.append({
            "FeedbackHeaderID": str(row["FeedbackHeaderID"]),
            "CreatedDate": row.get("CreatedDate", ""),
            "SubjectCategory": row.get("SubjectCategory", ""),
            "InitialDepartmentName": initial_dept,
            "HandledDepartmentName": handled_dept,
            "IsRerouted": is_rerouted,
            "PredictedDepartmentCode": DEPT_NAME_TO_CODE.get(pred_dept, ""),
            "PredictedDepartmentName": pred_dept,
            "PredictedCategory": "N/A (Classical ML)",
            "UrgencyLevel": "N/A",
            "FacilityItem": "N/A",
            "ConfidenceScore": round(conf, 3),
            "IsCorrect": is_correct,
            "WasRerouteFixed": was_reroute_fixed,
            "IsValidJson": 0,
            "LatencySeconds": round(lat, 6),
            "TotalTokens": 0,
            "ErrorMessage": ""
        })

    df_final = pd.DataFrame(results)
    assert len(df_final) == 500, f"Jumlah hasil harus 500, ditemukan {len(df_final)}"

    results_dir = base_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    pred_csv = results_dir / "classical_ml_predictions.csv"
    summary_json = results_dir / "classical_ml_summary.json"
    df_final.to_csv(pred_csv, index=False, encoding="utf-8")

    total = len(df_final)
    correct = int(df_final["IsCorrect"].sum())
    overall_acc = round(correct / total * 100, 2)

    p_macro, r_macro, f1_macro, _ = precision_recall_fscore_support(
        df_final["HandledDepartmentName"], df_final["PredictedDepartmentName"],
        labels=DEPARTMENTS, average="macro", zero_division=0
    )

    dept_metrics = {}
    for dept_name in DEPARTMENTS:
        d_df = df_final[df_final["HandledDepartmentName"] == dept_name]
        d_tot = len(d_df)
        d_cor = int(d_df["IsCorrect"].sum())
        dept_metrics[dept_name] = {
            "total_tickets": d_tot,
            "correct_predictions": d_cor,
            "accuracy_percent": round(d_cor / d_tot * 100, 2) if d_tot > 0 else 0.0
        }

    summary = {
        "timestamp": datetime.now().isoformat(),
        "scenario": "Skenario 1: Classical Supervised ML (TF-IDF + Logistic Regression)",
        "model_used": "TfidfVectorizer(ngram 1-2, 10k) + LogisticRegression(balanced)",
        "train_samples": len(df_train),
        "total_evaluated": total,
        "overall_accuracy_percent": overall_acc,
        "macro_precision_percent": round(float(p_macro * 100), 2),
        "macro_recall_percent": round(float(r_macro * 100), 2),
        "macro_f1_percent": round(float(f1_macro * 100), 2),
        "average_latency_seconds": round(float(df_final["LatencySeconds"].mean()), 5),
        "average_tokens_per_ticket": 0.0,
        "per_department_metrics": dept_metrics
    }

    with open(summary_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print("=" * 70)
    print("SKENARIO 1 (CLASSICAL ML: TF-IDF + LOGISTIC REGRESSION) SUMMARY:")
    print("=" * 70)
    print(f"Overall Accuracy : {overall_acc:.2f}% ({correct}/{total})")
    print(f"Macro-F1 Score   : {summary['macro_f1_percent']:.2f}%")
    print(f"Avg Latency      : {summary['average_latency_seconds']:.5f} s/ticket")
    for dept, m in dept_metrics.items():
        print(f"  - {dept:25s}: {m['accuracy_percent']:6.2f}% ({m['correct_predictions']}/{m['total_tickets']})")
    print("=" * 70)


if __name__ == "__main__":
    main()


"""
Pipeline Tahap 2a: Label Cleaning - Deteksi & Hapus Anomali Label Noise
==========================================================================
Masalah: Data legacy Binus Square tidak selalu memperbarui HandledDepartmentName
ketika tiket dialihkan. Contoh: keluhan tagihan listrik bisa tetap berlabel
"Estate Department" walau seharusnya ditangani Finance.

PENDEKATAN: Cleaning dilakukan di level FULL DATASET (bukan di benchmark),
sehingga benchmark yang dihasilkan di tahap 2b sudah 100% bersih dari awal.

Input : pipeline/01_data_filtering/data/feedback_2015_2025.csv
Output: pipeline/02_data_splitting/data/
        - feedback_2015_2025_clean.csv      <- dataset bersih (tanpa anomali)
        - anomaly_report.json               <- laporan temuan noise
        - anomaly_samples.csv               <- sampel tiket anomali
"""

import os, json
import pandas as pd

CURRENT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT  = os.path.abspath(os.path.join(CURRENT_DIR, '..', '..'))
INPUT_PATH    = os.path.join(PROJECT_ROOT, 'pipeline', '01_data_filtering', 'data', 'feedback_2015_2025.csv')
OUTPUT_DIR    = os.path.join(CURRENT_DIR, 'data')
CLEAN_PATH    = os.path.join(OUTPUT_DIR, 'feedback_2015_2025_clean.csv')
REPORT_PATH   = os.path.join(OUTPUT_DIR, 'anomaly_report.json')
SAMPLES_PATH  = os.path.join(OUTPUT_DIR, 'anomaly_samples.csv')

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ─────────────────────────────────────────────────────────────
# Rule Definitions
# Aturan 1: ED + keyword billing di teks keluhan
BILLING_KEYWORDS = [
    'tagihan', 'bayar', 'pembayaran', 'cicilan', 'iuran', 'biaya',
    'invoice', 'rekening', 'denda', 'kwh', 'penggunaan listrik',
    'struk', 'nota', 'tunggakan', 'administrasi', 'slip'
]
# Aturan 2: ED + SubjectCategory yang jelas urusan Finance
FINANCE_SUBJECT_CATEGORIES = {
    'Electricity Bill', 'Room Payment and Due Date', 'Security Deposit',
    'Billing', 'Payment', 'Invoice', 'Fine / Penalty'
}
# ─────────────────────────────────────────────────────────────


def detect_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    """Tambah kolom IsAnomalyFlagged + AnomalyType ke dataframe."""
    df = df.copy()
    df['IsAnomalyFlagged'] = 0
    df['AnomalyType']      = ''

    ed_mask = df['HandledDepartmentName'] == 'Estate Department'
    ed_df   = df[ed_mask].copy()

    for idx, row in ed_df.iterrows():
        text = str(row.get('CleanedComplaint', '') or row.get('RawMessage', '') or '').lower()
        subject = str(row.get('SubjectCategory', '') or '').strip()

        # Aturan 1 – keyword billing
        matched_kw = [kw for kw in BILLING_KEYWORDS if kw in text]
        if matched_kw:
            df.at[idx, 'IsAnomalyFlagged'] = 1
            df.at[idx, 'AnomalyType'] = f'suspected_finance_mislabeled_as_ED (keyword: {matched_kw[0]})'
            continue

        # Aturan 2 – subject category Finance
        if subject in FINANCE_SUBJECT_CATEGORIES:
            df.at[idx, 'IsAnomalyFlagged'] = 1
            df.at[idx, 'AnomalyType'] = f'ED_label_with_finance_subject_category ({subject})'

    return df


def run():
    print('=' * 65)
    print('PIPELINE 02a: LABEL CLEANING - DETEKSI ANOMALI FULL DATASET')
    print('=' * 65)

    if not os.path.exists(INPUT_PATH):
        print(f'[ERROR] File tidak ditemukan: {INPUT_PATH}')
        return False

    df = pd.read_csv(INPUT_PATH)
    total_raw = len(df)
    print(f'Input : {total_raw:,} tiket dari feedback_2015_2025.csv')

    # Deteksi
    df_flagged = detect_anomalies(df)
    anomaly_df = df_flagged[df_flagged['IsAnomalyFlagged'] == 1].copy()
    clean_df   = df_flagged[df_flagged['IsAnomalyFlagged'] == 0].drop(
        columns=['IsAnomalyFlagged', 'AnomalyType']
    ).reset_index(drop=True)

    n_anomaly = len(anomaly_df)
    n_clean   = len(clean_df)

    print(f'\n[HASIL DETEKSI ANOMALI]')
    print(f'  Total tiket    : {total_raw:,}')
    print(f'  Anomali ditemukan: {n_anomaly} ({n_anomaly/total_raw*100:.2f}%)')
    print(f'  Tiket bersih   : {n_clean:,}')

    print(f'\n[BREAKDOWN TIPE ANOMALI]')
    for atype, cnt in anomaly_df['AnomalyType'].value_counts().items():
        print(f'  * {atype}: {cnt} tiket')

    print(f'\n[DISTRIBUSI CLEAN DATA PER DEPARTEMEN]')
    for dept, cnt in clean_df['HandledDepartmentName'].value_counts().items():
        print(f'  * {dept:25}: {cnt:,}')

    # Simpan
    clean_df.to_csv(CLEAN_PATH, index=False, encoding='utf-8')
    anomaly_df.to_csv(SAMPLES_PATH, index=False, encoding='utf-8')

    report = {
        'stage': '02a_label_cleaning',
        'input_file': 'feedback_2015_2025.csv',
        'total_raw': int(total_raw),
        'total_anomaly': int(n_anomaly),
        'total_clean': int(n_clean),
        'anomaly_rate_pct': round(n_anomaly / total_raw * 100, 4),
        'anomaly_breakdown': anomaly_df['AnomalyType'].value_counts().to_dict(),
        'output_clean_file': 'feedback_2015_2025_clean.csv',
        'output_anomaly_file': 'anomaly_samples.csv'
    }
    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f'\n[SUCCESS]')
    print(f'  Clean dataset  : {CLEAN_PATH}')
    print(f'  Anomaly samples: {SAMPLES_PATH}')
    print(f'  Anomaly report : {REPORT_PATH}')
    print('=' * 65)
    return True


if __name__ == '__main__':
    run()

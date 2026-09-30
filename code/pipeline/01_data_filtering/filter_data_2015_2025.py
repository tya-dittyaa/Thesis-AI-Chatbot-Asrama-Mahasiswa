"""
Pipeline Tahap 1: Pemfilteran Data Keluhan Periode 2015 - 2025 (1 Dekade)
Input: data/processed/boarder_feedback_dataset.csv
Output: pipeline/01_data_filtering/data/feedback_2015_2025.csv
"""

import os
import pandas as pd

# Setup direktori
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))

INPUT_DATA_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "boarder_feedback_dataset.csv")
OUTPUT_DIR = os.path.join(CURRENT_DIR, "data")
OUTPUT_DATA_PATH = os.path.join(OUTPUT_DIR, "feedback_2015_2025.csv")

os.makedirs(OUTPUT_DIR, exist_ok=True)

def filter_data_2015_2025():
    print("=" * 60)
    print("PIPELINE 01: FILTER DATASET PERIODE 2015 - 2025")
    print("=" * 60)

    if not os.path.exists(INPUT_DATA_PATH):
        print(f"[ERROR] File input tidak ditemukan: {INPUT_DATA_PATH}")
        return False

    print(f"Membaca dataset utama dari: {INPUT_DATA_PATH}")
    df = pd.read_csv(INPUT_DATA_PATH)
    total_initial = len(df)
    print(f"Total baris awal: {total_initial:,}")

    # Parse tanggal dan ambil tahun
    df['CreatedDate'] = pd.to_datetime(df['CreatedDate'], errors='coerce')
    df['Year'] = df['CreatedDate'].dt.year

    # Filter rentang tahun 2015 - 2025
    mask = (df['Year'] >= 2015) & (df['Year'] <= 2025)
    df_filtered = df[mask].copy()

    # Drop kolom helper 'Year'
    df_filtered = df_filtered.drop(columns=['Year'])

    total_filtered = len(df_filtered)
    print(f"\n[HASIL FILTERING]")
    print(f"  -> Total tiket 2015 - 2025: {total_filtered:,} baris ({total_filtered/total_initial*100:.2f}% dari data)")
    print(f"  -> Data 2014 (fase awal) dibuang: {(df['Year'] == 2014).sum():,} baris")
    print(f"  -> Data 2026 (tahun berjalan) dibuang: {(df['Year'] == 2026).sum():,} baris")

    print("\n[DISTRIBUSI KELAS DEPARTEMEN PENANGAN (GROUND TRUTH)]")
    counts = df_filtered['HandledDepartmentName'].value_counts()
    pcts = df_filtered['HandledDepartmentName'].value_counts(normalize=True) * 100
    for dept, count in counts.items():
        print(f"  * {dept:25}: {count:,} tiket ({pcts[dept]:.2f}%)")

    # Simpan ke pipeline/01_data_filtering/data/
    df_filtered.to_csv(OUTPUT_DATA_PATH, index=False, encoding="utf-8")
    print("\n" + "=" * 60)
    print(f"[SUCCESS] Dataset 2015-2025 berhasil disimpan di:")
    print(f"  -> {OUTPUT_DATA_PATH}")
    print("=" * 60)
    return True

if __name__ == "__main__":
    filter_data_2015_2025()

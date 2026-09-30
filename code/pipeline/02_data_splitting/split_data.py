"""
Pipeline Tahap 2b: Data Splitting - Benchmark dari Data Bersih
==============================================================
Input : pipeline/02_data_splitting/data/feedback_2015_2025_clean.csv
Output:
  - data/test_golden_benchmark_500.csv  (500 tiket seimbang, BERSIH)
  - data/train_pool.csv                 (sisa tiket untuk pool latih)

CATATAN: Benchmark 500 ini sudah bersih dari anomali label noise karena
input-nya adalah clean dataset dari tahap 02a. Tidak ada "497" vs "500" —
benchmark SELALU 500 tiket bersih.
"""

import os
import pandas as pd

CURRENT_DIR  = os.path.dirname(os.path.abspath(__file__))
CLEAN_PATH   = os.path.join(CURRENT_DIR, 'data', 'feedback_2015_2025_clean.csv')
OUTPUT_DIR   = os.path.join(CURRENT_DIR, 'data')
OUTPUT_TEST  = os.path.join(OUTPUT_DIR, 'test_golden_benchmark_500.csv')
OUTPUT_TRAIN = os.path.join(OUTPUT_DIR, 'train_pool.csv')

os.makedirs(OUTPUT_DIR, exist_ok=True)


def split_dataset(samples_per_class: int = 100, random_seed: int = 42):
    print('=' * 65)
    print('PIPELINE 02b: DATA SPLITTING - GOLDEN BENCHMARK 500 (CLEAN)')
    print('=' * 65)

    if not os.path.exists(CLEAN_PATH):
        print(f'[ERROR] Clean dataset tidak ditemukan: {CLEAN_PATH}')
        print('  -> Jalankan 02a_clean_dataset.py terlebih dahulu!')
        return False

    df = pd.read_csv(CLEAN_PATH)
    print(f'Input: {len(df):,} tiket bersih dari feedback_2015_2025_clean.csv')

    departments = df['HandledDepartmentName'].value_counts()
    print(f'\n[KETERSEDIAAN DATA PER DEPARTEMEN]')
    for dept, cnt in departments.items():
        sufficient = 'OK' if cnt >= samples_per_class else f'KURANG (hanya {cnt})'
        print(f'  * {dept:25}: {cnt:,} tersedia, butuh {samples_per_class} -> {sufficient}')

    # Sampling stratified - 100 per departemen dari clean data
    test_golden = pd.concat([
        group.sample(n=min(samples_per_class, len(group)), random_state=random_seed)
        for _, group in df.groupby('HandledDepartmentName')
    ]).reset_index(drop=True)

    # Sisa jadi train pool
    test_ids   = set(test_golden['FeedbackHeaderID'])
    train_pool = df[~df['FeedbackHeaderID'].isin(test_ids)].reset_index(drop=True)

    total_benchmark = len(test_golden)
    print(f'\n[DISTRIBUSI GOLDEN BENCHMARK (TEST SET - {total_benchmark} TIKET BERSIH)]')
    print('-' * 50)
    for dept, cnt in test_golden['HandledDepartmentName'].value_counts().items():
        print(f'  * {dept:25}: {cnt} tiket')
    print(f'  {"TOTAL":25}: {total_benchmark} tiket')

    print(f'\n[DISTRIBUSI TRAIN / FEW-SHOT POOL ({len(train_pool):,} TIKET)]')
    print('-' * 50)
    for dept, cnt in train_pool['HandledDepartmentName'].value_counts().items():
        pct = cnt / len(train_pool) * 100
        print(f'  * {dept:25}: {cnt:,} ({pct:.2f}%)')

    test_golden.to_csv(OUTPUT_TEST,  index=False, encoding='utf-8')
    train_pool.to_csv(OUTPUT_TRAIN,  index=False, encoding='utf-8')

    print(f'\n[SUCCESS]')
    print(f'  Benchmark (test) : {OUTPUT_TEST}  ({total_benchmark} tiket)')
    print(f'  Train pool       : {OUTPUT_TRAIN}  ({len(train_pool):,} tiket)')
    print('=' * 65)
    return True


if __name__ == '__main__':
    split_dataset()

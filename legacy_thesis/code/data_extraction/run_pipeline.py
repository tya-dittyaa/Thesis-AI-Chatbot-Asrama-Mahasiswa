"""
Main Pipeline Runner untuk Ekstraksi & Pembersihan Data BSQ Feedback
Jalankan file ini untuk melakukan seluruh proses:
1. Ekstraksi data mentah dari SQL Server BSQDB -> data/raw/
2. Pembersihan & anonimisasi teks -> data/processed/
"""

import sys
from extract_raw import extract_raw_data
from clean_data import run_cleansing

def main():
    print("============================================================")
    print("   BSQ FEEDBACK DATA PIPELINE (THESIS ADITYA FAJRI)")
    print("============================================================\n")

    # Step 1: Ekstraksi Data Mentah dari Database
    success = extract_raw_data(include_details=True)
    if not success:
        print("\n[GAGAL] Ekstraksi data mentah gagal. Periksa koneksi VPN/database.")
        sys.exit(1)

    print("\n")
    # Step 2: Pembersihan, Pemfilteran Spam, dan Anonimisasi
    success = run_cleansing()
    if not success:
        print("\n[GAGAL] Proses pembersihan dataset gagal.")
        sys.exit(1)

    print("\n[FINISH] SELURUH PIPELINE SELESAI DENGAN SEMPURNA!")

if __name__ == "__main__":
    main()

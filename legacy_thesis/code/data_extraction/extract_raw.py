"""
Modul Ekstraksi Data Mentah (Raw Data Extraction) BSQ Feedback
Menarik 100% data asli dari database BSQDB tanpa modifikasi teks (URL-encoded HTML dipertahankan murni).
Output disimpan ke folder data/raw/.
"""

import os
import time
import pandas as pd
import sys
sys.path.append(os.path.dirname(__file__))
from db_connection import get_connection

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW_DATA_DIR = os.path.join(BASE_DIR, "data", "raw")
OUTPUT_RAW_FEEDBACK = os.path.join(RAW_DATA_DIR, "boarder_feedback_all_raw.csv")
OUTPUT_RAW_DETAILS = os.path.join(RAW_DATA_DIR, "boarder_feedback_details_raw.csv")

SQL_RAW_FEEDBACK = """
SELECT 
    h.FeedbackHeaderID,
    h.CreatedDate,
    h.CreatedUserID,
    h.Message AS RawMessage,
    h.SubjectID,
    COALESCE(s.SubjectName, 'Uncategorized') AS SubjectCategory,
    s.DepartmentID AS InitialDepartmentID,
    COALESCE(d.DepartmentName, 'Operations') AS InitialDepartmentName,
    COALESCE(d.Abbreviation, 'OP') AS InitialDepartmentCode,
    COALESCE(st.StatusName, 'Unknown') AS StatusName
FROM TrFeedbackHeader h
LEFT JOIN MsFeedbackSubject s ON h.SubjectID = s.SubjectID AND s.AuditedActivity != 'D'
LEFT JOIN MsDepartment d ON s.DepartmentID = d.DepartmentId AND d.AuditedActivity != 'D'
LEFT JOIN MsFeedbackStatus st ON h.StatusID = st.StatusID AND st.AuditedActivity != 'D'
WHERE h.AuditedActivity != 'D'
  AND h.Message IS NOT NULL
ORDER BY h.CreatedDate ASC;
"""

SQL_RAW_DETAILS = """
SELECT 
    dt.FeedbackDetailID,
    dt.FeedbackHeaderID,
    dt.AuditedTime AS ReplyTime,
    dt.AuditedUserID,
    dt.ReplyContent AS RawReplyContent,
    dt.DepartmentID AS DetailDepartmentID,
    COALESCE(d.DepartmentName, '') AS DetailDepartmentName,
    COALESCE(d.Abbreviation, '') AS DetailDepartmentCode,
    COALESCE(u.Name, '') AS StaffName,
    COALESCE(u.BinusianID, '') AS StaffBinusianID
FROM TrFeedbackDetail dt
LEFT JOIN MsDepartment d ON dt.DepartmentID = d.DepartmentId
LEFT JOIN MsUser u ON dt.AuditedUserID = u.UserID
WHERE dt.AuditedActivity != 'D'
ORDER BY dt.FeedbackHeaderID, dt.AuditedTime ASC;
"""

def extract_raw_data(include_details=True):
    """
    Ekstrak seluruh data keluhan (headers) dan balasan staff (details)
    langsung ke format CSV mentah di folder data/raw/.
    """
    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    print("=" * 60)
    print("[START] MEMULAI EKSTRAKSI DATA MENTAH (RAW) DARI BSQDB")
    print("=" * 60)

    conn = get_connection()
    if not conn:
        print("[ERROR] Koneksi database gagal. Pastikan VPN aktif.")
        return False

    # 1. Ekstraksi Feedback Header
    start_time = time.time()
    print("\n[1/2] Mengekstrak Feedback Headers (Keluhan Mahasiswa)...")
    df_headers = pd.read_sql(SQL_RAW_FEEDBACK, conn)
    elapsed_headers = time.time() - start_time
    print(f"  -> Selesai dalam {elapsed_headers:.2f} detik. Total: {len(df_headers):,} baris.")

    # Simpan ke CSV data mentah
    df_headers.to_csv(OUTPUT_RAW_FEEDBACK, index=False, encoding="utf-8")
    print(f"  -> File Header Mentah tersimpan di: {OUTPUT_RAW_FEEDBACK}")

    # 2. Ekstraksi Feedback Detail (Opsional / Granular)
    if include_details:
        start_time = time.time()
        print("\n[2/2] Mengekstrak Feedback Details (Riwayat Percakapan / Balasan Staff)...")
        df_details = pd.read_sql(SQL_RAW_DETAILS, conn)
        elapsed_details = time.time() - start_time
        print(f"  -> Selesai dalam {elapsed_details:.2f} detik. Total: {len(df_details):,} baris.")
        df_details.to_csv(OUTPUT_RAW_DETAILS, index=False, encoding="utf-8")
        print(f"  -> File Detail Mentah tersimpan di: {OUTPUT_RAW_DETAILS}")

    conn.close()
    print("\n" + "=" * 60)
    print("[SUCCESS] EKSTRAKSI DATA MENTAH BERHASIL!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    extract_raw_data(include_details=True)

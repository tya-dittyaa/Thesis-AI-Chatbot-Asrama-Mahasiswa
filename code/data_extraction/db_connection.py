"""
Modul Koneksi Database BSQ (Binus Square)
Menyediakan fungsi get_connection() dengan fallback otomatis
antara Windows Authentication (Domain Login) dan SQL Authentication.
"""

import pyodbc

DB_SERVER = "ssg5-binussquare-dev.binus.db"
DB_NAME = "BSQDB_20221117"

def get_connection():
    """
    Membuat koneksi ke database BSQDB.
    Mencoba Windows Authentication terlebih dahulu, lalu fallback ke SQL Authentication.
    """
    driver = "ODBC Driver 17 for SQL Server" if "ODBC Driver 17 for SQL Server" in pyodbc.drivers() else "SQL Server"

    # 1. Coba Windows Authentication (Domain Login)
    conn_str_win = (
        f"DRIVER={{{driver}}};"
        f"SERVER={DB_SERVER};"
        f"DATABASE={DB_NAME};"
        "Trusted_Connection=yes;"
        "TrustServerCertificate=yes;"
    )
    try:
        conn = pyodbc.connect(conn_str_win, timeout=5)
        print("[SUCCESS] Terhubung ke BSQDB via Windows Authentication.")
        return conn
    except Exception as e_win:
        print(f"[INFO] Windows Auth gagal ({e_win}), beralih ke SQL Auth...")

    # 2. Fallback SQL Authentication
    conn_str_sql = (
        f"DRIVER={{{driver}}};"
        f"SERVER={DB_SERVER};"
        f"DATABASE={DB_NAME};"
        "UID=bsq_app_uat;"
        "PWD=B!mW3oD7bDnU$D3v;"
        "TrustServerCertificate=yes;"
    )
    try:
        conn = pyodbc.connect(conn_str_sql, timeout=5)
        print("[SUCCESS] Terhubung ke BSQDB via SQL Authentication.")
        return conn
    except Exception as e_sql:
        print(f"[ERROR] Gagal terhubung ke database BSQDB: {e_sql}")
        return None

if __name__ == "__main__":
    print(f"Mengetes koneksi ke {DB_SERVER} / {DB_NAME}...")
    conn = get_connection()
    if conn:
        print("[TEST OK] Koneksi database berhasil!")
        conn.close()
    else:
        print("[TEST GAGAL] Pastikan GlobalProtect VPN Binus aktif.")

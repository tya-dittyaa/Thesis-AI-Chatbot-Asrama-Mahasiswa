"""
Modul Pembersihan & Pra-Pengolahan Teks (Data Cleansing & Thread Anonymization)
Membaca data mentah dari data/raw/ dan menghasilkan dataset komprehensif di data/processed/.

Fitur Pembersihan & Ekstraksi:
1. URL-decode & HTML Entity unescaping (&nbsp;, &quot;, &amp;, dll).
2. Penghapusan tag HTML (<p>, <img>, <span>, <br>, dll).
3. Pemfilteran data sampah testing developer/QA ('test sp linq', keyboard mash, dll).
4. Anonimisasi identitas (NIM, nomor kamar, nomor telepon) sesuai Bab 3.3 Tesis.
5. Pemisahan peran pengirim multi-turn (Boarder vs Staff).
6. Pengelompokan balasan: First Staff Reply, Latest Staff Reply, All Staff Replies, dan Conversation Thread lengkap.
7. Penentuan Departemen Riil Penangan (HandledDepartment / Ground Truth) & Deteksi Reroute (IsRerouted).
8. Ekstraksi metrik SLA respon (FirstResponseMinutes).
"""

import os
import re
import html
import urllib.parse
import collections
import pandas as pd
import numpy as np

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW_DATA_DIR = os.path.join(BASE_DIR, "data", "raw")
RAW_FILE_FEEDBACK = os.path.join(RAW_DATA_DIR, "boarder_feedback_all_raw.csv")
RAW_FILE_DETAILS = os.path.join(RAW_DATA_DIR, "boarder_feedback_details_raw.csv")

PROCESSED_DATA_DIR = os.path.join(BASE_DIR, "data", "processed")
OUTPUT_CLEAN_CSV = os.path.join(PROCESSED_DATA_DIR, "boarder_feedback_dataset.csv")

def clean_html_and_decode(text):
    """Decode URL encoding, unescape HTML entities, dan hapus tag HTML."""
    if not isinstance(text, str) or not text.strip():
        return ""
    # 1. URL Decode (%20, %3C, dll)
    try:
        decoded = urllib.parse.unquote_plus(text)
    except Exception:
        decoded = text
    # 2. HTML Entity Unescape (&nbsp; -> spasi, &amp; -> &, &quot; -> ", dll)
    unescaped = html.unescape(decoded)
    # 3. Hapus tag HTML
    no_html = re.sub(r'<[^>]+>', ' ', unescaped)
    # 4. Normalkan whitespace
    clean_text = ' '.join(no_html.split())
    return clean_text

def is_spam_or_test_entry(text):
    """
    Mendeteksi apakah teks adalah data testing developer/QA atau spam keyboard mashing.
    Contoh: 'Sjjsjsjsjsjsjjsjdjdjdjdjdjdjdjdjdjdj', 'test sp linq', 'p adu ml'.
    """
    if not isinstance(text, str):
        return True
    
    clean = text.strip()
    if len(clean) < 4:
        return True

    # 1. Deteksi ketikan asal berulang (keyboard mash seperti sjsjsj, jdjdjd, xxxxx)
    if re.search(r'([a-zA-Z])\1{4,}', clean, re.IGNORECASE):
        return True
    if re.search(r'(sj|jd|js|dj|sk|ks|sh|hs){3,}', clean, re.IGNORECASE):
        return True

    # 2. Deteksi teks testing murni di awal kalimat
    if re.match(r'^(test|tes|testing|coba|trial)\b', clean, re.IGNORECASE) and len(clean.split()) <= 4:
        return True

    # 3. Frasa pengujian developer spesifik
    qa_phrases = ["test sp linq", "p adu ml", "tes testing", "asdf", "qwerty"]
    if any(p in clean.lower() for p in qa_phrases):
        return True

    return False

def anonymize_text(text):
    """Sensor identitas pribadi sesuai Bab 3.3 Tesis."""
    if not isinstance(text, str):
        return ""

    # 1. Sensor NIM (10 digit angka berturut-turut)
    text = re.sub(r'\b\d{10}\b', '[NIM_ANONIM]', text)

    # 2. Sensor Gedung & Nomor Kamar (Oak, Pine, Ash, Sycamore, A1204, B.12.22, Kamar 402, dll)
    text = re.sub(r'(?i)\b(Oak|Pine|Ash|Sycamore)[ -]?\d{3,4}\b', '[KAMAR_ANONIM]', text)
    text = re.sub(r'(?i)\b[ABCD]\.?\d{2,4}\b', '[KAMAR_ANONIM]', text)
    text = re.sub(r'(?i)(kamar|kmr|room)\s*#?\s*([A-Za-z0-9\.\-]+)', r'\1 [KAMAR_ANONIM]', text)

    # 3. Sensor Nomor HP / Kontak (+62 atau 08)
    text = re.sub(r'(\+62|08)[0-9\-\s]{8,13}', '[PHONE_ANONIM]', text)

    return text.strip()

def run_cleansing():
    """Jalankan proses pembersihan dan penggabungan thread multi-reply dari raw ke processed."""
    os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)

    if not os.path.exists(RAW_FILE_FEEDBACK):
        print(f"[ERROR] File header mentah tidak ditemukan: {RAW_FILE_FEEDBACK}")
        return False
    if not os.path.exists(RAW_FILE_DETAILS):
        print(f"[ERROR] File detail mentah tidak ditemukan: {RAW_FILE_DETAILS}")
        return False

    print("=" * 60)
    print("[CLEAN] MEMULAI DATA CLEANSING, ANONYMIZATION & THREADING")
    print("=" * 60)

    # 1. Load Data
    print(f"Membaca data Header mentah: {RAW_FILE_FEEDBACK}")
    df_h = pd.read_csv(RAW_FILE_FEEDBACK)
    total_raw_headers = len(df_h)
    print(f"  -> Total Header mentah: {total_raw_headers:,} baris.")

    print(f"Membaca data Details mentah: {RAW_FILE_DETAILS}")
    df_d = pd.read_csv(RAW_FILE_DETAILS)
    print(f"  -> Total Detail balasan mentah: {len(df_d):,} baris.")

    # 2. Pembersihan & Filter Header
    print("\n[1/4] Membersihkan dan memfilter keluhan awal mahasiswa...")
    df_h['CleanedComplaint'] = df_h['RawMessage'].apply(clean_html_and_decode)
    is_spam = df_h['CleanedComplaint'].apply(is_spam_or_test_entry)
    spam_count = is_spam.sum()
    print(f"  -> Ditemukan {spam_count:,} tiket testing/spam developer yang dieliminasi.")
    df_h = df_h[~is_spam].copy()
    df_h['CleanedComplaint'] = df_h['CleanedComplaint'].apply(anonymize_text)

    # Buat map CreatedUserID untuk identifikasi pengirim di detail
    header_user_map = dict(zip(df_h['FeedbackHeaderID'], df_h['CreatedUserID']))
    valid_header_ids = set(df_h['FeedbackHeaderID'])

    # 3. Pembersihan & Pemetaan Peran Pengirim di Details
    print("\n[2/4] Membersihkan balasan dan memetakan peran pengirim (Boarder vs Staff)...")
    # Filter hanya details yang tiket headernya valid
    df_d = df_d[df_d['FeedbackHeaderID'].isin(valid_header_ids)].copy()
    df_d['CleanedReply'] = df_d['RawReplyContent'].apply(clean_html_and_decode)
    df_d['CleanedReply'] = df_d['CleanedReply'].apply(anonymize_text)

    # Menentukan peran pengirim: Boarder vs Staff
    def get_sender_role(row):
        boarder_uid = header_user_map.get(row['FeedbackHeaderID'])
        if pd.notna(boarder_uid) and pd.notna(row['AuditedUserID']) and str(row['AuditedUserID']).strip().upper() == str(boarder_uid).strip().upper():
            return 'Boarder'
        return 'Staff'

    df_d['SenderRole'] = df_d.apply(get_sender_role, axis=1)

    # 4. Pengelompokan Multi-turn Replies per Header
    print("\n[3/4] Mengagregasi balasan multi-turn, thread percakapan, dan Ground Truth departemen...")
    # Urutkan kronologis
    df_d = df_d.sort_values(by=['FeedbackHeaderID', 'ReplyTime'])

    # Simpan ke dict of lists untuk eksekusi cepat
    grouped_details = collections.defaultdict(list)
    for _, row in df_d.iterrows():
        grouped_details[row['FeedbackHeaderID']].append(row.to_dict())

    # Proses per tiket
    processed_records = []
    for _, h_row in df_h.iterrows():
        hid = h_row['FeedbackHeaderID']
        init_dept_name = str(h_row.get('InitialDepartmentName', 'Operations'))
        init_dept_code = str(h_row.get('InitialDepartmentCode', 'OP'))
        init_dept_id = h_row.get('InitialDepartmentID', None)
        created_time = h_row.get('CreatedDate', None)

        replies = grouped_details.get(hid, [])

        # Deduplikasi klik berulang (rapid repeated submit dari user yang sama)
        clean_replies = []
        prev_key = None
        for r in replies:
            reply_text = str(r.get('CleanedReply', '')).strip()
            if not reply_text:
                continue
            sender_id = str(r.get('AuditedUserID', ''))
            key = (sender_id, reply_text.lower())
            if key == prev_key:
                continue
            prev_key = key
            clean_replies.append(r)

        # Pisahkan staff replies dan boarder replies
        staff_replies = [r for r in clean_replies if r['SenderRole'] == 'Staff']
        boarder_replies = [r for r in clean_replies if r['SenderRole'] == 'Boarder']

        total_replies = len(clean_replies)
        total_staff_replies = len(staff_replies)
        total_boarder_replies = len(boarder_replies)

        # Ambil nama-nama dan ID staff
        staff_names_list = []
        staff_ids_list = []
        for r in staff_replies:
            s_name = str(r.get('StaffName', '')).strip()
            if s_name and s_name.lower() not in ['old user', 'staff', 'admin', 'unknown', 'nan']:
                if s_name not in staff_names_list:
                    staff_names_list.append(s_name)
            s_id = str(r.get('AuditedUserID', '')).strip()
            if s_id and s_id not in staff_ids_list and s_id.lower() != 'nan':
                staff_ids_list.append(s_id)

        staff_names_str = "; ".join(staff_names_list)
        staff_ids_str = "; ".join(staff_ids_list)

        # Balasan pertama, terakhir, dan gabungan staff
        first_staff_reply = staff_replies[0]['CleanedReply'] if staff_replies else ""
        latest_staff_reply = staff_replies[-1]['CleanedReply'] if staff_replies else ""
        all_staff_replies = " | ".join(r['CleanedReply'] for r in staff_replies)

        # Thread percakapan lengkap berurutan (multi-turn dialog dari keluhan awal sampai akhir)
        thread_parts = [f"[Boarder (Initial Complaint)]: {h_row['CleanedComplaint']}"]
        for r in clean_replies:
            txt = r['CleanedReply']
            if r['SenderRole'] == 'Boarder':
                thread_parts.append(f"[Boarder]: {txt}")
            else:
                dept_code = r.get('DetailDepartmentCode') or r.get('DetailDepartmentName') or 'Staff'
                s_name = r.get('StaffName', '')
                name_str = f" - {s_name}" if s_name and str(s_name).lower() not in ['old user', 'nan', ''] else ""
                thread_parts.append(f"[Staff - {dept_code}{name_str}]: {txt}")
        conversation_thread = " | ".join(thread_parts)

        # Penentuan Ground Truth Departemen Penangan (HandledDepartment)
        # Diutamakan dari departemen staff yang membalas tiket
        handled_dept_name = None
        handled_dept_code = None
        handled_dept_id = None

        for r in reversed(staff_replies):
            dept_n = str(r.get('DetailDepartmentName', '')).strip()
            if dept_n and dept_n.lower() not in ['unknown', 'nan', '']:
                handled_dept_name = dept_n
                handled_dept_code = str(r.get('DetailDepartmentCode', '')).strip()
                handled_dept_id = r.get('DetailDepartmentID', None)
                break

        # Fallback jika tidak ada balasan staff atau dept staff kosong
        if not handled_dept_name:
            handled_dept_name = init_dept_name
            handled_dept_code = init_dept_code
            handled_dept_id = init_dept_id

        # Flag Reroute: apakah departemen awal beda dengan departemen yang menangani
        is_rerouted = 1 if init_dept_name.strip().lower() != handled_dept_name.strip().lower() else 0

        # Waktu respon & SLA
        first_staff_time = staff_replies[0]['ReplyTime'] if staff_replies else None
        latest_staff_time = staff_replies[-1]['ReplyTime'] if staff_replies else None

        first_response_minutes = None
        if first_staff_time and created_time:
            try:
                t0 = pd.to_datetime(created_time)
                t1 = pd.to_datetime(first_staff_time)
                diff_sec = (t1 - t0).total_seconds()
                if diff_sec >= 0:
                    first_response_minutes = round(diff_sec / 60.0, 1)
            except Exception:
                pass

        processed_records.append({
            'FeedbackHeaderID': hid,
            'CreatedDate': created_time,
            'CreatedUserID': h_row.get('CreatedUserID', None),
            'StatusName': h_row.get('StatusName', 'Unknown'),
            'SubjectID': h_row.get('SubjectID', None),
            'SubjectCategory': h_row.get('SubjectCategory', 'Uncategorized'),
            'InitialDepartmentID': init_dept_id,
            'InitialDepartmentName': init_dept_name,
            'InitialDepartmentCode': init_dept_code,
            'HandledDepartmentID': handled_dept_id,
            'HandledDepartmentName': handled_dept_name,      # GROUND TRUTH TARGET UNTUK TRIASE
            'HandledDepartmentCode': handled_dept_code,      # GROUND TRUTH KODE
            'IsRerouted': is_rerouted,                       # FLAG APAKAH TIKET DIALIHKAN
            'CleanedComplaint': h_row['CleanedComplaint'],   # TEKS KOMPLAIN BERSIH
            'RawMessage': h_row.get('RawMessage', ''),
            'TotalReplies': total_replies,
            'TotalStaffReplies': total_staff_replies,
            'TotalBoarderReplies': total_boarder_replies,
            'StaffNames': staff_names_str,
            'StaffUserIDs': staff_ids_str,
            'FirstStaffReply': first_staff_reply,
            'LatestStaffReply': latest_staff_reply,
            'AllStaffReplies': all_staff_replies,
            'ConversationThread': conversation_thread,       # PERCAKAPAN MULTI-TURN LENGKAP
            'FirstStaffReplyTime': first_staff_time,
            'LatestStaffReplyTime': latest_staff_time,
            'FirstResponseMinutes': first_response_minutes
        })

    df_result = pd.DataFrame(processed_records)

    # 5. Simpan Hasil Akhir
    print("\n[4/4] Menyimpan dataset bersih siap latih ke CSV...")
    df_result.to_csv(OUTPUT_CLEAN_CSV, index=False, encoding="utf-8")
    print("\n" + "=" * 60)
    print("[SUCCESS] PIPELINE DATASET BERHASIL!")
    print(f"  -> File tersimpan di: {OUTPUT_CLEAN_CSV}")
    print(f"  -> Total tiket siap pakai: {len(df_result):,} baris")
    print(f"  -> Tiket yang mengalami reroute (IsRerouted=1): {df_result['IsRerouted'].sum():,} baris")
    print(f"  -> Tiket dengan multi-turn reply: {(df_result['TotalReplies'] >= 2).sum():,} baris")
    print("=" * 60)
    return True

if __name__ == "__main__":
    run_cleansing()

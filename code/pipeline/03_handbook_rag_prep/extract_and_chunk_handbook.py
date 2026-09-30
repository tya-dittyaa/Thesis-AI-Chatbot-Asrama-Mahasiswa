"""
Pipeline Tahap 3: Ekstraksi & Chunking Boarder Handbook 2025-2026 untuk Basis Pengetahuan RAG
Input: pipeline/03_handbook_rag_prep/data/boarder_handbook_2025_2026.pdf
Output:
  - pipeline/03_handbook_rag_prep/data/handbook_chunks.json (potongan teks semantik siap indeks RAG)
  - pipeline/03_handbook_rag_prep/data/handbook_pages_extracted.json (teks utuh per halaman)
"""

import os
import re
import json
import pypdf

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(CURRENT_DIR, "data")
PDF_PATH = os.path.join(DATA_DIR, "boarder_handbook_2025_2026.pdf")
OUTPUT_CHUNKS_PATH = os.path.join(DATA_DIR, "handbook_chunks.json")
OUTPUT_PAGES_PATH = os.path.join(DATA_DIR, "handbook_pages_extracted.json")

os.makedirs(DATA_DIR, exist_ok=True)

def extract_and_chunk_handbook():
    print("=" * 60)
    print("PIPELINE 03: EKSTRAKSI & CHUNKING BOARDER HANDBOOK 2025-2026")
    print("=" * 60)

    if not os.path.exists(PDF_PATH):
        print(f"[ERROR] File PDF tidak ditemukan: {PDF_PATH}")
        return False

    print(f"Membaca file PDF: {PDF_PATH}")
    reader = pypdf.PdfReader(PDF_PATH)
    total_pages = len(reader.pages)
    print(f"Total halaman: {total_pages}")

    # 1. Ekstrak teks per halaman dan bersihkan header/footer berulang
    pages_data = []
    full_text_blocks = []

    for idx, page in enumerate(reader.pages):
        page_num = idx + 1
        raw_text = page.extract_text() or ""
        
        # Bersihkan header berulang 'X    BOARDER HANDBOOK 2025-2026'
        cleaned = re.sub(r'(?i)^\s*\d+\s+BOARDER\s+HANDBOOK\s+2025-2026\s*', '', raw_text, flags=re.MULTILINE)
        cleaned = cleaned.strip()

        pages_data.append({
            "page_number": page_num,
            "text": cleaned,
            "char_count": len(cleaned)
        })

        if page_num >= 6 and len(cleaned) > 50:  # Halaman 1-5 adalah cover dan daftar isi
            full_text_blocks.append((page_num, cleaned))

    # Simpan ekstrak halaman murni
    with open(OUTPUT_PAGES_PATH, "w", encoding="utf-8") as f:
        json.dump(pages_data, f, indent=2, ensure_ascii=False)
    print(f"[1/3] Ekstrak per halaman tersimpan di: {OUTPUT_PAGES_PATH}")

    # 2. Semantic Chunking berdasarkan Pasal / Bab / Topik Aturan
    print("\n[2/3] Memproses pemotongan semantik (semantic chunking)...")
    chunks = []
    chunk_counter = 1

    # Pola heading nomor bab atau sub-bab (misal: '2. ROOM AND CONTRACT', '2.1. CHECK-IN', '3.1. VISITORS')
    heading_pattern = re.compile(r'(?m)^(\s*(?:[A-Z]\.|\d+\.|\d+\.\d+\.|\d+\.\d+\.\d+\.?)\s+[A-Z\s\(\)\-\,\/]{3,60})\s*$')

    current_section = "GENERAL REGULATIONS"
    current_text = []
    start_page = 6
    current_page = 6

    for page_num, page_txt in full_text_blocks:
        lines = page_txt.split('\n')
        for line in lines:
            match = heading_pattern.match(line)
            # Jika menemukan heading baru dan buffer sudah terisi cukup teks (>150 kata)
            if match and len(' '.join(current_text).split()) >= 80:
                chunk_body = ' '.join(current_text).strip()
                words = len(chunk_body.split())
                chunks.append({
                    "chunk_id": f"CHUNK_{chunk_counter:03d}",
                    "section_title": current_section.strip(),
                    "page_start": start_page,
                    "page_end": current_page,
                    "text_content": chunk_body,
                    "word_count": words,
                    "approx_tokens": int(words * 1.3)
                })
                chunk_counter += 1
                current_section = match.group(1).strip()
                current_text = [line]
                start_page = page_num
            else:
                if match:
                    current_section = match.group(1).strip()
                current_text.append(line)
        current_page = page_num

    # Flush sisa buffer terakhir
    if current_text:
        chunk_body = ' '.join(current_text).strip()
        words = len(chunk_body.split())
        chunks.append({
            "chunk_id": f"CHUNK_{chunk_counter:03d}",
            "section_title": current_section.strip(),
            "page_start": start_page,
            "page_end": current_page,
            "text_content": chunk_body,
            "word_count": words,
            "approx_tokens": int(words * 1.3)
        })

    # Simpan hasil chunking RAG
    with open(OUTPUT_CHUNKS_PATH, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)

    print(f"\n[3/3] Chunking selesai! Dihasilkan {len(chunks)} chunks semantik.")
    print(f"  -> File Chunks tersimpan di: {OUTPUT_CHUNKS_PATH}")
    print("\n" + "=" * 60)
    print("CONTOH HASIL CHUNKS BASIS PENGETAHUAN (RAG):")
    print("=" * 60)
    for c in chunks[:5]:
        preview = c['text_content'][:100].encode('ascii', errors='ignore').decode('ascii')
        print(f"[{c['chunk_id']}] Hal {c['page_start']}-{c['page_end']}: {c['section_title']} ({c['word_count']} kata, ~{c['approx_tokens']} token)")
        print(f"   Cuplikan: {preview}...\n")

    return True

if __name__ == "__main__":
    extract_and_chunk_handbook()

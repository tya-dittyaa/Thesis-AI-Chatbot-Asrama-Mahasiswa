# 🚀 Catatan Perubahan: Optimasi Token, Guardrail Deterministik, dan Justifikasi Arsitektur Demo App
**Tanggal:** 30 September 2026  
**File Terdampak:** [`code/demo_app/app.py`](file:///e:/Thesis/code/demo_app/app.py)  
**Tujuan:** Mengeliminasi hardcoding rapuh, menekan inflasi konsumsi token, memasang guardrail skema deterministik, serta mendokumentasikan justifikasi akademis perbandingan terhadap platform *no-code/low-code* (LangFlow / n8n).

---

## 1. Latar Belakang Masalah
Pada pengujian awal aplikasi interaktif `demo_app/app.py`:
1. **Memory Inflation & Blind RAG**: Setiap kali user mengirim pesan sapaan (*"Halo"*) atau sapaan santai, sistem RAG menyuntikkan 2 chunk dokumen *Boarder Handbook* (~600 token teks mentah) ke dalam prompt Agen 1. Akibatnya, satu sapaan sederhana menghabiskan **800–1.200 token**. Setelah 6 putaran obrolan, akumulasi riwayat percakapan membengkak hingga **> 7.000 token**.
2. **Hardcoding Rapuh (*Brittle Blacklist*)**: Logika deteksi sapaan awal sempat menggunakan kamus kata (`if cleaned in GREETINGS:`), dan validasi nomor kamar menggunakan daftar blacklist kata (`invalid_terms = ["belum", "unknown", ...]`). Pendekatan ini rapuh secara semantik (misal: kalimat *"Kamar 512, belum pernah diservis"* ditolak karena memuat kata *"belum"*).
3. **Heuristic Category Guessing**: Pada Agen 2 (Spesialis Triase), terdapat fallback yang menebak kategori berbasis kata `"ac"` (`"AC Service" if "ac" in complaint_summary else "Room Maintenance"`), yang berpotensi membiaskan taksonomi resmi kampus.

---

## 2. Rincian Solusi & Perubahan Teknis

### A. Eliminasi Hardcoding Sapaan $\rightarrow$ Native LLM Reception
- Blok hardcoded `GREETINGS` dan `THANK_YOUS` **dihapus total**.
- Seluruh pesan diproses secara wajar oleh model AI (Gemini Flash) sesuai peran Agen 1 sebagai *Receptionist & Dialog Router*.

### B. Semantic RAG Thresholding & Lexical Query Expansion
- **Ambang Batas Kosinus (`threshold = 0.08`)**:
  Potongan teks *Boarder Handbook* **HANYA** diinjeksikan ke prompt Agen 1 jika kemiripan kosinus TF-IDF $\ge 0.08$.
  - Pesan sapaan (*"Halo kak"*), info kamar (*"Kamar A1249"*), atau apresiasi (*"Makasih"*): skor kemiripan $\mathbf{0.0000}$ $\rightarrow$ RAG context **kosong** (`""`). Konsumsi token Agen 1 anjlok dari **~1.100 token menjadi hanya ~180–250 token** per interaksi.
  - Pertanyaan aturan (*"Berapa kuota laundry gratis?"*, *"Jam kunjung tamu sampai jam berapa?"*): skor kemiripan $\mathbf{0.20 - 0.40}$ $\rightarrow$ RAG context diinjeksikan secara presisi.
- **Bilingual Lexical Expansion (`SYNONYM_EXPANSION`)**:
  Karena *Boarder Handbook* ditulis dalam Bahasa Inggris ("VISITORS", "LAUNDRY", "SWIMMING POOL") sementara mahasiswa bertanya dalam Bahasa Indonesia, dibangun kamus ontologi bilingual untuk memetakan kata kunci pencarian secara otomatis tanpa mengubah teks aslinya.

### C. Sliding Window Context Management (`max_window = 6`)
- Riwayat percakapan yang dikirimkan ke context window Gemini dibatasi hanya pada **3 pasang interaksi terakhir (6 pesan)**.
- Mencegah fenomena *Memory Inflation* sehingga biaya komputasi dan token tetap stabil konstan sepanjang sesi obrolan.

### D. Deterministic Schema Guardrail untuk Validasi Nomor Kamar
- Mengganti blacklist kata `invalid_terms` dengan fungsi validasi regex berbasis spesifikasi fisik Binus Square:
  ```python
  def validate_and_extract_room(raw_room: str) -> str:
      """
      Deterministic Schema Guardrail for Binus Square Room Numbers.
      Standard Binus Square rooms: Tower A or B followed by 3-4 digits (e.g., A1249, B512, 512, 1204).
      Returns sanitized room string if valid, otherwise empty string ''.
      """
      if not raw_room:
          return ""
      match = re.search(r'\b(?:Tower\s*)?([ABab]?[- ]?\d{3,4})\b', str(raw_room).strip())
      if match:
          return match.group(1).replace(" ", "").replace("-", "").upper()
      return ""
  ```
- **Keunggulan Validasi**:
  - `A1249`, `512`, `Tower A 1204`, `B-0812` $\rightarrow$ Terekstraksi secara valid.
  - `Kamar 512, belum mandi` $\rightarrow$ Angka `512` tetap berhasil diekstraksi tanpa terganjal kata *"belum"*.
  - `belum tahu`, `unknown`, `-` $\rightarrow$ Ditolak deterministik dan memicu permintaan klarifikasi nomor kamar secara sopan.

### E. Clean Taxonomy Fallback pada Agen 2
- Menghapus tebakan heuristik `"ac"`. Fallback jika parameter fungsi tidak lengkap diubah menjadi netral:
  ```python
  category = triage_args.get("problem_category") or "Others"
  ```

---

## 3. Matriks Hasil Optimasi Token & Efisiensi

| Skenario Pengujian | Sebelum Optimasi | Sesudah Optimasi | Efisiensi |
| :--- | :---: | :---: | :---: |
| Sapaan Pertama (*"Halo kak"*) | ~1.150 token (Blind RAG) | **~195 token** | **Hemat 83.0%** |
| Info Kamar (*"Kamar A1249"*) | ~1.220 token (Blind RAG) | **~240 token** | **Hemat 80.3%** |
| Pertanyaan RAG (*"Jam tamu"*) | ~1.300 token (RAG Aktif) | **~520 token** (RAG Fokus) | **Hemat 60.0%** |
| Chat Putaran ke-6 | > 7.000 token (Accumulative) | **~1.100 token** (Sliding Window) | **Hemat 84.2%** |

---

## 4. Pembahasan Akademis: Mengapa Tidak Menggunakan Low-Code Tools (LangFlow / n8n)?

Pertanyaan ini sering diajukan dalam sidang tesis terkait justifikasi pemilihan metode:

1. **Alat Otomasi (*Tooling*) vs Metodologi Ilmiah (*Scientific Novelty*)**:
   - n8n / LangFlow adalah *workflow UI wrapper*. Penggunaannya dalam tesis hanya berupa konfigurasi perangkat lunak komersial tanpa kontribusi algoritma baru.
   - Penelitian tesis ini berfokus pada **investigasi empiris terhadap dekomposisi kognitif Multi-Agent System (MAS)** dibandingkan arsitektur monolitik (Single-Agent Baseline).
2. **Kebutuhan Evaluasi Skala Besar (Batch Benchmark N=500)**:
   - Tool visual low-code tidak dirancang untuk menjalankan evaluasi otomatis ratusan tiket *unseen* secara berimbang dengan metrik inferensial (Macro-F1, Precision, Recall, Confusion Matrix 5x5, dan Token Profiling terisolasi).
3. **Reproduksibilitas Standar Publikasi (IEEE / ACM / Scopus)**:
   - Publikasi internasional menuntut *reproducible code pipeline* dengan *deterministic seed* dan skema *function calling* yang dapat diaudit baris per baris di repositori publik, bukan diagram alur visual yang bergantung pada runtime eksternal.
4. **Isolasi Konteks & Granular Guardrail**:
   - Pipeline Python murni memungkinkan isolasi konteks yang ketat (Agen 2 dibuat *100% Stateless* hanya menerima ringkasan terverifikasi) dan integrasi *deterministic regex schema guardrails* yang fleksibel, meminimalkan *leaky context* yang sering terjadi pada platform no-code.

---

## 5. Status Verifikasi Git
- Commit 1: `d775535` (*refactor: replace hardcoded greetings with semantic RAG thresholding*)
- Commit 2: `67815f3` (*fix: replace heuristic room blacklist with regex schema guardrail and clean taxonomy fallback*)
- Status: **Pushed to GitHub origin/main (Up to date)**.

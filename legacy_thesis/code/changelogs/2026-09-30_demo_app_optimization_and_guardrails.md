# 🚀 Catatan Perubahan: Optimasi Token, Guardrail Deterministik, dan Justifikasi Arsitektur Demo App

**Tanggal:** 30 September 2026  
**File Terdampak:** [`code/demo_app/app.py`](file:///e:/Thesis/code/demo_app/app.py)  
**Tujuan:** Mengeliminasi hardcoding rapuh, menekan inflasi konsumsi token, memasang guardrail skema deterministik, serta mendokumentasikan justifikasi akademis perbandingan terhadap platform _no-code/low-code_ (LangFlow / n8n).

---

## 1. Latar Belakang Masalah

Pada pengujian awal aplikasi interaktif `demo_app/app.py`:

1. **Memory Inflation & Blind RAG**: Setiap kali user mengirim pesan sapaan (_"Halo"_) atau sapaan santai, sistem RAG menyuntikkan 2 chunk dokumen _Boarder Handbook_ (~600 token teks mentah) ke dalam prompt Agen 1. Akibatnya, satu sapaan sederhana menghabiskan **800–1.200 token**. Setelah 6 putaran obrolan, akumulasi riwayat percakapan membengkak hingga **> 7.000 token**.
2. **Hardcoding Rapuh (_Brittle Blacklist_)**: Logika deteksi sapaan awal sempat menggunakan kamus kata (`if cleaned in GREETINGS:`), dan validasi nomor kamar menggunakan daftar blacklist kata (`invalid_terms = ["belum", "unknown", ...]`). Pendekatan ini rapuh secara semantik (misal: kalimat _"Kamar 512, belum pernah diservis"_ ditolak karena memuat kata _"belum"_).
3. **Heuristic Category Guessing**: Pada Agen 2 (Spesialis Triase), terdapat fallback yang menebak kategori berbasis kata `"ac"` (`"AC Service" if "ac" in complaint_summary else "Room Maintenance"`), yang berpotensi membiaskan taksonomi resmi kampus.

---

## 2. Rincian Solusi & Perubahan Teknis

### A. Eliminasi Hardcoding Sapaan $\rightarrow$ Native LLM Reception

- Blok hardcoded `GREETINGS` dan `THANK_YOUS` **dihapus total**.
- Seluruh pesan diproses secara wajar oleh model AI (Gemini Flash) sesuai peran Agen 1 sebagai _Receptionist & Dialog Router_.

### B. Semantic RAG Thresholding & Lexical Query Expansion

- **Ambang Batas Kosinus (`threshold = 0.08`)**:
  Potongan teks _Boarder Handbook_ **HANYA** diinjeksikan ke prompt Agen 1 jika kemiripan kosinus TF-IDF $\ge 0.08$.
  - Pesan sapaan (_"Halo kak"_), info kamar (_"Kamar A1249"_), atau apresiasi (_"Makasih"_): skor kemiripan $\mathbf{0.0000}$ $\rightarrow$ RAG context **kosong** (`""`). Konsumsi token Agen 1 anjlok dari **~1.100 token menjadi hanya ~180–250 token** per interaksi.
  - Pertanyaan aturan (_"Berapa kuota laundry gratis?"_, _"Jam kunjung tamu sampai jam berapa?"_): skor kemiripan $\mathbf{0.20 - 0.40}$ $\rightarrow$ RAG context diinjeksikan secara presisi.
- **Bilingual Lexical Expansion (`SYNONYM_EXPANSION`)**:
  Karena _Boarder Handbook_ ditulis dalam Bahasa Inggris ("VISITORS", "LAUNDRY", "SWIMMING POOL") sementara mahasiswa bertanya dalam Bahasa Indonesia, dibangun kamus ontologi bilingual untuk memetakan kata kunci pencarian secara otomatis tanpa mengubah teks aslinya.

### C. Sliding Window Context Management (`max_window = 6`)

- Riwayat percakapan yang dikirimkan ke context window Gemini dibatasi hanya pada **3 pasang interaksi terakhir (6 pesan)**.
- Mencegah fenomena _Memory Inflation_ sehingga biaya komputasi dan token tetap stabil konstan sepanjang sesi obrolan.

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
  - `Kamar 512, belum mandi` $\rightarrow$ Angka `512` tetap berhasil diekstraksi tanpa terganjal kata _"belum"_.
  - `belum tahu`, `unknown`, `-` $\rightarrow$ Ditolak deterministik dan memicu permintaan klarifikasi nomor kamar secara sopan.

### E. Clean Taxonomy Fallback pada Agen 2

- Menghapus tebakan heuristik `"ac"`. Fallback jika parameter fungsi tidak lengkap diubah menjadi netral:
  ```python
  category = triage_args.get("problem_category") or "Others"
  ```

### F. Prompt Tightening & Eliminasi Redundansi Monolitik

- **Single Agent (Baseline):** Menghapus duplikasi pencatatan 35 kategori di teks _system prompt_ karena sudah tercantum dalam parameter `enum` skema fungsi `create_official_ticket`. Fixed prompt overhead Single Agent berhasil dipangkas dari **932 prompt tokens menjadi ~400 prompt tokens (hemat 57.1%)**.
- **Multi-Agent (Proposed):** Memadatkan teks instruksi Agen 1 dan parameter fungsi `delegate_to_triage`. Fixed prompt overhead Agen 1 berhasil dipangkas dari **386 prompt tokens menjadi ~240–280 prompt tokens**.

### G. Isolasi Pemicu Darurat Medis vs. Insiden Fasilitas

- **Masalah:** Frasa hiperbola atau insiden kamar (seperti _"kamar saya meledak"_) sebelumnya memicu aturan darurat yang menggabungkan kata "Darurat" dengan "Medis (RS Siloam)", menyebabkan model menyarankan rumah sakit padahal tidak ada cedera fisik.
- **Solusi:** Memisahkan pemicu secara tegas:
  - Kedaruratan medis (RS Siloam / Security Ext 0) **HANYA** dipicu jika mahasiswa secara eksplisit sakit, terluka, atau berdarah.
  - Insiden fisik kamar ekstrem (korsleting, ledakan alat, banjir) diarahkan sebagai kendala fasilitas darurat yang menanyakan nomor kamar dan objek terdampak secara tenang.

### H. Transparansi Metrik Frontend (Breakdown Prompt vs. Reply)

- Antarmuka Streamlit (pada balon chat dan Sidebar Live Inspector) diperkaya dengan pencatatan terpilah:
  $$\text{Format Tampilan: } \text{🪙 \textbf{Total Tokens} (Prompt: \textit{In} | Reply: \textit{Out})}$$
- Memudahkan penguji sidang mengaudit bahwa efisiensi Multi-Agent berasal dari pemangkasan konteks input (_prompt tokens_).

---

## 3. Matriks Hasil Optimasi Token & Efisiensi

| Skenario Pengujian                            | Awal Mula (Blind RAG) | Setelah Optimasi 1 | **Setelah Tightening Maksimal** | Efisiensi Kumulatif |
| :-------------------------------------------- | :-------------------: | :----------------: | :-----------------------------: | :-----------------: |
| Sapaan / Chat Biasa (_"bwng"_) — Multi-Agent  |     ~1.150 token      |     ~414 token     |      **~260 - 290 token**       |   **Hemat 76.5%**   |
| Sapaan / Chat Biasa (_"bwng"_) — Single Agent |     ~1.150 token      |     ~974 token     |      **~410 - 450 token**       |   **Hemat 62.6%**   |
| Pertanyaan Aturan RAG (_"Jam tamu"_)          |     ~1.300 token      |     ~520 token     |      **~480 - 520 token**       |   **Hemat 61.5%**   |
| Multi-turn Chat (Putaran ke-6)                |     > 7.000 token     |    ~1.100 token    |      **~750 - 950 token**       |   **Hemat > 86%**   |

---

## 4. Pembahasan Akademis: Mengapa Tidak Menggunakan Low-Code Tools (LangFlow / n8n)?

Pertanyaan ini sering diajukan dalam sidang tesis terkait justifikasi pemilihan metode:

1. **Alat Otomasi (_Tooling_) vs Metodologi Ilmiah (_Scientific Novelty_)**:
   - n8n / LangFlow adalah _workflow UI wrapper_. Penggunaannya dalam tesis hanya berupa konfigurasi perangkat lunak komersial tanpa kontribusi algoritma baru.
   - Penelitian tesis ini berfokus pada **investigasi empiris terhadap dekomposisi kognitif Multi-Agent System (MAS)** dibandingkan arsitektur monolitik (Single-Agent Baseline).
2. **Kebutuhan Evaluasi Skala Besar (Batch Benchmark N=500)**:
   - Tool visual low-code tidak dirancang untuk menjalankan evaluasi otomatis ratusan tiket _unseen_ secara berimbang dengan metrik inferensial (Macro-F1, Precision, Recall, Confusion Matrix 5x5, dan Token Profiling terisolasi).
3. **Reproduksibilitas Standar Publikasi (IEEE / ACM / Scopus)**:
   - Publikasi internasional menuntut _reproducible code pipeline_ dengan _deterministic seed_ dan skema _function calling_ yang dapat diaudit baris per baris di repositori publik, bukan diagram alur visual yang bergantung pada runtime eksternal.
4. **Isolasi Konteks & Granular Guardrail**:
   - Pipeline Python murni memungkinkan isolasi konteks yang ketat (Agen 2 dibuat _100% Stateless_ hanya menerima ringkasan terverifikasi) dan integrasi _deterministic regex schema guardrails_ yang fleksibel, meminimalkan _leaky context_ yang sering terjadi pada platform no-code.

---

## 5. Status Verifikasi Git

- `d775535` — _refactor: replace hardcoded greetings with semantic RAG thresholding_
- `67815f3` — _fix: replace heuristic room blacklist with regex schema guardrail and clean taxonomy fallback_
- `3809cf0` — _feat: compress prompts and display transparent prompt vs reply token breakdown in UI_
- `ff7fb1c` — _perf: tighten single agent and multi agent prompts to slash overhead tokens to ~240-400_
- `b228191` — _fix: refine emergency trigger so facility incidents ask for room number instead of hallucinating RS Siloam_
- Status: **Pushed to GitHub origin/main (Synchronized)**.

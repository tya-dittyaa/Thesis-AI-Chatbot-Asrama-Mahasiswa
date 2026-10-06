# 📐 Cetak Biru Bab 3: Metodologi Penelitian & Kerangka Metrik Evaluasi
**Topik:** Rekonstruksi Utuh Metodologi Penelitian Bab 3 (6 Tahapan Komputasi), Desain 4 Skenario Komparatif, dan Kerangka Metrik Evaluasi Lengkap (Precision, Recall, F1, Macro-F1, Latensi, Token, & Error Cascade)  
**Tanggal:** 2026-10-06  
**Peneliti:** Aditya Fajri (2602113205)  
**Program Studi:** Magister Teknik Informatika, Universitas Bina Nusantara  
**Target:** Draf Final Struktur Bab 3 Naskah Tesis dan Acuan Analisis Evaluasi Bab 4  

---

## 📌 1. Kerangka Alur Penelitian (Research Framework)

Metodologi penelitian dirancang ulang secara terpadu tanpa mengacu pada draf lama, berfokus murni pada pengujian komparatif 4 skenario sistem triase:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ TAHAP 1: PENGUMPULAN & FILTER DATASET HISTORIS (2015–2025)                  │
│ • Input : 35.000+ data mentah database keluhan Binus Square (2014-2026).    │
│ • Proses: Filter 1 dekade (2015-2025) & anonimisasi PII ([KAMAR_ANONIM]).   │
│ • Output: 30.314 tiket historis valid.                                      │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ TAHAP 2: STERILISASI LABEL NOISE & PEMBENTUKAN GOLDEN BENCHMARK             │
│ • Proses: Deteksi anomali tiket billing/listrik yang salah berlabel ED.     │
│ • Sampling: Stratified Random Sampling (100 tiket per departemen, Seed 42). │
│ • Output:                                                                   │
│   ├── test_golden_benchmark_500.csv  (500 tiket seimbang, Unseen Test Set)  │
│   └── train_pool.csv                 (29.814 tiket korpus latih)            │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ TAHAP 3: KONSTRUKSI BASIS PENGETAHUAN REGULASI (HANDBOOK RAG)               │
│ • Input : Boarder Handbook Binus Square 2025–2026 (PDF).                    │
│ • Proses: Ekstraksi teks & pemotongan 46 chunk semantik SOP asrama.         │
│ • Mesin : HandbookRetriever (TF-IDF N-Gram 1-2 & Cosine Similarity).        │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ TAHAP 4: IMPLEMENTASI 4 SKENARIO KOMPARATIF SISTEM TRIASE                   │
│                                                                             │
│  [Skenario 1] Classical ML Baseline (TF-IDF + Logistic Regression / SVM)    │
│  [Skenario 2] Monolithic Single-Agent LLM (Gemini 2.5 Flash, Zero-Shot)     │
│  [Skenario 3] Single-Agent LLM + RAG Handbook (Ablation Control)            │
│  [Skenario 4] Modular Chained Multi-Agent System (Native Function Calling)  │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ TAHAP 5: PENGUJIAN INFERENSI DI BAWAH KONTROL THROUGHPUT                    │
│ • Infrastruktur: Google AI Studio Standard Public API Tier.                 │
│ • Kontrol: Modul ApiKeyManager (4-Key Round Robin & HTTP 429 Retry).        │
│ • Pengukuran: Logging stopwatch latensi & token resmi Google Metadata.      │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ TAHAP 6: KERANGKA EVALUASI KOMPREHENSIF & ANALISIS PROPAGASI KESALAHAN      │
│ • Klasifikasi : Precision, Recall, F1-Score per kelas, Macro-F1, Accuracy.  │
│ • Keandalan   : Validitas skema JSON (100%) & Heatmap Confusion Matrix 5x5. │
│ • Efisiensi   : Latensi per tiket (detik), Token per tiket, Biaya komputasi.│
│ • Analisis    : Error Cascade Breakdown & Formulasi Hybrid ITSM Framework.  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔬 2. Rincian Metodologi 6 Tahapan (Subbab Bab 3)

### 3.1. Pengumpulan & Pra-pemrosesan Data (Tahap 1)
* **Kriteria Inklusi & Eksklusi:** Menyaring data tiket dari kurun waktu 2015 hingga 2025. Data tahun 2014 dieksklusi karena merupakan fase inisiasi sistem dengan banyak kolom kosong, sedangkan 2026 dieksklusi karena tahun berjalan belum tuntas.
* **Anonimisasi Data Pribadi (Privacy-Preserving NLP):** Menghapus nama mahasiswa dan mengganti nomor kamar menjadi token generik `[KAMAR_ANONIM]` guna mematuhi prinsip etika riset data dan regulasi perlindungan data pribadi.

### 3.2. Kurasi Data & Desain Sampling (Tahap 2)
* **Pembersihan Anomali Label Legacy:** Memfilter keluhan yang secara semantik memuat kata kunci transaksi keuangan (*tagihan, kwh, invoice, denda*) namun di database warisan masih berlabel *Estate Department*.
* **Stratified Balanced Sampling:** Membagi data menjadi 5 strata departemen penangan:
  - Estate Department (`ED`): 100 tiket
  - Operations (`OP`): 100 tiket
  - Finance (`FN`): 100 tiket
  - Marketing (`MR`): 100 tiket
  - Student Support Office (`SO`): 100 tiket  
  Total: **500 Tiket Golden Benchmark Seimbang** (`test_golden_benchmark_500.csv`).
* **Isolasi Ketat:** 500 tiket diisolasi penuh (*blind test*) dan tidak pernah dijadikan referensi dalam pembuatan prompt (*Anti-Data Snooping*). Sisa **29.814 tiket** dialokasikan ke `train_pool.csv`.

### 3.3. Pembangunan Knowledge Base Regulasi (Tahap 3)
* Dokumen teks handbook asrama disegmentasi menjadi **46 chunk semantik**.
* Dibangun mesin pencari *HandbookRetriever* berbasis pembobotan *TF-IDF* dan *Cosine Similarity* untuk mengembalikan $Top-K=2$ potongan regulasi yang paling relevan terhadap keluhan mahasiswa.

### 3.4. Spesifikasi 4 Skenario Eksperimen (Tahap 4)
* **Skenario 1 (Classical Supervised ML):**  
  Teks keluhan diekstraksi menggunakan `TfidfVectorizer(max_features=10000)` dari 29.814 data latih. Model diklasifikasikan dengan *Logistic Regression* / *Linear Support Vector Classifier (LinearSVC)*.
* **Skenario 2 (Monolithic Single-Agent LLM):**  
  Menggunakan model Google Gemini 2.5 Flash dengan 1 prompt panjang yang memuat taksonomi departemen, aturan urgensi, dan format JSON tanpa injeksi dokumen handbook.
* **Skenario 3 (Single-Agent LLM + RAG Handbook):**  
  Model Gemini 2.5 Flash monolitik yang disuntikkan potongan regulasi handbook hasil pencarian RAG pada awal prompt untuk mengontrol variabel RAG secara adil (*Fair Ablation Study*).
* **Skenario 4 (Modular Chained Multi-Agent System - Proposed):**  
  Arsitektur dekomposisi 3 agen spesialis:
  - *Agen 1 (Receptionist & RAG):* Meringkas keluhan dan menarik pasal handbook relevan.
  - *Agen 2 (Triage Specialist):* Mengeksekusi *Native Function Calling* `route_and_classify_complaint(...)`.
  - *Agen 3 (Response Drafter):* Menyusun balasan resmi tanda terima tiket (*SLA Acknowledgment*) kepada mahasiswa.

### 3.5. Spesifikasi Native Function Calling
Fungsi `route_and_classify_complaint` didaftarkan secara native ke arsitektur model Gemini (`types.Tool`) dengan 6 parameter keluaran:
1. `target_department` (Enum: `ED`, `OP`, `FN`, `MR`, `SO`)
2. `target_department_name` (Nama lengkap resmi departemen)
3. `problem_category` (Kategori taksonomi masalah)
4. `urgency_level` (Enum: `Low`, `Medium`, `High`, `Emergency`)
5. `facility_item` (Entitas fasilitas fisik / layanan yang rusak)
6. `location_context` (Entitas lokasi spesifik terjadinya masalah)
7. `confidence_score` (Skor keyakinan numerik: 0.0 s/d 1.0)
8. `reasoning_summary` (Justifikasi logis keputusan perutean)

### 3.6. Manajemen Lingkungan Komputasi (Tahap 5)
* Evaluasi berjalan di atas antarmuka *Google AI Studio Standard Public API Tier*.
* Manajemen beban menggunakan modul `ApiKeyManager` (4 API Key Round-Robin Balancing) dan penanganan galat HTTP 429 via *Exponential Backoff Retry* (3 kali percobaan dengan jeda adaptif).

---

## 📊 3. Kerangka Metrik Evaluasi Komprehensif (Subbab Evaluasi)

Seluruh skenario dievaluasi secara seragam menggunakan matriks evaluasi berikut:

### A. Metrik Klasifikasi per Departemen (Per-Class Metrics)
Untuk setiap departemen $k \in \{\text{ED}, \text{OP}, \text{FN}, \text{MR}, \text{SO}\}$:

1. **Precision ($P_k$):**  
   Mengukur ketepatan routing — mencegah pengiriman tiket salah sasaran ke departemen lain:
   $$P_k = \frac{TP_k}{TP_k + FP_k}$$
2. **Recall ($R_k$):**  
   Mengukur kelengkapan tangkapan — mencegah adanya keluhan departemen $k$ yang kelolosan:
   $$R_k = \frac{TP_k}{TP_k + FN_k}$$
3. **F1-Score ($F1_k$):**  
   Rata-rata harmonik antara Precision dan Recall:
   $$F1_k = 2 \times \frac{P_k \times R_k}{P_k + R_k}$$

### B. Metrik Agregat Keseluruhan (Global Metrics)
1. **Macro-Averaged F1 Score ($F1_{\text{macro}}$) — STANDAR UTAMA:**  
   Menilai performa model secara adil di semua departemen tanpa bias kelas mayoritas:
   $$F1_{\text{macro}} = \frac{1}{K} \sum_{k=1}^{K} F1_k \quad (K=5)$$
2. **Akurasi Keseluruhan ($Accuracy$):**  
   $$Accuracy = \frac{\sum_{k=1}^K TP_k}{N} \times 100\% \quad (N=500)$$
3. **Confusion Matrix Heatmap (5 $\times$ 5):**  
   Tabel kontingensi yang memvisualisasikan persebaran prediksi benar versus salah untuk menganalisis ke mana tiket yang salah dialihkan (*misclassification route*).

### C. Metrik Keandalan Struktural & Ekstraksi Informasi
1. **Validitas Skema JSON ($JSON\_Validity$):**  
   Persentase payload yang dapat di-parse dan mematuhi skema tanpa galat *JSONDecodeError*.
2. **Kelayakan Ekstraksi Urgensi & Entitas:**  
   Tingkat keberhasilan pengisian parameter `urgency_level`, `facility_item`, dan `location_context`.

### D. Metrik Efisiensi Komputasi & Operasional
1. **Rata-rata Latensi per Tiket (detik):** Stopwatch waktu inferensi bersih sejak masukan dikirim hingga respon tuntas.
2. **Konsumsi Token Rata-rata per Tiket:** Total prompt tokens + candidate output tokens resmi dari metadata API.
3. **Estimasi Biaya Operasional Finansial:** Proyeksi biaya komputasi per 500 tiket berdasarkan tarif resmi penyedia model.

### E. Analisis Propagasi Kesalahan (Error Cascade Analysis)
Khusus pada Skenario 4 (MAS), setiap tiket yang salah diklasifikasikan dilacak titik kegagalannya:
$$\text{Total Galat MAS} = \text{Galat Retrieval (Agen 1)} + \text{Galat Penalaran Skema (Agen 2)} + \text{Galat Draf Balasan (Agen 3)}$$

---

## 📋 4. Template Tabel Hasil Bab 4 (Classification Report)

Tabel berikut disajikan untuk masing-masing skenario di Bab 4:

| Departemen Penangan | Precision (%) | Recall (%) | F1-Score (%) | Support |
| :--- | :---: | :---: | :---: | :---: |
| **Estate Department (ED)** | ... | ... | ... | 100 |
| **Operations (OP)** | ... | ... | ... | 100 |
| **Finance (FN)** | ... | ... | ... | 100 |
| **Marketing (MR)** | ... | ... | ... | 100 |
| **Student Support (SO)** | ... | ... | ... | 100 |
| **Macro Average** | **...** | **...** | **...** | **500** |
| **Akurasi Keseluruhan** | — | — | **...%** | **500** |
| **Validitas Skema JSON** | — | — | **100%** | **500** |
| **Rata-rata Latensi** | — | — | **... detik** | **500** |
| **Konsumsi Token** | — | — | **... token** | **500** |

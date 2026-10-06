# BAB III METODOLOGI PENELITIAN

## 3.1. Kerangka Berpikir dan Tahapan Penelitian
Penelitian ini dirancang menggunakan pendekatan eksperimental komputasi empiris (*Empirical Computational Research*) untuk mengevaluasi efektivitas, keandalan, dan efisiensi empat skenario arsitektur triase keluhan pada fasilitas hunian mahasiswa. Alur metodologi penelitian diorganisir ke dalam enam tahapan komputasi yang saling terhubung secara terstruktur:

```
[ TAHAP 1: FILTER TEMPORAL & ANONIMISASI DATA HISTORIS 2015-2025 ]
                               │
                               ▼
[ TAHAP 2: STERILISASI LABEL NOISE & PEMBAGIAN BENCHMARK SEIMBANG ]
  ├── Train Pool (N = 29.814 tiket) ───────────────┐
  └── Golden Benchmark (N = 500 tiket steril) ────┼───────────────────────────┐
                               │                  │                           │
                               ▼                  ▼                           │
[ TAHAP 3: KONSTRUKSI KNOWLEDGE BASE REGULASI ]   │                           │
  └── Ekstraksi & Chunking Handbook RAG (46 chunk)│                           │
                               │                  │                           │
                               ▼                  │                           │
[ TAHAP 4: IMPLEMENTASI 4 SKENARIO KOMPARATIF ]   │                           │
  ├── Skenario 1: Classical Supervised ML ◄───────┘                           │
  ├── Skenario 2: Monolithic Single-Agent LLM (Zero-Shot)                     │
  ├── Skenario 3: Single-Agent LLM + RAG Handbook (Ablation Control)          │
  └── Skenario 4: Modular Chained Multi-Agent System (Native Function Calling)│
                               │                                              │
                               ▼                                              │
[ TAHAP 5: PENGUJIAN INFERENSI DI BAWAH KONTROL THROUGHPUT ] ◄────────────────┘
  └── Eksekusi N=500, Rotasi 4 Kunci API, & Logging Metrik Riil
                               │
                               ▼
[ TAHAP 6: EVALUASI MULTIDIMENSI & ANALISIS PROPAGASI KESALAHAN ]
  └── Precision, Recall, F1, Macro-F1, Latensi, Token, & Error Cascade
```

---

## 3.2. Pengumpulan dan Kurasi Data (Tahap 1 & 2a)

### 3.2.1. Sumber Data dan Pemfilteran Temporal
Data mentah diperoleh dari database operasional *Boarder Feedback & Ticketing System* Binus Square Hall of Residence periode 2014 hingga awal 2026 yang mencakup 35.000+ catatan interaksi. Pemfilteran data dilakukan berdasarkan kriteria:
1. **Rentang Waktu 1 Dekade (2015–2025):** Data tahun 2014 dieksklusi karena merupakan masa rintisan sistem dengan integritas data belum stabil, sedangkan data tahun 2026 dieksklusi karena tahun berjalan belum tuntas.
2. **Ketersediaan Informasi:** Tiket wajib memiliki teks keluhan (`RawMessage` atau `CleanedComplaint`) dan departemen penangan definitif (`HandledDepartmentName`).
3. **Privasi Penghuni (Data Sanitization):** Nomor kamar dan identitas personal penghuni disamarkan secara otomatis menggunakan token anonim `[KAMAR_ANONIM]`.

Proses ini menghasilkan korpus data historis terfilter sebanyak **30.314 tiket**.

### 3.2.2. Deteksi dan Pembersihan Anomali Label (*Label Noise Cleaning*)
Pada data operasional historis, ditemukan anomali di mana staf operasional sering kali tidak memperbarui nilai kolom `HandledDepartmentName` ketika tiket dialihkan secara informal (*rerouted*). Anomali paling dominan terjadi pada tiket penagihan listrik: mahasiswa mengeluhkan denda listrik (kewenangan Finance), namun tiket tetap tercatat dengan label *Estate Department* karena staf resepsionis salah memilih kategori awal.

Guna mencegah bias evaluasi (*garbage in, garbage out*), Tahap 2a menerapkan aturan deteksi anomali leksikal:
* Tiket yang berlabel *Estate Department* namun memuat kata kunci transaksi penagihan (`tagihan`, `invoice`, `kwh`, `denda`, `bayar`, `rekening`, `deposit`, `refund`) atau memiliki subjek kategori formal *Finance* ditandai sebagai data anomali dan dieksklusi dari calon data uji.

Hasil pembersihan menghasilkan dataset steril yang menjadi dasar pembentukan benchmark pengujian.

---

## 3.3. Desain Pembagian Data & Golden Benchmark 500 (Tahap 2b)

### 3.3.1. Justifikasi Ukuran Sampel (Cochran's Sampling Formula)
Pengujian inferensi pada arsitektur LLM berskala besar dibatasi pada sampel representatif untuk menjaga kelayakan komputasi tanpa mengurangi kekuatan inferensi statistik. Berdasarkan rumus statistika inferensial Cochran untuk populasi terbatas ($N = 30.314$), tingkat kepercayaan 95% ($Z = 1.96$), dan *Margin of Error* $e = \pm 4.38\%$:

$$n = \frac{n_0}{1 + \frac{n_0 - 1}{N}} \quad \text{di mana} \quad n_0 = \frac{Z^2 \cdot p \cdot (1-p)}{e^2} \approx 500 \text{ sampel}$$

Dengan demikian, ukuran sampel $N=500$ memenuhi syarat representasi statistik formal.

### 3.3.2. Pengambilan Sampel Berimbang (Stratified Random Sampling)
Populasi asli memiliki ketimpangan kelas (*class imbalance*) ekstrem, di mana *Estate Department* mendominasi >50% populasi, sedangkan *Student Support Office* hanya mencakup ~1.5%. Jika dievaluasi pada data timpang, akurasi model akan terdistorsi oleh kelas mayoritas.

Oleh karena itu, Tahap 2b menerapkan **Stratified Random Sampling** dengan mengunci generator acak `random_state = 42` untuk mengambil tepat **100 tiket per strata departemen**:
* 100 Tiket Estate Department (`ED`)
* 100 Tiket Operations (`OP`)
* 100 Tiket Finance (`FN`)
* 100 Tiket Marketing (`MR`)
* 100 Tiket Student Support Office (`SO`)

Total: **500 Tiket Golden Benchmark Seimbang** (`test_golden_benchmark_500.csv`).  
Dataset ini diisolasi ketat sebagai *Held-Out Unseen Test Set* (tidak pernah dilihat selama perancangan prompt). Sisa **29.814 tiket** dialokasikan ke `train_pool.csv` sebagai korpus pelatihan model klasik.

---

## 3.4. Pembangunan Basis Pengetahuan Regulasi (Handbook RAG)
Dokumen resmi *Binus Square Boarder Handbook 2025–2026* memuat 40+ halaman regulasi tata tertib, prosedur check-in/out, kuota listrik kamar, dan ketentuan pemeliharaan fisik:
1. **Segmentasi Semantik (*Chunking*):** Teks diekstraksi dan dipecah berdasarkan batas pasal alami, menghasilkan **46 chunk semantik**.
2. **Mesin Pengindeksan & Pencarian (*HandbookRetriever*):** Setiap chunk ditransformasikan menjadi representasi vektor bobot kata *TF-IDF* dengan rentang $N$-gram $(1,2)$.
3. **Pencarian Relevansi (*Cosine Similarity*):** Ketika keluhan masuk, sistem menghitung kedekatan sudut kosinus antara teks keluhan dan vektor dokumen, mengembalikan $Top-K = 2$ potongan pasal paling relevan dengan skor relevansi di atas ambang batas 0.01.

---

## 3.5. Implementasi 4 Skenario Arsitektur Komparatif

Penelitian membangun dan menguji 4 skenario sistem triase:

### 3.5.1. Skenario 1: Classical Supervised Machine Learning
* **Tujuan:** Baseline kontrol era pra-LLM untuk menjawab mengapa LLM diperlukan.
* **Arsitektur:** Menggunakan representasi leksikal `TfidfVectorizer(ngram_range=(1,2), max_features=10000)` yang dilatih pada 29.814 data `train_pool.csv`.
* **Klasifikator:** Model *Logistic Regression* / *Linear Support Vector Classifier (LinearSVC)* yang mengklasifikasikan tiket langsung ke dalam 5 kelas departemen.

### 3.5.2. Skenario 2: Monolithic Single-Agent LLM (Zero-Shot)
* **Tujuan:** Menguji batas pengetahuan dasar (*prior world knowledge*) model fondasi tanpa regulasi handbook.
* **Arsitektur:** Model Google Gemini 2.5 Flash yang dipandu 1 prompt sistem tunggal. Prompt memuat taksonomi 5 departemen dan meminta keluaran JSON terstruktur dalam satu panggilan API tunggal.

### 3.5.3. Skenario 3: Single-Agent LLM + RAG Handbook (Ablation Control)
* **Tujuan:** Mengontrol variabel RAG secara adil (*Fair Ablation Study*) untuk membuktikan apakah peningkatan akurasi murni disebabkan oleh RAG atau struktur Multi-Agent.
* **Arsitektur:** Model Gemini 2.5 Flash monolitik yang disuntikkan potongan pasal regulasi handbook teratas hasil pencarian *HandbookRetriever* langsung pada konteks prompt masukannya.

### 3.5.4. Skenario 4: Modular Chained Multi-Agent System (Proposed MAS)
* **Tujuan:** Sistem utama yang diusulkan, menerapkan dekomposisi peran menjadi 3 agen spesialis berbasis prinsip *Separation of Concerns*:
  1. **Agen 1 (Receptionist & Policy Retriever):** Menerima pesan teks informal mahasiswa, menarik 2 pasal handbook terkait via *HandbookRetriever*, dan menyusun ringkasan konteks keluhan.
  2. **Agen 2 (Triage Specialist via Native Function Calling):** Menerima ringkasan Agen 1, lalu secara native mengeksekusi fungsi `route_and_classify_complaint(...)` untuk memproduksi parameter terstruktur.
  3. **Agen 3 (Empathetic Staff Response Generator):** Menerima payload Agen 2 dan menyusun draf balasan resmi berempati (*Service Acknowledgment & SLA Expectation Setting*) kepada mahasiswa tanpa berhalusinasi atas data saldo/database.

---

## 3.6. Antarmuka Native Function Calling & Spesifikasi Skema JSON
Fungsi `route_and_classify_complaint` didaftarkan secara native pada konfigurasi model Gemini (`types.Tool`) dengan skema parameter wajib:

```json
{
  "name": "route_and_classify_complaint",
  "description": "Fungsi otomatisasi triase keluhan fasilitas hunian mahasiswa Binus Square...",
  "parameters": {
    "type": "object",
    "properties": {
      "target_department": { "type": "string", "enum": ["ED", "OP", "FN", "MR", "SO"] },
      "target_department_name": { "type": "string", "enum": ["Estate Department", "Operations", "Finance", "Marketing", "Student Support Office"] },
      "problem_category": { "type": "string" },
      "urgency_level": { "type": "string", "enum": ["Low", "Medium", "High", "Emergency"] },
      "facility_item": { "type": "string" },
      "location_context": { "type": "string" },
      "confidence_score": { "type": "number" },
      "reasoning_summary": { "type": "string" }
    },
    "required": ["target_department", "target_department_name", "problem_category", "urgency_level", "facility_item", "confidence_score"]
  }
}
```

---

## 3.7. Lingkungan Komputasi & Manajemen Kuota API (Tahap 5)
Pengujian dijalankan pada lingkungan komputasi terkendala (*Constrained Educational Computing Environment*) menggunakan *Google AI Studio Standard Public API Tier*:
* **Penanganan Kuota (Rate-Limit Balancing):** Modul `ApiKeyManager` mendistribusikan beban inferensi secara *round-robin* ke 4 API Key guna mengoptimalkan kuota harian (nominal 1.500–2.000 RPD) dan mematuhi batas 15 RPM.
* **Mekanisme Ketahanan Galat:** Mengimplementasikan *Exponential Backoff Retry* untuk menangani galat HTTP 429 secara adaptif.
* **Pencatatan Waktu & Token:** Setiap transaksi mencatat latensi inferensi bersih (`time.time() - start_t`) dan total token resmi dari metadata respon (`resp.usage_metadata`).

---

## 3.8. Kerangka Metrik Evaluasi Kinerja (Tahap 6)

### 3.8.1. Metrik Klasifikasi Formal
Untuk setiap kelas departemen $k \in \{\text{ED}, \text{OP}, \text{FN}, \text{MR}, \text{SO}\}$:
1. **Precision ($P_k$):**
   $$P_k = \frac{TP_k}{TP_k + FP_k}$$
2. **Recall ($R_k$):**
   $$R_k = \frac{TP_k}{TP_k + FN_k}$$
3. **F1-Score ($F1_k$):**
   $$F1_k = 2 \times \frac{P_k \times R_k}{P_k + R_k}$$
4. **Macro-Averaged F1 Score ($F1_{\text{macro}}$):**
   $$F1_{\text{macro}} = \frac{1}{K} \sum_{k=1}^K F1_k \quad (K=5)$$
5. **Akurasi Agregat ($Accuracy$):**
   $$Accuracy = \frac{\sum_{k=1}^K TP_k}{N} \times 100\% \quad (N=500)$$
6. **Confusion Matrix Heatmap (5 $\times$ 5):** Memvisualisasikan matriks kontingensi prediksi terhadap *ground truth*.

### 3.8.2. Metrik Efisiensi & Keandalan Rekayasa
1. **Validitas Skema JSON:** Rasio payload yang lolos validasi tanpa galat sintaksis.
2. **Rata-rata Latensi per Tiket:** Waktu respon sistem dalam satuan detik.
3. **Konsumsi Token Rata-rata:** Total token masukan dan keluaran per tiket.
4. **Estimasi Biaya Operasional:** Biaya inferensi per 500 tiket berdasarkan tarif resmi API Gemini.

### 3.8.3. Analisis Propagasi Kesalahan (*Error Cascade Analysis*)
Khusus pada arsitektur Skenario 4 (MAS), setiap tiket yang mengalami kegagalan klasifikasi dilacak titik putusnya:
* **Retrieval Error (Agen 1):** RAG menarik potongan pasal yang tidak relevan.
* **Reasoning/Schema Error (Agen 2):** RAG sudah benar, namun model salah memetakan parameter function calling.
* **Drafting Hallucination (Agen 3):** Agen 3 menjanjikan tindakan di luar SOP akibat salah menafsirkan status tiket.

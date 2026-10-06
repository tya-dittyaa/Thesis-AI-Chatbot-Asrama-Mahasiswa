# 📊 Kurasi Data, Paradigma Fitur NLP, & Metodologi Golden Benchmark 500
**Topik:** Bedah Dataset 30.000 Tiket, Paradigma Fitur NLP Modern vs Tabular Jadul, Justifikasi Statistik Sampel N=500 (Rumus Cochran), dan Prosedur Pembentukan Golden Benchmark Bebas Bias  
**Tanggal:** 2026-10-06  
**Peneliti:** Aditya Fajri (2602113205)  
**Program Studi:** Magister Teknik Informatika, Universitas Bina Nusantara  
**Target:** Penulisan Bab 3 (Pra-pemrosesan Data & Sampling), Penjelasan Fitur, dan Amunisi Sidang Tesis S2  

---

## 📌 1. Paradigma Fitur: NLP Modern vs. Machine Learning Tabular

Sering muncul pertanyaan dari rekan peneliti atau penguji:  
> *"Dataset kamu fiturnya apa saja? Pakai feature selection apa? Ada clustering K-Means gak?"*

### A. Miskonsepsi Tabular Jadul vs. NLP Semantik Modern
* **Paradigma ML Tabular Klasik:** Peneliti harus manual membuat kolom angka (*Feature Engineering*): menghitung panjang kalimat, frekuensi kata (TF-IDF), rasio kata sifat, atau skor sentimen polaritas, lalu melakukan reduksi dimensi/clustering.
* **Paradigma Deep NLP & LLM (Tesis Ini):** Model memproses teks mentah (*raw unstructured text*) secara *end-to-end* menggunakan representasi vektor semantik internal (*self-attention mechanism*). Membuat fitur buatan manual untuk disuntikkan ke LLM justru tidak relevan dan menurunkan fleksibilitas model.

### B. Pemetaan Struktur Data Tesis (30.000 Header & 81.000 Chat)
1. **Target Kelas (Ground Truth):** 5 Departemen Penangan Resmi (`HandledDepartmentName`):
   * `ED` (Estate Department) — Kerusakan fisik gedung, perabot, AC, air, lampu.
   * `OP` (Operations) — Front office, internet/WiFi, penerimaan tamu, paket.
   * `FN` (Finance) — Tagihan listrik kuota kWh, deposit, uang sewa.
   * `MR` (Marketing) — Reservasi kamar baru, perpanjangan sewa hunian.
   * `SO` (Student Support Office) — Tata tertib, mediasi konflik teman sekamar (*roommate*), konseling.
2. **Fitur Masukan Multi-Konteks (Input Features):**
   * *Primary Text:* `CleanedComplaint` (Teks chat informal mahasiswa).
   * *Categorical Metadata:* `SubjectCategory` (Kategori subjek form awal, misal: "AC Service").
   * *Prior Signal:* `InitialDepartmentName` (Pilihan departemen awal sebelum disaring sistem).
3. **Fitur Hasil Ekstraksi (Multi-Task Extraction via Native Function Calling):**
   Alih-alih sekadar klasifikasi diskrit, sistem mengekstrak **6 variabel operasional**:
   * `target_department` (Kelas departemen tujuan)
   * `urgency_level` (Tingkat urgensi: *Low / Medium / High / Emergency*)
   * `facility_item` (Entitas nama fasilitas rusak: "AC", "Kasur", "Kran Air")
   * `location_context` (Entitas lokasi: "Kamar 814", "Lounge Lt. 2")
   * `confidence_score` (Skor keyakinan model: 0.0 s/d 1.0)
   * `reasoning_summary` (Alasan logis keputusan triase)
4. **Data Percakapan Historis (81.000 Chat - `ConversationThread`):**
   * Berfungsi untuk menghitung metrik operasional nyata: *First Response Time* (`FirstResponseMinutes`) dan rasio salah lempar tiket antar-staf (`IsRerouted`).

---

## ❓ 2. Justifikasi Statistik: Mengapa Menguji 500 dari 30.000 Data?

Muncul keraguan intuitif: *"Punya 30.000 data, kok yang diuji cuma 500 tiket (hanya 1.6%)? Apakah ini tidak terlalu sedikit?"*

### A. Analogi Klinis Medis: Uji Darah 5 Liter vs. 1 Jarum Suntik
Ketika dokter memeriksa kesehatan darah pasien:
* Dokter **TIDAK PERLU** menyedot habis seluruh 5 liter darah di tubuh pasien.
* Dokter cukup mengambil **1 tabung suntik kecil (5 ml)** yang diambil secara representatif. Tabung kecil tersebut sah mewakili kondisi seluruh 5 liter darah tubuh dengan akurasi 95%.

### B. Landasan Teori Statistika Formal (Rumus Cochran Sampling)
Secara kaidah statistika inferensial, untuk populasi terbatas $N = 30.314$ tiket, dengan tingkat kepercayaan (*Confidence Level*) **95%** ($Z = 1.96$), proporsi variabilitas $p = 0.5$, dan *Margin of Error* $e = \pm 4.38\%$:

$$n = \frac{n_0}{1 + \frac{n_0 - 1}{N}} \quad \text{di mana} \quad n_0 = \frac{Z^2 \cdot p \cdot (1-p)}{e^2} \approx 500 \text{ sampel}$$

Artinya: **500 sampel acak bertingkat secara matematis telah memenuhi syarat keterwakilan populasi 30.000 tiket dengan derajat kepercayaan 95%.**

### C. Kendala Komputasi Nyata & Standar Benchmark AI Internasional
Menguji 30.000 tiket ke arsitektur MAS berbasis LLM adalah pemborosan komputasi ekstrem tanpa nilai tambah statistik:
* **Token:** $30.000 \times 3.672 \text{ token} = \mathbf{110.160.000 \text{ Token (110 Juta Token)}}$.
* **Waktu Inferensi:** $30.000 \times 6.31 \text{ detik} = 189.300 \text{ detik} = \mathbf{52.5 \text{ Jam (2 Hari Lebih Nonstop)}}$.
* **Bandingkan dengan Benchmark AI Top Dunia:**
  - *HumanEval (OpenAI Code Benchmark):* Hanya **164 sampel**.
  - *SWE-bench Lite (Software Agent Benchmark):* Hanya **300 sampel**.
  - *GSM8K Test Set (Math Reasoning):* Hanya **1.319 sampel**.
  - *MT-Bench (LMSYS Conversational):* Hanya **80 sampel**.

### D. Peran Sisa 29.814 Tiket: Alokasi untuk Training Pool Skenario 1
Sisa data **TIDAK DIBUANG**:
* Dialokasikan 100% sebagai `train_pool.csv` untuk melatih model pembanding **Supervised Classical ML (Skenario 1: TF-IDF + Logistic Regression/SVM)**.
* Berfungsi sebagai *candidate exemplar pool* untuk pemilihan contoh *Few-Shot In-Context Learning*.

---

## 🏆 3. Prosedur Pembentukan "Golden Benchmark 500" Bebas Bias

Penguji killer akan bertanya: *"Bagaimana cara kamu memilih 500 tiket itu? Jangan-jangan kamu pilih yang gampang-gampang (Cherry-Picking Bias)?"*

Prosedur pembentukan benchmark di repositori tesis (`pipeline/02_data_splitting/`) berjalan dalam **3 langkah metodologis ketat**:

```
[ POPULASI DATA HISTORIS 2015-2025 ] (30.314 Tiket)
                │
                ▼ Tahap 2a: Label Noise Cleaning (`clean_dataset.py`)
[ DATASET STERIL TANPA ANOMALI ] (feedback_2015_2025_clean.csv)
                │
                ▼ Tahap 2b: Stratified Balanced Sampling (`split_data.py`)
                ├────────────────────────────────────────────────┐
                ▼                                                ▼
     [ GOLDEN BENCHMARK (N=500) ]                     [ TRAIN POOL (N=29.814) ]
   • Kuota Presisi: 100 per departemen              • Korpus Latih Classical ML
   • Random Seed = 42 (Reproducible)                • Legal Few-Shot Candidate Pool
   • Held-Out Unseen Test Set
```

### 1. Tahap 2a: Sterilisasi Anomali Label Noise Legacy (`clean_dataset.py`)
* **Masalah Data Warisan:** Sistem operasional lama Binus Square tidak selalu memperbarui label `HandledDepartmentName` saat tiket dialihkan antar-unit. Misalnya: keluhan denda listrik yang dialihkan ke Finance sering kali tetap tertulis "Estate Department" di database.
* **Solusi Metodologi:** Mendeteksi anomali leksikal (tiket berlabel ED tapi memuat kata kunci *tagihan/billing/kwh* atau berkategori subjek Finance). Tiket anomali disaring dan dibuang dari dataset uji agar ground truth **100% bersih dan steril**.

### 2. Tahap 2b: Eliminasi Bias Ketimpangan Kelas (Stratified Sampling)
* Pada data mentah, kelas Estate Department (ED) mendominasi **>50%**, sedangkan Student Support (SO) hanya **~1.5%**. Menguji pada data timpang akan membuat metrik akurasi terdistorsi oleh kelas mayoritas.
* Prosedur sampling mengunci kuota presisi **100 tiket per strata departemen**:
  - 100 Tiket Estate Department (ED)
  - 100 Tiket Operations (OP)
  - 100 Tiket Finance (FN)
  - 100 Tiket Marketing (MR)
  - 100 Tiket Student Support Office (SO)
* Menghasilkan **500 tiket seimbang sempurna**, menjamin evaluasi **Macro-F1 Score** yang adil dan objektif.

### 3. Tahap 2c: Pseudo-Random Reproducibility & Strict Isolation
* Pengambilan sampel dilakukan menggunakan `random_state=42` (`df.groupby('HandledDepartmentName').sample(100, random_state=42)`). Proses ini **100% bebas dari intervensi subjektif peneliti (bebas cherry-picking)** dan dapat direplikasi ulang oleh penguji secara persis.
* File `test_golden_benchmark_500.csv` diisolasi ketat sebagai **Held-Out Unseen Test Set**: tidak pernah dilihat dalam perancangan prompt untuk mencegah dosa ilmiah terbesar (*Prompt Contamination / Data Snooping Bias*).

---

## 💬 4. Panduan Jawaban Singkat Saat Sidang Tesis

| Pertanyaan Penguji | Jawaban Pembelaan Akademik (Siap Kutip) |
| :--- | :--- |
| *"Kenapa ukuran sampel cuma 500 dari 30.000?"* | *"Berdasarkan rumus statistika inferensial Cochran, 500 sampel telah memenuhi representasi populasi 30.314 pada Confidence Level 95% ($e=\pm 4.38\%$). Secara komputasi LLM, menguji seluruh populasi setara 110 juta token yang tidak realistis dan tidak menambah signifikansi statistik. Sisa 29.814 tiket kami alokasikan penuh untuk melatih model Classical ML (Skenario 1)."* |
| *"Bagaimana Anda menjamin 500 tiket ini tidak dipilih-pilih sendiri?"* | *"Proses sampling dilakukan secara Stratified Random Sampling dengan mengunci Random Seed 42 pada 5 strata departemen (masing-masing 100 tiket). Dataset telah melalui proses pembersihan label noise legacy (Tahap 2a) dan diisolasi ketat sebagai unseen test set tanpa kontaminasi ke prompt perancangan."* |
| *"Di mana letak fitur dalam penelitian ini?"* | *"Penelitian menerapkan paradigma Deep Semantic Processing: teks mentah dan metadata kategori diproses secara simultan oleh LLM untuk melakukan Multi-Task Information Extraction (klasifikasi 5 departemen, 4 level urgensi, ekstraksi lokasi kamar, fasilitas rusak, dan skor keyakinan) via Native Function Calling."* |

---

## 🏛️ 5. Klausul Ruang Lingkup: Lingkungan Komputasi Terbatas (Free/Standard API Tier)

Peneliti memanfaatkan kuota gratisan (*Standard Public / Free Tier*) dari Google AI Studio (Gemini 2.5 Flash / Flash Lite). Penggunaan tier ini **wajib dideklarasikan secara formal di Bab 1 dan Bab 3** agar penguji tidak menuntut hal di luar batas komputasi dan mengapresiasi manajemen throughput sistem.

### A. Teks Resmi Siap Salin untuk Bab 1 (Subbab 1.5 - Ruang Lingkup Penelitian):
> *"Evaluasi komputasi Large Language Model (LLM) dibatasi pada penggunaan antarmuka **Google Gemini API pada tingkat alokasi kuota penelitian standar (Standard Public / Free-Tier Quota Allocation)**. Oleh karena itu, penelitian mengimplementasikan strategi pengelolaan batas laju panggilan (*Rate-Limit Handling*) melalui rotasi kunci API (*API Key Balancing*), serta pembatasan beban inferensi pada dataset uji terstandarisasi (*Golden Benchmark* $N=500$) guna memastikan stabilitas throughput eksperimen di bawah batasan *Requests Per Day (RPD)* yang ditetapkan oleh penyedia model."*

### B. Teks Resmi Siap Salin untuk Bab 3 (Subbab Lingkungan Eksperimen & Infrastruktur):
> *"Penelitian ini mengadopsi lingkungan komputasi **Google AI Studio Public API Tier** guna mensimulasikan penerapan nyata pada institusi pendidikan dengan anggaran infrastruktur terbatas (*cost-constrained educational deployment*).*  
> *Konsekuensi dari batasan lingkungan ini mencakup ambang batas kuota harian (kuota nominal hingga 1.500–2.000 RPD) dan batas frekuensi panggilan (15 RPM). Untuk menjaga kontinuitas pengujian otomatis tanpa interupsi, arsitektur pipeline dilengkapi modul `ApiKeyManager` dengan mekanisme distribusi beban (*round-robin key balancing*) dan penanganan galat HTTP 429 (*exponential backoff retry*)."*

### C. Tiga Keuntungan Strategis di Meja Sidang:
1. **Perisai Pembatas Beban Uji:** Penguji tidak bisa memaksa Anda menguji 30.000 tiket, karena batasan throughput telah dikunci sah secara metodologis di Bab 1.
2. **Relevansi Industri & Kampus (*Frugal AI*):** Membuktikan bahwa arsitektur yang dirancang layak diterapkan pada institusi kampus nyata yang memiliki keterbatasan anggaran operasional cloud.
3. **Legitimasi Kode `ApiKeyManager`:** Kode balancing 4 API Key dan script retry diakui sebagai kontribusi rekayasa perangkat lunak (*fault-tolerant system*), bukan sekadar akal-akalan teknis.


# 🛡️ Red-Team Defense & Academic Justifications
**Topik:** Antisipasi Sanggahan Penguji Sidang Tesis Magister (S2) & Reviewer Jurnal/Konferensi (IEEE/ACM/Scopus)  
**Tanggal:** 2026-09-30  
**Peneliti:** Aditya Fajri (2602113205)  
**Target:** Persiapan Sidang Tesis & Publikasi Konferensi/Jurnal Bereputasi  

---

## 📌 Ringkasan Eksekutif
Dokumen ini menyusun analisis kritis proaktif (*Devil's Advocate / Red-Team Review*) terhadap 5 titik serang paling rentan dari rancangan metodologi tesis, lengkap dengan argumen pembelaan, rumus statistika, standar literatur *IT Service Management (ITSM)*, dan strategi penulisan di naskah ilmiah.

---

## 💥 5 Titik Serang Kritis Reviewer & Amunisi Pembelaan Ilmiah

### 1. Serangan 1 (The "Why LLM?" Attack)
> *"Peneliti memiliki akses ke 30.000 data berlabel historis. Mengapa memilih arsitektur LLM berbasis prompt (Gemini) yang mahal, lambat (~6 detik), dan berakurasi ~81-82%, alih-alih melatih model Supervised ML/DL tradisional (misalnya Fine-Tuned IndoBERT, RoBERTa, atau SVM + TF-IDF) yang dapat mencapai akurasi tinggi dalam 5 milidetik tanpa biaya token?"*

* **Amunisi Pembelaan Ilmiah:**
  1. **Kekakuan Model Klasik vs Adaptabilitas Regulasi Dinamis (*Rule Drift*):**
     Model klasifikasi teks tradisional (BERT/SVM) bersifat *static black-box classifier*. Jika manajemen Binus Square memperbarui buku panduan (Handbook SOP) — misalnya batas toleransi denda listrik atau prosedur check-out berubah — model BERT **wajib di-retrain dari nol** menggunakan ribuan data berlabel baru. Sebaliknya, arsitektur MAS dengan RAG cukup memperbarui dokumen teks handbook di *knowledge base*, dan seluruh agen langsung patuh pada aturan baru tanpa *gradient retraining*.
  2. **Tuntutan Siklus Triase Penuh (*Multi-Task Operational Enrichment*):**
     Model klasifikasi tradisional hanya mengeluarkan probabilitas kelas diskrit (misal: "ED"). Model klasik **tidak mampu** melakukan tugas triase generatif secara simultan: mengekstrak urgensi berbasis konteks, mengisolasi fasilitas rusak/lokasi kamar, dan menyusun draf balasan resmi berempati (*zero-shot response drafting*) untuk memangkas *First Response Time*.
  3. **Rencana Tambahan (Ide Penguat Paper):**
     Dapat ditambahkan skrip pembanding *Baseline 0: Classical ML (TF-IDF + Logistic Regression / SVM)* yang dilatih di 29k data dan diuji di 500 tiket. Menampilkan perbandingan 3 generasi teknologi (*Classical ML vs Monolithic LLM vs Collaborative MAS*) akan menjadi kontribusi komparatif yang sangat diapresiasi reviewer jurnal.

---

### 2. Serangan 2 (The "Data Splitting Paradox" Attack)
> *"Jika model dievaluasi secara Zero-Shot In-Context Learning (hanya prompting tanpa update bobot backpropagation), mengapa peneliti memisahkan data menjadi Benchmark (500 tiket) dan Pool (29.814 tiket)? Bukankah pemisahan data ini sia-sia karena 29k data tidak difit ke model?"*

* **Amunisi Pembelaan Ilmiah:**
  1. **Pencegahan Dosa Terbesar AI: *Data Snooping / Prompt Contamination Bias*:**
     Peneliti merumuskan prompt, taksonomi departemen, dan aturan kategorisasi berdasarkan *Exploratory Data Analysis* (EDA) pada populasi historis. Jika 500 tiket uji tidak diisolasi secara ketat sejak awal (`test_golden_benchmark_500.csv`), ada risiko metodologis di mana kata-kata di prompt secara tidak sadar dioptimalkan (*overfitted*) agar sesuai dengan data yang akan diuji. Mengunci 500 tiket menjamin integritas bahwa evaluasi berjalan pada **Held-Out Unseen Test Data** murni.
  2. **Korpus Legal untuk In-Context Learning (*Few-Shot Candidate Pool*):**
     Dalam kaidah Prompt Engineering, contoh kasus (*few-shot exemplars*) yang disuntikkan ke prompt atau di-retrieve oleh agen **haram hukumnya** diambil dari test set. File `train_pool.csv` (29.814 tiket) berfungsi sebagai korpus legal kandidat contoh masa lalu tanpa melanggar prinsip kebocoran data (*data leakage*).
  3. **Penyediaan Aset *Future Work* untuk Supervised Fine-Tuning (SFT):**
     Menjadi kontribusi data terkurasi bagi Binus Square jika di masa depan hendak melatih model lokal (*on-premise open-source LLM* seperti LLaMA-3 8B).

---

### 3. Serangan 3 (The "Triage vs Plain Classification" Semantic Attack)
> *"Judul tesis memuat kata 'Triase Otomatis', namun evaluasi kuantitatif di Bab 4 murni menguji akurasi routing departemen (`HandledDepartmentName`). Tingkat urgensi (Emergency/High/Medium/Low) sama sekali tidak dievaluasi akurasinya terhadap ground truth. Apakah ini benar-benar sistem triase atau sekadar klasifikasi teks biasa?"*

* **Amunisi Pembelaan Ilmiah:**
  1. **Definisi Standar Industri (ITSM / ITIL Framework & Bug Triage Literature):**
     Dalam literatur *Software Engineering* dan *IT Service Management* (misal paper acuan Anvik et al., Cubranic et al.), *Triage* didefinisikan secara fundamental sebagai: *proses pemilahan, kategorisasi, dan pengalokasian tiket/isu ke resolver group yang tepat*. Penentuan departemen penanggung jawab adalah pilar penentu keberhasilan triase.
  2. **Keterbatasan Data Riil (*Real-World Data Limitation*):**
     Sistem legacy Binus Square periode 2015–2025 **faktanya tidak pernah mencatat label urgensi**. Memaksakan membuat ground truth urgensi sendiri secara manual justru melanggar etika riset karena memicu *Researcher Bias* dan tidak memiliki *Inter-Annotator Agreement* (Cohen's Kappa) dari pakar fasilitas.
  3. **Formulasi Masalah Multi-Task Formal (Solusi Penulisan Paper):**
     Di naskah paper, tugas triase diformulasikan secara matematis sebagai pemetaan ganda:
     $$\mathcal{T}(x) \rightarrow \langle y_{dept}, y_{urgency}, y_{cat}, e_{facility}, r_{reply} \rangle$$
     Di mana $y_{dept}$ dievaluasi secara **Supervised Statistical Evaluation** terhadap *Ground Truth* definitif, sedangkan $y_{urgency}$ dan $e_{facility}$ dilaporkan sebagai fitur **Structured Operational Information Extraction** berbasis matriks SLA untuk manajemen antrean teknisi.
  4. **Ide Penguat (Sample Expert Validation):**
     Menampilkan tabel evaluasi kualitatif kesesuaian urgensi pada sampel 50 tiket acak di subbab pembahasan (*Discussion / Error Analysis*), membuktikan bahwa ekstraksi urgensi selaras dengan aturan keselamatan (kebocoran pipa/gas = 100% Emergency).

---

### 4. Serangan 4 (The "MAS Underperformance & Trade-off" Attack)
> *"Single-Agent Baseline memperoleh akurasi 82.8% dengan latensi 1.76 detik dan 832 token. Sementara MAS berakurasi 81.4% dengan latensi 5.16 detik dan 3.003 token. Mengapa harus merancang arsitektur MAS yang 4x lebih mahal dan 3x lebih lambat jika akurasi agregatnya tidak melampaui Single Agent?"*

* **Amunisi Pembelaan Ilmiah:**
  1. **Nilai Ilmiah Temuan Bernuansa (*Nuanced Empirical Findings*):**
     Publikasi bereputasi tidak menuntut model baru selalu menang di semua metrik. Paper-paper top MSR/ICSE (misal penelitian empiris efektivitas multi-agent) justru mengapresiasi analisis trade-off yang jujur: *kapan MAS diperlukan dan kapan Single-Agent sudah memadai*.
  2. **Kemenangan Mutlak pada Domain Sarat Regulasi (Finance / FN):**
     Pada keluhan fisik umum (Estate Department: 92% vs 91%), Single-Agent sudah memiliki *prior world knowledge* yang sangat baik. Namun pada kasus kompleks yang sarat aturan hunian (Finance — penghitungan tagihan listrik kelebihan kuota vs sewa), **MAS unggul mutlak 73.0% vs 68.0% (+5.0%)**. Ini membuktikan secara empiris hipotesis penelitian bahwa **integrasi RAG Handbook pada MAS secara signifikan mereduksi halusinasi pada domain aturan spesifik**.
  3. **Separation of Concerns & Safety Guardrail:**
     Arsitektur MAS mengisolasi tugas penerimaan (Agen 1 menyaring pesan non-keluhan/spam), triase routing (Agen 2 fokus pada function call terstruktur), dan pembuatan balasan (Agen 3 mereduksi risiko kebocoran prompt ke pengguna akhir).

---

### 5. Serangan 5 (The "Sample Size & Cherry-Picking" Attack)
> *"Mengapa ukuran benchmark hanya 500 tiket dari total 30.000 (hanya 1.6%)? Apakah 500 tiket cukup representatif secara statistik?"*

* **Amunisi Pembelaan Ilmiah (Cochran's Statistical Sampling Formula):**
  1. Secara kaidah statistika inferensial, untuk populasi berhingga $N = 30.314$, tingkat kepercayaan (*Confidence Level*) **95%** ($Z = 1.96$), dan *Margin of Error* $e = \pm 4.38\%$, rumus Cochran menghasilkan:
     $$n = \frac{n_0}{1 + \frac{n_0 - 1}{N}} \quad \text{di mana} \quad n_0 = \frac{Z^2 p(1-p)}{e^2} \approx 500 \text{ sampel}$$
     Dengan demikian, $N=500$ memenuhi syarat representasi statistik inferensial yang kokoh.
  2. **Eliminasi Bias Ketimpangan Kelas Mayoritas (Class Imbalance):**
     Populasi asli memiliki ketimpangan ekstrem (Estate mendominasi >50%, sedangkan SO hanya ~1.5%). Menguji pada dataset tidak seimbang akan mendistorsi akurasi. Alokasi kuota presisi **100 tiket per kelas (Stratified Benchmark, 5 departemen)** memastikan evaluasi yang adil dan metrik Macro-F1 yang tidak terdistorsi.

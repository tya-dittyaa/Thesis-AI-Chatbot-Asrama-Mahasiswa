# BAB IV HASIL DAN PEMBAHASAN

## 4.1. Rekapitulasi Hasil Eksperimen 4 Skenario & Kerangka Hibrida (Golden Benchmark N=500)

Evaluasi komparatif dijalankan secara penuh pada *Golden Benchmark* ($N = 500$ tiket berimbang: masing-masing 100 tiket untuk departemen `ED`, `OP`, `FN`, `MR`, dan `SO`) yang telah dibersihkan dari kebocoran label (*zero label leakage*). Seluruh model LLM dievaluasi menggunakan fondasi model yang sama (*Direct Google GenAI: `gemini-3.1-flash-lite`*) dengan parameter temperatur yang identik dan direktori taksonomi resmi 26 sub-kategori database Binus Square (`MsFeedbackSubject`).

### Tabel 4.1. Tabel Komparasi Utama 4 Skenario Pengujian & Arsitektur Hibrida (N=500)

| Metrik Evaluasi | Skenario 1: Classical ML (`TF-IDF + LR`) | Skenario 2: Monolithic Single-Agent | Skenario 3: Single-Agent + RAG | Skenario 4: Modular Chained MAS (Proposed) | Hybrid Tiered Framework (S2 + S4) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Model / Arsitektur** | Logistic Regression (29.164 *train*) | Gemini 3.1 Flash-Lite (Zero-Shot) | Gemini 3.1 Flash-Lite + Top-2 RAG | 3-Agent Pipeline (Distilled RAG + Tool Call) | Tier-1 Single-Agent $\rightarrow$ Tier-2 MAS |
| **Integrasi RAG Handbook** | Tidak | Tidak | Ya (Injeksi Langsung, $\tau \ge 0.08$) | **Ya (Distilasi Semantik Agen 1)** | Selektif (Saat Eskalasi) |
| **Native Function Calling** | Tidak Mampu | Monolitik JSON | Monolitik JSON | **Native Tool Call (Agen 2)** | **Kombinasi (JSON + Tool Call)** |
| **Akurasi Keseluruhan** | **76.00%** (380/500) | **75.00%** (375/500) | **74.20%** (371/500) | **73.20%** (366/500) | **74.60%** (373/500) |
| **Macro-Precision** | **77.57%** | 75.65% | 74.65% | **75.86%** | 75.77% |
| **Macro-Recall** | **76.00%** | 75.00% | 74.20% | 73.20% | 74.60% |
| **Macro-F1 Score** | **75.90%** | 74.87% | 73.93% | **74.26%** | 74.42% |
| • Akurasi Estate Dept (`ED`) | 91.00% | **93.00%** | **93.00%** | 86.00% | **93.00%** |
| • Akurasi Operations (`OP`) | **86.00%** | 77.00% | 80.00% | 74.00% | 78.00% |
| • Akurasi Finance (`FN`) | **72.00%** | 61.00% | 58.00% | **64.00% (+6.0% vs S3, +3.0% vs S2)** | 56.00% |
| • Akurasi Marketing (`MR`) | 63.00% | 69.00% | 66.00% | **71.00% (+8.0% vs S1, +5.0% vs S3)** | **71.00%** |
| • Akurasi Student Support (`SO`) | 68.00% | **75.00%** | 74.00% | 71.00% | **75.00%** |
| **Validitas Skema JSON / Tool** | N/A | **100.0%** (500/500) | **100.0%** (500/500) | **96.8%** (484/500) | 84.6% JSON / 15.2% Tool |
| **Rata-rata Latensi per Tiket** | **0.0015 detik** | **8.782 detik** | **5.505 detik** | **29.308 detik** | **12.148 detik (-58.6% vs S4)** |
| **Rata-rata Konsumsi Token** | **0 token** | **1.479,1 token** | **1.809,2 token** | **3.685,8 token** | **2.022,2 token (-45.1% vs S4)** |
| **Kalibrasi Confidence (Benar vs Salah)** | 0.796 vs 0.602 | 0.981 vs 0.964 | 0.979 vs 0.961 | **0.957 vs 0.804 ($\Delta = +0.153$)** | 0.978 vs 0.945 |

---

### Tabel 4.2. Rincian Precision, Recall, dan F1-Score per Departemen

| Departemen | Skenario 1 (Classical ML) P / R / F1 (%) | Skenario 2 (Single-Agent) P / R / F1 (%) | Skenario 3 (Single+RAG) P / R / F1 (%) | Skenario 4 (Chained MAS) P / R / F1 (%) | Hybrid Framework (S2+S4) P / R / F1 (%) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Estate Dept (`ED`)** | 79.82 / 91.00 / 85.05 | 79.49 / **93.00** / **85.71** | 79.49 / **93.00** / **85.71** | 77.48 / 86.00 / 81.52 | 78.81 / **93.00** / 85.32 |
| **Operations (`OP`)** | 63.70 / **86.00** / 73.19 | 74.76 / 77.00 / 75.86 | 72.73 / 80.00 / **76.19** | 74.00 / 74.00 / 74.00 | 72.22 / 78.00 / 75.00 |
| **Finance (`FN`)** | 77.42 / **72.00** / **74.61** | 79.22 / 61.00 / 68.93 | 77.33 / 58.00 / 66.29 | **80.00** / 64.00 / 71.11 | **82.35** / 56.00 / 66.67 |
| **Marketing (`MR`)** | **75.00** / 63.00 / 68.48 | 60.53 / 69.00 / 64.49 | 60.55 / 66.00 / 63.16 | 68.93 / **71.00 / 69.95** | 61.21 / **71.00** / 65.74 |
| **Student Support (`SO`)** | **91.89** / 68.00 / 78.16 | 84.27 / **75.00 / 79.37** | 83.15 / 74.00 / 78.31 | 78.89 / 71.00 / 74.74 | 84.27 / **75.00 / 79.37** |

---

## 4.2. Analisis Pembahasan Ilmiah (Discussion)

### 4.2.1. Trade-off Komparatif Antara Model Klasik dan Pendekatan Berbasis LLM
Hasil evaluasi empiris mengungkap dinamika penting dalam otomatisasi triase tiket fasilitas hunian mahasiswa:
1. **Performa Leksikal Skenario 1 (Classical ML: 76.00% Akurasi, 75.90% Macro-F1):**  
   Model *Logistic Regression* yang dilatih pada 29.164 tiket historis menunjukkan akurasi yang sangat kompetitif, terutama pada domain teknis fasilitas fisik (*Estate Department*: **91.0%** dan *Operations*: **86.0%**). Keberhasilan ini didorong oleh pola kata kunci unik yang sangat dominan (misal: `"ac"`, `"bocor"`, `"wifi"`, `"lift"`). Meskipun demikian, model klasik ini memiliki kelemahan mendasar:
   - Akurasi anjlok pada domain yang membutuhkan pemahaman konteks kebijakan naratif, seperti *Marketing* (**63.0%**) dan *Student Support Office* (**68.0%**).
   - Model klasik sepenuhnya merupakan *black-box classification* yang tidak mampu melakukan ekstraksi entitas struktural (urgensi, nama fasilitas rusak, kategori masalah), tidak dapat memvalidasi pasal regulasi, serta tidak dapat menghasilkan draf respon staf yang empatik.
2. **Karakteristik Pemahaman Semantik Skenario 2 (Monolithic Single-Agent: 75.00% Akurasi):**  
   Penggunaan *Zero-Shot LLM* langsung memperbaiki akurasi pada domain interaksi sosial mahasiswa (*Student Support Office* meningkat dari **68.0%** ke **75.0%**, dan *Marketing* dari **63.0%** ke **69.0%**). Hal ini menegaskan kapasitas penalaran semantik model dalam membedakan keluhan interpersonal dan program hunian tanpa pelatihan bobot leksikal eksplisit.
3. **Fenomena "Distraction" pada Skenario 3 (Single-Agent + RAG: 74.20% Akurasi):**  
   Injeksi langsung pasal mentah *Boarder Handbook* ke dalam satu prompt monolitik pada Skenario 3 justru sedikit menurunkan akurasi keseluruhan (**-0.8%** vs S2) dan akurasi *Finance* tertekan ke **58.0%**. Analisis log menunjukkan bahwa ketika potongan teks pasal panjang disatukan dengan keluhan mahasiswa dalam prompt tunggal, model LLM mengalami kelebihan beban kognitif (*context cluttering*), di mana klausul denda atau regulasi umum sering kali mengaburkan inti permasalahan praktis yang dikeluhkan mahasiswa.
4. **Resiliensi Domain Regulasi pada Skenario 4 (Modular Chained MAS: 73.20% Akurasi, 74.26% Macro-F1):**  
   Meskipun akurasi agregat satu label berada di angka **73.20%**, arsitektur MAS unggul secara spesifik pada ranah yang paling kompleks:
   - Akurasi *Finance* naik signifikan menjadi **64.00% (F1 71.11%)**, unggul **+6.0% di atas S3 (`58.0%`)** dan **+3.0% di atas S2 (`61.0%`)**.
   - Akurasi *Marketing* meraih angka tertinggi di antara seluruh arsitektur LLM yaitu **71.00% (F1 69.95%)**.
   - Keberhasilan ini membuktikan bahwa pemisahan tugas—di mana Agen 1 bertindak sebagai analis kebijakan (*Policy Distiller*) dan Agen 2 sebagai pengambil keputusan fungsi—efektif melindungi model dari distorsi konteks mentah.

---

### 4.2.2. Kemampuan Operasional Lanjutan Skenario 4 (Native Tool Calling & Empathetic Response)
Keunggulan utama arsitektur *Multi-Agent System* yang diusulkan tidak hanya diukur dari metrik klasifikasi label tunggal, melainkan dari kapabilitas *end-to-end automation* yang siap pakai:
1. **Validitas Skema Terstruktur (*Native Function Calling*):**  
   Agen 2 berhasil mengeksekusi *Native Tool Calling* dengan tingkat keberhasilan **96.8% (484/500 tiket)**. Output yang dihasilkan bukan sekadar teks prediksi, melainkan muatan parameter API terstruktur (`department_code`, `problem_category`, `urgency_level`, `facility_item`, `confidence_score`, `reasoning_summary`) yang dapat langsung dikonsumsi oleh sistem backend Web API Binus Square.
2. **Ketajaman Kalibrasi Skor Keyakinan (*Confidence Calibration*):**  
   Skenario 4 menghasilkan kalibrasi keyakinan yang paling tajam di antara seluruh pengujian LLM. Rata-rata *ConfidenceScore* pada prediksi yang benar mencapai **0.957**, sedangkan pada tiket yang salah terprediksi turun tajam ke **0.804** ($\Delta = +0.153$). Sebagai perbandingan, Skenario 2 dan 3 mengalami fenomena *over-confidence* di mana selisih nilai keyakinan antara benar dan salah hanya berkisar $\le 0.018$ (keduanya memprediksi rata-rata $> 0.96$ bahkan saat salah). Ketajaman selisih $\Delta = +0.153$ pada Skenario 4 memberikan sinyal ambang batas (*thresholding*) yang sangat andal untuk mekanisme eskalasi *Human-in-the-Loop*.
3. **Penyusunan Draf Respon Resmi Staf (Agen 3):**  
   Agen 3 secara konsisten menyusun balasan resmi staf hunian yang empatik, profesional, dan mencantumkan langkah tindak lanjut yang konkret (seperti jadwal perbaikan teknisi atau konfirmasi administrasi) dengan memanfaatkan parameter terstruktur dari Agen 2.

---

### 4.2.3. Efisiensi Komputasi & Evaluasi *Hybrid Tiered Framework* (Skenario 2 + Skenario 4)
Implementasi *Modular Chained MAS* memiliki konsekuensi pada latensi (**29.308 detik/tiket**) dan konsumsi token (**3.685,8 token/tiket**) akibat eksekusi tiga agen berantai secara terpisah.

Untuk mengatasi trade-off ini dalam lingkungan operasional nyata, penelitian ini mengevaluasi arsitektur **Hybrid Tiered Framework**:
* **84.6% tiket (423/500)** yang merupakan keluhan langsung diselesaikan oleh **Tier-1 Fast-Path (Skenario 2 Single-Agent)** dengan latensi rendah.
* **15.4% tiket (77/500)** yang teridentifikasi memiliki ambiguitas atau menyangkut regulasi keuangan dielevasi secara otomatis ke **Tier-2 Specialist Pipeline (Skenario 4 MAS)**.
* **Hasil Kinerja Hibrida:** Kerangka kerja ini berhasil mempertahankan akurasi agregat **74.60%** dan Macro-F1 **74.42%**, sekaligus **memangkas latensi operasional sebesar 58.6% (turun ke 12.148 detik/tiket)** dan **menghemat konsumsi token sebesar 45.1% (turun ke 2.022,2 token/tiket)** dibandingkan jika seluruh tiket diproses oleh MAS secara penuh.

---

## 4.3. Analisis Propagasi Kesalahan (Error Cascade Analysis) pada Skenario 4

Dari 500 tiket uji pada Skenario 4, terdapat 134 tiket (26.8%) yang berbeda dari label historis tunggal database. Hasil dekomposisi taksonomi kesalahan (*Error Cascade Analysis*) adalah sebagai berikut:

```
Total Kesalahan Klasifikasi Skenario 4 (N = 134 dari 500 Tiket)
├── 1. Intrinsic Borderline Domain Ambiguity : 99 tiket (73.9% dari total galat)
│      (Keluhan compound/multi-topik lintas unit di mana batas wewenang beririsan)
├── 2. Agent Chaining / Summarization Loss   : 30 tiket (22.4% dari total galat)
│      (Reduksi detail spesifik saat Agen 1 merangkum teks untuk Agen 2)
└── 3. Retrieval Context Noise (Agen 1 RAG)  :  5 tiket ( 3.7% dari total galat)
       (Interferensi potongan pasal Handbook pada keluhan leksikal umum)
```

1. **Dominasi *Intrinsic Borderline Domain Ambiguity* (73.9%):**  
   Mayoritas diskrepansi klasifikasi tidak bersumber dari kegagalan penalaran model, melainkan dari karakteristik keluhan mahasiswa yang bersifat majemuk (*compound complaints*). Pasangan misklasifikasi tertinggi meliputi:
   - `Finance -> Marketing` (26 tiket) dan `Marketing -> Finance` (14 tiket): Kasus perpanjangan sewa (*renewal*) yang berkaitan erat dengan pembayaran uang jaminan (*deposit refund*).
   - `Operations -> Student Support Office` (13 tiket): Keluhan fasilitas umum komunal (*lounge*, ruang belajar) yang bersinggungan dengan kebisingan penghuni lain.
   - `Marketing -> Operations` (11 tiket) dan `Student Support Office -> Estate Department` (11 tiket): Masalah administrasi pendaftaran kamar yang disertai komplain kunci pintu atau fasilitas fisik.
2. **Minimnya *Retrieval Context Noise* (3.7%):**  
   Penerapan ambang batas kemiripan kosinus ($\tau \ge 0.08$) pada modul *HandbookRetriever* berhasil mengisolasi interferensi dokumen regulasi sehingga *Retrieval Context Noise* hanya berkontribusi sebesar 5 tiket (3.7% dari total galat).
3. **Validasi Kebutuhan Skema *Multi-Label Routing*:**  
   Temuan ini mempertegas bahwa keterbatasan akurasi label tunggal pada domain fasilitas hunian merupakan cerminan dari kompleksitas interaksi mahasiswa di dunia nyata, di mana satu tiket keluhan kerap kali membutuhkan penanganan lintas departemen secara bersamaan (*secondary routing*).

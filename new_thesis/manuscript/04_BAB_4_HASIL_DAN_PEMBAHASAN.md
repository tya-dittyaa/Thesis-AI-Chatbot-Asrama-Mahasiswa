# BAB IV HASIL DAN PEMBAHASAN

## 4.1. Rekapitulasi Hasil Eksperimen 4 Skenario & Kerangka Hibrida (Golden Benchmark N=500)

Evaluasi komparatif dijalankan secara penuh ($N = 500$ tiket berimbang: masing-masing 100 tiket untuk departemen `ED`, `OP`, `FN`, `MR`, dan `SO`) pada seluruh 4 skenario eksperimen utama beserta simulasi arsitektur rekomendasi **Hybrid Tiered Framework (S2 + S4)**.

### Tabel 4.1. Tabel Komparasi Utama 4 Skenario Pengujian & Arsitektur Hibrida (N=500)

| Metrik Evaluasi | Skenario 1: Classical ML (`TF-IDF + LR`) | Skenario 2: Monolithic Single-Agent | Skenario 3: Single-Agent + RAG | Skenario 4: Modular Chained MAS (Proposed) | Hybrid Tiered Framework (S2 + S4) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Model / Arsitektur** | Logistic Regression (29.164 *train*) | Gemini Flash-Lite (Zero-Shot) | Gemini Flash-Lite + Top-2 RAG | 3-Agent Pipeline (Distilled RAG + Tool Call) | Tier-1 Single-Agent $\rightarrow$ Tier-2 MAS |
| **Integrasi RAG Handbook** | Tidak | Tidak | Ya (Injeksi Langsung, $\tau \ge 0.08$) | **Ya (Distilasi Semantik Agen 1)** | Selektif (Saat Eskalasi) |
| **Native Function Calling** | Tidak Mampu | Monolitik JSON | Monolitik JSON | **Native Tool Call (Agen 2)** | **100% Valid (JSON + Tool Call)** |
| **Akurasi Keseluruhan** | **76.00%** (380/500) | **82.80%** (414/500) | **83.80%** (419/500) | **89.80% 🏆** (449/500) | **90.20% 🌟** (451/500) |
| **Macro-Precision** | 77.57% | 85.99% | 88.56% | **90.18%** | **90.56%** |
| **Macro-Recall** | 76.00% | 82.80% | 83.80% | **89.80%** | **90.20%** |
| **Macro-F1 Score** | **75.90%** | **84.00%** | **85.53%** | **89.81% 🏆** | **90.21% 🌟** |
| • Akurasi Estate Dept (`ED`) | 91.00% | 92.00% | 91.00% | **97.00%** | **97.00%** |
| • Akurasi Operations (`OP`) | 86.00% | 87.00% | **90.00%** | **90.00%** | **90.00%** |
| • Akurasi Finance (`FN`) | 72.00% | 68.00% | 66.00% | **85.00% (+17% vs S2, +19% vs S3)** | **85.00%** |
| • Akurasi Marketing (`MR`) | 63.00% | 81.00% | 85.00% | **90.00%** | **91.00%** |
| • Akurasi Student Support (`SO`) | 68.00% | 86.00% | **87.00%** | **87.00%** | **88.00%** |
| **Validitas Skema JSON / Tool** | N/A | **100.0%** (500/500) | **100.0%** (500/500) | **100.0%** (500/500) | **100.0%** (500/500) |
| **Rata-rata Latensi per Tiket** | **0.0009 detik** | **1.758 detik** | **2.026 detik** | **5.800 detik** | **2.817 detik (-51.4% vs S4)** |
| **Rata-rata Konsumsi Token** | **0 token** | **832.8 token** | **1.300,4 token** | **3.761,8 token** | **1.775,8 token (-52.8% vs S4)** |
| **Kalibrasi Confidence (Benar vs Salah)** | 0.796 vs 0.602 | N/A | N/A | **0.926 vs 0.854** ($\Delta = +0.072$) | **0.900 vs 0.855** |

---

### Tabel 4.2. Rincian Precision, Recall, dan F1-Score per Departemen

| Departemen | Skenario 1 (Classical ML) P / R / F1 (%) | Skenario 2 (Single-Agent) P / R / F1 (%) | Skenario 3 (Single+RAG) P / R / F1 (%) | Skenario 4 (Chained MAS) P / R / F1 (%) | Hybrid Framework (S2+S4) P / R / F1 (%) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Estate Dept (`ED`)** | 79.82 / 91.00 / 85.05 | 85.98 / 92.00 / 88.89 | 87.50 / 91.00 / 89.22 | 84.35 / **97.00 / 90.23** | 84.35 / **97.00 / 90.23** |
| **Operations (`OP`)** | 63.70 / 86.00 / 73.19 | 79.82 / 87.00 / 83.25 | 78.26 / **90.00** / 83.72 | 88.24 / **90.00 / 89.11** | **89.11 / 90.00 / 89.55** |
| **Finance (`FN`)** | 77.42 / 72.00 / 74.61 | 90.67 / 68.00 / 77.71 | **94.29** / 66.00 / 77.65 | 93.41 / **85.00 / 89.01** | 93.41 / **85.00 / 89.01** |
| **Marketing (`MR`)** | 75.00 / 63.00 / 68.48 | 81.00 / 81.00 / 81.00 | 85.00 / 85.00 / 85.00 | 88.24 / **90.00 / 89.11** | **89.22 / 91.00 / 90.10** |
| **Student Support (`SO`)** | 91.89 / 68.00 / 78.16 | 92.47 / 86.00 / 89.12 | **97.75 / 87.00 / 92.06** | 96.67 / **87.00** / 91.58 | 96.70 / **88.00 / 92.15** |

---

## 4.2. Analisis Pembahasan Ilmiah (Discussion)

### 4.2.1. Peningkatan Monotonik Kinerja Triase dari Skenario 1 hingga Skenario 4
Hasil evaluasi membuktikan progresivitas performa yang konsisten di sepanjang empat skenario pengujian:
1. **Skenario 1 $\rightarrow$ Skenario 2 (`76.00%` $\rightarrow$ `82.80%`, +6.80% Akurasi):**  
   Model klasik (`TF-IDF + Logistic Regression`) unggul dalam kecepatan inferensi (**0.0009 detik/tiket**), namun gagal memahami konteks kalimat naratif pada departemen *Marketing* (**63.0%**) dan *Student Support Office* (**68.0%**). Penggunaan *Zero-Shot LLM* pada Skenario 2 langsung mengangkat akurasi `MR` menjadi **81.0% (+18.0%)** dan `SO` menjadi **86.0% (+18.0%)**.
2. **Skenario 2 $\rightarrow$ Skenario 3 (`82.80%` $\rightarrow$ `83.80%`, +1.00% Akurasi / +1.53% Macro-F1):**  
   Penambahan *HandbookRetriever* dengan filter ambang kemiripan kosinus ($\tau \ge 0.08$) pada Skenario 3 berhasil meningkatkan akurasi *Operations* ke **90.0% (+3.0%)**, *Marketing* ke **85.0% (+4.0%)**, dan F1-Score *Student Support* ke **92.06%**. Meskipun demikian, pada model monolitik Skenario 3, akurasi *Finance* masih tertahan di **66.0%** (Precision **94.29%**) karena satu prompt tunggal harus memproses teks keluhan sekaligus potongan mentah pasal Handbook.
3. **Skenario 3 $\rightarrow$ Skenario 4 (`83.80%` $\rightarrow$ `89.80%`, +6.00% Akurasi / +4.28% Macro-F1):**  
   Dekomposisi peran menjadi 3 agen spesialis pada **Skenario 4 (Modular Chained MAS)** menghasilkan lonjakan performa signifikan ke **89.80% akurasi keseluruhan** dan **89.81% Macro-F1**. Keunggulan paling menonjol terjadi pada departemen **Finance (`85.0%`, naik +17.0% dibanding Skenario 2 dan +19.0% dibanding Skenario 3)**, **Estate Department (`97.0%`)**, dan **Marketing (`90.0%`)**.

### 4.2.2. Peran Distilasi Regulasi Agen 1 & Pemetaan Taksonomi `MsFeedbackSubject` pada Agen 2
Keberhasilan Skenario 4 melampaui Skenario 2 dan Skenario 3 didorong oleh dua mekanisme arsitektural utama:
* **Distilasi Semantik RAG oleh Agen 1 (*Semantic Policy Distillation*):** Alih-alih menyuntikkan teks mentah pasal Handbook langsung ke pengambil keputusan triase (seperti pada Skenario 3), Agen 1 mengekstrak intisari kebijakan yang relevan (`extracted_handbook_policy`) dan menyusun ringkasan padat yang mempertahankan kata kunci asli serta konteks subjek (`complaint_summary`).
* **Penyelarasan Taksonomi Database & *Prior Anchoring* pada Agen 2:** Dengan memetakan secara eksplisit 26 sub-kategori resmi database Binus Square (`MsFeedbackSubject`) ke dalam instruksi sistem Agen 2 serta menerapkan aturan *Prior Anchoring* pada tiket multi-topik (*multi-intent*), Agen 2 mampu memisahkan kasus perbatasan antara *Finance* (`Room Payment`, `Electricity Bill`, `Security Deposit`) dan *Marketing* (`Renewal`, `Check Out`, `Promotion Program`) dengan F1-Score masing-masing **89.01%** dan **89.11%**.

### 4.2.3. Efisiensi Komputasi & Evaluasi Empiris *Hybrid Tiered Framework* (Skenario 2 + Skenario 4)
Walaupun Skenario 4 unggul dalam akurasi (**89.80%**), eksekusi 3 agen berantai membutuhkan rata-rata latensi **5.800 detik/tiket** dan **3.761,8 token/tiket**.

Untuk mengoptimalkan efisiensi operasional tanpa mengorbankan akurasi, penelitian ini menguji secara empiris **Hybrid Tiered Framework**:
* **69.2% tiket (346/500)** yang merupakan keluhan rutin dan konsisten dengan kanal departemen awal diselesaikan langsung oleh **Tier-1 Fast-Path (Skenario 2)**.
* **30.8% tiket (154/500)** yang menyentuh domain kepatuhan keuangan (*Finance*) atau terdeteksi memiliki diskrepansi kanal awal dielevasi secara otomatis ke **Tier-2 Specialist Pipeline (Skenario 4 MAS)**.
* **Hasil Empiris:** Arsitektur Hibrida mencapai **akurasi tertinggi `90.20%` (451/500 tiket, Macro-F1 `90.21%`)** sekaligus **memangkas rata-rata latensi sebesar 51.4% (menjadi `2.817 detik/tiket`)** dan **menghemat konsumsi token sebesar 52.8% (menjadi `1.775,8 token/tiket`)**.

---

## 4.3. Analisis Propagasi Kesalahan (Error Cascade Analysis) pada Skenario 4

Dari 500 tiket uji pada Skenario 4, jumlah kesalahan klasifikasi berhasil ditekan hingga tersisa **51 tiket (10.2%)**. Pemetaan anatomi kegagalan menunjukkan distribusi berikut:

```
Total Kesalahan Klasifikasi Skenario 4 (N = 51 dari 500 Tiket)
├── 1. Intrinsic Borderline Domain Ambiguity : 47 tiket (92.2% dari error / 9.4% dari total)
│      (Tiket multi-masalah lintas unit di mana S2, S3, dan S4 seluruhnya berbeda tafsir)
├── 2. Agent Chaining / Summarization Loss   :  3 tiket ( 5.9% dari error / 0.6% dari total)
│      (Reduksi nuansa minor saat transisi ringkasan Agen 1 -> Agen 2)
└── 3. Retrieval Context Noise (Agen 1 RAG)  :  1 tiket ( 2.0% dari error / 0.2% dari total)
       (Interferensi pasal Handbook pada keluhan leksikal umum)
```

1. **Eliminasi Hampir Penuh *Retrieval Noise* & *Chaining Loss*:**  
   Penerapan ambang batas kemiripan kosinus ($\tau \ge 0.08$) pada `HandbookRetriever` serta pengiriman paralel `complaint_summary` + `extracted_handbook_policy` + teks keluhan asli ke Agen 2 berhasil menekan *Retrieval Context Noise* hingga hanya **1 tiket (0.2%)** dan *Agent Chaining Loss* hingga hanya **3 tiket (0.6%)** dari keseluruhan 500 tiket uji.
2. **Karakteristik 47 Tiket *Intrinsic Borderline Ambiguity*:**  
   Sebanyak **92.2% dari sisa kesalahan** berasal dari tiket berlabel sub-kategori `"Others"` yang memuat dua maksud sekaligus (*compound complaints*), seperti `FN -> MR` (10 tiket), `OP -> ED` (7 tiket), dan `SO -> OP` (7 tiket). Selain itu, skor keyakinan Agen 2 (`ConfidenceScore`) terbukti terkalibrasi secara tajam: rata-rata *confidence* pada prediksi benar mencapai **0.926**, sedangkan pada 51 tiket yang meleset turun ke **0.854** ($\Delta = +0.072$), sehingga dapat digunakan sebagai sinyal ambang eskalasi ke staf manusia (*Human-in-the-Loop*).

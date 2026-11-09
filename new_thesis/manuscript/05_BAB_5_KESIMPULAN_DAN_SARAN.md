# BAB V KESIMPULAN DAN SARAN

## 5.1. Kesimpulan

Berdasarkan hasil investigasi komparatif empiris terhadap 4 skenario arsitektur triase tiket keluhan di fasilitas hunian mahasiswa pada *Golden Benchmark* ($N = 500$ tiket berimbang), dapat ditarik empat kesimpulan ilmiah utama:

1. **Peningkatan Monotonik dan Keunggulan Arsitektur Multi-Agent (Skenario 1 s/d Skenario 4):**  
   Pengujian empiris menunjukkan peningkatan kinerja secara konsisten dari pendekatan klasik hingga multi-agen:
   - **Skenario 1 (`Classical ML: TF-IDF + Logistic Regression`):** Mencapai akurasi **76.00%** (**Macro-F1 75.90%**, latensi **0.0009 detik/tiket**), namun lemah pada keluhan naratif seperti *Marketing* (**63.00%**) dan *Student Support Office* (**68.00%**) serta tidak mampu mengekstrak entitas parameter API.
   - **Skenario 2 (`Monolithic Single-Agent Zero-Shot`):** Meningkatkan akurasi menjadi **82.80%** (**Macro-F1 84.00%**), membuktikan keunggulan pemahaman semantik LLM di atas representasi leksikal *bag-of-words*.
   - **Skenario 3 (`Single-Agent + RAG Handbook`):** Meningkatkan akurasi menjadi **83.80%** (**Macro-F1 85.53%**), dengan perbaikan pada *Operations* (**90.00%**) dan *Marketing* (**85.00%**), namun pada domain *Finance* masih tertahan di **66.00%** akibat beban pemrosesan konteks mentah pada satu prompt monolitik.
   - **Skenario 4 (`Modular Chained MAS` — Proposed):** Meraih performa tertinggi di antara skenario mandiri dengan **akurasi keseluruhan `89.80%` (449/500 tiket)** dan **Macro-F1 `89.81%`** (**+7.00% di atas Skenario 2** dan **+6.00% di atas Skenario 3**).

2. **Efektivitas Distilasi Regulasi RAG pada Domain Kepatuhan (RQ1):**  
   Dekomposisi peran pada Skenario 4—di mana **Agen 1** menyaring dan mendistilasi pasal *Boarder Handbook* (`extracted_handbook_policy`) sebelum diserahkan ke **Agen 2**—berhasil mendongkrak akurasi departemen **Finance menjadi `85.00%` (F1-Score `89.01%`)**, meningkat **+17.00% dibanding Skenario 2 (`68.00%`)** dan **+19.00% dibanding Skenario 3 (`66.00%`)**. Hal ini membuktikan secara ilmiah bahwa *policy grounding* RAG pada sistem triase membutuhkan pemisahan antara agen pendistilasi kebijakan dan agen eksekutor fungsi.

3. **Keandalan Native Function Calling & Eliminasi Propagasi Kesalahan (RQ2):**  
   Implementasi *Native Function Calling* (`route_and_classify_complaint`) pada Agen 2 mencapai **100.0% validitas skema (500/500 tiket)** dan menghasilkan skor keyakinan yang terkalibrasi baik (**0.926** pada prediksi benar vs **0.854** pada prediksi salah, $\Delta = +0.072$). Melalui penyelarasan taksonomi sub-kategori resmi (`MsFeedbackSubject`) dan pengiriman paralel ringkasan beserta teks asli ke Agen 2, galat *Retrieval Context Noise* berhasil ditekan menjadi **1 tiket (0.2%)** dan *Agent Chaining Loss* menjadi **3 tiket (0.6%)**, menyisakan **47 tiket (9.4%)** yang murni merupakan kasus *compound multi-intent* lintas departemen.

4. **Pertukaran Efisiensi Komputasi & Validasi Empiris *Hybrid Tiered Framework* (RQ3):**  
   Meskipun Skenario 4 membutuhkan rata-rata latensi **5.800 detik/tiket** dan **3.761,8 token/tiket**, penerapan **Hybrid Tiered Framework**—yang menyelesaikan **69.2% tiket rutin** melalui jalur cepat *Single-Agent* (Skenario 2) dan mengelevasi **30.8% tiket regulasi/diskrepansi** ke *Modular MAS* (Skenario 4)—terbukti secara empiris mampu mencapai **akurasi agregat `90.20%` (451/500 tiket, Macro-F1 `90.21%`)** sekaligus **memangkas latensi sebesar 51.4% (`2.817 detik/tiket`)** dan **menghemat konsumsi token sebesar 52.8% (`1.775,8 token/tiket`)**.

---

## 5.2. Saran dan Penelitian Lanjutan

1. **Dukungan Skema *Multi-Label Routing* untuk Tiket *Multi-Intent*:**  
   Mengingat 92.2% dari sisa kesalahan pada Skenario 4 (47 dari 51 tiket) merupakan keluhan gabungan yang memotong dua departemen (seperti `FN <-> MR` pada kasus *check-out* sekaligus pencairan deposit), penelitian selanjutnya disarankan menambahkan parameter opsional `secondary_cc_department` pada skema *Function Calling* agar tiket dapat ditembuskan ke dua departemen secara paralel.
2. **Integrasi Transaksional Level 1/2 pada Intranet Kampus:**  
   Mengintegrasikan gerbang triase Level 0 ini langsung ke *endpoint* Web API internal `.NET` Binus Square serta basis data operasional guna mengotomasi pengecekan status tagihan dan jadwal teknisi secara *real-time*.
3. **Distilasi Model Lokal (*On-Premise SLM Fine-Tuning*):**  
   Memanfaatkan korpus `train_pool.csv` (29.164 tiket) dan luaran terstruktur dari Skenario 4 sebagai *teacher labels* (*Knowledge Distillation*) untuk melatih *Small Language Model* lokal (seperti Qwen-2.5-7B atau Llama-3.1-8B) agar institusi bebas dari biaya token API eksternal.

# BAB V KESIMPULAN DAN SARAN

## 5.1. Kesimpulan

Berdasarkan hasil investigasi komparatif empiris terhadap 4 skenario arsitektur triase tiket keluhan di fasilitas hunian mahasiswa Binus Square pada *Golden Benchmark* ($N = 500$ tiket berimbang dengan kondisi *zero label leakage*), dapat ditarik empat kesimpulan ilmiah utama:

1. **Trade-off Antara Klasifikasi Leksikal dan Pemahaman Semantik Terstruktur (RQ1):**  
   Pengujian komparatif menunjukkan dinamika unik antara model klasik dan model berbasis *Large Language Model*:
   - **Skenario 1 (`Classical ML: TF-IDF + Logistic Regression`):** Mencapai akurasi **76.00%** (**Macro-F1 75.90%**, latensi **0.0015 detik/tiket**) dengan performa tinggi pada kategori fasilitas fisik (*Estate Department*: 91.0%, *Operations*: 86.0%). Namun, model ini mengalami degradasi performa pada kategori naratif (*Marketing*: 63.0%, *Student Support*: 68.0%) serta tidak mampu mengekstraksi parameter entitas dan tidak dapat menghasilkan draf respon staf.
   - **Skenario 2 (`Monolithic Single-Agent Zero-Shot`):** Menghasilkan akurasi **75.00%** (**Macro-F1 74.87%**), dengan peningkatan pemahaman pada domain sosial (*Student Support*: 75.0%, *Marketing*: 69.0%), membuktikan keunggulan inferensi semantik di atas pencocokan kata kunci.
   - **Skenario 3 (`Single-Agent + RAG Handbook`):** Menghasilkan akurasi **74.20%** (**Macro-F1 73.93%**). Injeksi langsung pasal Handbook secara mentah ke dalam prompt monolitik menimbulkan fenomena *context cluttering*, yang menekan akurasi *Finance* ke level 58.0%.
   - **Skenario 4 (`Modular Chained MAS` — Proposed):** Meraih akurasi **73.20%** (**Macro-F1 74.26%**), dengan keunggulan spesifik pada domain regulasi kepatuhan yang kompleks, yaitu mendongkrak akurasi *Finance* ke **64.00% (F1 71.11%, naik +6.0% di atas S3)** dan *Marketing* ke **71.00% (F1 69.95%)**.

2. **Peran Distilasi Kebijakan RAG dalam Mengurangi Distorsi Konteks (RQ1):**  
   Dekomposisi tugas pada arsitektur MAS—di mana **Agen 1** bertindak sebagai penyaring semantik regulasi (*Policy Distiller*) sebelum diteruskan ke **Agen 2**—terbukti efektif menekan *Retrieval Context Noise* hingga hanya sebesar **3.7% dari total galat (5 dari 134 kesalahan)**. Hal ini membuktikan bahwa pemisahan antara agen analis regulasi dan agen pengambil keputusan triase melindungi model dari kelebihan beban konteks mentah.

3. **Keandalan Ekstraksi Parameter Terstruktur & Kalibrasi Keyakinan (RQ2):**  
   Implementasi *Native Function Calling* (`route_and_classify_complaint`) pada Agen 2 mencapai **96.8% validitas skema (484/500 tiket)**, yang secara otomatis mengekstrak urgensi, fasilitas rusak, dan kategori ke dalam format API backend. Lebih lanjut, Skenario 4 menunjukkan kalibrasi keyakinan yang paling tajam di mana *ConfidenceScore* pada prediksi benar mencapai rata-rata **0.957** dan turun ke **0.804** pada prediksi salah ($\Delta = +0.153$), menyediakan sinyal ambang batas yang solid bagi mekanisme *Human-in-the-Loop*.

4. **Efisiensi Komputasi & Solusi *Hybrid Tiered Framework* (RQ3):**  
   Meskipun eksekusi 3 agen berantai pada Skenario 4 membutuhkan rata-rata latensi **29.308 detik/tiket** dan **3.685,8 token/tiket**, penerapan **Hybrid Tiered Framework**—yang memproses **84.6% tiket rutin** melalui jalur cepat *Single-Agent* (Skenario 2) dan mengelevasi **15.4% tiket ambigu/finansial** ke *Modular MAS* (Skenario 4)—berhasil mempertahankan kinerja akurasi **74.60% (Macro-F1 74.42%)** sekaligus **memangkas latensi sebesar 58.6% (`12.148 detik/tiket`)** dan **menghemat konsumsi token sebesar 45.1% (`2.022,2 token/tiket`)**.

---

## 5.2. Saran dan Penelitian Lanjutan

1. **Dukungan Skema *Multi-Label Routing* untuk Tiket Majemuk (*Multi-Intent*):**  
   Analisis galat membuktikan bahwa 73.9% dari kesalahan klasifikasi pada Skenario 4 (99 dari 134 tiket) bersumber dari *Intrinsic Borderline Domain Ambiguity* (tiket gabungan seperti perpanjangan sewa dan pencairan deposit, atau komplain fasilitas komunal dan kebisingan). Penelitian selanjutnya disarankan mengimplementasikan *Multi-Label Function Calling* dengan parameter `secondary_department` guna mendukung penanganan tiket lintas departemen secara simultan.
2. **Pengembangan Mekanisme *Thresholding Human-in-the-Loop* Berbasis Kalibrasi:**  
   Memanfaatkan selisih tajam nilai keyakinan Agen 2 ($\Delta = +0.153$) sebagai *guardrail* operasional otomatis: tiket dengan *confidence* $< 0.85$ dapat langsung dialihkan ke meja staf operasional untuk verifikasi manual sebelum diteruskan ke sistem tiket utama.
3. **Integrasi Produksi dengan Web API dan Basis Data Operasional:**  
   Menghubungkan arsitektur *Hybrid Framework* secara langsung dengan endpoint backend ASP.NET Binus Square untuk otomatisasi penerbitan tiket *Work Order* dan notifikasi *real-time* kepada mahasiswa penghuni.
4. **Eksplorasi Fine-Tuning *Small Language Model* (SLM) Lokal:**  
   Memanfaatkan korpus data latihan (29.164 tiket) untuk melakukan *fine-tuning* pada model sumber terbuka berukuran ringkas (seperti Qwen-2.5-7B atau Llama-3.1-8B) sebagai agen lokal pada Tier-1, guna meminimalisir ketergantungan pada API komersial eksternal.

# 🏛️ Academic Audit & Thesis Elevation Strategy (Scopus / S2 Standard)
**Topik:** Audit Kritis Validitas Ilmiah, Mitigasi Titik Serang Penguji Sidang S2, dan Rekonstruksi Kontribusi Riset  
**Tanggal:** 2026-10-06  
**Peneliti:** Aditya Fajri (2602113205)  
**Program Studi:** Magister Teknik Informatika, Universitas Bina Nusantara  
**Konteks:** Menjawab keraguan orisinalitas riset, fenomena *low-code AI agent drag-and-drop*, dan ketiadaan arahan pembimbing melalui simulasi *Killer Examiner* (Scopus Q1 / IEEE / ACM Reviewer).

---

## 📌 1. Latar Belakang & Motivasi Audit

Peneliti menghadapi keraguan mendasar terkait bobot akademis tesis Magister (S2):
1. **Komoditisasi AI Agent:** Saat ini agen LLM dengan *Function Calling* dapat dibangun dengan mudah menggunakan platform *drag-and-drop / low-code* (Dify, Flowise, Coze, n8n) tanpa perlu riset mendalam.
2. **Keterbatasan Peran Model:** Penelitian menggunakan LLM komersial siap pakai (*foundation model API*) tanpa melatih model dari awal (*pre-training*).
3. **Diferensiasi Single vs Multi-Agent:** Perbedaan teknis terasa hanya sebatas pembagian *context window* dan sekuensial *prompting* ke 3 jendela LLM.
4. **Pasivitas Pembimbing:** Minimnya arahan substantif dari dosen pembimbing berisiko meloloskan metodologi yang rentan dibongkar oleh tim penguji independen di meja sidang tesis.

Audit ini merangkum bedah kritis independen terhadap repositori tesis beserta peta jalan ilmiah (*elevation roadmap*) untuk mentransformasikan riset dari sekadar **pekerjaan rekayasa perangkat lunak (S1)** menjadi **kontribusi penelitian komputasi empiris tingkat magister (S2)**.

---

## 💥 2. Evaluasi Kritis: 4 "Dosa Ilmiah" Utama (Titik Serang Penguji Killer)

### Dosa 1: Inflasi Istilah (*Semantic Inflation*) — "Multi-Agent" vs "Linear Prompt Chaining"
* **Temuan Realitas:** Implementasi pada `run_multi_agent_system.py` menerapkan alur linier murni:  
  $$\text{Input} \longrightarrow \text{Agen 1 (RAG)} \longrightarrow \text{Agen 2 (Function Call)} \longrightarrow \text{Agen 3 (Drafter)} \longrightarrow \text{Output}$$
* **Serangan Penguji:** Dalam literatur ilmiah kecerdasan buatan (AAMAS, NeurIPS, JAAMAS), *Multi-Agent System* mensyaratkan adanya otonomi keputusan (*autonomous agency*), negosiasi, konsensus, arbitrase konflik, atau percabangan dinamis (*dynamic routing / reflection*). Alur sekuensial statis ini secara formal adalah **Modular Prompt Chaining / Task Decomposition**, bukan multi-agent otonom.
* **Risiko Sidang:** Penguji akan mendiskreditkan judul tesis sebagai *buzzword inflation* jika diklaim sebagai arsitektur MAS otonom tanpa justifikasi taksonomi yang tepat.

---

### Dosa 2: Cacat Metodologis Eksperimental (*Confounding Variable Bias*)
* **Temuan Realitas:** Pada Bab 4, peneliti membanggakan temuan bahwa MAS unggul pada departemen Finance (+5.0%, 73% vs 68%).
* **Serangan Penguji:** Perbandingan antara *Single-Agent Baseline* dan *MAS* **tidak adil (*apple-to-orange*)**:
  - *Single-Agent Baseline* dieksekusi **tanpa** konteks dokumen RAG.
  - *MAS (Agen 1)* menyuntikkan dokumen Handbook RAG ke dalam pipeline.
* **Konsekuensi Ilmiah:** Peningkatan performa pada departemen Finance **bukan disebabkan oleh arsitektur Multi-Agent**, melainkan murni efek dari **keberadaan informasi RAG**. Jika Single-Agent diberikan teks RAG yang sama, performanya berpotensi menyamai atau bahkan melampaui MAS dengan latensi yang jauh lebih cepat. Ini adalah *confounding variable* fatal dalam desain eksperimen.

---

### Dosa 3: Diskrepansi Janji Proposal vs Implementasi (*SFT Phantom Discrepancy*)
* **Temuan Realitas:** Naskah Bab 1 Halaman 10 (Ruang Lingkup Butir 3) dan Bab 2 Halaman 6 secara eksplisit menjanjikan:
  > *"Sistem dikembangkan menggunakan model komersial Google Gemini yang diakses melalui lingkungan Vertex AI. Model ini disesuaikan perilakunya melalui Supervised Fine-Tuning (SFT) menggunakan dataset berformat .jsonl."*
* **Serangan Penguji:** Di dalam kode pipeline aktual (`run_multi_agent_system.py` dan `run_single_agent_baseline.py`), peneliti **sama sekali tidak melakukan Fine-Tuning (SFT)**. Seluruh sistem berjalan murni di atas *Zero-Shot In-Context Learning (ICL)* menggunakan free-tier Google AI Studio API yang bahkan sempat terkena limit kuota HTTP 429 pada 90 tiket.
* **Risiko Sidang:** Diskrepansi antara metodologi tertulis dan eksekusi empiris merupakan pelanggaran integritas pelaporan ilmiah yang dapat berakibat penundaan kelulusan.

---

### Dosa 4: Paradoks Efisiensi — *"Why LLM for 5-Class Text Classification?"*
* **Temuan Realitas:** Peneliti memiliki **30.314 tiket historis**, namun tugas kuantitatif utama di Bab 4 hanya memprediksi 5 kelas departemen tujuan (`ED`, `OP`, `FN`, `MR`, `SO`).
* **Serangan Penguji:** Model *Supervised Classical ML/DL* (seperti Fine-Tuned IndoBERT, RoBERTa, atau TF-IDF + LightGBM/SVM) yang dilatih pada 25.000 data historis dapat menyelesaikan klasifikasi 5 kelas ini dengan akurasi $\ge 88\%$ dalam waktu **3 milidetik** tanpa biaya token dan tanpa ketergantungan API eksternal.  
  Mengapa harus menggunakan LLM yang 3.6x lebih lambat (6.3 detik), 4.4x lebih boros token (3.672 token), dan menghasilkan akurasi agregat yang lebih rendah (81.4% vs 82.8%)?

---

## 🚀 3. Strategi Elevasi: Mengubah "Rakit Bot" Menjadi "Sains Komputasi S2"

Untuk membuat tesis ini berbobot magister dan lolos standar publikasi Scopus/IEEE, peneliti tidak perlu membuang sistem yang telah dibangun. Peneliti harus **mereposisi sudut pandang ilmiah (*scientific reframing*)**, **memperbaiki kontrol variabel**, dan **menghadirkan analisis yang tidak bisa dilakukan oleh platform drag-and-drop**.

```
                           PARADIGMA LAMA (Tingkat S1 / Engineering)
                    "Bagaimana cara membuat bot triase multi-agent pakai LLM?"
                                                │
                                                ▼ Transformasi Reframing
                           PARADIGMA BARU (Tingkat S2 / Sains Komputasi)
    "Bagaimana trade-off dekomposisi tugas, akumulasi latensi, dan propagasi kesalahan
      (error propagation) ketika LLM berinteraksi dalam pipeline ITSM semi-terstruktur?"
```

---

### Strategi A: Perluasan Matriks Komparasi Eksperimental (Fair Evaluation)
Wajib menambahkan **Baseline 2 (Single-Agent + RAG)** dan **Baseline 0 (Supervised IndoBERT / Classical ML)** agar matriks pengujian lengkap dan kedap kritik:

| Skenario Pengujian | Deskripsi Arsitektur | Variabel RAG | Target Hipotesis Ilmiah |
| :--- | :--- | :---: | :--- |
| **Baseline 0 (Classical ML)** | IndoBERT / TF-IDF + SVM dilatih pada 29k data | Tidak | Menjawab justifikasi: *"Kelebihan & kekurangan representasi vektor klasik vs penalaran semantik LLM"*. |
| **Baseline 1 (Monolithic LLM)** | 1 Prompt Tunggal tanpa konteks handbook | Tidak | Menjawab batas kemampuan *zero-shot world knowledge* model dasar. |
| **Baseline 2 (Single-Agent + RAG)** | **1 Prompt Tunggal + Injeksi Dokumen RAG Handbook** | **Ya** | **Mengontrol variabel RAG secara adil (*Fair Ablation Study*) untuk membuktikan apakah MAS benar-benar dibutuhkan.** |
| **Proposed (Modular Chained MAS)** | 3 Agen Terdekomposisi (RAG $\rightarrow$ Tool Call $\rightarrow$ Drafter) | Ya | Mengukur efisiensi *Separation of Concerns* vs penalti latensi dan biaya komputasi. |

---

### Strategi B: Analisis Kegagalan Khusus — *Error Propagation Cascade Analysis*
Alat *drag-and-drop* hanya menghubungkan blok. Kontribusi riset S2 terletak pada **analisis mendalam terhadap anatomi kegagalan sistem komputasi**.

Peneliti perlu membedah tiket yang gagal pada MAS dan memetakan probabilitas transfer kesalahannya (*Cascading Error*):
1. **Retrieval Error (Agen 1):** Kasus di mana pasal handbook yang ditarik tidak relevan dengan esensi keluhan penghuni.
2. **Schema & Reasoning Error (Agen 2):** Kasus di mana pasal handbook sudah tepat, namun LLM salah memetakan parameter *Function Calling* (`HandledDepartmentName` atau `UrgencyLevel`).
3. **Cascading Hallucination (Agen 3):** Kasus di mana Agen 3 menghasilkan balasan staf yang menjanjikan tindakan di luar SOP karena salah menafsirkan *output* Agen 2.

Menyajikan diagram alir probabilitas akumulasi kesalahan (*Error Cascade Flow*) di Bab 4 akan menjadi poin keunggulan utama yang diapresiasi penguji dan reviewer jurnal.

---

### Strategi C: Pembelaan Nilai Positif dari *"Negative / Trade-off Results"*
Dalam publikasi ilmiah bereputasi, **sistem baru tidak wajib selalu menang dalam setiap metrik**. Paper-paper empiris terkemuka (ICSE, MSR, EMNLP) justru memberi nilai tinggi pada pembuktian batas kinerja (*boundary condition*):
* **Fakta Empiris:** MAS memiliki latensi 3.6x lebih lambat dan biaya token 4.4x lebih mahal dengan akurasi umum yang bersaing ketat (81.4% vs 82.8%).
* **Nilai Ilmiah:** Peneliti membuktikan bahwa **dekomposisi tugas linier (MAS) tidak serta-merta meningkatkan akurasi klasifikasi umum**, namun memberikan isolasi keamanan (*guardrail modularity*) dan kemampuan grounding regulasi dinamis pada sub-domain spesifik (Finance).
* **Rekomendasi Arsitektural:** Merumuskan arsitektur hibrida (*Hybrid Escalation Architecture*): Tiket diproses cepat via Single-Agent; jika tingkat kepastian (*confidence score*) rendah atau tiket menyentuh ranah finansial, sistem mengelevasi tiket ke MAS.

---

### Strategi D: Koreksi Naskah Tesis (Rekonsiliasi Integritas Ilmiah)
1. **Eliminasi Klaim SFT Palsu:** Hapus istilah *Supervised Fine-Tuning via Vertex AI* pada Bab 1 (Ruang Lingkup) dan Bab 3 (Metodologi). Gantilah dengan formulasi formal:  
   *"In-Context Learning (ICL) berbasis deklarasi skema JSON Function Calling dan Retrieval-Augmented Generation (RAG)"*.
2. **Klarifikasi Definisi Arsitektur:** Di Bab 3, beri subbab penegasan: *"Karakterisasi Arsitektur: Task-Decomposed Sequential Pipeline with Specialized Role Prompts"*, untuk menghindari perdebatan definisi MAS otonom.
3. **Penyelesaian 91 Tiket Terpotong:** Eksekusi script `retry_failed_mas_tickets.py` agar evaluasi Bab 4 berdiri di atas 500/500 tiket utuh (tanpa distorsi HTTP 429).

---

## 📋 4. Action Plan & Checklist Eksekusi Riset

- [ ] **Aksi 1 (Data & Pipeline):** Eksekusi `retry_failed_mas_tickets.py` untuk melengkapi 91 tiket SO yang tertunda hingga N=500 tiket valid 100%.
- [ ] **Aksi 2 (Ablation Test Baru):** Buat eksperimen pembanding `Single-Agent + RAG` (injeksi potongan handbook ke prompt single-agent) pada 500 tiket untuk menutup celah *confounding variable*.
- [ ] **Aksi 3 (Naskah Bab 1 & 3):** Sinkronisasi klaim naskah: hapus referensi SFT, perjelas ruang lingkup *In-Context Learning*, dan perkuat landasan dekomposisi tugas.
- [ ] **Aksi 4 (Naskah Bab 4):** Tambahkan subbab *Analisis Propagasi Kesalahan (Error Propagation Analysis)* dan *Analisis Trade-Off Biaya Operasional vs Manfaat Isolasi Guardrail*.
- [ ] **Aksi 5 (Amunisi Sidang):** Gunakan dokumen ini dan `2026-09-30_red_team_academic_defense.md` sebagai panduan mempertahankan tesis di hadapan dewan penguji.

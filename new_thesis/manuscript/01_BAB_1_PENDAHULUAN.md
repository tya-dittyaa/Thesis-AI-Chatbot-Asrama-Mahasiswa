# BAB I PENDAHULUAN

## 1.1. Latar Belakang Masalah
Pengelolaan fasilitas hunian terpadu berskala besar (*Student Hall of Residence / Asrama Mahasiswa*) menghadapi tantangan operasional yang semakin kompleks seiring peningkatan jumlah penghuni. Pada fasilitas hunian kampus modern, efisiensi penanganan insiden fisik (seperti pendingin ruangan, sanitasi, dan kelistrikan) serta layanan administratif (seperti perpanjangan kontrak sewa, reservasi, dan rekonsiliasi denda kuota listrik) menjadi parameter vital yang menentukan kepuasan dan kualitas hidup mahasiswa.

Tantangan nyata ini teridentifikasi pada tata kelola fasilitas hunian Binus Square Hall of Residence di Kampus XYZ. Pihak pengelola bertanggung jawab penuh atas operasional empat gedung utama yang mencakup asrama putra, asrama putri, serta akomodasi penginapan tamu. Namun, seluruh interaksi layanan meja depan (*front desk*) untuk keempat gedung tersebut pada jam operasional harian secara praktis hanya ditangani oleh satu hingga dua orang staf resepsionis secara bergantian. Keterbatasan sumber daya manusia ini menciptakan tekanan kognitif (*cognitive overload*) yang tinggi, di mana staf harus melayani tamu tatap muka sekaligus melakukan triase manual terhadap puluhan laporan keluhan penghuni yang masuk setiap hari.

Hambatan utama dalam alur pelaporan ini bersumber dari perbedaan medium dan format komunikasi antara mahasiswa dan sistem tata kelola kampus:
1. **Preferensi Komunikasi Informal:** Mahasiswa cenderung menghindari pengisian formulir terstruktur pada aplikasi pelaporan web portal internal karena alurnya dinilai kaku dan memakan waktu. Sebaliknya, mahasiswa lebih menyukai komunikasi informal melalui aplikasi perpesanan instan (*WhatsApp*) dengan gaya bahasa sehari-hari, santai, dan sering kali ambigu.
2. **Beban Transkripsi Manual Staf Resepsionis:** Setiap pesan informal yang masuk mewajibkan staf resepsionis membaca, menafsirkan konteks masalah, menentukan tingkat keparahan (*urgency/severity*), memetakan departemen penangan yang berwenang, mengekstrak nomor kamar dan jenis perabot rusak, lalu mengetikkan variabel-variabel tersebut satu per satu ke dalam sistem portal tiket berbasis *.NET Web API* milik manajemen.
3. **Risiko Galat Alokasi Tiket (*Misclassification & Rerouting*):** Data historis 10 tahun (2015–2025) mencatat ribuan kasus salah alokasi tiket (*rerouted tickets*), di mana keluhan dilempar antar-departemen akibat ambiguitas istilah (misalnya istilah "meteran listrik anjlok" yang sering salah dialokasikan ke Departemen Keuangan alih-alih Departemen Pemeliharaan Fisik). Kondisi ini memperpanjang waktu tunggu penanganan (*First Response Time* dan *Mean Time to Resolve / MTTR*).

Kemajuan *Natural Language Processing (NLP)* melalui *Large Language Models (LLM)* menawarkan peluang otomatisasi gerbang triase layanan (*IT Service Management / ITSM Level 0*). Berbeda dengan *chatbot* percakapan biasa yang hanya menghasilkan teks obrolan bebas tanpa efek komputasi terstruktur, arsitektur modern LLM dilengkapi kapabilitas **Native Function Calling (Tool Calling)**. Fitur tingkat model ini memungkinkan LLM bertindak sebagai mesin inferensi terstruktur yang menerjemahkan bahasa bebas menjadi pemanggilan fungsi formal (`route_and_classify_complaint`) dengan payload JSON yang 100% tervalidasi dan siap dikonsumsi langsung oleh *endpoint* API pelaporan kampus.

Namun, penerapan arsitektur LLM untuk triase semi-terstruktur memicu dilema rekayasa sistem (*system engineering dilemma*):
* Pendekatan **Monolithic Single-Agent** (satu prompt tunggal panjang) memiliki keunggulan latensi cepat dan hemat biaya, namun rentan mengalami penurunan akurasi pada kasus yang sarat kepatuhan regulasi hunian (*Boarder Handbook SOP*).
* Sebaliknya, pendekatan **Modular Chained Multi-Agent System (MAS)** memecah tugas menjadi agen-agen spesialis (validasi regulasi via RAG, spesialis eksekusi Function Calling, dan generator balasan berempati) untuk menjamin isolasi peran (*Separation of Concerns*). Namun, literatur terkini mengindikasikan bahwa sistem multi-agen dapat memicu penalti latensi inferensi yang signifikan, konsumsi token berlipat ganda, dan risiko perambatan kesalahan antar-tahap (*error propagation cascade*).

Hingga saat ini, belum terdapat studi empiris komprehensif yang menguji batas kinerja (*boundary conditions*), pertukaran efisiensi (*trade-offs*), dan keandalan skema fungsional antara model pembelajaran mesin konvensional, model LLM monolitik, model teraugmentasi RAG, dan arsitektur *Multi-Agent* pada dataset riil layanan fasilitas kampus skala 1 dekade. Oleh karena itu, penelitian ini dirancang untuk mengisi kesenjangan tersebut melalui studi komparatif faktorial yang ketat.

---

## 1.2. Rumusan Masalah
Berdasarkan latar belakang yang diuraikan, rumusan masalah dalam penelitian ini dirumuskan sebagai berikut:

1. **RQ1 (Akurasi & Grounding Regulasi):**  
   Bagaimana efektivitas perbandingan kinerja klasifikasi dan perutean tiket antara model *Classical Machine Learning* (TF-IDF + LR/SVM), *Monolithic Single-Agent*, *Single-Agent + RAG*, dan *Modular Multi-Agent System (MAS)* pada dataset berimbang 500 tiket uji (*Golden Benchmark*), khususnya pada departemen yang sarat aturan kepatuhan (*Finance*)?
2. **RQ2 (Dekomposisi Peran & Propagasi Kesalahan):**  
   Bagaimana dampak dekomposisi peran pada arsitektur *Multi-Agent System* terhadap jaminan validitas skema *Native Function Calling* (JSON payload) dan mitigasi halusinasi respon staf, dibandingkan dengan risiko perambatan kesalahan (*error cascade*) antar-agen?
3. **RQ3 (Trade-off Komputasi & Efisiensi Operasional):**  
   Bagaimana pertukaran efisiensi komputasi dari keempat skenario ditinjau dari latensi inferensi (detik), konsumsi token, proyeksi biaya operasional, serta kelayakannya diterapkan pada infrastruktur kampus dengan kuota komputasi terbatas (*constrained environment*)?

---

## 1.3. Tujuan Penelitian
Tujuan yang hendak dicapai dalam penelitian ini adalah:
1. Membangun dan mengevaluasi 4 skenario arsitektur triase komparatif (Skenario 1: Classical ML, Skenario 2: Monolithic Single-Agent, Skenario 3: Single-Agent + RAG Handbook, dan Skenario 4: Modular Chained MAS).
2. Mengukur secara empiris kemampuan *Native Function Calling* dalam mengekstrak 6 variabel operasional terstruktur (departemen, kategori masalah, tingkat keparahan/urgensi, entitas fasilitas, lokasi, dan skor keyakinan) dari teks informal mahasiswa.
3. Mengkuantifikasi pertukaran kinerja (*trade-offs*) antara akurasi makro (Macro-F1), latensi, konsumsi token, dan tingkat propagasi kesalahan pada masing-masing arsitektur.
4. Merumuskan pedoman arsitektural hibrida (*Hybrid ITSM Triage Decision Framework*) yang merekomendasikan ambang batas pengalihan tiket antara jalur cepat (*Fast-Path Single-Agent*) dan jalur mendalam (*Deep-Path Multi-Agent*).

---

## 1.4. Manfaat Penelitian
Manfaat dari penelitian ini dijabarkan sebagai berikut:
1. **Manfaat Teoretis & Akademis:**  
   Memberikan kontribusi empiris pada literatur *Empirical Software Engineering* dan *Applied AI* terkait analisis batas kinerja dekomposisi tugas LLM, membuktikan secara objektif kapan sistem multi-agen memberikan nilai tambah dan kapan ia memicu inefisiensi komputasi.
2. **Manfaat Praktis Operasional:**  
   Menyediakan gerbang otomatisasi triase Level 0 (L0) yang memangkas beban kerja manual staf resepsionis meja depan lebih dari 90%, mengeliminasi keharusan pengisian formulir manual, dan mempercepat waktu tanggap awal pelaporan (*First Response Time*).
3. **Manfaat Keamanan Informasi:**  
   Menghadirkan cetak biru pemisahan gerbang publik dan logika bisnis tiket tanpa memberikan LLM akses langsung ke basis data transaksional mahasiswa (*Least Privilege Compliance*).

---

## 1.5. Ruang Lingkup dan Batasan Penelitian
Guna memastikan penelitian terfokus dan memiliki validitas metodologis yang dapat diuji ulang (*reproducible*), ruang lingkup penelitian dibatasi sebagai berikut:
1. **Data Historis Riil:** Pengujian menggunakan populasi 30.314 tiket keluhan historis (periode 2015–2025) dari Binus Square Hall of Residence, dengan evaluasi komparatif formal difokuskan pada dataset uji terstandarisasi bebas anomali (*Stratified Golden Benchmark* $N=500$, presisi 100 tiket per departemen).
2. **Karakterisasi Batas Sistem (ITSM L0 Triage Gateway):** Sistem dirancang murni sebagai gerbang triase dan ekstraksi informasi terstruktur di lapisan hulu (*Upstream Ingestion & Dispatcher*). Sistem **secara sengaja tidak mengintegrasikan kueri langsung ke basis data transaksional mahasiswa** (seperti kueri saldo tagihan atau meteran listrik riil) demi mematuhi prinsip *Least Privilege*, perlindungan data pribadi (PII), dan pencegahan halusinasi data faktual.
3. **Basis Pengetahuan Regulasi (RAG):** Dokumen regulasi yang digunakan sebagai acuan kepatuhan operasional terbatas pada *Binus Square Boarder Handbook 2025–2026* yang disegmentasi menjadi 46 chunk semantik dan diindeks menggunakan *TF-IDF Cosine Similarity*.
4. **Lingkungan Komputasi Terbatas (*Constrained Computing Environment*):** Evaluasi inferensi LLM dilakukan menggunakan *Google AI Studio Standard Public API Tier* (model Gemini 2.5 Flash / Flash Lite). Penelitian menerapkan strategi kontrol throughput via modul `ApiKeyManager` (rotasi kunci API dan *exponential backoff retry*) guna menjaga kontinuitas eksperimen di bawah batasan kuota harian (*Requests Per Day*).
5. **Metode Adaptasi Model:** Model LLM dievaluasi menggunakan paradigma *In-Context Learning (ICL)* dan *Native Function Calling*, tanpa melakukan pelatihan ulang bobot internal (*Supervised Fine-Tuning / SFT*).

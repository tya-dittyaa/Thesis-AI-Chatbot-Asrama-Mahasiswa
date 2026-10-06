# 🛡️ Batasan Sistem: RAG Statis vs. Database Dinamis & Arsitektur ITSM Triage
**Topik:** Justifikasi Ilmiah Ketiadaan Kueri Database Transaksional, Batasan Peran RAG Statis, dan Mitigasi Halusinasi Respon  
**Tanggal:** 2026-10-06  
**Peneliti:** Aditya Fajri (2602113205)  
**Program Studi:** Magister Teknik Informatika, Universitas Bina Nusantara  
**Target:** Penulisan Bab 1 (Ruang Lingkup), Bab 3 (Batasan Sistem), Bab 4 (Analisis Kasus), dan Amunisi Sidang Tesis S2  

---

## 📌 1. Permasalahan & Titik Rawan Sidang

### Realitas Sistem Saat Ini:
* Basis pengetahuan sistem murni mengandalkan **Boarder Handbook 2025–2026** (dokumen teks statis berisi 46 chunk seputar regulasi asrama).
* Banyak laporan keluhan mahasiswa membutuhkan **data faktual dinamis/transaksional yang tersimpan di basis data** (misalnya: riwayat tagihan listrik, status pembayaran sewa, status pengerjaan tiket teknisi sebelumnya, atau ketersediaan kamar kosong).
* Sistem tesis **tidak melakukan pemanggilan (*query*) ke basis data operasional** secara dinamis.

### Serangan Penguji Killer:
> *"Mahasiswa mengeluh: 'Tagihan listrik kamar 814 saya bulan ini kena denda Rp 200.000, padahal saya sedang magang di luar kota selama 3 minggu. Tolong dicek!'*  
> *Sistem Anda tidak terhubung ke database meteran/billing. Bagaimana RAG Handbook Anda bisa menyelesaikan keluhan ini? Bukankah tanpa database, bot Anda hanya bisa berhalusinasi atau memberikan jawaban normatif yang tidak berguna?"*

---

## ⚖️ 2. Paradigma Ilmiah: Resolution Agent vs. Triage Gateway

Kegalauan muncul karena kerancuan peran sistem. Dalam rekayasa perangkat lunak enterprise dan literatur kecerdasan buatan, terdapat dikotomi tegas:

```
┌───────────────────────────────────────────────┐
│       KONSEP A: AGENT RESOLUSI TRANSAKSIONAL  │
│          (Autonomous Resolution Bot)          │
├───────────────────────────────────────────────┤
│ • Tujuan : Menyelesaikan masalah ujung-ke-    │
│            ujung (End-to-End).                │
│ • Kebutuhan : Akses baca/tulis ke database    │
│               keuangan, billing, & inventaris.│
│ • Risiko Tanpa DB : HALUSINASI FATAL &        │
│                     menyesatkan mahasiswa.    │
└───────────────────────────────────────────────┘
                       VS
┌───────────────────────────────────────────────┐
│     KONSEP B: GERBANG TRIASE OTOMATIS (ITSM)  │
│        (Upstream Ingestion & Triage Gateway)  │  <── POSISI RESMI TESIS INI!
├───────────────────────────────────────────────┤
│ • Tujuan : Mengonversi teks informal menjadi  │
│            payload tiket terstruktur (JSON).  │
│ • Kebutuhan : Ekstraksi entitas, penentuan    │
│               urgensi, & routing departemen.  │
│ • Sifat : Gerbang Tingkat 0 (ITSM L0 Ingest). │
└───────────────────────────────────────────────┘
```

> **Prinsip Utama Sidang:**  
> Jangan pernah memposisikan sistem ini sebagai **Konsep A**. Posisikan sistem secara formal sebagai **Konsep B (ITSM Automated Triage Gateway)**.  
> Ketiadaan akses database dinamis **bukanlah kekurangan teknis yang tidak sempat dibuat**, melainkan **keputusan desain arsitektur yang disengaja (*Deliberate Architectural Design Decision*)**.

---

## 🏛️ 3. Tiga Landasan Ilmiah Pembelaan Ketiadaan Akses Database Dinamis

Gunakan 3 argumen enterprise berbobot magister ini saat menjawab penguji:

### 1. Prinsip Keamanan *Least Privilege* & Perlindungan Privasi (PII Protection)
* Agen triase berada di gerbang publik terdepan (*public-facing front door*) yang berinteraksi langsung dengan teks bebas mahasiswa.
* Memberikan LLM publik akses *Read/Write* langsung ke database transaksional (tabel penagihan, histori penghuni, data pribadi) melanggar standar keamanan informasi (ISO 27001 / OWASP Top 10 for LLMs).
* Akses langsung memicu risiko kerentanan **Prompt Injection**, **Indirect Data Leakage**, dan **Unauthorized SQL Modification**. Agen triase publik secara ketat hanya boleh mengakses dokumen regulasi publik (*Handbook*).

### 2. Standar Manajemen Layanan TI (ITSM / ITIL v4 Separation of Concerns)
* Dalam kerangka kerja standar industri ITIL v4, siklus hidup insiden dipisahkan secara tegas:
  - **Level 0 (L0 - Incident Ingestion & Triage):** Mengurai pesan ambigu, menetapkan taksonomi masalah, mengukur tingkat keparahan (*severity*), dan meneruskan tiket ke resolver group yang sah. **(Fokus Tesis Ini)**
  - **Level 1/2 (L1/L2 - Incident Investigation & Resolution):** Dikerjakan oleh staf manusia atau bot internal terotentikasi (*Finance Specialist / Maintenance Dispatcher*) yang memiliki hak akses legal ke sistem core-banking/ERP.
* Mencampuradukkan triase dengan resolusi transaksional pada satu agen tunggal melanggar prinsip *Single Responsibility Principle* dalam rekayasa perangkat lunak.

### 3. Validitas Metodologis Data Historis (*Temporal Consistency*)
* Evaluasi empiris menggunakan dataset sekunder 2015–2025 (data historis dingin).
* Melakukan koneksi kueri ke database operasional saat ini untuk tiket yang tercatat pada tahun 2018 adalah cacat metodologi (*Temporal Data Inconsistency / Leakage*), karena status rekening dan hunian tahun 2018 sudah tidak mencerminkan kondisi saat ini.

---

## 📖 4. Rekonseptualisasi Peran RAG Handbook

Jika RAG tidak memiliki data dinamis, untuk apa RAG disuntikkan ke Agen 1 dan Agen 2?

**Fungsi RAG bukan untuk mengecek status personal mahasiswa, melainkan sebagai penegak batas aturan (*Business Rule Grounding & Policy Compliance*):**

1. **Mengoreksi Kesalahan Routing Akibat Istilah Semantik Ganda:**
   * *Contoh Kasus:* Mahasiswa menulis: *"Listrik kamar saya mati total karena meteran turun."*
   * *Tanpa RAG:* Model bisa salah mengarahkan ke Finance (karena ada kata "listrik/meteran").
   * *Dengan RAG:* Potongan Handbook Bagian Fasilitas menyatakan bahwa korsleting/meteran anjlok ditangani oleh teknisi darurat Estate Department. Model berhasil merutekan ke ED dengan urgensi *High/Emergency*.
2. **Menstandarkan Kategori & SLA:**
   * Handbook memandu Agen 2 mengisi parameter `problem_category` sesuai taksonomi resmi kampus, bukan nama bebas yang dibuat-buat oleh LLM.

---

## 🚫 5. Red-Line Guardrail: Mencegah Halusinasi Agen 3 (Response Drafter)

Salah satu titik bunuh penguji adalah jika Agen 3 (pembuat draf balasan) berlagak tahu isi database mahasiswa.

### ❌ Contoh Respon HALUSINASI (DILARANG KERAS):
> *"Halo Kak Aditya, kami telah memeriksa tagihan listrik kamar 814 Anda dan benar terdapat kelebihan pemakaian AC sebesar 50 kWh sehingga dikenakan denda Rp 200.000. Denda ini tidak bisa dihapus..."*  
> *(PENGUJI AKAN LANGSUNG MENGGUGURKAN ANDA: Dari mana bot tahu ada kelebihan 50 kWh padahal tidak punya akses DB? Ini halusinasi berat!)*

### ✅ Contoh Respon FORMAL ITSM TRIAGE (BENAR & ILMIAH):
> *"Halo Kak Aditya, laporan keluhan Anda mengenai ketidaksesuaian denda tagihan listrik kamar 814 telah kami catat dan diteruskan ke **Finance Department** dengan kategori **[Electricity Usage & Billing]** dan tingkat urgensi **[Medium]**.*  
> *Berdasarkan Boarder Handbook Bagian 4.2, tim Finance akan melakukan audit fisik meteran listrik dalam waktu 1x24 jam kerja. Bukti pelaporan Anda telah tersimpan dengan nomor antrean triase resmi."*

**Kaidah Desain Agen 3:**
Agen 3 berfungsi sebagai **Acknowledgment & Expectation Setting Receipt (Tanda Terima & Penyelaras Ekspektasi SLA)**, bukan pemutus perkara transaksi.

---

## 📝 6. Klausul Redaksi Siap Salin untuk Naskah Tesis

Berikut adalah redaksi formal yang dapat langsung ditempatkan di dokumen tesis:

### Untuk Bab 1 (Subbab 1.5 - Ruang Lingkup Penelitian):
> *"Ruang lingkup operasional sistem dalam penelitian ini dibatasi secara khusus sebagai **Upstream Triage Gateway** pada lapisan Level 0 (L0) IT Service Management. Sistem berfokus pada otomatisasi klasifikasi, ekstraksi variabel keluhan, dan penentuan urgensi tiket, serta **secara sengaja tidak mengintegrasikan kueri langsung ke basis data transaksional mahasiswa** (seperti saldo tagihan real-time atau pencatatan meteran) demi mematuhi prinsip keamanan informasi Least Privilege dan pencegahan halusinasi data faktual."*

### Untuk Bab 3 (Subbab Metodologi & Batasan Desain):
> *"Integrasi Retrieval-Augmented Generation (RAG) dalam arsitektur ini dirancang murni untuk **Grounding Regulasi Operasional (Policy Compliance)** berbasis Boarder Handbook, bukan sebagai repositori basis data transaksional. Peran respons otomatis staf (Agen 3) dikonfigurasi sebagai *Service Acknowledgment & SLA Expectation Setting*, sehingga model tidak melakukan spekulasi atas status data yang memerlukan verifikasi manual staf keuangan atau teknisi lapangan."*

### Untuk Bab 5 (Saran & Future Work):
> *"Penelitian selanjutnya dapat memperluas arsitektur triase ini menjadi sistem resolusi otonom terpadu (Level 1/2) dengan menambahkan sub-agen terautentikasi khusus yang beroperasi di dalam jaringan privat kampus (VPN/Intranet) untuk mengeksekusi kueri terenkripsi ke database Core-Billing dan Work-Order Management System."*

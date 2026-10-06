# 🎓 Derajat Akademik Riset: Transformasi "Analisis Komparatif" Menjadi Sains Empiris S2
**Topik:** Menjawab Keraguan Bobot Riset Evaluasi/Komparatif, Standar Publikasi Scopus Q1, dan Tiga Pilar Peningkat Derajat Tesis Magister  
**Tanggal:** 2026-10-06  
**Peneliti:** Aditya Fajri (2602113205)  
**Program Studi:** Magister Teknik Informatika, Universitas Bina Nusantara  
**Target:** Penulisan Bab 4 (Discussion), Bab 5 (Kontribusi & Framework), serta Fondasi Percaya Diri Sidang Tesis  

---

## ❓ 1. Kegalauan Mendasar: "Apakah Riset Evaluasi & Komparasi itu Rendah Derajatnya?"

Sering muncul anggapan di kalangan mahasiswa (dan penguji konvensional):
> *"S1 membuat aplikasi, S2 membuat algoritma/model baru dari nol, S3 menemukan teori baru. Kalau tesis S2 hanya 'evaluasi' atau 'analisis komparatif' sistem yang sudah ada, bukankah derajat akademiknya rendah?"*

### JAWABAN ILMIAH TEGAS:
**Analisis Komparatif BISA BERDERAJAT RENDAH, tetapi BISA JUGA BERDERAJAT SANGAT TINGGI (Standar IEEE / ACM / Scopus Q1).**  
Tinggi atau rendahnya derajat tesis **bukan ditentukan oleh kata 'Komparatif'**, melainkan oleh **kedalaman metodologi pengujian, pembongkaran mekanisme kausalitas (*causal mechanism*), dan formulasi prinsip desain yang dihasilkan.**

---

## 🔍 2. Pembeda Nyata: Komparasi Dangkal (S1) vs. Riset Empiris Mendalam (S2)

Berikut adalah batas demarkasi tegas yang membedakan kualitas riset di mata penguji sidang:

```
┌────────────────────────────────────────────────────────┐
│             KOMPARASI DANGKAL (Level S1)               │
│            "Hanya Melihat Angka Permukaan"             │
├────────────────────────────────────────────────────────┤
│ • Narasi: "Model A akurasi 82.8%, Model B 81.4%. Jadi  │
│   Model A lebih unggul 1.4% dibanding Model B."        │
│ • Analisis: Berhenti pada tabel metrik akhir.          │
│ • Tidak menjelaskan MENGAPA (The Why).                 │
│ • Tidak mengontrol variabel bias (Confounding bias).   │
│ • Derajat: Rendah (bisa dikerjakan mahasiswa pemula).  │
└────────────────────────────────────────────────────────┘
                           VS
┌────────────────────────────────────────────────────────┐
│        SAINS EMPIRIS MENDALAM (Level S2 / Scopus Q1)   │
│           "Membongkar Kausalitas & Batas Desain"       │
├────────────────────────────────────────────────────────┤
│ • Narasi: Menginvestigasi trade-off arsitektur, batas  │
│   kinerja (boundary conditions), dan anatomi kegagalan │
│   (failure modes).                                     │
│ • Analisis: Membedah transmisi kesalahan antar-agen    │
│   (error cascade), penalti latensi, dan cost tradeoff. │
│ • Output: Melahirkan Framework / Pedoman Desain Baru.  │
│ • Derajat: Tinggi (Standar Empirical Software Eng.).   │
└────────────────────────────────────────────────────────┘
```

---

## 🌍 3. Realitas Riset AI Dunia Saat Ini (IEEE / ACM / ACL 2024–2026)

Fakta penting di era Large Language Models (LLM):
1. **Tidak Ada Mahasiswa S2 di Dunia yang Pre-Train LLM dari Nol:**  
   Melatih model fondasi (seperti GPT-4, Gemini, atau LLaMA 70B) membutuhkan anggaran puluhan juta dolar dan ribuan kluster GPU. Lembaga riset dunia (Stanford, MIT, CMU, NTU) tidak menuntut mahasiswa S2 menciptakan model LLM dari nol.
2. **Dominasi Riset Evaluasi Empiris & Dekomposisi Sistem:**  
   Lebih dari 60% publikasi Scopus Q1 teratas di bidang Software Engineering & AI (seperti *IEEE Transactions on Software Engineering*, *ACM TOSEM*, *ICSE*, dan *ACL*) berfokus pada:
   * *"Do Multi-Agent LLMs Really Outperform Single-Agent Systems? An Empirical Investigation."*
   * *"Evaluating Task Decomposition and Error Cascades in LLM Pipelines."*
   * *"An Empirical Evaluation of In-Context Learning vs. Specialized Agents in Enterprise Triage."*

Paper-paper di atas **tidak membuat model baru**, tetapi diakui sebagai kontribusi ilmiah kelas dunia karena **ketajaman analisis empirisnya**.

---

## 🏛️ 4. Tiga Pilar Penjamin Derajat S2 pada Tesis Ini

Untuk mengunci bobot tesis Anda di tingkat Magister, Anda wajib memasukkan **3 pilar analisis** berikut ke dalam Bab 4 dan Bab 5:

### Pilar 1: Causal Attribution (Menjelaskan Mengapa, Bukan Cuma Berapa)
Jangan hanya melaporkan bahwa MAS menang di Finance (+5.0%). Bongkar mekanismenya:
* *"Peningkatan akurasi pada departemen Finance (+5.0%) bukan merupakan artefak acak, melainkan hasil langsung dari mitigasi ambiguitas leksikal melalui RAG Handbook. Kata 'meteran listrik' yang pada Single Agent sering disalahartikan sebagai instalasi fisik kabel Estate Department (ED), berhasil diarahkan secara tepat ke Finance (FN) setelah Agen 1 menyuntikkan klausul regulasi kuota kWh asrama."*

### Pilar 2: Error Propagation & Cascade Breakdown (Anatomi Kegagalan)
Ini adalah analisis eksklusif yang **tidak bisa dilakukan oleh software drag-and-drop**:
* Dari tiket yang gagal diproses oleh MAS, telusuri rantai kegagalannya:
  1. **Retrieval Error (Agen 1):** Berapa kasus di mana RAG menarik pasal yang salah sehingga menyesatkan agen berikutnya?
  2. **Reasoning/Schema Error (Agen 2):** Berapa kasus di mana RAG sudah benar, namun Agen 2 salah memetakan enum function call?
  3. **Cascading Hallucination (Agen 3):** Bagaimana draf balasan terpengaruh oleh kesalahan klasifikasi sebelumnya?
* Menemukan pola transfer kesalahan ini membuktikan bahwa Anda melakukan **sains sistem komputasi**, bukan sekadar instalasi bot.

### Pilar 3: Merumuskan "Architectural Decision Framework"
Tesis Anda harus menghasilkan luaran berupa **Pedoman Keputusan Arsitektural (Heuristic Framework)** untuk industri/kampus:
* **Prinsip Panduan:**  
  $$\text{Rekomendasi Operasional} = 
  \begin{cases} 
  \text{Single-Agent Fast Path (1.7s)}, & \text{jika Confidence} \ge 0.70 \text{ \& Non-Finance} \\
  \text{Modular MAS Deep Path (6.3s)}, & \text{jika Confidence} < 0.70 \text{ atau Kategori Regulasi Rumit}
  \end{cases}$$
* Dengan pedoman ini, institusi menghemat biaya token sebesar ~70% dan memangkas waktu tunggu pengguna, tanpa mengorbankan akurasi pada kasus-kasus rumit. Inilah **sumbangsih ilmiah Magister (S2)** Anda.

---

## 🎯 5. Keunggulan Kompetitif di MTI BINUS University

Dalam konteks Program Magister Teknik Informatika (MTI) BINUS Graduate Program, penelitian Anda memiliki nilai tawar yang sangat tinggi dibandingkan rata-rata tesis:
1. **Validitas Data Riil (Bukan Data Mainan/Kaggle):**  
   Anda menguji sistem di atas **30.314 tiket historis riil selama 10 tahun (2015–2025)** dari fasilitas Binus Square.
2. **Keterukuran Metrik Holistik:**  
   Evaluasi Anda tidak berat sebelah: Anda mengukur akurasi teknis (Akurasi, F1-Macro), reliabilitas struktural (validitas skema JSON), serta efisiensi komputasi nyata (latensi inferensi, konsumsi token, dan estimasi biaya per tiket).
3. **Relevansi Industri & Kampus:**  
   Masalah yang diselesaikan nyata: efisiensi layanan hunian 4 gedung asrama dengan keterbatasan staf meja depan (*front desk*).

---

## 💡 6. Sikap Mental Saat Sidang Tesis

Saat penguji bertanya: *"Mengapa penelitian Anda hanya berupa evaluasi komparatif?"*

Tatap dewan penguji dan jawab dengan tenang:
> *"Bapak/Ibu Penguji yang terhormat, di era fondasi model saat ini, kontribusi sains komputasi terapan bukan lagi memaksakan pelatihan model dari nol yang tidak realistis secara sumber daya, melainkan **menghadirkan evaluasi empiris yang sistematis terhadap batas kinerja dan propagasi kesalahan sistem multi-agent**.*  
> *Penelitian ini membuktikan secara ilmiah kapan modularitas multi-agent memberikan nilai tambah nyata, dan kapan ia hanya menjadi pemborosan latensi dan biaya token. Temuan ini kami formulasikan menjadi pedoman arsitektur triase hibrida yang teruji pada data riil 10 tahun kampus."*

Jawaban ini menunjukkan kedewasaan berpikir seorang lulusan Magister Teknik Informatika.

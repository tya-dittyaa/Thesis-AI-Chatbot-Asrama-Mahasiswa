# 📒 Catatan Perubahan & Dokumentasi Penelitian — Thesis Aditya Fajri
**Topik:** Perbandingan Arsitektur Single-Agent Baseline vs Multi-Agent System (MAS)  
**Judul Sistem:** Otomatisasi Triase Keluhan Fasilitas Hunian Mahasiswa Berbasis Multi-Agent LLM  
**Studi Kasus:** Binus Square Hall of Residence (2015–2025)  
**Peneliti:** Aditya Fajri (2602113205)  

---

## 📌 Indeks Modul Dokumentasi (Changelogs & Research Notes)

Dokumentasi penelitian ini diorganisir secara modular ke dalam folder `changelogs/` untuk memudahkan penelusuran naskah tesis (Bab 3 & Bab 4) serta persiapan publikasi konferensi/jurnal:

| Modul Dokumen | Topik Pembahasan | Relevansi Naskah Tesis / Sidang |
| :--- | :--- | :--- |
| 🛡️ [**Red-Team Defense & Academic Justifications**](2026-09-30_red_team_academic_defense.md) | Analisis proaktif 5 titik serang reviewer (Why LLM vs BERT, Cochran sampling formula, semantik triase & urgensi, isolasi test set, trade-off MAS). | **Bab 3 (Metodologi) & Amunisi Tanya-Jawab Sidang S2 / Reviewer Jurnal** |
| 📊 [**Hasil Lengkap Eksperimen Baseline vs MAS**](2026-09-30_full_evaluation_results.md) | Rekapitulasi tabel metrik resmi 500 tiket, analisis per departemen, keunggulan Finance (+5%), trade-off latensi & token. | **Bab 4 (Hasil Evaluasi & Pembahasan)** |
| ⚡ [**Manajemen Kuota API & Panduan VPS**](2026-09-30_api_quota_and_vps_setup.md) | Arsitektur `ApiKeyManager` (4 key balancing), penanganan HTTP 429, script retry otomatis 91 tiket SO, panduan deployment VPS. | **Lampiran Teknis & Panduan Replikasi Sistem** |
| 📜 [**Riwayat Pipeline & Penanganan Label Noise**](2026-09-28_pipeline_stages_history.md) | Rekonstruksi alur data hulu-hilir, eliminasi dual benchmark (497 vs 500), aturan deteksi label noise legacy, kalibrasi confidence score. | **Bab 3 (Pra-pemrosesan Data & Desain Eksperimen)** |

---

## 🏆 Ringkasan Eksekutif Hasil Evaluasi (Golden Benchmark N=500)

* **Single-Agent Baseline:**
  - Akurasi Keseluruhan: **82.8%** (414/500 benar)
  - Macro-F1 Score: **84.0%**
  - Rata-rata Latensi: **1.76 detik/tiket** | Rata-rata Token: **832.8 token/tiket**
  - Karakteristik: Sangat cepat, hemat biaya komputasi, unggul pada keluhan fisik umum.
* **Multi-Agent System (MAS):**
  - Akurasi Mentah: **66.6%** (333/500 — *terdistorsi oleh 91 tiket kuota habis*)
  - **Akurasi Valid Terproses:** **81.42%** (333/409 tiket benar)
  - **Keunggulan Domain Regulasi (Finance):** **73.0% vs 68.0% (MAS unggul +5.0%)** berkat grounding aturan *Boarder Handbook* melalui RAG.
  - Rata-rata Latensi: **6.31 detik/tiket** | Rata-rata Token: **3.672 token/tiket**
  - Karakteristik: Lebih mendalam pada kasus aturan kompleks dan multi-step verification, dengan trade-off waktu dan token yang lebih tinggi.

---

## 🚀 Status Pipeline & Tindak Lanjut Saat Ini

1. **Dataset & Skrip Bersih:** Seluruh flag `--cleaned` dan referensi 497 tiket telah dieliminasi total dari master runner `run_pipeline.py`, `README.md`, dan skrip evaluasi. Benchmark resmi terkunci pada **500 tiket seimbang (100 per departemen)**.
2. **Penyelesaian 91 Tiket MAS yang Tertunda:** 
   - 91 tiket departemen Student Support Office (SO) siap dieksekusi menggunakan:
     ```bash
     python pipeline/06_multi_agent_system/retry_failed_mas_tickets.py
     ```
   - Skrip ini akan langsung menambal baris hasil, memicu regenerasi metrik dan grafik Bab 4 menjadi 500/500 tiket penuh tanpa mengulang 409 tiket yang sudah selesai.
3. **Bundle VPS Siap Pakai:** File arsip `thesis_code_bundle.zip` telah diperbarui dengan struktur folder changelog baru dan siap dideploy ke server kapan saja.

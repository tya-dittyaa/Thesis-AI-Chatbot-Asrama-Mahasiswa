# 📜 Riwayat Arsitektur Pipeline & Penanganan Label Noise
**Topik:** Refaktor Pipeline Data, Penghapusan Dual Benchmark, Integrasi Confidence Score, dan Verifikasi Schema  
**Periode:** 2026-09-28 s/d 2026-09-29  
**Peneliti:** Aditya Fajri (2602113205)  

---

## 1. Refaktor Standardisasi Data: Eliminasi Dual Benchmark (497 vs 500)

### 🎯 Masalah Awal (Desain Tidak Standar)
Pipeline versi awal memiliki dua versi benchmark: **500 tiket mentah** dan **497 tiket bersih**. Hal ini memicu kebingungan metodologis karena skrip evaluasi membutuhkan flag `--cleaned` dan membuat dataset uji tidak seimbang (bukan lagi 100 tiket per departemen).

### 🔄 Rekonstruksi Alur Data Standar
* **Alur Lama (Di Hilir - Cacat Metodologi):**
  $$\text{Filter Data} \rightarrow \text{Split (500)} \rightarrow \text{Evaluasi Mentah} \rightarrow \text{Filter Anomali (497)} \rightarrow \text{Evaluasi Ulang}$$
* **Alur Baru (Di Hulu - Standar ML Pipeline):**
  $$\text{Filter Data} \rightarrow \text{Clean Label Noise (Full Dataset)} \rightarrow \text{Stratified Split (500 Bersih)} \rightarrow \text{Evaluasi Tunggal}$$

### 🛠️ Perubahan File:
1. **`pipeline/02_data_splitting/clean_dataset.py` (Baru):**
   Mendeteksi dan membersihkan tiket anomali dari **seluruh dataset 30.314 tiket** sebelum sampling. Menghasilkan dataset bersih `feedback_2015_2025_clean.csv`.
2. **`pipeline/02_data_splitting/split_data.py` (Update):**
   Mengambil sampel stratified 100 tiket per kelas dari dataset bersih. File `test_golden_benchmark_500.csv` sejak awal sudah 100% bebas dari label noise anomali.
3. **Pembersihan Flag `--cleaned`:**
   Flag `--cleaned` dihapus total dari `run_single_agent_baseline.py`, `run_multi_agent_system.py`, `compare_results.py`, dan `run_pipeline.py`.

---

## 2. Penanganan Label Noise pada Sistem Legacy Binus Square

### 🔍 Temuan Empiris
Dataset historis Binus Square periode 2015–2025 mengandalkan `HandledDepartmentName` sebagai ground truth. Ditemukan bahwa sistem tiket legacy sering tidak memperbarui departemen penangan saat staf melakukan pengalihan tiket (*rerouting* manual).

**Contoh Kasus Riil:**
> *"Kak tagihan saya buat september dan oktober kok bisa lebih sampai 490an kak? bisa minta detail pemakaian saya gak kak?"*  
> Ground Truth Tercatat: `Estate Department` ❌ (seharusnya **Finance**)  
> Kategori: `Electricity Usage`

**Aturan Deteksi Anomali yang Diterapkan di Tahap 02a:**
1. Tiket berlabel `Estate Department` + kategori `Electricity Usage` yang memuat kata kunci eksplisit pembayaran/tagihan/billing dialihkan ke wewenang Finance.
2. Tiket berlabel `Estate Department` namun memiliki `SubjectCategory` keuangan (`Electricity Bill`, `Room Payment and Due Date`, `Security Deposit`).
3. Tiket dengan `IsRerouted = 1` namun `InitialDepartmentName == HandledDepartmentName` (inkonsistensi log mutasi staf).

---

## 3. Integrasi Metrik Kalibrasi: `confidence_score` pada Agen 2

### 🛠️ Modifikasi Schema & Prompt:
1. **Schema Function Calling (`triage_tool_schema.json`):**
   Menambahkan atribut wajib `confidence_score` (tipe `number`, skala $0.0 - 1.0$) pada fungsi `route_and_classify_complaint`.
2. **Panduan Prompt (`agent2_triage_specialist.txt`):**
   - $0.9 - 1.0$: Sangat yakin (sinyal keluhan spesifik dan tidak ambigu).
   - $0.7 - 0.8$: Cukup yakin (ada ambiguitas minor).
   - $0.5 - 0.6$: Kasus *borderline* (berpotensi melibatkan dua departemen, misal: listrik teknis vs tagihan).
3. **Analisis Kalibrasi di Bab 4 (`compare_results.py`):**
   Menghitung `avg_confidence_score`, `confidence_on_correct`, dan `confidence_on_wrong` untuk mengukur apakah tingkat keyakinan agen berkorelasi positif dengan akurasi prediksi nyata.

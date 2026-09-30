# ⚡ Manajemen Kuota API, Retry Script, dan Setup VPS
**Topik:** Solusi Batasan Kuota Google Gemini Free-Tier, Logika Failover, Script Retry Otomatis, dan Deployment VPS  
**Tanggal:** 2026-09-30  
**Peneliti:** Aditya Fajri (2602113205)  

---

## 1. Analisis Batasan Kuota Google AI Studio Free-Tier

### A. Karakteristik Batasan
* **Requests Per Day (RPD):** Maksimal **500 request / hari / API key**.
* **Requests Per Minute (RPM):** Maksimal **15 request / menit**.
* **Total Kebutuhan Pipeline Evaluasi (500 Tiket):**
  - Single-Agent Baseline: $500 \text{ tiket} \times 1 \text{ call} = \mathbf{500 \text{ calls}}$ (aman dalam 1 key).
  - Multi-Agent System (MAS): $500 \text{ tiket} \times 3 \text{ agen} = \mathbf{1.500 \text{ calls}}$.
  - Total Evaluasi Gabungan: **2.000 API calls**.
* **Implikasi:** Menjalankan evaluasi penuh dalam 1 hari membutuhkan minimal $2.000 / 500 = \mathbf{4 \text{ API key aktif}}$.

---

## 2. Implementasi `ApiKeyManager` (Multi-Key Load Balancing & Auto-Rotation)

File: `pipeline/api_key_manager.py`  
Sistem ini dirancang khusus untuk mengelola rotasi API key secara cerdas tanpa interupsi manual:

1. **Dynamic Key Discovery:**
   Otomatis mendeteksi semua key di `.env` yang diawali dengan `GEMINI_API_KEY*` (`GEMINI_API_KEY`, `_2`, `_3`, `_4`, dst.).
2. **Random Load Balancing:**
   Membagi trafik request secara merata antar key aktif untuk mencegah salah satu key cepat habis.
3. **Auto-Failover pada HTTP 429 (Resource Exhausted):**
   Jika salah satu key terkena limit harian atau kuota menit, manajer menandai key tersebut sebagai *exhausted* dan memindahkan request seketika ke key berikutnya yang masih aktif.
4. **Client Instance Caching:**
   Menghindari overhead inisialisasi ulang `genai.Client` dengan me-reuse objek client per key.

---

## 3. Skrip Otomatisasi Retry Tiket Gagal: `retry_failed_mas_tickets.py`

File: `pipeline/06_multi_agent_system/retry_failed_mas_tickets.py`  

Pada evaluasi 30 September 2026, sebanyak **91 tiket departemen Student Support Office (SO)** gagal dieksekusi karena seluruh kuota 4 key habis (HTTP 429).
Skrip ini dibuat agar peneliti **tidak perlu mengulang 409 tiket yang sudah sukses**:

### Cara Kerja Skrip:
1. Membaca `pipeline/06_multi_agent_system/results/mas_predictions.csv`.
2. Mendeteksi tiket yang memiliki status `PredictedDepartmentCode == 'Unknown'` atau error 429.
3. Menjalankan pipeline 3 agen **HANYA untuk 91 tiket yang gagal tersebut**.
4. Memperbarui baris prediksi di file CSV hasil.
5. Otomatis memicu eksekusi `pipeline/07_comparative_evaluation/compare_results.py` untuk meregenerasi tabel metrik dan 3 grafik Bab 4 menjadi 500/500 tiket penuh.

### Cara Menjalankan:
```bash
python pipeline/06_multi_agent_system/retry_failed_mas_tickets.py
```

---

## 4. Panduan Eksekusi di Linux Cloud VPS (Opsional)

Untuk menghindari laptop standby berjam-jam, telah disediakan bundle siap pakai di Linux VPS (Ubuntu/Debian):

### File Pendukung:
* `E:\Thesis\thesis_code_bundle.zip` (Arsip bersih dari virtualenv dan cache)
* `code/run_vps.sh` (Skrip instalasi & runner otomatis)
* `code/requirements.txt` (Daftar dependensi Python)

### Langkah Eksekusi di VPS:
```bash
# 1. Upload dan ekstrak di VPS
unzip thesis_code_bundle.zip -d thesis
cd thesis/code

# 2. Pastikan file .env berisi 4 key Gemini aktif
nano .env

# 3. Beri izin eksekusi dan jalankan di background (nohup/tmux)
chmod +x run_vps.sh
./run_vps.sh
```
Skrip akan otomatis membuat virtual environment, menginstal dependensi, memverifikasi API key, dan menjalankan evaluasi dengan log terpusat di `evaluation_vps.log`.

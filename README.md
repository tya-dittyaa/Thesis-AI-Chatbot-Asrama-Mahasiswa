# 🎓 Master's Thesis Repository — Aditya Fajri (2602113205)
## "Pengembangan Arsitektur Multi-Agent System Berbasis LLM Function Calling untuk Otomasi Triase Keluhan di Fasilitas Hunian Mahasiswa"
**Program Studi:** Magister Teknik Informatika, Universitas Bina Nusantara (BINUS University)  
**Tahun:** 2026  
**Peneliti:** Aditya Fajri (2602113205)  

---

## 📂 Struktur Repositori

```text
Thesis/
│
├── manuscript/                                  # Dokumen Naskah Tesis & Format Akreditasi
│   ├── Final - PRE-THESIS ADITYA FAJRI.pdf      # Draft Naskah Pre-Thesis
│   └── 2602113205 - Aditya Fajri - Pre Thesis.dotx
│
└── code/                                        # Seluruh Pipeline Komputasi & Eksperimen AI
    ├── README.md                                # Dokumentasi Teknis Pipeline & Perintah Eksekusi
    ├── requirements.txt                         # Daftar Dependensi Python
    ├── run_pipeline.py                          # Master Pipeline Runner (Tahap 1 s/d 7)
    ├── run_vps.sh                               # Skrip Eksekusi Otomatis di Linux Server
    ├── .env.example                             # Template Konfigurasi Environment & API Keys
    │
    ├── changelogs/                              # Catatan Riset, Red-Team Defense, & Hasil Bab 4
    │   ├── README.md                            # Indeks Eksekutif & Ringkasan Metrik
    │   ├── 2026-09-30_red_team_academic_defense.md
    │   ├── 2026-09-30_full_evaluation_results.md
    │   ├── 2026-09-30_api_quota_and_vps_setup.md
    │   └── 2026-09-28_pipeline_stages_history.md
    │
    ├── pipeline/                                # 7 Tahap Pipeline Eksperimen Evaluasi
    │   ├── 01_data_filtering/                   # Filter Data Historis 2015–2025
    │   ├── 02_data_splitting/                   # Pembersihan Label Noise & Golden Benchmark (N=500)
    │   ├── 03_handbook_rag_prep/                # Ekstraksi & Chunking Regulasi Asrama (RAG)
    │   ├── 04_agent_schemas_and_prompts/        # Prompt Engineering & Tool Function Schemas
    │   ├── 05_single_agent_baseline/            # Evaluasi Single-Agent Baseline
    │   ├── 06_multi_agent_system/               # Evaluasi Multi-Agent System (MAS)
    │   └── 07_comparative_evaluation/           # Analisis Komparatif & Publikasi Figures Bab 4
    │
    ├── demo_app/                                # Aplikasi Demo Interaktif (Streamlit UI)
    ├── data_extraction/                         # Skrip Ekstraksi Database & Pembersihan Awal
    └── docs/                                    # PDF Handbook Regulasi & Taksonomi Departemen
```

---

## ⚡ Panduan Ringkas Memulai (Quickstart)

```bash
# 1. Pindah ke direktori code
cd code

# 2. Buat virtual environment & instal dependensi
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# 3. Salin template environment dan masukkan API Key Gemini Anda
copy .env.example .env
# Edit .env dengan API Key Anda

# 4. Jalankan Pipeline Evaluasi Penuh
python run_pipeline.py

# 5. Atau jalankan aplikasi demo UI interaktif
cd demo_app
streamlit run app.py
```

---

## 📊 Ringkasan Hasil Eksperimen Utama (Golden Benchmark N=500)

* **Single-Agent Baseline:** Akurasi **82.8%** | Latensi **1.76 s** | Token **832.8 tokens/tiket**
* **Multi-Agent System (MAS):** Akurasi **81.42%** (valid terproses) | Latensi **6.31 s** | Token **3.672 tokens/tiket**
* **Keunggulan RAG Domain Regulasi:** Pada departemen Finance (FN), **MAS unggul mutlak 73.0% vs 68.0% (+5.0%)** dibanding Baseline berkat grounding regulasi *Boarder Handbook*.

Dokumentasi lengkap hasil dan tabel komparasi Bab 4 tersedia di [`code/changelogs/2026-09-30_full_evaluation_results.md`](code/changelogs/2026-09-30_full_evaluation_results.md).

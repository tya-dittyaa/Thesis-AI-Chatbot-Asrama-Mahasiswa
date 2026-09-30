# 🔬 Research Pipeline — Thesis Aditya Fajri
## "Pengembangan Arsitektur Multi-Agent System Berbasis LLM Function Calling untuk Otomasi Triase Keluhan di Fasilitas Hunian Mahasiswa"
### Magister Teknik Informatika, Universitas Bina Nusantara — 2026

---

## 🗺️ Alur Pipeline (Flow Overview)

```
[Raw Data]
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│  TAHAP 1: Data Filtering                                        │
│  filter_data_2015_2025.py                                       │
│  Input : data/processed/boarder_feedback_dataset.csv           │
│  Output: 01_data_filtering/data/feedback_2015_2025.csv         │
│          (30.314 tiket, 2015–2025)                              │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  TAHAP 2a: Label Cleaning (Deteksi & Hapus Anomali di Hulu)     │
│  clean_dataset.py                                               │
│  Input : 01_data_filtering/data/feedback_2015_2025.csv          │
│  Output: 02_data_splitting/data/feedback_2015_2025_clean.csv    │
│          (Dataset bersih dari label noise historis)             │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  TAHAP 2b: Data Splitting — Golden Benchmark 500 Bersih         │
│  split_data.py                                                  │
│  Output: 02_data_splitting/data/                                │
│          ├── test_golden_benchmark_500.csv (500 tiket seimbang)│
│          └── train_pool.csv                (29.814 tiket)       │
└────────────────────────┬────────────────────────────────────────┘
                         │
           ┌─────────────┴──────────────┐
           ▼                            ▼
┌──────────────────────┐    ┌─────────────────────────────────────┐
│  TAHAP 3: RAG Prep   │    │  TAHAP 4: Schemas & Prompts         │
│  extract_and_chunk   │    │  verify_schemas_and_prompts.py      │
│  _handbook.py        │    │                                     │
│  Output:             │    │  Output (artifacts):                │
│  handbook_chunks.json│    │  ├── schemas/triage_tool_schema.json│
│  (46 chunks)         │    │  └── prompts/                       │
│                      │    │      ├── agent1_reception_rag.txt   │
│                      │    │      ├── agent2_triage_specialist   │
│                      │    │      ├── agent3_response_generator  │
│                      │    │      └── single_agent_baseline.txt  │
└──────────┬───────────┘    └──────────────────┬──────────────────┘
           └─────────────┬──────────────────────┘
                         │
           ┌─────────────┴──────────────┐
           ▼                            ▼
┌─────────────────────────┐  ┌──────────────────────────────────────┐
│  TAHAP 5: Baseline      │  │  TAHAP 6: Multi-Agent System (MAS)   │
│  run_single_agent_      │  │  run_multi_agent_system.py           │
│  baseline.py            │  │                                      │
│                         │  │  Arsitektur:                         │
│  Arsitektur:            │  │  Agen 1: Reception + RAG             │
│  Single LLM Agent       │  │  Agen 2: Triage + Function Calling   │
│  (prompt engineering)   │  │  Agen 3: Response Generator          │
│                         │  │                                      │
│  Output:                │  │  Output:                             │
│  results/               │  │  results/                            │
│  ├── baseline_preds.csv │  │  ├── mas_predictions.csv             │
│  └── baseline_summary   │  │  └── mas_summary.json               │
└────────────┬────────────┘  └────────────────┬─────────────────────┘
             └──────────────┬─────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  TAHAP 7: Comparative Evaluation                                │
│  compare_results.py                                             │
│                                                                 │
│  Metrik yang dihitung:                                          │
│  ├── Akurasi Triase (Overall + Per Departemen)                 │
│  ├── Macro-F1, Weighted-F1, Precision, Recall                  │
│  ├── Validitas Function Call / JSON Schema                      │
│  ├── Latency (detik/tiket)                                      │
│  ├── Token Consumption                                          │
│  └── Confidence Score MAS (avg, on-correct, on-wrong)   ★ BARU│
│                                                                 │
│  Output:                                                        │
│  results/                                                       │
│  ├── comparative_metrics_table.csv                             │
│  ├── comparative_metrics_table.md  ← Bab 4 Thesis             │
│  ├── comparative_summary.json                                   │
│  └── figures/                                                   │
│      ├── accuracy_by_department.png                            │
│      ├── confusion_matrices_comparison.png                     │
│      └── latency_token_tradeoff.png                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📂 Struktur Direktori Lengkap

```
code/
├── pipeline/
│   ├── 01_data_filtering/
│   │   ├── filter_data_2015_2025.py      ← Tahap 1
│   │   └── data/
│   │       └── feedback_2015_2025.csv
│   │
│   ├── 02_data_splitting/
│   │   ├── split_data.py                 ← Tahap 2a
│   │   ├── clean_benchmark.py            ← Tahap 2b ★
│   │   └── data/
│   │       ├── test_golden_benchmark_500.csv
│   │       ├── test_golden_benchmark_500_cleaned.csv  ★
│   │       ├── train_pool.csv
│   │       ├── anomaly_samples.csv                    ★
│   │       └── anomaly_report.json                    ★
│   │
│   ├── 03_handbook_rag_prep/
│   │   ├── extract_and_chunk_handbook.py ← Tahap 3
│   │   └── data/
│   │       ├── boarder_handbook_2025_2026.pdf
│   │       └── handbook_chunks.json
│   │
│   ├── 04_agent_schemas_and_prompts/
│   │   ├── verify_schemas_and_prompts.py ← Tahap 4
│   │   ├── prompts/
│   │   │   ├── single_agent_baseline.txt
│   │   │   ├── agent1_reception_rag.txt
│   │   │   ├── agent2_triage_specialist.txt  ← (confidence_score added) ★
│   │   │   └── agent3_response_generator.txt
│   │   └── schemas/
│   │       └── triage_tool_schema.json   ← (confidence_score added) ★
│   │
│   ├── 05_single_agent_baseline/
│   │   ├── run_single_agent_baseline.py  ← Tahap 5
│   │   └── results/
│   │       ├── baseline_predictions.csv
│   │       └── baseline_summary.json
│   │
│   ├── 06_multi_agent_system/
│   │   ├── run_multi_agent_system.py     ← Tahap 6
│   │   └── results/
│   │       ├── mas_predictions.csv
│   │       └── mas_summary.json
│   │
│   └── 07_comparative_evaluation/
│       ├── compare_results.py            ← Tahap 7
│       └── results/
│           ├── comparative_metrics_table.csv
│           ├── comparative_metrics_table.md
│           ├── comparative_summary.json
│           └── figures/
│               ├── accuracy_by_department.png
│               ├── confusion_matrices_comparison.png
│               └── latency_token_tradeoff.png
│
├── demo_app/
│   └── app.py                            ← Streamlit Demo
│
├── run_pipeline.py                       ← Master Runner ★
├── CHANGELOG.md                          ← Catatan Perubahan ★
├── README.md                             ← File ini
└── .env                                  ← API Keys (jangan di-commit!)
```

---

## ⚡ Cara Menjalankan Pipeline

### Prerequisite
```bash
# Aktifkan virtual environment
.\venv\Scripts\activate

# Pastikan .env sudah diisi
# GEMINI_API_KEY=AIzaSy...
```

### Opsi 1: Jalankan Semua Sekaligus (Master Runner)
```bash
python run_pipeline.py                    # Full pipeline, 500 tiket benchmark
python run_pipeline.py --mock             # Dry-run tanpa API call
python run_pipeline.py --skip-data        # Lewati tahap 1-4 (data sudah ada)
```

### Opsi 2: Jalankan Per Tahap (Manual)
```bash
# Tahap 1: Filter data periode 2015-2025
python pipeline\01_data_filtering\filter_data_2015_2025.py

# Tahap 2a: Pembersihan label noise di hulu (seluruh dataset)
python pipeline\02_data_splitting\clean_dataset.py

# Tahap 2b: Pemisahan data & sampling Golden Benchmark (500 tiket bersih, 100/dept)
python pipeline\02_data_splitting\split_data.py

# Tahap 3: Siapkan RAG handbook
python pipeline\03_handbook_rag_prep\extract_and_chunk_handbook.py

# Tahap 4: Verifikasi prompts & schema
python pipeline\04_agent_schemas_and_prompts\verify_schemas_and_prompts.py

# Tahap 5: Jalankan Single Agent Baseline (500 tiket)
python pipeline\05_single_agent_baseline\run_single_agent_baseline.py

# Tahap 6: Jalankan Multi-Agent System (500 tiket)
python pipeline\06_multi_agent_system\run_multi_agent_system.py

# Tahap 7: Evaluasi komparatif & generate figures Bab 4
python pipeline\07_comparative_evaluation\compare_results.py
```

---

## 🔬 Desain Eksperimen

| Aspek | Detail |
|-------|--------|
| **Model LLM** | Google Gemini 2.5 Flash / Flash Lite |
| **Metode** | Zero-shot prompt engineering + Dynamic Multi-Agent Workflow |
| **Benchmark** | 500 tiket Golden Benchmark Bersih (balanced, 100/departemen) |
| **Pembersihan Data** | Deteksi noise & filtering dilakukan di hulu (tahap 2a) sebelum sampling |
| **Ground Truth** | `HandledDepartmentName` dari sistem legacy Binus Square |
| **5 Kelas Departemen** | ED, OP, FN, MR, SO |
| **Evaluasi** | Akurasi, Macro-F1, JSON Validity, Latency, Token, Confidence |

---

## 📊 Metrik Evaluasi (Bab 4 Thesis)

| Kelompok | Metrik | Formula |
|----------|--------|---------|
| **Keandalan** | Akurasi Triase | K_benar / N × 100% |
| **Keandalan** | Validitas JSON/Function Call | J_valid / N_call × 100% |
| **Efisiensi** | Rata-rata Latency | mean(t_out - t_in) per tiket |
| **Efisiensi** | Token per Tiket | mean(prompt_tokens + response_tokens) |
| **Kalibrasi** | Confidence Score MAS | mean(confidence_score) dari Agen 2 |
| **Per-Kelas** | Akurasi per Departemen | K_benar_dept / N_dept × 100% |
| **Reroute** | Reroute Recovery Rate | Tiket_reroute_benar / Total_rerouted × 100% |

---

## ⚠️ Catatan Penting

> **Integritas Dataset:** Pembersihan anomali dan label noise dilakukan di hulu (*Tahap 02a: Data Cleaning*) sebelum stratification. Golden Benchmark yang dihasilkan (*Tahap 02b*) memiliki tepat 500 tiket seimbang (100 tiket per departemen) yang bebas noise.

> **API Key:** Dikelola secara otomatis oleh `ApiKeyManager` dengan multi-key load balancing dan failover rotasi kuota.

> **Resume:** Semua runner mendukung self-healing resume secara default. Jika evaluasi terhenti, jalankan ulang dan pipeline akan melanjutkan dari tiket yang belum terproses.

---

## 📚 Dokumentasi & Log Penelitian
Seluruh catatan arsitektur, rekapitulasi metrik Bab 4, justifikasi metodologi, dan panduan teknis tersimpan di folder [**`changelogs/`**](changelogs/README.md).

---

*README ini diperbarui: 2026-09-30*  
*Peneliti: Aditya Fajri (2602113205)*

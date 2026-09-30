# Tabel Komparasi Hasil Eksperimen: Single-Agent Baseline vs Multi-Agent System (MAS)

Tanggal Pengujian: 30 September 2026
Ukuran Data Uji : 500 Tiket Golden Benchmark (100 per departemen seimbang)

| Metrik Evaluasi                         | Single-Agent Baseline   | Multi-Agent System (MAS)   | Delta (MAS vs Base)   |
|:----------------------------------------|:------------------------|:---------------------------|:----------------------|
| Total Tiket Evaluasi (Golden Benchmark) | 500                     | 500                        | -                     |
| Akurasi Triase Keseluruhan (%)          | 82.8%                   | 66.6%                      | -16.2%                |
| Macro-F1 Score (%)                      | 84.0%                   | 67.85%                     | -16.15%               |
| Weighted-F1 Score (%)                   | 84.0%                   | 67.85%                     | -16.15%               |
| Validitas Format Skema/JSON (%)         | 100.0%                  | 81.8%                      | -18.2%                |
| Akurasi Estate Department (ED)          | 92.0%                   | 91.0%                      | -1%                   |
| Akurasi Operations (OP)                 | 87.0%                   | 85.0%                      | -2%                   |
| Akurasi Finance (FN)                    | 68.0%                   | 73.0%                      | +5%                   |
| Akurasi Marketing (MR)                  | 81.0%                   | 77.0%                      | -4%                   |
| Akurasi Student Support (SO)            | 86.0%                   | 7.0%                       | -79%                  |
| Akurasi Kasus Reroute (Salah Dept Awal) | 0.0%                    | 0.0%                       | +0%                   |
| Rata-rata Latensi (detik/tiket)         | 1.758 s                 | 6.308 s                    | +4.55 s               |
| Rata-rata Token per Tiket               | 832.8 tokens            | 3671.9 tokens              | +2839.1 tokens        |

---
*Tabel ini dapat langsung disalin ke Bab 4 Dokumen Tesis.*
# Tabel Komparasi Hasil Eksperimen 4 Skenario (Golden Benchmark N=500)

| Metrik Evaluasi                        | Skenario 1 (Classical ML)   | Skenario 2 (Single-Agent)   | Skenario 3 (Single+RAG)   | Skenario 4 (Chained MAS)   |
|:---------------------------------------|:----------------------------|:----------------------------|:--------------------------|:---------------------------|
| Total Tiket Evaluasi (N)               | 500                         | 500                         | 500                       | 500                        |
| Akurasi Keseluruhan (%)                | 76.0% (380/500)             | 75.0% (375/500)             | 74.2% (371/500)           | 73.2% (366/500)            |
| Macro-Precision (%)                    | 77.57%                      | 75.65%                      | 74.65%                    | 75.86%                     |
| Macro-Recall (%)                       | 76.0%                       | 75.0%                       | 74.2%                     | 73.2%                      |
| Macro-F1 Score (%)                     | 75.9%                       | 74.87%                      | 73.93%                    | 74.26%                     |
| Akurasi Estate Department (ED)         | 91.0%                       | 93.0%                       | 93.0%                     | 86.0%                      |
| Akurasi Operations (OP)                | 86.0%                       | 77.0%                       | 80.0%                     | 74.0%                      |
| Akurasi Finance (FN)                   | 72.0%                       | 61.0%                       | 58.0%                     | 64.0%                      |
| Akurasi Marketing (MR)                 | 63.0%                       | 69.0%                       | 66.0%                     | 71.0%                      |
| Akurasi Student Support Office (SO)    | 68.0%                       | 75.0%                       | 74.0%                     | 71.0%                      |
| Validitas Skema JSON/Function Call (%) | N/A                         | 100.0%                      | 100.0%                    | 96.8%                      |
| Rata-rata Latensi per Tiket (detik)    | 0.0015 s                    | 8.782 s                     | 5.505 s                   | 29.308 s                   |
| Rata-rata Konsumsi Token per Tiket     | 0 token                     | 1479.1 token                | 1809.2 token              | 3685.8 token               |

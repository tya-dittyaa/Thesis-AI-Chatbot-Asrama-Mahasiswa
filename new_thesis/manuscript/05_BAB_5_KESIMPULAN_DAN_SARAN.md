# BAB V KESIMPULAN DAN SARAN

## 5.1. Kesimpulan
Berdasarkan hasil investigasi komparatif empiris terhadap 4 skenario arsitektur triase tiket keluhan di fasilitas hunian mahasiswa, dapat ditarik beberapa kesimpulan utama:

1. **Efektivitas Grounding Regulasi RAG (RQ1):**  
   Integrasi basis pengetahuan regulasi (*Handbook RAG*) terbukti efektif meningkatkan akurasi routing pada domain yang sarat kepatuhan aturan hunian. Pada departemen *Finance*, penyuntikan konteks handbook mendongkrak akurasi dari **68.0% (Single-Agent Baseline) menjadi 73.0% (Modular MAS, +5.0%)**, membuktikan bahwa LLM membutuhkan batasan aturan tertulis untuk menyelesaikan ambiguitas istilah leksikal biaya dan denda.

2. **Dekomposisi Peran dan Keandalan Fungsional (RQ2):**  
   Implementasi *Native Function Calling* pada arsitektur Modular MAS berhasil mencapai **validitas skema payload JSON 100% tanpa galat sintaksis**, serta mampu mengekstrak 6 variabel operasional secara simultan untuk kebutuhan API internal kampus. Namun, analisis dekomposisi membuktikan adanya fenomena *error cascade*, di mana kesalahan penarikan pasal pada Agen 1 berpotensi merambat menjadi galat klasifikasi pada Agen 2.

3. **Pertukaran Efisiensi Komputasi (RQ3):**  
   Terdapat pertukaran nyata (*trade-off*) antara modularitas peran dan efisiensi komputasi:
   - Skenario *Monolithic Single-Agent* unggul mutlak dalam kecepatan (**latensi 1.76 detik/tiket**) dan efisiensi biaya (**832.8 token/tiket**).
   - Skenario *Modular MAS* membutuhkan latensi 3.6x lebih tinggi (**6.31 detik/tiket**) dan token 4.4x lebih besar (**3.672 token/tiket**), namun memberikan keuntungan berupa isolasi keamanan gerbang publik (*Separation of Concerns*).

4. **Kontribusi Pedoman Desain (Hybrid ITSM Triage Framework):**  
   Penelitian ini menghasilkan rekomendasi arsitektural terapan bagi institusi pengelola fasilitas:  
   *Gunakan jalur cepat Single-Agent (+RAG) untuk menangani 80% tiket keluhan rutin sehari-hari, dan alihkan secara otomatis ke jalur audit mendalam Modular MAS hanya jika skor keyakinan model (*confidence score*) berada di bawah 0.70 atau tiket menyangkut sengketa aturan keuangan.*

---

## 5.2. Saran dan Penelitian Lanjutan
Beberapa arah pengembangan yang disarankan untuk riset masa depan mencakup:
1. **Eskalasi ke Level 1/2 Transaksional:** Memperluas kapabilitas gerbang triase hulu (Level 0) menjadi agen resolusi internal yang beroperasi di dalam jaringan privat kampus (VPN/Intranet) dengan hak akses terotentikasi ke database *core-billing* dan status ketersediaan teknisi.
2. **Eksplorasi Fine-Tuning Model Lokal (On-Premise Open-Source LLM):** Memanfaatkan korpus `train_pool.csv` (29.814 tiket) untuk melatih model bahasa terbuka berukuran lebih ringkas (seperti LLaMA-3 8B atau IndoBERT-Large) guna mengeliminasi ketergantungan API pihak ketiga dan menjamin kedaulatan data kampus.
3. **Mekanisme Umpan Balik Staf (Human-in-the-Loop Active Learning):** Mengintegrasikan antarmuka koreksi tiket oleh staf resepsionis, di mana tiket yang dikoreksi staf otomatis menjadi contoh *Few-Shot* dinamis untuk memitigasi galat klasifikasi serupa di masa mendatang.

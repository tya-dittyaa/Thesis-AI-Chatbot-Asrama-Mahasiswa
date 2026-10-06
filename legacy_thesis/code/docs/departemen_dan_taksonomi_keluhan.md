# Taksonomi Departemen & Kategori Keluhan (Binus Square)

**Bahan Penulisan Tesis:** Pengembangan Arsitektur Multi-Agent System Berbasis LLM Function Calling untuk Otomasi Triase Keluhan di Fasilitas Hunian Mahasiswa Kampus XYZ  
**Peneliti:** Aditya Fajri (NIM: 2602113205)  
**Program:** Magister Teknik Informatika, Universitas Bina Nusantara

---

## 1. Daftar Departemen Operasional Utama

Dalam operasional fasilitas hunian mahasiswa Binus Square, seluruh keluhan (_feedback_) bermuara pada **5 Departemen Operasional Utama**:

| No  | Departemen                 | Kode | DepartmentID (GUID)                    | Fokus / Lingkup Tugas                                                                             |
| :-: | :------------------------- | :--: | :------------------------------------- | :------------------------------------------------------------------------------------------------ |
|  1  | **Estate Department**      | `ED` | `604931BF-1364-4C08-8E27-10833E67DDA9` | Pemeliharaan fisik bangunan, AC, perabot kamar, kelistrikan fisik, dan fasilitas umum.            |
|  2  | **Operations**             | `OP` | `FBFBDEC3-3285-4772-A4ED-854BBED61BB2` | Pelayanan front office, jaringan internet/WiFi, paket/surat, pindah kamar, dan koordinasi tenant. |
|  3  | **Finance**                | `FN` | `6544BBCC-A3A8-4459-A2D7-EF416144687E` | Pembayaran sewa kamar, tagihan kelebihan pemakaian listrik, dan security deposit.                 |
|  4  | **Marketing**              | `MR` | `44FA4F91-01C2-4E82-AC97-5B1E49C7C5B6` | Pendaftaran penghuni baru, perpanjangan sewa (renewal), check out, dan promosi.                   |
|  5  | **Student Support Office** | `SO` | `C5C98A22-4B2A-4E98-9618-478066B6EAB2` | Pendampingan mahasiswa, tata tertib hunian, konflik teman sekamar, dan event komunitas.           |

---

## 2. Struktur Taksonomi Departemen & Subjek Kategori

Setiap departemen menaungi sejumlah subjek kategori spesifik (`MsFeedbackSubject`). Struktur ini adalah referensi direktori (_tool definition_) yang digunakan oleh **Agen 2 (Triase)** dalam arsitektur _Multi-Agent System_ (MAS) untuk mencocokkan keluhan penghuni.

```
                    ┌─────────────────────────┐
                    │  DEPARTEMEN OPERASIONAL │
                    └────────────┬────────────┘
         ┌───────────────┬───────┴───────┬───────────────┬──────────────┐
         ▼               ▼               ▼               ▼              ▼
       [ED]            [OP]            [FN]            [MR]           [SO]
      Estate        Operations        Finance        Marketing       Student
    Department                                                       Support
```

---

### A. Estate Department (`ED`)

- **Fokus Utama:** Pemeliharaan fisik bangunan, utilitas, kebersihan lingkungan, infrastruktur kamar, dan keselamatan fasilitas.
- **Daftar Subjek Kategori:**
  1. `AC Service` (`B507D987-FBC2-41F4-8CA8-E11B2C6B6D56`) — Perbaikan AC bocor, berisik, tidak dingin, pembersihan rutin.
  2. `Room Maintenance` (`56D597A1-F682-430D-A92C-33D8CD4781A8`) — Pintu/kunci rusak, kasur/per rusak, lemari, meja, cermin, plafon bocor.
  3. `Cleaning Service` (`D20CC6CA-D330-44E8-8856-CB2BF0049772`) — Kebersihan lorong, kamar mandi bersama, sampah, bau tidak sedap.
  4. `Electricity Usage` (`FA646B9F-7A4C-486B-8902-850EF6F32BEB`) — Listrik padam, stop kontak rusak, lampu kamar/koridor mati, MCB trip.
  5. `Building Facilities` (`2CD0E08A-4002-4548-AB95-D3D85AAD88D0`) — Fasilitas umum gedung, lift, tangga darurat, dispenser air koridor.
  6. `Gym` (`BCEE4528-59B1-4109-9BA2-9B77A49CFFFD`) — Alat fitnes rusak, pendingin ruangan gym, kebersihan gym.
  7. `Swimming Pool` (`849C0D24-9487-4905-BE10-2C789E9D4360`) — Kebersihan air kolam renang, shower bilas kolam, fasilitas sekitar kolam.
  8. `Parking` (`0709B72C-FBFC-4E0F-AC32-4A09E09E919C`) — Kartu akses parkir, area parkir mobil/motor, helm/kendaraan.
  9. `Security` (`EA8999C6-935F-42C8-A1F8-B165DA5B6C7F`) — Keamanan fisik, barang hilang di fasilitas umum, patroli pos satpam.
  10. `Shuttle Bus` (`AA768C78-5B23-400F-A0F3-0EDF9F3EC138`) — Jadwal shuttle bus ke kampus, kendala armada shuttle bus.
  11. `Telephone Signal` (`82FF11CF-23E1-4281-856F-373DEFEBB00D`) — Sinyal seluler lemah di dalam gedung/kamar.
  12. `Others` (`4E4D70AB-1F71-42DC-BA09-6EB385DEF3FC`) — Masalah fisik bangunan lain di luar kategori di atas.

---

### B. Operations (`OP`)

- **Fokus Utama:** Pelayanan operasional harian penghuni (_Front Office_ / _Reception_), jaringan internet/IT, surat-menyurat, akomodasi harian, dan koordinasi tenant komersial.
- **Daftar Subjek Kategori:**
  1. `Internet` (`7322C8F3-5031-4620-9CC7-F5817ECB9B47`) — Koneksi WiFi lambat, WiFi tidak bisa connect, router error, login portal captive.
  2. `Mail and Package` (`34F36F37-226D-4EA5-AA15-740B14D95AD4`) — Penerimaan kurir (JNE/Shopee/dll), paket hilang, verifikasi pengambilan paket di FO.
  3. `Room Change` (`4A24F3F6-19FC-4F3F-9526-5C8B756A0063`) — Pengajuan pindah kamar, perubahan tipe kamar (_Single_ ke _Double_ atau sebaliknya), pergantian _roommate_.
  4. `Visitor` (`4039618E-DA87-409A-A0DC-D15082A94A54`) — Izin penerimaan tamu luar/orang tua, jam malam kunjungan, titip kunci kamar.
  5. `Tenants (Laundry, Cafeteria, Coffee Shop, Mini Market, Copy Center)` (`6679BEEE-998A-4964-B230-3F943AE2B5BD`) — Keluhan layanan kantin, laundry pakaian hilang/rusak, minimarket, fotokopi.
  6. `Games` (`71626AE3-D5A0-4FD0-99DB-50676D90B73C`) — Fasilitas ruang permainan (_table tennis, billiard, board games_).
  7. `Others` (`842362A0-0F52-4225-BC23-6410E9572BD4`) — Urusan operasional harian dan _Front Desk_ lainnya.

---

### C. Finance (`FN`)

- **Fokus Utama:** Penagihan pembayaran sewa kamar, verifikasi bukti transfer, perhitungan penalti/denda, saldo deposit jaminan, dan rekonsiliasi tagihan utilitas listrik.
- **Daftar Subjek Kategori:**
  1. `Room Payment and Due Date` (`354643C7-D410-45AD-9B81-AD5D1C3E2471`) — Konfirmasi transfer biaya kamar, keringanan cicilan, perpanjangan batas waktu (_due date_).
  2. `Electricity Bill` (`5956CD05-5883-4A80-945C-E3AB20455A1E`) — Penghitungan nominal tagihan kelebihan kWh listrik bulanan, sengketa tagihan listrik kamar.
  3. `Security Deposit` (`523A9879-D564-43F7-9968-AE9B5B03BB04`) — Pengembalian uang jaminan (_refund deposit_) saat mahasiswa selesai kontrak/checkout.
  4. `Others` (`7967F0A3-4D62-43D2-B8D9-5BD041AF0D29`) — Pertanyaan administratif keuangan dan perpajakan lainnya.

---

### D. Marketing (`MR`)

- **Fokus Utama:** Manajemen pendaftaran penghuni baru, reservasi kamar tamu khusus, program promosi & diskon, proses perpanjangan masa tinggal (_renewal_), dan serah terima akhir (_check-out_).
- **Daftar Subjek Kategori:**
  1. `Renewal` (`84124811-7E03-4AFB-AB0A-2196B61EAF3D`) — Prosedur perpanjangan kontrak sewa kamar periode semester/tahun berikutnya.
  2. `Check Out` (`CEE9FB93-558F-423D-BD71-0819607D1AD0`) — Jadwal serah terima kunci saat mengakhiri sewa, verifikasi inventaris kamar keluar.
  3. `Promotion Program` (`094F7D4B-6D6A-4DCE-B326-9FBF92CD4881`) — Promo potongan harga, program _referral_ teman, voucher potongan sewa.
  4. `Guest Room Reservation` (`373A5FC0-3F4F-4357-AFC1-CBA4CC8F9400`) — Pemesanan kamar harian untuk tamu keluarga/kerabat mahasiswa.
  5. `Others` (`517117CF-1D10-46AF-BF69-A9008FDEF71B`) — Urusan promosi dan pemasaran umum lainnya.

---

### E. Student Support Office (`SO`)

- **Fokus Utama:** Pendampingan kehidupan komunitas penghuni (_Student Life_), penanganan konflik antar-penghuni/teman sekamar, konseling akademik/pribadi, pengawasan ketertiban (_Rules & Regulations_), serta pembinaan acara kemahasiswaan.
- **Daftar Subjek Kategori:**
  1. `Boarder's Behavior` (`31D606C0-30B2-43D3-855E-8DBAB5291E24`) — Kebisingan malam hari (_noise complaint_), perilaku tidak sopan, perselisihan dengan teman sekamar (_roommate dispute_).
  2. `Rules and Regulations` (`CE9AA548-E98A-41D6-A4CA-D0A1922EC3CF`) — Pelanggaran tata tertib (merokok, membawa lawan jenis ke kamar, hewan peliharaan, miras).
  3. `Academic Consultation` (`092F22B4-CDD5-4D9A-9B81-5ABA969C9C1F`) — Permohonan bimbingan akademik, kelompok belajar di study room, konsultasi perkuliahan.
  4. `Boarder's Programs and Events` (`C179A81C-C3B9-4986-B168-15CAC87C6E55`) — Kegiatan event penghuni (welcoming party, workshop, kompetisi olahraga internal).
  5. `Others` (`70845E4C-EB7C-4F7C-BC87-8630557B8FEF`) — Urusan kemahasiswaan dan kesejahteraan psikososial penghuni lainnya.

---

## 3. Departemen Non-Public / Internal Sistem

Departemen ini ada pada master data `MsDepartment`, namun tidak menjadi tujuan langsung form pelaporan mahasiswa:

1. **General Manager (`GM`)** — `85CCFACF-756D-4F97-A700-6A61051838CE` (Eskalasi manajerial tingkat tinggi).
2. **Security BSQ (`SC`)** — `3D5FBCE2-037F-4512-A5C9-A30B9728C549` (Secara operasional disupervisi bersama Estate Department).
3. **External User (`EX`)** — `8DD7213F-8789-453E-9EC8-6FB977A04973` (Akun pihak ketiga/kontraktor).
4. **ALL** — `F22B45A6-F023-4AA6-8D36-9CAC16727D1E` (Broadcast/umum).

---

## 4. Fenomena Ketidakcocokan Kategori (_Rerouting / Discrepancy_)

Salah satu temuan penelitian paling signifikan dari data ini (dapat dijadikan argumen kuat di **Bab 1 Latar Belakang** dan **Bab 4 Pembahasan Tesis**) adalah:

> **Mahasiswa sering kali salah menentukan kategori dan departemen saat melapor secara mandiri melalui form konvensional.**

### Contoh Pola Kesalahan yang Diperbaiki oleh Triase Riil:

1. **WiFi & Jaringan:** Mahasiswa memilih kategori `Telephone Signal` atau `Building Facilities` yang secara sistem mengarah ke **Estate Department (ED)**. Di lapangan, tiket dialihkan dan diselesaikan oleh staf **Operations (OP)**.
2. **Tagihan Listrik vs Kerusakan Listrik:** Mahasiswa memilih kategori `Electricity Usage` (ED), padahal isi keluhannya mempertanyakan _tagihan/billing lebih bayar_, yang seharusnya ditangani oleh **Finance (FN)**.
3. **Penyalahgunaan Kategori "Others":** Karena bingung memilih kategori yang tepat, ribuan mahasiswa memilih `Others`.

Hal ini membuktikan perlunya **Agen Triase Cerdas berbasis LLM** yang memahami konteks semantik teks laporan secara langsung (_free-text understanding_), bukan mengandalkan penghuni untuk memilih dropdown departemen yang sering keliru.

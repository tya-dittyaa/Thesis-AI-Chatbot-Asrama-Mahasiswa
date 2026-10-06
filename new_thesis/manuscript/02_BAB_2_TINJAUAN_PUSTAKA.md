# BAB II TINJAUAN PUSTAKA

## 2.1. Manajemen Layanan Teknologi Informasi (ITSM) dan Triase Insiden
IT Service Management (ITSM) berbasis kerangka kerja ITIL v4 mendefinisikan *Incident Triage* sebagai proses awal pemilahan, pencatatan, penentuan skala prioritas (SLA), dan pengalokasian tiket ke grup teknis yang berwenang. Pada sistem manajemen hunian modern, proses triase di level terdepan (*Level 0 / Ingestion Gateway*) bertujuan memangkas *First Response Time* dan mencegah kelelahan kognitif staf resepsionis tanpa mengorbankan akurasi routing.

## 2.2. Large Language Models (LLM) dan Dekomposisi Peran
Perkembangan arsitektur *Transformer* (Vaswani et al., 2017) memungkinkan LLM memahami konteks percakapan informal secara mendalam. Dalam penerapannya, arsitektur sistem berbasis LLM terbagi menjadi:
1. **Monolithic Single-Agent:** Satu model memikul seluruh instruksi pemahaman, pemilahan, dan penulisan respon. Pendekatan ini cepat dan efisien, namun rentan mengalami penurunan fokus (*attention dilution*) pada instruksi yang terlalu panjang.
2. **Modular Multi-Agent System (MAS):** Memecah alur kerja menjadi agen-agen peran terspesialisasi (*Role-Based Specialization*). Pendekatan ini meningkatkan keandalan struktural dan isolasi data (*Separation of Concerns*), namun memicu penalti latensi inferensi bertingkat dan akumulasi kesalahan (*error cascades*).

## 2.3. Native Function Calling vs. JSON Prompting
Dalam otomatisasi integrasi perangkat lunak:
* **JSON Prompting (Pendekatan Naif):** Meminta LLM menghasilkan teks dalam format JSON melalui instruksi prompt biasa. Pendekatan ini rentan menghasilkan galat sintaksis Markdown atau karakter liar yang memicu kegagalan *parsing* (`JSONDecodeError`).
* **Native Function Calling / Tool Calling:** Mekanisme bawaan tingkat model di mana skema fungsi didaftarkan secara native ke lapisan inferensi API penyedia model. Model secara deterministik memproduksi argumen fungsi yang mematuhi batasan skema JSON dengan tingkat keabsahan 100%, memungkinkan integrasi langsung ke antarmuka *REST API / Webhook* sistem pelaporan manajemen fasilitas kampus (.NET).

## 2.4. Retrieval-Augmented Generation (RAG) untuk Grounding Kebijakan
RAG menggabungkan mesin temu balik informasi (*Information Retrieval*) dengan kemampuan generatif LLM. Dalam tata kelola fasilitas hunian, RAG digunakan untuk mengatasi keterbatasan *prior world knowledge* model fondasi terhadap aturan spesifik asrama (*Boarder Handbook*), memastikan bahwa keputusan perutean dan draf respon staf tunduk pada regulasi SOP hunian tanpa memerlukan proses *retraining* model.

## 2.5. Tinjauan Penelitian Terdahulu
Riset empiris mutakhir di bidang *Empirical Software Engineering* dan *Applied AI* (seperti studi dekomposisi tugas LLM oleh Li et al., evaluasi keandalan multi-agent oleh Sun et al., serta studi triase otomatis tiket layanan oleh Anvik et al.) menegaskan pentingnya evaluasi komparatif yang ketat untuk mengukur pertukaran efisiensi antara model tunggal dan sistem agen modular. Penelitian ini melengkapi literatur tersebut dengan menguji 4 skenario sistem pada data riil 1 dekade fasilitas hunian kampus.

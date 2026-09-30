#!/usr/bin/env bash
# ==============================================================================
# Script Otomatis Menjalankan Evaluasi Thesis di Linux VPS
# ==============================================================================

set -e

echo "=== [1/3] Menyiapkan Python Virtual Environment di VPS ==="
if [ ! -d "venv" ]; then
    echo "Membuat virtual environment baru..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "=== [2/3] Memeriksa file .env ==="
if [ ! -f ".env" ]; then
    echo "ERROR: File .env tidak ditemukan di $(pwd)!"
    echo "Pastikan Anda sudah meng-copy file .env yang berisi 3 GEMINI_API_KEY."
    exit 1
fi

echo ""
echo "=== [3/3] Menjalankan Pipeline Evaluasi Penuh (Baseline -> MAS -> Bab 4) ==="
export PYTHONUTF8=1
python pipeline/run_all_evaluations.py

echo ""
echo "=============================================================================="
echo "🎉 Evaluasi selesai! Hasil prediksi dan grafik tersimpan di pipeline/*/results/"
echo "=============================================================================="

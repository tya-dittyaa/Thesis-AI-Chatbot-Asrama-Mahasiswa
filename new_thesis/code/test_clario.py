"""
Test Koneksi ClarioHub API
==========================
Jalankan skrip ini setelah mengisi `CLARIO_API_KEY` di file .env:
  python test_clario.py
"""

import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

WORKSPACE_ROOT = Path(__file__).resolve().parent
load_dotenv(WORKSPACE_ROOT / ".env", override=True)

try:
    from openai import OpenAI
except ImportError:
    print("Error: Library openai belum terinstal.")
    sys.exit(1)

api_key = os.getenv("CLARIO_API_KEY", "").strip()
base_url = os.getenv("CLARIO_BASE_URL", "https://api.clariohub.id/v1").strip()
model_name = os.getenv("CLARIO_MODEL", "clario/gemini-3.7-flash").strip()

print("=" * 60)
print("TEST KONEKSI CLARIOHUB")
print("=" * 60)
print(f"Base URL : {base_url}")
print(f"Model    : {model_name}")
print(f"API Key  : {api_key[:12]}...{api_key[-4:] if len(api_key) > 16 else ''}")
print("=" * 60)

if not api_key or "YOUR_API_KEY" in api_key:
    print("\n[PERINGATAN] CLARIO_API_KEY belum diisi di file .env!")
    print("Silakan buka file .env dan isi CLARIO_API_KEY dengan key dari https://clariohub.id/dashboard")
    sys.exit(1)

client = OpenAI(base_url=base_url, api_key=api_key)

# 1. Cek daftar model yang tersedia
print("\n[1/2] Mengecek daftar model aktif di Clario...")
try:
    models = client.models.list()
    model_ids = [m.id for m in models.data]
    gemini_models = [m for m in model_ids if "gemini" in m.lower()]
    print(f"Total model tersedia: {len(model_ids)}")
    print("Model Gemini yang terdeteksi:")
    for gm in gemini_models:
        prefix = "-> [DIPILIH] " if gm == model_name else "   "
        print(f"{prefix}{gm}")
except Exception as e:
    print(f"[Warning] Gagal mengambil list model: {e}")

# 2. Test chat completion
print(f"\n[2/2] Mengirim pesan uji coba ke model `{model_name}`...")
try:
    t0 = time.time()
    resp = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": "Anda adalah asisten AI triase."},
            {"role": "user", "content": "Tes satu kata: apakah sistem aktif?"}
        ],
        temperature=0.1,
        max_tokens=20
    )
    lat = time.time() - t0
    reply = resp.choices[0].message.content.strip()
    print(f"[BERHASIL] Respons diterima dalam {lat:.2f}s:")
    print(f"Output: \"{reply}\"")
    print(f"Token : {resp.usage.prompt_tokens} input, {resp.usage.completion_tokens} output")
    print("\nKoneksi ClarioHub siap digunakan untuk pipeline tesis!")
except Exception as e:
    print(f"\n[GAGAL] Error saat request ke model: {e}")
    print("\nTips: Pastikan model ID sama persis dengan yang ada di daftar model Clario di atas.")


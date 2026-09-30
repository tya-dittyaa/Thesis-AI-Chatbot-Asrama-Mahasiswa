"""
API Key Manager — Multi-Key Load Balancer & Rotation untuk Thesis Pipeline
==========================================================================
Membaca key dari .env (GEMINI_API_KEY, GEMINI_API_KEY_2, GEMINI_API_KEY_3).
Mendukung:
- Random load balancing antar key aktif untuk mendistribusikan RPM & RPD secara merata.
- Auto-failover / rotation ketika salah satu key kena rate limit (429) atau kuota habis.
- Client caching agar efisien tanpa instansiasi berulang.
"""

import os
import time
import random
from typing import List, Set, Optional
from dotenv import load_dotenv

try:
    from google import genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


class ApiKeyManager:
    def __init__(self, env_path: Optional[str] = None):
        if env_path:
            load_dotenv(dotenv_path=env_path)
        else:
            load_dotenv()

        # Kumpulkan semua key yang tersedia (GEMINI_API_KEY, GEMINI_API_KEY_2, GEMINI_API_KEY_3, dst.)
        self.keys: List[str] = []
        val = os.getenv("GEMINI_API_KEY", "").strip()
        if val and val != "your_gemini_api_key_here" and not val.startswith("#"):
            self.keys.append(val)

        for i in range(2, 21):
            val = os.getenv(f"GEMINI_API_KEY_{i}", "").strip()
            if val and val != "your_gemini_api_key_here" and not val.startswith("#"):
                self.keys.append(val)

        if not self.keys:
            raise ValueError(
                "Tidak ada API key ditemukan!\n"
                "Tambahkan GEMINI_API_KEY di file .env"
            )

        if not GENAI_AVAILABLE:
            raise ImportError("google-genai belum terinstal.")

        self.clients = [genai.Client(api_key=k) for k in self.keys]
        self.current_idx = random.randint(0, len(self.keys) - 1)
        self.exhausted: Set[int] = set()

        print(f"[ApiKeyManager] {len(self.keys)} key aktif terdeteksi. Mode: RANDOM LOAD BALANCING.")

    @property
    def current_key(self) -> str:
        return self.keys[self.current_idx]

    def get_client(self, randomize: bool = True):
        """Kembalikan genai.Client aktif. Jika randomize=True, pilih acak dari key yang tersedia."""
        available = [i for i in range(len(self.keys)) if i not in self.exhausted]
        if not available:
            # Semua key exhausted — tunggu dan reset
            all_exhausted_wait = 60
            print(f"\n[ApiKeyManager] ⚠️  SEMUA KEY ({len(self.keys)}) KENA RATE LIMIT!")
            print(f"  Tunggu {all_exhausted_wait}s lalu reset semua key...")
            time.sleep(all_exhausted_wait)
            self.exhausted.clear()
            available = list(range(len(self.keys)))

        if randomize and len(available) > 1:
            self.current_idx = random.choice(available)
        elif self.current_idx in self.exhausted:
            self.current_idx = available[0]

        return self.clients[self.current_idx]

    def get_random_client(self):
        """Alias eksplisit untuk mengambil client acak."""
        return self.get_client(randomize=True)

    def rotate(self, wait_sec: int = 2):
        """
        Tandai key saat ini sebagai exhausted, lalu pilih key lain yang masih tersedia.
        """
        self.exhausted.add(self.current_idx)
        print(f"\n[ApiKeyManager] Key #{self.current_idx + 1} kena rate limit / exhausted.")
        available = [i for i in range(len(self.keys)) if i not in self.exhausted]
        
        if available:
            self.current_idx = random.choice(available)
            print(f"[ApiKeyManager] Berpindah ke Key #{self.current_idx + 1} ({len(available)}/{len(self.keys)} keys aktif). Tunggu {wait_sec}s...")
            time.sleep(wait_sec)
            return self.clients[self.current_idx]
        else:
            return self.get_client(randomize=True)

    def status(self) -> str:
        return (
            f"ApiKeyManager: {len(self.keys)} keys, "
            f"aktif=#{self.current_idx + 1}, "
            f"exhausted={[i+1 for i in self.exhausted]}"
        )

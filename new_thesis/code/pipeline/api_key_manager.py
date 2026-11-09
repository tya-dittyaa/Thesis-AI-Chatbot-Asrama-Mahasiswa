"""
API Key Manager — Thread-Safe Multi-Key Load Balancer & Rate Pacer
==================================================================
Mendukung:
- Thread-safe round-robin load balancing antar key aktif.
- Per-key rate pacing (default 4.15s antar request pada key yang sama = ~14.4 RPM/key,
  aman di bawah batas 15 RPM Free Tier).
- Auto-failover / rotation ketika salah satu key kena 429 (kuota harian RPD habis) atau invalid.
"""

import os
import sys
import time
import threading
import warnings
from typing import List, Set, Optional

warnings.filterwarnings("ignore", message=".*automatic function calling.*")
warnings.filterwarnings("ignore", category=UserWarning, module="google.genai")

from dotenv import load_dotenv
from google import genai


class ApiKeyManager:
    def __init__(self, env_path: Optional[str] = None, min_interval_per_key: float = 4.15):
        if env_path:
            load_dotenv(dotenv_path=env_path, override=True)
        else:
            load_dotenv(override=True)

        self.keys: List[str] = []
        val = os.getenv("GEMINI_API_KEY", "").strip()
        if val and val != "your_gemini_api_key_here" and not val.startswith("#"):
            self.keys.append(val)

        for i in range(2, 21):
            val = os.getenv(f"GEMINI_API_KEY_{i}", "").strip()
            if val and val != "your_gemini_api_key_here" and not val.startswith("#"):
                self.keys.append(val)

        if not self.keys:
            raise ValueError("Tidak ada API key ditemukan di .env!")

        self.clients = [genai.Client(api_key=k) for k in self.keys]
        self.min_interval = min_interval_per_key
        self.last_used = [0.0 for _ in self.keys]
        self.exhausted: Set[int] = set()
        self.daily_exhausted: Set[int] = set()
        self.invalid: Set[int] = set()
        self.current_idx = 0
        self.lock = threading.Lock()

        print(f"[ApiKeyManager] {len(self.keys)} key aktif terdeteksi. Mode: THREAD-SAFE PACED LOAD BALANCING.")

    def acquire_client_with_index(self) -> tuple[int, genai.Client]:
        """Pilih key yang paling siap dan tunggu di luar lock jika belum mencapai min_interval."""
        while True:
            with self.lock:
                available = [i for i in range(len(self.keys)) if i not in self.exhausted and i not in self.invalid and i not in self.daily_exhausted]
                if not available:
                    valid_keys = [i for i in range(len(self.keys)) if i not in self.invalid and i not in self.daily_exhausted]
                    if not valid_keys:
                        raise RuntimeError(f"Semua {len(self.keys)} API key kuota harian habis (RPD limit) atau invalid!")
                    print(f"\n[ApiKeyManager] Semua key aktif ({len(valid_keys)}) kena RPM pacing. Tunggu reset...")
                    self.exhausted.clear()
                    available = valid_keys
                    for i in available:
                        self.last_used[i] = time.time() + 5.0

                # Pilih key dengan waktu tunggu paling singkat
                now = time.time()
                best_idx = min(available, key=lambda i: self.last_used[i])
                wait_needed = (self.last_used[best_idx] + self.min_interval) - now
                if wait_needed <= 0:
                    self.last_used[best_idx] = now
                    self.current_idx = best_idx
                    return best_idx, self.clients[best_idx]
                else:
                    # Reserve slot untuk key ini
                    self.last_used[best_idx] = self.last_used[best_idx] + self.min_interval
                    self.current_idx = best_idx
                    client = self.clients[best_idx]

            if wait_needed > 0:
                time.sleep(wait_needed)
            return best_idx, client

    def get_client(self, randomize: bool = False):
        _, client = self.acquire_client_with_index()
        return client

    def get_random_client(self):
        _, client = self.acquire_client_with_index()
        return client

    def mark_invalid(self, idx: Optional[int] = None):
        with self.lock:
            target = idx if idx is not None else self.current_idx
            self.invalid.add(target)
            print(f"\n[ApiKeyManager] Key #{target + 1} ditandai INVALID.")

    def mark_daily_exhausted(self, idx: Optional[int] = None):
        with self.lock:
            target = idx if idx is not None else self.current_idx
            self.daily_exhausted.add(target)
            avail = len([i for i in range(len(self.keys)) if i not in self.daily_exhausted and i not in self.invalid])
            print(f"\n[ApiKeyManager] Key #{target + 1} kuota harian habis (RPD limit), dinonaktifkan ({avail} key tersisa).")

    def rotate(self, wait_sec: int = 1, idx: Optional[int] = None):
        with self.lock:
            target = idx if idx is not None else self.current_idx
            self.exhausted.add(target)
            avail = len([i for i in range(len(self.keys)) if i not in self.exhausted and i not in self.invalid])
            print(f"\n[ApiKeyManager] Key #{target + 1} kena limit, rotasi ({avail} key aktif tersisa).")
        if wait_sec > 0:
            time.sleep(wait_sec)

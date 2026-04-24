import requests
import time

from src.core.cache import load_cache, save_cache
from src.config.config import HEADERS, CACHE_TTL

# -------------------------
# Fetcher with caching
# -------------------------


def fetch(url: str) -> str:
    cache = load_cache()

    key = url  # könyvenként már külön file, nem kell START prefix

    entry = cache.get(key)
    if entry:
        age = time.time() - entry["timestamp"]
        if age < CACHE_TTL:
            # print(f"  [cache] {url}")
            return entry["html"]

    # print(f"  [fetch] {url}")
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    html = r.text

    cache[key] = {
        "timestamp": time.time(),
        "html": html
    }

    save_cache(cache)
    return html
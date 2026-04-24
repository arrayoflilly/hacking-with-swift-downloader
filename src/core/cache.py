# cache.py

import json

from src.config.config import CACHE_DIR, CACHE_PATH


# -------------------------
# Cache tools
# -------------------------

def load_cache() -> dict:
    
    CACHE_DIR.mkdir(exist_ok=True, parents=True)

    if CACHE_PATH.exists():
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_cache(cache: dict):
    CACHE_DIR.mkdir(exist_ok=True, parents=True)

    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)
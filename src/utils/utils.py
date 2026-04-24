# utils.py

import base64
import requests
import shutil
import os

from pathlib import Path
from src.config.config import CACHE_DIR, PDF_DIR

def load_image_base64(path):
    if not Path(path).exists():
        raise FileNotFoundError(f"Cover image not found: {path}")
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def download_file(url: str, out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with requests.get(url, stream=True) as r:
        r.raise_for_status()

        with out_path.open("wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)

    return out_path


def reset_outputs_and_cache():
    for path in [PDF_DIR, CACHE_DIR]:
        if os.path.exists(path):
            shutil.rmtree(path)

    os.makedirs(PDF_DIR, exist_ok=True)
    os.makedirs(CACHE_DIR, exist_ok=True)

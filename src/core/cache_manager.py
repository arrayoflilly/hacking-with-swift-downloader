# cache_manager.py

from pathlib import Path
import hashlib

class CacheManager:
    def __init__(self, base_dir: str):
        self.base = Path(base_dir)
        self.base.mkdir(parents=True, exist_ok=True)

    def _safe_dir(self, name: str) -> Path:
        path = self.base / name
        path.mkdir(parents=True, exist_ok=True)
        return path

    def youtube_dir(self, video_id: str) -> Path:
        return self._safe_dir("youtube") / video_id

    def image_dir(self, image_id: str) -> Path:
        return self._safe_dir("images") / image_id

    def mp4_dir(self, video_id: str) -> Path:
        return self._safe_dir("mp4") / video_id

    def gif_dir(self) -> Path:
        return self._safe_dir("gifs")

    def hash_key(self, url: str) -> str:
        return hashlib.sha256(url.encode()).hexdigest()[:16]
    
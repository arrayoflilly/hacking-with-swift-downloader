import re
from bs4 import Tag

from src.core.cache_manager import CacheManager
from src.utils.utils import download_file

YOUTUBE_EMBED_RE = re.compile(r"(?:youtube\.com|youtube-nocookie\.com)/embed/([a-zA-Z0-9_-]+)")
YOUTUBE_WATCH_RE = re.compile(r"(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]+)")


def _extract_video_id(src: str) -> str | None:
    match = YOUTUBE_EMBED_RE.search(src) or YOUTUBE_WATCH_RE.search(src)
    if not match:
        return None
    return match.group(1)


def extract_youtube_thumbnail(element: Tag, cache: CacheManager):
    iframe = element
    if not isinstance(iframe, Tag):
        return None

    src = iframe.get("src")
    # print("SRC:", src)

    if isinstance(src, list):
        src = src[0] if src else None

    if not isinstance(src, str) or not src.strip():
        return None

    video_id = _extract_video_id(src)
    if not video_id:
        return None

    thumbnail_url = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
    video_url = f"https://www.youtube.com/watch?v={video_id}"

    image_id = cache.hash_key(video_id)
    out_dir = cache.youtube_dir(image_id)
    out_path = out_dir / "thumbnail.jpg"

    if not out_path.exists():
        try:
            download_file(thumbnail_url, out_path)
        except Exception:
            out_path = None

    return {
        "provider": "youtube",
        "id": video_id,
        "src": src,
        "url": video_url,
        "thumbnail_path": str(out_path) if out_path else "",
    }

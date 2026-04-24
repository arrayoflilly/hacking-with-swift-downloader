import re
from bs4 import Tag

from src.utils.utils import download_file
from src.core.cache_manager import CacheManager


VIMEO_RE = re.compile(r"vimeo\.com/(?:video/)?(\d+)")


def extract_vimeo_thumbnail(element: Tag, cache: CacheManager):
    iframe = element
    if not isinstance(iframe, Tag):
        return None

    src = iframe.get("src")
    if not isinstance(src, str) or not src.strip():
        return None

    m = VIMEO_RE.search(src)
    if not m:
        return None

    video_id = m.group(1)

    # Vimeo thumbnail via oEmbed is ideal, but fallback:
    thumb_url = f"https://vumbnail.com/{video_id}.jpg"
    video_url = f"https://vimeo.com/{video_id}"

    image_id = cache.hash_key(video_id)
    out_dir = cache.youtube_dir(image_id)
    out_path = out_dir / "thumbnail.jpg"

    if not out_path.exists():
        try:
            download_file(thumb_url, out_path)
        except Exception:
            return None

    return {
        "provider": "vimeo",
        "id": video_id,
        "src": src,
        "url": video_url,
        "thumbnail_path": str(out_path),
    }

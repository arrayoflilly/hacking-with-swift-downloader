# renderers.py

from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters.html import HtmlFormatter
import base64
import hashlib
from pathlib import Path
from typing import Optional
from src.config.config import CACHE_DIR

try:
    from PIL import Image
except Exception:  # pragma: no cover
    Image = None


_formatter = HtmlFormatter(style="nord", cssclass="code")


def _cache_key_for_path(path: Path) -> str:
    stat = path.stat()
    raw = f"{path.resolve()}:{stat.st_mtime_ns}:{stat.st_size}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _path_to_data_uri(path: str) -> str:
    file_path = Path(path)
    ext = file_path.suffix.lower().lstrip(".")
    mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
            "gif": "image/gif", "webp": "image/webp"}.get(ext, "image/png")

    # Disk cache for data URIs to avoid repeated large in-memory transforms.
    cache_dir = CACHE_DIR / "data_uri"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"{_cache_key_for_path(file_path)}.txt"

    if cache_file.exists():
        return cache_file.read_text(encoding="utf-8")

    data = file_path.read_bytes()
    data_uri = f"data:{mime};base64,{base64.b64encode(data).decode()}"
    cache_file.write_text(data_uri, encoding="utf-8")
    return data_uri


def _intrinsic_size(path: str) -> tuple[Optional[int], Optional[int]]:
    if Image is None:
        return None, None
    try:
        with Image.open(path) as img:
            return int(img.width), int(img.height)
    except Exception:
        return None, None


def _image_style(meta: dict) -> str:
    max_w = meta.get("display_max_width_px") or meta.get("display_width_px")
    max_h = meta.get("display_max_height_px") or meta.get("display_height_px")
    path = meta.get("path") or meta.get("local_path", "")
    iw, ih = _intrinsic_size(path) if isinstance(path, str) and path else (None, None)
    if iw:
        max_w = min(int(max_w), iw) if max_w else iw
    if ih:
        max_h = min(int(max_h), ih) if max_h else ih

    bits = []
    if max_w:
        bits.append(f"max-width:min(88%, {int(max_w)}px)")
    if max_h:
        bits.append(f"max-height:min(62vh, {int(max_h)}px)")
    bits.append("width:auto")
    bits.append("height:auto")
    return ";".join(bits)


def render_code(code: str) -> str:
    highlighted = highlight(
        code,
        get_lexer_by_name("swift"),
        _formatter,
    )
    return f"<div class='code'>{highlighted}</div>"


def render_image(meta: dict) -> str:
    path = meta.get("path") or meta.get("local_path", "")
    src = meta.get("src") or ""
    alt = meta.get("alt", "")
    style = _image_style(meta)

    if path and Path(path).exists():
        data_uri = _path_to_data_uri(path)
        return f'<div class="asset image"><img src="{data_uri}" alt="{alt}" style="{style}" /></div>'

    if src:
        return f'<div class="asset image"><img src="{src}" alt="{alt}" style="{style}" /></div>'

    return ""


def render_youtube(meta: dict) -> str:
    assets = meta.get("assets") or {}

    thumb_path = (
        meta.get("thumbnail_path")
        or assets.get("thumbnail")
        or meta.get("thumbnail")
        or ""
    )

    url = (
        meta.get("url")
        or assets.get("url")
        or ""
    )

    if not thumb_path:
        return f'<div class="asset youtube"><a href="{url}">{url}</a></div>'

    # ha file path
    if isinstance(thumb_path, str) and Path(thumb_path).exists():
        data_uri = _path_to_data_uri(thumb_path)
    else:
        # ha már URL vagy data URI
        data_uri = thumb_path

    return f'''<div class="asset youtube">
    <a href="{url}" target="_blank">
        <img src="{data_uri}" alt="YouTube thumbnail" />
    </a>
    <div style="text-align:center;font-size:10pt;margin-top:4px;">
        <a href="{url}">Watch on YouTube →</a>
    </div>
</div>'''


def render_video_link(meta: dict) -> str:
    provider = (meta.get("provider") or "video").strip().title()
    url = meta.get("url") or meta.get("src") or ""
    thumb_path = meta.get("thumbnail_path") or ""

    if not url:
        return ""

    if thumb_path and isinstance(thumb_path, str) and Path(thumb_path).exists():
        thumb_src = _path_to_data_uri(thumb_path)
        image_html = f'<img class="thumb-rounded" src="{thumb_src}" alt="{provider} thumbnail" />'
    else:
        image_html = f'<div style="padding:16px;border:1px solid #ddd;border-radius:8px;">{provider} video</div>'

    return f'''<div class="asset video-link">
    <a href="{url}" target="_blank">
        {image_html}
    </a>
    <div style="text-align:center;font-size:10pt;margin-top:4px;">
        <a href="{url}">Open {provider} video</a>
    </div>
</div>'''


def render_video_frames(meta: dict) -> str:
    frames = (meta.get("frames", []) or [])[:4]
    if not frames:
        return ""
    imgs = "\n".join(
        f'<img src="{_path_to_data_uri(f)}" />'
        for f in frames
        if Path(f).exists()
    )
    return f'<div class="asset video-frames">{imgs}</div>'

def render_inline(tokens):
    html = []

    for t, v in tokens:
        if t == "text":
            html.append(v)
        elif t == "inline_code":
            html.append(f"<code>{v}</code>")

    return "".join(html)

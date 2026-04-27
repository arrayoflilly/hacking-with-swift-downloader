import re
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from src.core.cache_manager import CacheManager
from src.config.config import START, BASE
from src.media.mp4 import extract_mp4
from src.media.vimeo import extract_vimeo_thumbnail
from src.media.youtube import extract_youtube_thumbnail
from src.utils.utils import download_file


_MEDIA_CONTAINER_TAGS = {"p", "div", "figure", "picture"}


def _parse_px(value: str) -> Optional[int]:
    m = re.search(r"(\d+(?:\.\d+)?)\s*px", value.lower())
    if not m:
        return None
    try:
        return int(float(m.group(1)))
    except ValueError:
        return None


def _extract_size_hints(img: Tag) -> dict:
    hints: dict = {}

    width_attr = img.get("width")
    height_attr = img.get("height")
    if isinstance(width_attr, str) and width_attr.strip().isdigit():
        hints["display_width_px"] = int(width_attr.strip())
    if isinstance(height_attr, str) and height_attr.strip().isdigit():
        hints["display_height_px"] = int(height_attr.strip())

    style = img.get("style")
    if isinstance(style, str) and style.strip():
        for part in style.split(";"):
            piece = part.strip()
            if ":" not in piece:
                continue
            key, raw_val = piece.split(":", 1)
            key = key.strip().lower()
            val = raw_val.strip()
            px = _parse_px(val)
            if px is None:
                continue
            if key == "width":
                hints["display_width_px"] = px
            elif key == "height":
                hints["display_height_px"] = px
            elif key == "max-width":
                hints["display_max_width_px"] = px
            elif key == "max-height":
                hints["display_max_height_px"] = px

    return hints


def _best_src_from_srcset(srcset: str) -> Optional[str]:
    candidates = []
    for part in srcset.split(","):
        item = part.strip()
        if not item:
            continue
        chunks = item.split()
        url = chunks[0]
        score = 1.0
        if len(chunks) > 1:
            marker = chunks[1].lower()
            if marker.endswith("x"):
                try:
                    score = float(marker[:-1])
                except ValueError:
                    score = 1.0
            elif marker.endswith("w"):
                try:
                    score = float(marker[:-1]) / 100.0
                except ValueError:
                    score = 1.0
        candidates.append((score, url))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


def get_links(html: str):
    soup = BeautifulSoup(html, "html.parser")

    seen = set()
    items = []

    for el in soup.find_all(True):
        if el.name == "h2":
            txt = el.get_text(strip=True)
            if txt:
                items.append(("chapter", txt))
            continue

        if el.name != "a":
            continue

        href = el.get("href")
        if not href:
            continue

        if START in str(href):
            full = urljoin(BASE, str(href))
            if full.rstrip("/") == f"{BASE}{START}".rstrip("/"):
                continue
            if full not in seen:
                seen.add(full)
                title = el.get_text(strip=True)
                items.append(("link", title, full))

    return items


def _infer_media_extension(url: str, default: str = ".png") -> str:
    suffix = Path(url.split("?")[0]).suffix.lower()
    if suffix in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}:
        return suffix
    return default


def _resolve_image_src(src: str, cache: CacheManager) -> Optional[str]:
    full_url = urljoin(BASE, src)
    image_id = cache.hash_key(full_url)
    ext = _infer_media_extension(full_url)
    out_dir = cache.image_dir(image_id)
    out_path = out_dir / f"image{ext}"

    if not out_path.exists():
        try:
            download_file(full_url, out_path)
        except Exception:
            return None

    return str(out_path)


def _extract_image_from_tag(tag: Tag, cache: CacheManager) -> Optional[tuple]:
    img = tag if tag.name == "img" else tag.find("img")
    if not isinstance(img, Tag):
        return None

    srcset = img.get("srcset") or img.get("data-srcset")
    src = _best_src_from_srcset(str(srcset)) if isinstance(srcset, str) and srcset.strip() else (img.get("src") or img.get("data-src"))
    if not isinstance(src, str) or not src.strip():
        return None

    local_path = _resolve_image_src(src, cache)
    if not local_path:
        return None

    alt = img.get("alt", "")
    size_hints = _extract_size_hints(img)
    return (
        "image",
        {
            "src": urljoin(BASE, src),
            "path": local_path,
            "alt": alt,
            **size_hints,
        },
    )


def _extract_video_iframe(tag: Tag, cache: CacheManager) -> Optional[tuple]:
    iframe = tag if tag.name == "iframe" else tag.find("iframe")
    if not isinstance(iframe, Tag):
        return None

    src = iframe.get("src") or iframe.get("data-src")
    if not isinstance(src, str) or not src.strip():
        return None

    if "youtube.com" in src or "youtu.be" in src or "youtube-nocookie.com" in src:
        yt = extract_youtube_thumbnail(iframe, cache)
        if yt:
            return ("video_frame", yt)

    if "vimeo.com" in src:
        vm = extract_vimeo_thumbnail(iframe, cache)
        if vm:
            return ("video_frame", vm)

    return (
        "video_frame",
        {
            "provider": "generic",
            "src": src,
            "url": src,
        },
    )


def _find_mp4_url(tag: Tag) -> Optional[str]:
    def _score(url: str) -> int:
        u = url.lower()
        score = 0
        if "@2x" in u or "hd" in u or "1080" in u or "high" in u:
            score += 100
        if "mobile" in u or "small" in u or "low" in u:
            score -= 80
        m = re.search(r"(\d{3,4})p", u)
        if m:
            try:
                score += int(m.group(1))
            except ValueError:
                pass
        return score

    candidates: list[str] = []

    if tag.name == "video":
        src = tag.get("src")
        if isinstance(src, str) and src.strip():
            candidates.append(src)

    for source in tag.find_all("source"):
        src = source.get("src")
        typ = source.get("type", "")

        if isinstance(src, str) and src.strip():
            if ".mp4" in src.lower() or "video/mp4" in str(typ).lower():
                candidates.append(src)

    for a in tag.find_all("a"):
        href = a.get("href")
        if isinstance(href, str) and ".mp4" in href.lower():
            candidates.append(href)

    if candidates:
        return max(candidates, key=_score)

    return None


def _extract_mp4_from_tag(tag: Tag, cache: CacheManager) -> Optional[tuple]:
    mp4_src = _find_mp4_url(tag)
    if not mp4_src:
        return None

    mp4_url = urljoin(BASE, mp4_src)
    meta = extract_mp4(mp4_url, cache)
    return ("video_frame", meta)


def _extract_embedded_media(tag: Tag, cache: CacheManager) -> list[tuple]:
    media_items = []

    iframe_item = _extract_video_iframe(tag, cache)
    if iframe_item:
        media_items.append(iframe_item)

    mp4_item = _extract_mp4_from_tag(tag, cache)
    if mp4_item:
        media_items.append(mp4_item)

    image_item = _extract_image_from_tag(tag, cache)
    if image_item:
        media_items.append(image_item)

    deduped = []
    seen = set()

    for item in media_items:
        marker = repr(item)
        if marker not in seen:
            seen.add(marker)
            deduped.append(item)

    return deduped


def _is_content_started(el: Tag, started: bool) -> bool:
    classes = el.get("class") or []

    if "lead" in classes:
        return True

    if "hws-main-title" in classes:
        return True

    return started


def _is_ebtc_footer_block(tag: Tag) -> bool:
    text = tag.get_text(" ", strip=True).lower()
    if "everything but the code" in text:
        return True

    for img in tag.find_all("img"):
        src = img.get("src")
        if isinstance(src, str) and "ebtc-footer" in src:
            return True

    for a in tag.find_all("a"):
        href = a.get("href")
        if isinstance(href, str) and "/store/everything-but-the-code" in href:
            return True

    return False


def _extract_xcode_project_link(tag: Tag) -> Optional[tuple]:
    for a in tag.find_all("a"):
        href = a.get("href")
        text = a.get_text(" ", strip=True)
        if not isinstance(href, str):
            continue
        if "download this as an xcode project" in text.lower():
            full = urljoin(BASE, href)
            return ("p", f'<a href="{full}">Download this as an Xcode project</a>')
    return None


def extract(html: str, cache: CacheManager):
    soup = BeautifulSoup(html, "html.parser")
    current_section: Optional[dict] = None

    container = soup.select_one("div.col-lg-9")
    if not container:
        return []

    out = []
    started = False
    first_heading_skipped = False

    for el in container.children:
        if not isinstance(el, Tag):
            continue

        classes = el.get("class") or []

        if "hws-sponsor" in classes:
            continue

        if not started:
            started = _is_content_started(el, started)
            continue

        if _is_ebtc_footer_block(el):
            break

        if el.name == "h3":
            txt = el.get_text(" ", strip=True)
            if "similar" in txt.lower():
                current_section = {
                    "type": "similar_articles",
                    "title": txt,
                    "items": [],
                }

        if el.name == "ul" and current_section:
            for li in el.find_all("li", recursive=False):
                a = li.find("a")
                if not a:
                    continue

                href = a.get("href")
                if isinstance(href, str) and href.strip():
                    current_section["items"].append(
                        {
                            "title": a.get_text(strip=True),
                            "url": urljoin(BASE, href),
                        }
                    )

            out.append(("similar_articles", current_section))
            current_section = None
            break

        if el.name in {"img", "iframe", "video", "picture", "figure"}:
            out.extend(_extract_embedded_media(el, cache))
            continue

        if el.name in _MEDIA_CONTAINER_TAGS and el.find(["img", "iframe", "video", "picture", "figure", "source"]):
            xcode_link = _extract_xcode_project_link(el)
            if xcode_link:
                out.append(xcode_link)
                continue

            media_items = _extract_embedded_media(el, cache)
            if media_items:
                out.extend(media_items)

            plain_text = el.get_text(" ", strip=True)
            if plain_text and re.search(r"\w", plain_text):
                out.append(("p", plain_text))
            continue

        if el.name == "p":
            if el.find("a", href="/about"):
                continue
            if el.find("em"):
                em  = el.find("em")
                emphasized_text = em.get_text(" ", strip=True) # type: ignore
                if re.search(r"updated?\s+for", emphasized_text, re.IGNORECASE):
                    continue
            
            xcode_link = _extract_xcode_project_link(el)
            
            if xcode_link:
                out.append(xcode_link)
                continue

            inner_html = "".join(str(child) for child in el.children).strip()
            if inner_html:
                out.append(("p", inner_html))
            continue

        if el.name in ["h1", "h2", "h3"] or el.name.startswith("h"):
            if current_section and current_section.get("type") == "similar_articles":
                continue

            txt = el.get_text(" ", strip=True)
            if txt:
                if not first_heading_skipped:
                    first_heading_skipped = True
                    continue
                out.append((el.name, txt))
            continue

        if el.name == "pre":
            out.append(("code", el.get_text("\n", strip=False)))
            continue

        if el.name in ["ul", "ol"]:
            if current_section and current_section.get("type") == "similar_articles":
                continue

            items = []
            for li in el.find_all("li", recursive=False):
                inner_html = "".join(str(child) for child in li.children).strip()
                if inner_html:
                    items.append(inner_html)

            if items:
                out.append(
                    (
                        "list",
                        {
                            "ordered": el.name == "ol",
                            "items": items,
                        },
                    )
                )
            continue

        if el.name == "blockquote":
            inner_html = "".join(str(child) for child in el.children).strip()
            if inner_html:
                out.append(("quote", inner_html))
            continue

    return out

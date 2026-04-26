# src/run.py

from src.config.config import BASE, START, DATE_STR, TITLE, AUTHOR, PDF_PATH, CACHE_DIR, BOOK_ID
from src.pipeline.fetcher import fetch
from src.pipeline.extract import get_links, extract
from src.pipeline.normalizer import normalize
from src.core.chapter_id_injector import inject_chapter_ids
from src.rendering.builder import build_html
from src.rendering.renderer import html_to_pdf
from src.core.cache_manager import CacheManager
from src.core.logger import log_reset
from src.utils.utils import reset_outputs_and_cache
from src.crawlers.ios_swiftui import get_links_ios_swiftui, extract_ios_swiftui
from src.crawlers.sixty import get_links_sixty, extract_sixty
from src.crawlers.hundred import get_links_hundred, extract_hundred_day

cache = CacheManager(str(CACHE_DIR))

PASSTHROUGH_TYPES = {"chapter", "p", "list", "section_title", "heading", "quote", "code"}

def get_crawler(book_id: int):
    if book_id == 0:
        return get_links_ios_swiftui, extract_ios_swiftui, False
    if book_id == 2:
        return get_links_sixty, extract_sixty, True
    if book_id == 7:
        return get_links_hundred, extract_hundred_day, False
    return get_links, lambda html, url, cache: extract(html, cache), True

# -------------------------
# main pipeline
# -------------------------

def run():
    # Debug reset only once, otherwise previously downloaded assets disappear.
    reset_outputs_and_cache()
    log_reset()

    get_links_fn, extract_fn, inject_section_title = get_crawler(BOOK_ID)

    index_html = fetch(BASE + START)
    items = get_links_fn(index_html)

    all_sections = []
    i = 1
    
    toc = []  # List of (id, title) for TOC generation

    for item in items:
        if item[0] in PASSTHROUGH_TYPES:
            all_sections.append(item)
            continue

        _, link_text, url = item

        print(f"[{i}] {link_text}")

        html = fetch(url)
        content = extract_fn(html, url, cache)

        if inject_section_title:
            anchor = f"section-{i}"
            all_sections.append(("section_title", link_text.strip(), {"id": anchor}))

        all_sections.extend(content)
        i += 1

    nodes = normalize(all_sections)
    nodes, toc = inject_chapter_ids(nodes)

    youtube_count = sum(
        1 for n in nodes
        if n.get("type") == "video_frame" and (n.get("meta") or {}).get("provider") == "youtube"
    )
    vimeo_count = sum(
        1 for n in nodes
        if n.get("type") == "video_frame" and (n.get("meta") or {}).get("provider") == "vimeo"
    )
    mp4_count = sum(
        1 for n in nodes
        if n.get("type") == "video_frame" and (n.get("meta") or {}).get("provider") == "mp4"
    )
    image_count = sum(1 for n in nodes if n.get("type") == "image")
    print(f"[summary] images={image_count} youtube={youtube_count} vimeo={vimeo_count} mp4={mp4_count}")

    html_doc = build_html(nodes, TITLE, DATE_STR, AUTHOR)
    html_to_pdf(html_doc, str(PDF_PATH))


if __name__ == "__main__":
    run()
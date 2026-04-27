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
from src.crawlers.sixty import get_links_sixty, extract_sixty
from src.crawlers.hundred import get_links_hundred, extract_hundred_day, _extract_glossary
from src.core.logger import log

cache = CacheManager(str(CACHE_DIR))

# Ezek a tuple típusok közvetlenül kerülnek all_sections-be,
# nem igényelnek URL letöltést.
PASSTHROUGH_TYPES = {"chapter", "p", "list", "section_title", "subsection_title", "sub_subsection_title", "subpage_header", "heading", "quote", "code"}


def get_crawler(book_id: int):
    """
    Visszaad: (get_links_fn, extract_fn, inject_section_title)

    inject_section_title: True  → run.py injektálja a section_title-t fetch után
                          False → a crawler maga adja ki a section_title-t
    """
    
    if book_id == 2:   # Swift in Sixty Seconds
        return get_links_sixty, extract_sixty, True
    if book_id == 7 or book_id == 8:   # 100 Days of Swift
        return get_links_hundred, extract_hundred_day, False
    # book_id == 1: Swift for Complete Beginners
    return get_links, lambda html, url, cache: extract(html, cache), True


# -------------------------
# main pipeline
# -------------------------

def run():
    # Debug reset only once, otherwise previously downloaded assets disappear.
    # reset_outputs_and_cache()
    log_reset()

    get_links_fn, extract_fn, inject_section_title = get_crawler(BOOK_ID)

    index_html = fetch(BASE + START)
    items = get_links_fn(index_html)

    all_sections = []
    i = 1

    for item in items:
        # Passthrough elemek — nem URL-ek, közvetlenül all_sections-be
        if item[0] in PASSTHROUGH_TYPES:
            all_sections.append(item)
            continue

        # glossary_fetch: azonnal letöltjük és beinjektáljuk, sorszám nélkül
        if item[0] == "glossary_fetch":
            _, _, url = item
            log(f"Fetching glossary from {url} (run)")
            glossary_html = fetch(url)
            all_sections.extend(_extract_glossary(glossary_html))
            continue

        # link tuple: ("link", title, url)
        _, link_text, url = item

        print(f"[{i}] {link_text}")
        log(f"{i} {link_text} ({url})")

        html = fetch(url)
        content = extract_fn(html, url, cache)

        # inject_section_title=True esetén a run.py injektálja az oldal boundary-t
        # inject_section_title=False esetén a crawler maga adja ki (pl. hundred)
        if inject_section_title:
            anchor = f"section-{i}"
            all_sections.append(("section_title", link_text.strip(), {"id": anchor}))
        else:
            # A crawler adja ki a section_title-t az aloldal H1-jéből,
            # de a TOC-ban a főoldali lista szövegét kell mutatni.
            # Az első section_title tuple toc_title mezőjét patcheljük.
            for j, c in enumerate(content):
                if isinstance(c, tuple) and len(c) >= 3 and c[0] == "section_title":
                    meta = dict(c[2]) if isinstance(c[2], dict) else {}
                    meta["toc_title"] = link_text.strip()
                    content[j] = (c[0], c[1], meta)
                    break

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
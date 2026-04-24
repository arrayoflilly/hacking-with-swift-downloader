from src.config.config import BASE, START, DATE_STR, TITLE, AUTHOR, PDF_PATH, CACHE_DIR
from src.pipeline.fetcher import fetch
from src.pipeline.extract import get_links, extract
from src.pipeline.normalizer import normalize
from src.core.chapter_id_injector import inject_chapter_ids
from src.rendering.builder import build_html
from src.rendering.renderer import html_to_pdf
from src.core.cache_manager import CacheManager
from src.core.logger import log_reset
from src.utils.utils import reset_outputs_and_cache

cache = CacheManager(str(CACHE_DIR))

# -------------------------
# main pipeline
# -------------------------

def run():
    # Debug reset only once, otherwise previously downloaded assets disappear.
    # reset_outputs_and_cache()
    log_reset()

    index_html = fetch(BASE + START)
    items = get_links(index_html)

    all_sections = []
    i = 1

    for item in items:

        if item[0] == "chapter":
            all_sections.append(("chapter", item[1]))
            continue

        _, link_text, url = item

        print(f"[{i}] {link_text}")

        html = fetch(url)
        content = extract(html, cache)

        chapter_title = link_text.strip()
        anchor = f"section-{i}"

        all_sections.append(("section_title", chapter_title, {"id": anchor}))

        all_sections.extend(content)

        i += 1

    # ONLY ONE NORMALIZATION STEP
    nodes = normalize(all_sections)
    nodes, toc = inject_chapter_ids(nodes)

    # Quick extraction summary for verification.
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

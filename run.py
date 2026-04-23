from config import BASE, START, DATE_STR, TITLE, AUTHOR, PDF_PATH
from fetcher import fetch
from extract import get_links, extract
from builder import build_html
from renderer import html_to_pdf

# -------------------------
# main pipeline
# -------------------------

def run():
    index_html = fetch(BASE + START)
    items = get_links(index_html)

    all_sections = []

    toc = []
    date_str = DATE_STR
    title = TITLE
    author = AUTHOR

    i = 1

    for item in items:

        # ---- CHAPTER TITLE ----
        if item[0] == "chapter":
            chapter_name = item[1]

            # chapter megjelenik külön oldalon
            all_sections.append(("chapter", chapter_name))

            # TOC-ban csak szekcióválasztó
            toc.append(("chapter", chapter_name))
            continue

        # ---- LINK ----
        _, link_text, url = item

        print(f"[{i}] {url}")

        html = fetch(url)
        content = extract(html)

        print("CONTENT SIZE:", len(content))

        # FONTOS: NINCS slug, NINCS case módosítás
        chapter_title = link_text.strip()
        anchor = f"section-{i}"

        # TOC ENTRY (ugyanaz a cím, amit a link ad)
        toc.append(("link", chapter_title, anchor))

        # SECTION HEADER
        all_sections.append(("h_main", chapter_title, anchor))        
        all_sections.extend(content)

        i += 1

    html_doc = build_html(all_sections, toc, title, date_str, author)
    html_to_pdf(html_doc, str(PDF_PATH))
    
if __name__ == "__main__":
    run()
import requests
import base64
import json
import time
from pathlib import Path

from bs4 import BeautifulSoup, Tag
from urllib.parse import urljoin

from pygments import highlight
from pygments.lexers import SwiftLexer # type: ignore
from pygments.formatters.html import HtmlFormatter

from playwright.sync_api import sync_playwright

BASE = "https://www.hackingwithswift.com"
START = "/quick-start/swiftdata"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

IMG_PATH = Path(__file__).parent / "img" / "cover 3.png"

FONT_ROBOTO = Path("font/Roboto-VariableFont_wdth,wght.ttf").absolute().as_uri()
FONT_ROBOTO_ITALIC = Path("font/Roboto-Italic-VariableFont_wdth,wght.ttf").absolute().as_uri()
FONT_SLAB = Path("font/RobotoSlab-VariableFont_wght.ttf").absolute().as_uri()
FONT_MONTSERRAT = Path("font/Montserrat-VariableFont_wght.ttf").absolute().as_uri()

AUTHOR = "Paul Hudson (Hacking with Swift)"
TITLE = "SwiftData by Example"
DATE_STR = "Updated for Xcode 16.4"

PDF_PATH = "swiftdata-by-example.pdf"

CACHE_PATH = Path(__file__).parent / "cache.json"
CACHE_TTL = 60 * 60 * 24  # 24 óra másodpercben
# -------------------------
# utils
# -------------------------

def slug_to_title(slug: str) -> str:
    return slug.replace("-", " ")


def load_cache() -> dict:
    if CACHE_PATH.exists():
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cache(cache: dict):
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def fetch(url: str) -> str:
    cache = load_cache()

    entry = cache.get(url)
    if entry:
        age = time.time() - entry["timestamp"]
        if age < CACHE_TTL:
            print(f"  [cache] {url}")
            return entry["html"]

    print(f"  [fetch] {url}")
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    html = r.text

    cache[url] = {
        "timestamp": time.time(),
        "html": html
    }
    save_cache(cache)

    return html


def load_image_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


# -------------------------
# link extraction
# -------------------------

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

        if el.name == "a":
            href = el.get("href")

            if not href:
                continue

            if START in str(href):
                full = urljoin(BASE, str(href))

                if full not in seen:
                    seen.add(full)
                    title = el.get_text(strip=True)
                    items.append(("link", title, full))

    return items


# -------------------------
# content extraction
# -------------------------

def extract(html: str):
    soup = BeautifulSoup(html, "html.parser")

    container = soup.select_one("div.col-lg-9")
    if not container:
        return []

    out = []
    started = False

    for el in container.children:

        if not isinstance(el, Tag):
            continue

        classes = el.get("class") or []

        if "lead" in classes:
            started = True
            continue

        if "hws-sponsor" in classes:
            break

        if not started:
            continue

        if el.name == "p":
            for a in el.find_all("a", href=True):
                href = a.get("href")
                if isinstance(href, str):
                    a["href"] = urljoin(BASE, href)

            inner_html = "".join(str(child) for child in el.children).strip()
            if inner_html:
                out.append(("p", inner_html))

        elif el.name in ["h1", "h2", "h3"]:
            txt = el.get_text(" ", strip=True)
            if txt:
                out.append(("h", txt, None))

        elif el.name == "pre":
            out.append(("code", el.get_text("\n", strip=False)))

        elif el.name == "ul":
            for li in el.find_all("li", recursive=False):
                li_html = "".join(str(child) for child in li.children).strip()
                if li_html:
                    out.append(("li", li_html))

        elif el.name == "blockquote":
            inner_html = "".join(str(child) for child in el.children).strip()
            if inner_html:
                out.append(("quote", inner_html))

    return out


# -------------------------
# HTML builder
# -------------------------

from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters.html import HtmlFormatter


def build_html(all_sections, toc_items, title, date_str, author):
    formatter = HtmlFormatter(style="nord", cssclass="code")
    base_css = formatter.get_style_defs(".code")

    img_base64 = load_image_base64(IMG_PATH)

    custom_css = f"""
    @font-face {{
        font-family: 'Roboto';
        src: url('{FONT_ROBOTO}');
        font-weight: 100 900;
    }}

    @font-face {{
        font-family: 'Roboto';
        src: url('{FONT_ROBOTO_ITALIC}');
        font-style: italic;
        font-weight: 100 900;
    }}

    @font-face {{
        font-family: 'Roboto Slab';
        src: url('{FONT_SLAB}');
        font-weight: 100 900;
    }}

    @font-face {{
        font-family: 'Montserrat';
        src: url('{FONT_MONTSERRAT}');
        font-weight: 100 900;
    }}

    """ + base_css + """

    body {
        font-family: 'Roboto', sans-serif;
        margin: 0;
        padding: 0;
        line-height: 1.4;
        font-size: 12pt;
    }

    @page {
        margin: 20mm;
    }

    .cover {
        width: 100%;
        height: 100vh;
        background: #363636;
        color: white;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
        page-break-after: always;
    }

    .cover img {
        width: 300px;
        height: auto;
        margin-bottom: 20px;
        display: block;
    }

    .cover h1 {
        font-size: 34pt;
        margin: 0;
    }

    .cover .meta {
        margin-top: 10px;
        font-size: 11pt;
        color: #ddd;
    }

    .chapter-page {
        height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
        page-break-before: always;
        page-break-after: always;
        text-align: center;
    }

    .chapter-page h2 {
        font-size: 26pt;
    }

    .toc {
        page-break-after: always;
    }

    .toc h3 {
        margin-top: 16px;
    }

    .toc a {
        display: block;
        margin: 4px 0 4px 12px;
        font-size: 11pt;
        color: #4ea1ff;
        text-decoration: none;
    }

    .section-title {
        page-break-before: always;
        font-size: 20pt;
        margin-bottom: 2.5em;
    }
    
    a {
        font-size: 11pt;
        color: #4ea1ff;
        text-decoration: none;
    }

    p {
        text-align: justify;
    }
    
    code {
        font-family: "JetBrains Mono", monospace;        
        background: #ececec;
        color: #2d2d2d;
        padding: 1px 3px;
        margin: 0 2px;
        border-radius: 2px;
        font-size: 0.9em;
        font-weight: 500;
    }

    .code {
        background: #363636 !important;
        border-radius: 10px;
        overflow-wrap: break-word;
        padding: 0;
        margin: 10px 0;
    }

    .code,
    .code .highlight,
    .code pre {
        -webkit-box-decoration-break: clone;
        box-decoration-break: clone;
    }

    .code pre {
        background: transparent !important;
        margin: 0;
        padding: 20px;
        font-size: 8pt;
        line-height: 1.4;
    }

    blockquote {
        border-left: 4px solid #363636;
        background: #f0f0f0;
        padding: 12px;
        margin: 20px 0;
    }

    """

    html = []
    html.append(f"""
<html>
<head>
<meta charset="utf-8">
<style>{custom_css}</style>
</head>
<body>
""")

    # COVER
    html.append(f"""
<div class="cover">
<img src="data:image/png;base64,{img_base64}" />
<h1>{title}</h1>
<div class="meta">{author}<br>{date_str}</div>
</div>
""")

    # TOC
    html.append("<div class='toc'><h2>Table of Contents</h2>")

    for item in toc_items:
        if item[0] == "chapter":
            html.append(f"<h3>{item[1]}</h3>")
        else:
            _, name, anchor = item
            html.append(f"<a href='#{anchor}'>{name}</a>")

    html.append("</div>")

    # CONTENT
    in_list = False

    for section in all_sections:
        kind = section[0]

        if kind == "chapter":
            if in_list:
                html.append("</ul>")
                in_list = False

            html.append(f"""
<div class="chapter-page">
<h2>{section[1]}</h2>
</div>
""")

        elif kind == "h":
            if in_list:
                html.append("</ul>")
                in_list = False
            html.append(f"<h1 class='section-title' id='{section[2]}'>{section[1]}</h1>")

        elif kind == "p":
            if in_list:
                html.append("</ul>")
                in_list = False
            html.append(f"<p>{section[1]}</p>")

        elif kind == "quote":
            if in_list:
                html.append("</ul>")
                in_list = False
            html.append(f"<blockquote>{section[1]}</blockquote>")

        elif kind == "li":
            if not in_list:
                html.append("<ul>")
                in_list = True
            html.append(f"<li>{section[1]}</li>")

        elif kind == "code":
            if in_list:
                html.append("</ul>")
                in_list = False

            highlighted = highlight(
                section[1],
                get_lexer_by_name("swift"),
                formatter
            )
            html.append(f"<div class='code'>{highlighted}</div>")

    if in_list:
        html.append("</ul>")

    html.append("</body></html>")
    return "\n".join(html)


# -------------------------
# PDF render
# -------------------------

def html_to_pdf(html_str: str, out_path: str):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        page.set_content(html_str, wait_until="networkidle")

        page.pdf(
            path=out_path,
            format="A4",
            print_background=True,
            scale=1.0,
            margin={
                "top": "25mm",
                "bottom": "25mm",
                "left": "20mm",
                "right": "20mm"
            },
            display_header_footer=True,
            header_template=f"""
            <div style="width:100%; font-size:12px; text-align:center; font-family: 'Roboto', sans-serif; color: #000;">
                <span>{TITLE} - Hacking with Swift</span>
                <hr style="border: none; border-top: 1px solid #ccc; margin: 20px 15%;" />
            </div>
            """,
            footer_template="""
            <div style="width:100%; font-size:12px; text-align:center; font-family: 'Roboto', sans-serif; color: #000;">
                <hr style="border: none; border-top: 1px solid #ccc; margin: 20px 15%;" />
                <span class="pageNumber"></span> / <span class="totalPages"></span>
            </div>
            """
        )

        browser.close()


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
        all_sections.append(("h", chapter_title, anchor))
        all_sections.extend(content)

        i += 1

    html_doc = build_html(all_sections, toc, title, date_str, author)
    html_to_pdf(html_doc, PDF_PATH)


if __name__ == "__main__":
    run()
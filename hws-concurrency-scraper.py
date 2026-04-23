import requests
import base64
from pathlib import Path

from bs4 import BeautifulSoup, Tag
from urllib.parse import urljoin

from pygments import highlight
from pygments.lexers import SwiftLexer # type: ignore
from pygments.formatters.html import HtmlFormatter

from playwright.sync_api import sync_playwright

BASE = "https://www.hackingwithswift.com"
START = "/quick-start/concurrency"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

IMG_PATH = Path(__file__).parent / "img" / "cover.png"
IMG_PATH = IMG_PATH.resolve().as_uri()

FONT_ROBOTO = Path("font/Roboto-VariableFont_wdth,wght.ttf").absolute().as_uri()
FONT_ROBOTO_ITALIC = Path("font/Roboto-Italic-VariableFont_wdth,wght.ttf").absolute().as_uri()
FONT_SLAB = Path("font/RobotoSlab-VariableFont_wght.ttf").absolute().as_uri()
FONT_MONTSERRAT = Path("font/Montserrat-VariableFont_wght.ttf").absolute().as_uri()

# -------------------------
# utils
# -------------------------

def slug_to_title(slug: str) -> str:
    return slug.replace("-", " ")


def fetch(url: str) -> str:
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    return r.text


# -------------------------
# link extraction (ORDERED)
# -------------------------

def get_links(html: str):
    soup = BeautifulSoup(html, "html.parser")

    seen = set()
    items = []

    for el in soup.find_all(True):

        # ---- CHAPTER TITLE
        if el.name == "h2":
            txt = el.get_text(strip=True)
            if txt:
                items.append(("chapter", txt))
            continue

        # ---- LINK
        if el.name == "a":
            href = el.get("href")

            if not href:
                continue

            if "/quick-start/concurrency/" in str(href):
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

        # START
        if "lead" in classes:
            started = True
            continue

        # STOP
        if "hws-sponsor" in classes:
            break

        if not started:
            continue

        # --------
        # PARAGRAPH (FIXED)
        # --------
        if el.name == "p":
            for a in el.find_all("a", href=True):
                href = a.get("href")
                if href:
                    href = a.get("href")

                    if isinstance(href, str):
                        a["href"] = urljoin(BASE, href)
            
            inner_html = "".join(str(child) for child in el.children).strip()
            if inner_html:
                out.append(("p", inner_html))

        # --------
        # HEADINGS
        # --------
        elif el.name in ["h1", "h2", "h3"]:
            txt = el.get_text(" ", strip=True)
            if txt:
                out.append(("h", txt, None))  # Anchor will be added later

        # --------
        # CODE
        # --------
        elif el.name == "pre":
            out.append(("code", el.get_text("\n", strip=False)))

        # --------
        # LIST
        # --------
        elif el.name == "ul":
            for li in el.find_all("li", recursive=False):
                li_html = "".join(str(child) for child in li.children).strip()
                if li_html:
                    out.append(("li", li_html))
                    
        # --------
        # BLOCKQUOTE (NEW)
        # --------
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
    img_base64 = load_image_base64("img/cover.png")
    
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
    font-family: 'Roboto', -apple-system, sans-serif;
    margin: 0;
    padding: 0;
    line-height: 1.3;
    font-size: 12pt;
}

h1, h2, h3,
.section-title,
.cover h1,
.chapter-page h2 {
    font-family: 'Roboto Slab', serif;
    font-weight: 600;
}

/* PDF GLOBAL MARGINS RESET */
@page {
    margin: 20mm;
}

/* COVER (FULL BLEED INSIDE PAGE OVERRIDE) */
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
    width: 160px;
    height: auto;
    margin-bottom: 20px;
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

/* CHAPTER PAGE */
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
    font-size: 28pt;
}

/* TOC */
.toc {
    page-break-after: always;
    padding-top: 10px;
}

.toc h2 {
    font-size: 18pt;
    margin-bottom: 16px;
}

.toc h3 {
    margin-top: 18px;
    font-size: 13pt;
    color: #444;
}

.toc a {
    display: block;
    margin: 4px 0 4px 14px;
    font-size: 11pt;
    color: #4ea1ff;
    text-decoration: none;
}

/* CODE */
code {
    font-family: Menlo, Monaco, monospace;
    background: #eeeeee;
    color: #363636;
    padding: 1px 5px;
    margin: 0 2px;
    border-radius: 2px;
    font-size: 0.9em;
    font-weight: 500;
}

.code {
    background: #363636 !important;
    border-radius: 10px;
    overflow: hidden;
}

.code pre {
    background: transparent !important;
    color: #c0caf5;
    line-height: 1.4;
    font-size: 7pt;
    margin-top: 5px;
    margin-bottom: 5px;
    padding: 12px 14px;
    white-space: pre-wrap;
    word-break: break-word;
    box-sizing: border-box;
}

/* TEXT */
.section-title {
    page-break-before: always;
    font-size: 20pt;
    margin-bottom: 10px;
}

h1 {
    font-size: 20pt;
    margin-bottom: 24px;
}

h2 {
    font-size: 18pt;
    margin-bottom: 18px;
}

h3 {
    font-size: 16pt;
    margin-bottom: 12px;
}

p {
    font-size: 12pt;
    text-align: justify;
    hyphens: auto;
    font-weight: 400;
}

strong {
    font-weight: 600;
}

em {
    font-style: italic;
}

li {
    font-size: 12pt;
}

/* LINKS */
a {
    font-size: 10pt;
    color: #4ea1ff;
    text-decoration: none;
}

blockquote {
    border-left: 4px solid #363636;
    border-radius: 0px;
    background: #f0f0f0;
    margin: 50px 0;
    padding: 14px 10px;
    color: #2a2a2a;
    font-style: italic;
}
"""

    html = []
    html.append(f"""
<html>
<head>
<meta charset="utf-8">
<style>
{custom_css}
</style>
</head>
<body>
""")

    # -------------------------
    # COVER
    # -------------------------
    html.append(f"""
<div class="cover">
<img src="data:image/png;base64,{img_base64}" width="400"/>
<h1>{title}</h1>
    <div class="meta">
        Author: {author}<br>
        {date_str}
    </div>
</div>
""")

    # -------------------------
    # TOC
    # -------------------------
    html.append("<div class='toc'>")
    html.append("<h2>Table of Contents</h2>")

    for item in toc_items:
        if item[0] == "chapter":
            html.append(f"<h3>{item[1]}</h3>")
        else:
            _, name, anchor = item
            html.append(f"<a href='#{anchor}'>{name}</a>")

    html.append("</div>")

    # -------------------------
    # CONTENT
    # -------------------------
    in_list = False

    for section in all_sections:
        kind = section[0]

        # CHAPTER PAGE (NO NUMBERS)
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

            anchor = section[2] if len(section) > 2 else ""
            html.append(f"<h1 class='section-title' id='{anchor}'>{section[1]}</h1>")

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
# utils for html builder
# -------------------------
def load_image_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


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
    scale=1.2,   
    margin={
        "top": "20mm",
        "bottom": "20mm",
        "left": "20mm",
        "right": "20mm"
    },
    display_header_footer=True,
    header_template="""
        <div></div>
    """,
    footer_template="""
        <div style="width:100%; font-size:10px; text-align:center; color:#363636;">
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
    date_str = "Updated for Xcode 16.4"
    title = "Swift Concurrency"
    author = "Paul Hudson (Hacking with Swift)"

    i = 1

    for item in items:

        # ---- CHAPTER TITLE ----
        if item[0] == "chapter":
            chapter_name = item[1]
            toc.append(("chapter", chapter_name))
            all_sections.append(("chapter", chapter_name))
            continue

        # ---- LINK ----
        _, _, url = item

        print(f"[{i}] {url}")

        html = fetch(url)
        content = extract(html)

        print("CONTENT SIZE:", len(content))

        slug = url.split("/")[-1]
        chapter_title = slug_to_title(slug)
        anchor = f"section-{i}"

        # TOC ENTRY
        toc.append(("link", f"{chapter_title}", anchor))

        # SECTION HEADER
        all_sections.append(("h", f"{chapter_title}", anchor))
        all_sections.extend(content)

        i += 1

    html_doc = build_html(all_sections, toc, title, date_str, author)
    html_to_pdf(html_doc, "swift_concurrency.pdf")



if __name__ == "__main__":
    run()
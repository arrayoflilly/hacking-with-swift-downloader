import requests
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

# -------------------------
# utils
# -------------------------

def slug_to_title(slug: str) -> str:
    words = slug.replace("-", " ").split()
    return words[0].capitalize() + " " + " ".join(w.lower() for w in words[1:])


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
    ordered = []

    for a in soup.find_all("a", href=True):
        href = a.get("href")

        if not href:
            continue

        if "/quick-start/concurrency/" in str(href):
            full = urljoin(BASE, str(href))

            if full not in seen:
                seen.add(full)
                ordered.append(full)

    return ordered


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
    formatter = HtmlFormatter(style="native", cssclass="code")
    base_css = formatter.get_style_defs(".code")

    custom_css = base_css + """
body {
    font-family: -apple-system, sans-serif;
    max-width: 800px;
    margin: 20px auto;
    line-height: 1.7;
    font-size: 12pt;
}

/* COVER */
.cover {
    height: 100vh;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    page-break-after: always;
    text-align: center;
    padding: 40px;
}

.cover h1 {
    font-size: 36pt;
    margin-bottom: 20px;
}/* COVER */
.cover {
    height: 100vh;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    page-break-after: always;
    text-align: center;
    padding: 40px;
}

/* TOC */
.toc {
    /*
    page-break-after: always;
    */
}

.toc h2 {
    font-size: 18pt;
    margin-bottom: 16px;
}

.toc a {
    display: block;
    margin: 6px 0;
    font-size: 11pt;
    color: #4ea1ff;
    text-decoration: none;
}

.toc a:hover {
    text-decoration: underline;
}

/* CODE */
.code {
    background: #1a1b26 !important;
    border-radius: 10px;
    padding: 14px;
}

.code pre {
    background: transparent !important;
    color: #c0caf5 !important;
    margin: 0;
}

/* HEADINGS */
.section-title {
    page-break-before: always;
    font-size: 22pt;
    margin-bottom: 12px;
}

/* TEXT */
p {
    font-size: 12pt;
}

li {
    font-size: 12pt;
}

/* QUOTES */
blockquote {
    border-left: 4px solid #444;
    margin: 20px 0;
    padding: 10px 16px;
    color: #444;
    background: #f6f6f6;
    font-style: italic;
}

/* LISTS */
ul {
    padding-left: 20px;
    margin-bottom: 16px;
}

/* LINKS */
a {
    font-size: 10pt;
    color: #4ea1ff;
    text-decoration: none;
    word-break: break-word;
}

a:hover {
    text-decoration: underline;
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

    # COVER
    html.append(f"""
<div class="cover">
    <h1>{title}</h1>
    <div class="meta">
        Author: {author}<br>
        {date_str}
    </div>
</div>
""")

    # TOC
    html.append("<div class='toc'>")
    html.append("<h2>Table of Contents</h2>")

    for i, (name, anchor) in enumerate(toc_items, start=1):
        html.append(f"<a href='#{anchor}'>{i}. {name}</a>")

    html.append("</div>")

    # CONTENT
    in_list = False

    for section in all_sections:
        kind = section[0]

        if kind == "h":
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
    scale=1.3,   # EZ A FONTOS
    margin={
        "top": "10mm",
        "bottom": "10mm",
        "left": "10mm",
        "right": "10mm"
    }
)

        browser.close()


# -------------------------
# main pipeline
# -------------------------

def run():
    index_html = fetch(BASE + START)
    links = get_links(index_html)

    all_sections = []

    toc = []
    date_str = "Updated for Xcode 16.4"
    title = "Swift Concurrency"
    author = "Paul Hudson (Hacking with Swift)"

    for i, url in enumerate(links, start=1):
        print(f"[{i}] {url}")

        html = fetch(url)
        content = extract(html)

        print("CONTENT SIZE:", len(content))

        slug = url.split("/")[-1]
        chapter_title = slug_to_title(slug)
        anchor = f"section-{i}"

        # TOC ENTRY
        toc.append((chapter_title, anchor))

        # SECTION HEADER (FIXED TUPLE SHAPE)
        all_sections.append(("h", f"{i}. {chapter_title}", anchor))

        all_sections.extend(content)

    html_doc = build_html(all_sections, toc, title, date_str, author)
    html_to_pdf(html_doc, "swift_concurrency.pdf")


if __name__ == "__main__":
    run()
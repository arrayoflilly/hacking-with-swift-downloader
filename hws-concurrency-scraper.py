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

    # state machine
    started = False

    for el in container.children:

        if not isinstance(el, Tag):
            continue

        # START POINT: first lead paragraph
        classes = el.get("class") or []
        if "lead" in classes:
            started = True
            continue

        # STOP POINT
        classes = el.get("class") or []
        if "hws-sponsor" in classes:
            break

        if not started:
            continue

        # CONTENT
        if el.name == "p":
            txt = el.get_text(strip=False)
            if txt:
                out.append(("p", txt))

        elif el.name in ["h1", "h2", "h3"]:
            txt = el.get_text(strip=True)
            if txt:
                out.append(("h", txt))

        elif el.name == "pre":
            out.append(("code", el.get_text("\n", strip=False)))

        elif el.name == "ul":
            for li in el.find_all("li", recursive=False):
                out.append(("li", li.get_text(strip=True)))

    return out


# -------------------------
# HTML builder
# -------------------------

from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters.html import HtmlFormatter

def build_html(all_sections):
    formatter = HtmlFormatter(style="native", cssclass="code")

    base_css = formatter.get_style_defs(".code")

    custom_css = base_css + """
body {
    font-family: -apple-system, sans-serif;
    max-width: 850px;
    margin: 40px auto;
    line-height: 1.6;
}

/* code block */
.code {
    background: #1a1b26 !important;
    border-radius: 10px;
    padding: 14px;
}

.code .highlight {
    background: #1a1b26 !important;
}

.code pre {
    background: transparent !important;
    color: #c0caf5 !important;
    padding: 0;
    margin: 0;
}

/* heading page break */
h1 {
    page-break-before: always;
}

# /* FIX: inline emphasis spacing issue in PDF render */
# em, strong, i, b {
#     margin: 0 0.15em;
#     display: inline-block;
# }
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

    for section in all_sections:
        kind = section[0]

        if kind == "h":
            html.append(f"<h1>{section[1]}</h1>")

        elif kind == "p":
            html.append(f"<p>{section[1]}</p>")

        elif kind == "li":
            html.append(f"<li>{section[1]}</li>")

        elif kind == "code":
            highlighted = highlight(
                section[1],
                get_lexer_by_name("swift"),
                formatter
            )
            html.append(f"<div class='code'>{highlighted}</div>")

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
            margin={
                "top": "15mm",
                "bottom": "15mm",
                "left": "15mm",
                "right": "15mm"
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

    for i, url in enumerate(links, start=1):
        print(f"[{i}] {url}")

        html = fetch(url)
        content = extract(html)
        
        print("CONTENT SIZE:", len(content))
        print(content[:5])

        slug = url.split("/")[-1]
        title = slug_to_title(slug)

        all_sections.append(("h", f"{i}. {title}"))
        all_sections.extend(content)

    html_doc = build_html(all_sections)
    html_to_pdf(html_doc, "swift_concurrency.pdf")


if __name__ == "__main__":
    run()
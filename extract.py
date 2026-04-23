from bs4 import BeautifulSoup, Tag
from urllib.parse import urljoin

from config import START, BASE

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
    first_heading_skipped = False   # <- IDE

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
                if not first_heading_skipped:
                    first_heading_skipped = True
                    continue

                out.append((el.name, txt))   # <- NEM "h"

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
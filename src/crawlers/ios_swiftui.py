# src/crawlers/ios_swiftui.py

from bs4 import BeautifulSoup, Tag
from urllib.parse import urljoin

from src.pipeline.extract import extract

BASE = "https://www.hackingwithswift.com"
_LINK_PREFIX = "/books/ios-swiftui/"


def get_links_ios_swiftui(html: str) -> list:
    soup = BeautifulSoup(html, "html.parser")

    container = soup.select_one("div.container div[style*='max-width']")
    if not container:
        container = soup.select_one("div.container")
    if not container:
        return []

    seen = set()
    items = []
    prev_was_h2 = False

    for el in container.children:
        if not isinstance(el, Tag):
            continue

        if el.name == "h2":
            txt = el.get_text(strip=True)
            if txt:
                items.append(("chapter", txt))
                prev_was_h2 = True
            continue

        if el.name == "p":
            if prev_was_h2:
                inner = "".join(str(c) for c in el.children).strip()
                if inner:
                    items.append(("p", inner))
            prev_was_h2 = False
            continue

        prev_was_h2 = False

        if el.name == "h4":
            txt = el.get_text(strip=True)
            if txt:
                items.append(("chapter", txt))
            continue

        if el.name == "ul":
            for li in el.find_all("li", recursive=False):
                a = li.find("a")
                if not a:
                    continue
                href = str(a.get("href", ""))
                if href.startswith(_LINK_PREFIX):
                    full = urljoin(BASE, href)
                    if full not in seen:
                        seen.add(full)
                        items.append(("link", a.get_text(strip=True), full))
            continue

    return items


def extract_ios_swiftui(html: str, url: str, cache) -> list:
    return extract(html, cache)
# src/crawlers/sixty.py

from bs4 import BeautifulSoup, Tag
from urllib.parse import urljoin

from src.pipeline.extract import extract

BASE = "https://www.hackingwithswift.com"


def get_links_sixty(html: str) -> list:
    soup = BeautifulSoup(html, "html.parser")
    container = soup.select_one("div.col-lg-10")
    if not container:
        return []

    seen = set()
    items = []

    for el in container.children:
        if not isinstance(el, Tag):
            continue

        if el.name == "h3":
            txt = el.get_text(strip=True)
            if txt:
                items.append(("chapter", txt))
            continue

        if el.name in ("ul", "ol"):
            for li in el.find_all("li", recursive=False):
                a = li.find("a")
                if not a:
                    continue
                href = str(a.get("href", ""))
                if "/sixty/" in href:
                    full = urljoin(BASE, href)
                    if full not in seen:
                        seen.add(full)
                        items.append(("link", a.get_text(strip=True), full))
            continue

    return items


def extract_sixty(html: str, url  : str, cache) -> list:
    return extract(html, cache)
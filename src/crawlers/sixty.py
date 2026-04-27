from bs4 import BeautifulSoup
from urllib.parse import urljoin

from src.pipeline.extract import extract

BASE = "https://www.hackingwithswift.com"


def get_links_sixty(html: str) -> list:
    soup = BeautifulSoup(html, "html.parser")

    # Az oldalon két div.col-lg-10 van.
    # Az első a "Before you start" FAQ szekciót tartalmazza — nincs benne h3 közvetlen gyerekként.
    # A második tartalmazza a h3+ul párokat (chapter + linkek).
    # Azt a containert keressük, amelyiknek van közvetlen h3 gyereke.
    all_containers = soup.select("div.col-lg-10")
    container = next(
        (c for c in all_containers if c.find("h3", recursive=False)),
        None,
    )
    if not container:
        return []

    seen = set()
    items = []

    # A közvetlen gyerekeket sorban járjuk be, hogy a chapter→link sorrend megmaradjon.
    # h3  → ("chapter", szöveg)
    # ul  → az összes li > a href, amelyik /sixty/-et tartalmaz → ("link", szöveg, url)
    for el in container.children:
        if not hasattr(el, "name") or not el.name: # type: ignore
            continue

        if el.name == "h3": # type: ignore
            txt = el.get_text(strip=True)
            if txt:
                items.append(("chapter", txt))
            continue

        if el.name == "ul": # type: ignore
            for li in el.find_all("li", recursive=False): # type: ignore
                a = li.find("a", href=True)
                if not a:
                    continue

                href = str(a.get("href", ""))
                if "/sixty/" not in href:
                    continue

                full = urljoin(BASE, href)
                if full in seen:
                    continue

                seen.add(full)
                items.append(("link", a.get_text(strip=True), full))

    return items


def extract_sixty(html: str, url: str, cache) -> list:
    return extract(html, cache)
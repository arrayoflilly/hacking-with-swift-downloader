# src/crawlers/hundred.py

from bs4 import BeautifulSoup, Tag
from urllib.parse import urljoin

from src.pipeline.extract import extract, _is_ebtc_footer_block
from src.pipeline.fetcher import fetch

from src.core.logger import log

BASE = "https://www.hackingwithswift.com"

_SKIP_PREFIXES = (
    "/review",
    "/store/",
    "/plus",
    "/files/",
)

_SKIP_EXACT = (
    "/",
    "/read",
    "/sixty",
    "/100",
)


_SKIP_CLASSES = (
    "chatparent",
    "chatparent-header",
    "hws-sponsor",
)


def _should_fetch(href: str) -> bool:
    if not href.startswith("/"):
        return False
    if href.endswith(".pdf"):
        return False
    if href in _SKIP_EXACT:
        return False
    for skip in _SKIP_PREFIXES:
        if href.startswith(skip):
            return False
    if href.startswith("/100/"):
        return False
    return True


def get_links_hundred(html: str) -> list:
    soup = BeautifulSoup(html, "html.parser")
    container = soup.select_one("div.col-lg-10")
    
    if not container:
        return []

    seen = set()
    items = []
    in_course_section = False

    for el in container.children:
        if not isinstance(el, Tag):
            continue

        classes = el.get("class") or []

        if "hws-sponsor" in classes:
            continue

        if _is_ebtc_footer_block(el):
            break

        if el.name == "table":
            continue

        if el.name == "h2":
            txt = el.get_text(strip=True)
            if "The Course" in txt:
                in_course_section = True
            else:
                if txt:
                    items.append(("chapter", txt))
            continue

        if not in_course_section:
            if el.name == "p":
                inner = "".join(str(c) for c in el.children).strip()
                if inner and inner != "&nbsp;":
                    items.append(("p", inner))
                continue

            if el.name == "h3":
                txt = el.get_text(strip=True)
                if txt:
                    items.append(("chapter", txt))
                continue

            if el.name == "p":
                inner = "".join(str(c) for c in el.children).strip()
                if inner and inner != "&nbsp;":
                    items.append(("p", inner))
                continue

            if el.name in ("ul", "ol"):
                for li in el.find_all("li", recursive=False):
                    a = li.find("a")
                    if not a:
                        continue
                    href = str(a.get("href", ""))
                    if href.startswith("/100/"):
                        full = urljoin(BASE, href)
                        if full not in seen:
                            seen.add(full)
                            items.append(("link", a.get_text(strip=True), full))

                continue
            
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
                if href.startswith("/100/"):
                    full = urljoin(BASE, href)
                    if full not in seen:
                        seen.add(full)
                        items.append(("link", a.get_text(strip=True), full))
            continue

    return items


def _extract_day_intro(soup: BeautifulSoup) -> list:
    container = soup.select_one("div.col-lg-10")
    if not container:
        return []

    items = []

    for el in container.children:
        if not isinstance(el, Tag):
            continue

        classes = el.get("class") or []

        if "hws-sponsor" in classes:
            continue

        if any(c in classes for c in _SKIP_CLASSES):
            continue

        if _is_ebtc_footer_block(el):
            break

        if el.name == "table":
            continue

        if el.name == "p":
            inner = "".join(str(c) for c in el.children).strip()
            if inner and inner != "&nbsp;":
                items.append(("p", inner))
            continue

        if el.name in ("h2", "h3"):
            txt = el.get_text(strip=True)
            if txt:
                items.append((el.name, txt))
            continue

        if el.name in ("ul", "ol"):
            list_items = []
            for li in el.find_all("li", recursive=False):
                top_text = ""
                for child in li.children:
                    if isinstance(child, Tag):
                        if child.name == "ul":
                            continue
                        top_text += child.get_text(" ", strip=True)
                    else:
                        top_text += str(child)
                top_text = top_text.strip()
                if top_text:
                    list_items.append(top_text)
            if list_items:
                items.append(("list", {
                    "ordered": el.name == "ol",
                    "items": list_items,
                }))
            continue

    return items


def _collect_sublinks(soup: BeautifulSoup) -> list:
    container = soup.select_one("div.col-lg-10")
    if not container:
        return []

    seen = set()
    urls = []

    for a in container.find_all("a", href=True):
        href = str(a.get("href", ""))
        if not href.startswith("/"):
            continue
        if href in ("/", "/read", "/sixty", "/100"):
            continue
        if href.startswith("/100/"):
            continue
        if href.startswith("/review/"):
            continue
        full = urljoin(BASE, href)
        if full not in seen:
            seen.add(full)
            urls.append(full)

    return urls


def extract_hundred_day(html: str, url: str, cache) -> list:
    soup = BeautifulSoup(html, "html.parser")
    items = []

    items.extend(_extract_day_intro(soup))

    sub_urls = _collect_sublinks(soup)
    log(f"sublinks ({len(sub_urls)}): {sub_urls}")

    
    for sub_url in sub_urls:
        sub_html = fetch(sub_url)
        items.extend(extract(sub_html, cache))

    return items
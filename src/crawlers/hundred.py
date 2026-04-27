# src/crawlers/hundred.py

import hashlib
from bs4 import BeautifulSoup, Tag
from urllib.parse import urljoin

from src.pipeline.extract import extract, _is_ebtc_footer_block
from src.pipeline.fetcher import fetch
from src.core.logger import log
from src.config.config import CONTENT_HINTS, CTA_PHRASES

BASE = "https://www.hackingwithswift.com"
GLOSSARY_URL = f"{BASE}/glossary"

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
    "/100/",
)

_SKIP_CLASSES = (
    "chatparent",
    "chatparent-header",
    "hws-sponsor",
)

_SUBSECTION_PREFIXES = (
    "/sixty/",
    "/quick-start/",
    "/read/",
    "/guide/",
)

def _is_valid_subsection_href(href: str) -> bool:
    for prefix in _SUBSECTION_PREFIXES:
        if href.startswith(prefix):
            return True
    return False


def _is_needhelp_block(item: tuple) -> bool:
    """Szűri a 'Need help? Tweet me @twostraws!' szövegű elemeket."""
    if not isinstance(item, tuple) or item[0] != "p":
        return False
    text = str(item[1]).lower()
    return "twostraws" in text and "need help" in text

def _item_text(item: tuple) -> str:
    if not isinstance(item, tuple) or not item:
        return ""

    def clean(html: str) -> str:
        return BeautifulSoup(html, "html.parser").get_text(" ", strip=True).lower()

    t = item[0]

    if t == "p":
        return clean(item[1])
    if t == "heading":
        return str(item[2]).lower()
    if t == "subpage_header":
        return str(item[1]).lower()
    if t == "link":
        return f"{item[1]} {item[2]}".lower()

    return " ".join(str(x) for x in item[1:]).lower()

def _is_cta_start(item: tuple) -> bool:
    text = _item_text(item)
    return (
        "how can this day be improved" in text or
        "share your progress" in text
    )


def _is_cta_end(item: tuple) -> bool:
    text = _item_text(item)
    return "need help?" in text

def _is_social_footer_block(item: tuple) -> bool:
    text = _item_text(item)

    if not text:
        return False

    # ha content jel van → NEM szűrjük
    if any(h in text for h in CONTENT_HINTS):
        return False

    # CTA csak ha explicit phrase
    if any(p in text for p in CTA_PHRASES):
        return True

    return False

def _stable_id(url: str) -> str:
    return hashlib.sha1(url.encode()).hexdigest()[:8]


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


def _li_full_text(li: Tag) -> str:
    """
    A <li> teljes szövege, al-lista (nested <ul>/<ol>) tartalmát kihagyva.
    Ezt használjuk a TOC-beli section_title/subsection_title szövegéhez.
    """
    parts = []
    for child in li.children:
        if isinstance(child, Tag) and child.name in ("ul", "ol"):
            continue
        if isinstance(child, Tag):
            parts.append(child.get_text(" ", strip=True))
        else:
            parts.append(str(child))
    return " ".join(parts).split()  # type: ignore  # list of words — join below


def _li_label(li: Tag) -> str:
    """Összefűzött, whitespace-normalizált szöveg a <li>-ből, al-lista nélkül."""
    parts = []
    for child in li.children:
        if isinstance(child, Tag) and child.name in ("ul", "ol"):
            continue
        if isinstance(child, Tag):
            parts.append(child.get_text(" ", strip=True))
        else:
            parts.append(str(child).strip())
    return " ".join(" ".join(parts).split())


def get_links_hundred(html: str) -> list:
    """
    A /100 főoldal TOC parser.

    Kimenet:
      - Első h2 ("How it works") → section_title (page boundary)
      - Bevezető h3-ak ("Rules", "Tips") → heading
      - Bevezető p-k → p passthrough
      - Bevezető listák → list passthrough
      - Glossary link (a bevezetőben) → glossary_link (a bevezetés UTÁN injektálva)
      - "The Course" h2 után: h3-ak → chapter (TOC grouping)
      - "The Course" h2 után: p-k → p passthrough
      - "The Course" h2 után: ul/li /100/N linkek → link (teljes li szöveg)
        - nested ul Optional: elemek → subsection_title
        - Test: elemek → kihagyva
    """
    soup = BeautifulSoup(html, "html.parser")
    container = soup.select_one("div.col-lg-10")
    if not container:
        return []

    seen = set()
    intro_items = []       # section_title + bevezető tartalom
    glossary_item = None   # a főoldalon talált glossary link
    course_items = []      # "The Course" szekció tartalma
    in_course_section = False
    first_heading_done = False

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

        if el.name == "hr":
            continue

        if el.name == "h2":
            txt = el.get_text(strip=True)
            if not txt:
                continue
            if "The Course" in txt:
                in_course_section = True
                continue
            if not first_heading_done:
                # log(f"Injecting section_title for intro: {txt} (anchor: section-intro) (crawler)")  # debug
                intro_items.append(("section_title", txt, {"id": "section-intro"}))
                first_heading_done = True
            else:
                intro_items.append(("heading", "h2", txt))
            continue

        if not in_course_section:
            if el.name == "h3":
                txt = el.get_text(strip=True)
                if txt:
                    intro_items.append(("heading", "h3", txt))
                continue

            if el.name == "p":
                inner = "".join(str(c) for c in el.children).strip()
                if inner and inner != "&nbsp;":
                    intro_items.append(("p", inner))
                continue

            if el.name in ("ul", "ol"):
                # Ellenőrizzük, hogy ez a lista tartalmaz-e glossary linket
                for li in el.find_all("li", recursive=False):
                    a = li.find("a")
                    if a:
                        href = str(a.get("href", ""))
                        if "/glossary" in href:
                            full = urljoin(BASE, href)
                            if glossary_item is None:
                                glossary_item = ("glossary_fetch", "Glossary", full)
                            continue

                list_items = []
                for li in el.find_all("li", recursive=False):
                    inner = "".join(str(c) for c in li.children).strip()
                    if inner:
                        list_items.append(inner)
                if list_items:
                    intro_items.append(("list", {
                        "ordered": el.name == "ol",
                        "items": list_items,
                    }))
                continue

            continue

        # --- "The Course" szekció ---

        if el.name == "h3":
            txt = el.get_text(strip=True)
            if txt:
                course_items.append(("chapter", txt))
            continue

        if el.name == "p":
            inner = "".join(str(c) for c in el.children).strip()
            if inner and inner != "&nbsp;":
                course_items.append(("p", inner))
            continue

        if el.name in ("ul", "ol"):
            for li in el.find_all("li", recursive=False):
                a = li.find("a", recursive=False) or li.find("a")
                if not a:
                    continue
                href = str(a.get("href", ""))
                if not href.startswith("/100/"):
                    continue
                full = urljoin(BASE, href)
                if full in seen:
                    continue
                seen.add(full)

                # Teljes li szöveg (al-lista nélkül) a TOC-beli névhez
                label = _li_label(li)

                course_items.append(("link", label, full))

                # Nested <ul> feldolgozása: Optional → subsection_title, Test → kihagyva
                nested_ul = li.find("ul")
                if nested_ul:
                    for sub_li in nested_ul.find_all("li", recursive=False):
                        sub_text = sub_li.get_text(" ", strip=True)
                        sub_a = sub_li.find("a")
                        if not sub_a:
                            continue
                        sub_href = str(sub_a.get("href", ""))
                        sub_full = urljoin(BASE, sub_href)
                        sub_label = sub_a.get_text(strip=True)

                        if sub_text.strip().lower().startswith("test"):
                            continue

                        if sub_text.strip().lower().startswith("optional"):
                            # log(f"Adding Optional sub-subsection: {sub_label} (anchor: sec-{_stable_id(sub_full)}) (crawler) - his should be sub_subsection_title")  # debug
                            course_items.append((
                                "subsection_title",
                                f"(Optional) {sub_label}",
                                {"id": f"sec-{_stable_id(sub_full)}", "url": sub_full},
                            ))
                            continue

                        # Egyéb al-elem (nem Optional, nem Test) → subsection_title prefix nélkül
                        # log(f"Adding subsection: {sub_label} (anchor: sec-{_stable_id(sub_full)}) (crawler)")
                        course_items.append((
                            "subsection_title",
                            sub_label,
                            {"id": f"sec-{_stable_id(sub_full)}", "url": sub_full},
                        ))

            continue

    # Összerakjuk: bevezető → glossary (ha van) → kurzus tartalom
    items = list(intro_items)
    if glossary_item:
        items.append(glossary_item)
    items.extend(course_items)
    return items


def _extract_glossary(html: str) -> list:
    """
    A /glossary oldal extractora.
    Struktúra: section#courses > div.container
      - p bevezető → section_title (első elem) + p
      - h2.title betűk (@, a, b, c...) → heading
      - ul/li definíciók → list
    """
    soup = BeautifulSoup(html, "html.parser")
    container = soup.select_one("section#courses div.container")
    if not container:
        return []

    items = []
    section_injected = False

    for el in container.children:
        if not isinstance(el, Tag):
            continue

        if el.name == "p":
            inner = "".join(str(c) for c in el.children).strip()
            if not inner or inner == "&nbsp;":
                continue
            if not section_injected:
                items.append(("section_title", "Glossary", {
                    "id": "section-glossary",
                    "special": "glossary",
                }))
                section_injected = True
            items.append(("p", inner))
            continue

        if el.name == "h2":
            txt = el.get_text(strip=True)
            if not txt:
                continue
            if not section_injected:
                items.append(("section_title", "Glossary", {
                    "id": "section-glossary",
                    "special": "glossary",
                }))
                section_injected = True
            items.append(("heading", "h2", txt))
            continue

        if el.name == "ul":
            list_items = []
            for li in el.find_all("li", recursive=False):
                inner = "".join(str(c) for c in li.children).strip()
                if inner:
                    list_items.append(inner)
            if list_items:
                items.append(("list", {
                    "ordered": False,
                    "items": list_items,
                }))
            continue

    return items


def _extract_day_intro(soup: BeautifulSoup) -> list:
    """
    Egy /100/N nap oldal tartalmát szedi ki.

    Első h1/h2 → section_title (page boundary)
    Többi h2/h3 → heading
    p → paragraph
    ul/ol → list (top-level li szövege, al-lista kihagyva)
    Sponsor, chatparent, ebtc → kihagyva
    """
    container = soup.select_one("div.col-lg-10")
    if not container:
        return []

    items = []
    first_heading_done = False

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

        if el.name == "hr":
            continue

        if el.name in ("h1", "h2"):
            txt = el.get_text(strip=True)
            if not txt:
                continue
            if not first_heading_done:
                items.append(("section_title", txt, {
                    "id": f"section-day-{hash(txt) & 0xFFFFFF}",
                }))
                first_heading_done = True
            else:
                items.append(("heading", el.name, txt))
            continue

        if el.name == "h3":
            txt = el.get_text(strip=True)
            if txt:
                items.append(("heading", "h3", txt))
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
                if not _is_valid_subsection_href(href):
                    continue
                sub_full = urljoin(BASE, href)
                sub_label = a.get_text(strip=True)
                sub_id = f"sec-{_stable_id(sub_full)}"

                items.append((
                    "subsection_title",
                    sub_label,
                    {"id": sub_id, "url": sub_full},
                ))

                nested_ul = li.find("ul")
                if not nested_ul:
                    continue

                for sub_li in nested_ul.find_all("li", recursive=False):
                    sub_text = sub_li.get_text(" ", strip=True)
                    sub_sub_a = sub_li.find("a")
                    if not sub_sub_a:
                        continue
                    sub_sub_href = str(sub_sub_a.get("href", ""))
                    sub_sub_full = urljoin(BASE, sub_sub_href)
                    sub_sub_label = sub_sub_a.get_text(strip=True)

                    if sub_text.strip().lower().startswith("test"):
                        continue

                    if sub_text.strip().lower().startswith("optional"):
                        items.append((
                            "sub_subsection_title",
                            f"(Optional) {sub_sub_label}",
                            {"id": f"sec-{_stable_id(sub_sub_full)}", "url": sub_sub_full},
                        ))
                        continue

                    items.append((
                        "sub_subsection_title",
                        sub_sub_label,
                        {"id": f"sec-{_stable_id(sub_sub_full)}", "url": sub_sub_full},
                    ))

            continue

    return items


def _collect_sublinks(soup: BeautifulSoup) -> list:
    """
    A nap oldaláról összegyűjti a letöltendő aloldal URL-eket.
    A _should_fetch() szabályai szerint szűr.
    """
    container = soup.select_one("div.col-lg-10")
    if not container:
        return []

    seen = set()
    urls = []

    for a in container.find_all("a", href=True):
        href = str(a.get("href", ""))
        if _should_fetch(href):
            full = urljoin(BASE, href)
            if full not in seen:
                seen.add(full)
                urls.append(full)

    return urls


def _extract_subpage(html: str, url: str, cache) -> list:
    """
    Egy aloldal tartalmát szedi ki.
    - subpage_header node-ot injektál a H1-ből: page break + cím, de NEM TOC entry
    - Az anchor az _extract_day_intro() subsection_title node-ján van (azonos ID)
    - Az extract() maga kihagyja az h1-et (first_heading_skipped logika)
    - "Need help? Tweet me @twostraws!" szűrve
    """
    items = []

    sub_soup = BeautifulSoup(html, "html.parser")
    title_el = sub_soup.select_one("h1.hws-main-title")
    if title_el:
        title_txt = title_el.get_text(strip=True)
        items.append(("subpage_header", title_txt, {}))

    raw = extract(html, cache)
    for item in raw:
        if _is_needhelp_block(item) or _is_social_footer_block(item):
            log(f"FILTERED: {item}")
            continue
        items.append(item)

    return items


def extract_hundred_day(html: str, url: str, cache) -> list:
    """
    Egy /100/N nap oldal teljes tartalmát adja vissza.
    1. Nap oldal saját tartalma (bevezető + section_title)
    2. Aloldalak letöltése és extract()-olása, section_title injektálással
       - /glossary → _extract_glossary()
       - minden más → _extract_subpage()
    """
    soup = BeautifulSoup(html, "html.parser")
    items = []

    items.extend(_extract_day_intro(soup))

    sub_urls = _collect_sublinks(soup)
    # log(f"sublinks ({len(sub_urls)}): {sub_urls}")

    for sub_url in sub_urls:
        sub_html = fetch(sub_url)
        if sub_url.rstrip("/") == GLOSSARY_URL:
            items.extend(_extract_glossary(sub_html))
        else:
            items.extend(_extract_subpage(sub_html, sub_url, cache))

    return items
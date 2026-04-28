from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from src.pipeline.fetcher import fetch

BASE = "https://www.hackingwithswift.com"


def get_links_news(html: str) -> list:
    """
    Lista oldalak struktúrája:
      div.card-blog  (osztály: "card card-blog" vagy "card-plain card-blog")
        h3.card-title > a[href=/articles/NNN/slug]  → cím + link

    A div.card.card-blog selector kihagyja a card-plain card-blog elemeket,
    ezért div.card-blog-ot használunk, ami mindkét variánst megfogja.

    Pagination: a[href="/articles/page/N"] "Older Posts" linkként.
    Az összes oldalt a fetch_all_news_links() járja be.
    """
    return _extract_page_links(html)


def fetch_all_news_links(start_html: str) -> list:
    """
    Az összes listázó oldalt bejárja a pagination linkeket követve,
    és egyetlen összesített items listát ad vissza.

    Ezt a run.py-ból kell hívni get_links_fn-ként (szignatúra azonos).
    """
    seen_urls = set()
    all_items = []

    html = start_html
    page = 1

    while True:
        items = _extract_page_links(html)
        for item in items:
            if item[2] not in seen_urls:
                seen_urls.add(item[2])
                all_items.append(item)

        next_href = _next_page_href(html)
        if not next_href:
            break

        next_url = urljoin(BASE, next_href)
        print(f"[news] fetching page {page + 1}: {next_url}")
        html = fetch(next_url)
        page += 1

    return all_items


def _extract_page_links(html: str) -> list:
    soup = BeautifulSoup(html, "html.parser")
    seen = set()
    items = []

    # div.card-blog fogja meg a "card card-blog" és "card-plain card-blog" elemeket is
    for card in soup.select("div.card-blog"):
        # A cím és a link ugyanabban az a tagban van a h3.card-title-n belül
        title_a = card.select_one("h3.card-title a")
        if not title_a:
            continue

        title = title_a.get_text(strip=True)
        if not title:
            continue

        href = str(title_a.get("href", ""))
        if not href or "/articles/" not in href or "/category/" in href:
            continue

        full = urljoin(BASE, href)
        if full in seen:
            continue

        seen.add(full)
        items.append(("link", title, full))

    return items


def _next_page_href(html: str):
    """Visszaadja a következő lap href-jét, vagy None-t ha nincs."""
    soup = BeautifulSoup(html, "html.parser")
    a = soup.select_one("a[href*='/articles/page/']")
    if a:
        txt = a.get_text(strip=True).lower()
        if "older" in txt or "next" in txt:
            return a.get("href")
    return None


def extract_news(html: str, url: str, cache) -> list:
    """
    Cikk oldal struktúrája (div.col-lg-9 > div.row[0..3]):

      row[0]: h1.title       → cím, run.py injektálja section_title-ként → kihagyjuk
              p.lead.description → subtitle → kell
      row[1]: p > a(szerző) + time(dátum) → kell
      row[2]: img.img-responsive → header kép → kell
      row[3]: fő tartalom — p, h3, ol, ul, pre, blockquote
              div.hws-sponsor → kihagyjuk
    """
    soup = BeautifulSoup(html, "html.parser")

    container = soup.select_one("div.col-lg-9")
    if not container:
        return []

    rows = [el for el in container.children if isinstance(el, Tag) and el.name == "div"]
    if len(rows) < 4:
        return []

    out = []

    # --- row[0]: subtitle ---
    subtitle_el = rows[0].select_one("p.lead.description")
    if subtitle_el:
        txt = subtitle_el.get_text(strip=True)
        if txt:
            out.append(("p", f"<em>{txt}</em>"))

    # --- row[1]: szerző + dátum ---
    meta_p = rows[1].select_one("p")
    if meta_p:
        author_a = meta_p.find("a")
        time_el = meta_p.find("time")
        author = author_a.get_text(strip=True) if author_a else ""
        date = time_el.get_text(strip=True) if time_el else ""
        parts = [p for p in [author, date] if p]
        if parts:
            out.append(("p", " · ".join(parts)))

    # --- row[2]: header kép ---
    img = rows[2].find("img")
    if isinstance(img, Tag):
        from src.pipeline.extract import _extract_image_from_tag
        img_tuple = _extract_image_from_tag(img, cache)
        if img_tuple:
            out.append(img_tuple)

    # --- row[3]: fő tartalom ---
    content_div = rows[3].select_one("div.col-md-12")
    if content_div:
        out.extend(_extract_content(content_div, cache))

    return out


def _extract_content(container: Tag, cache) -> list:
    import re
    from src.pipeline.extract import (
        _extract_embedded_media,
        _extract_xcode_project_link,
        _MEDIA_CONTAINER_TAGS,
    )

    out = []

    for el in container.children:
        if not isinstance(el, Tag):
            continue

        classes = el.get("class") or []

        # Sponsor blokk kihagyása
        if "hws-sponsor" in classes:
            continue

        # Önálló media elemek
        if el.name in {"img", "iframe", "video", "picture", "figure"}:
            out.extend(_extract_embedded_media(el, cache))
            continue

        # Media container tagek
        if el.name in _MEDIA_CONTAINER_TAGS and el.find(
            ["img", "iframe", "video", "picture", "figure", "source"]
        ):
            xcode_link = _extract_xcode_project_link(el)
            if xcode_link:
                out.append(xcode_link)
                continue
            media = _extract_embedded_media(el, cache)
            if media:
                out.extend(media)
            plain = el.get_text(" ", strip=True)
            if plain and re.search(r"\w", plain):
                out.append(("p", plain))
            continue

        # Bekezdés
        if el.name == "p":
            inner = "".join(str(c) for c in el.children).strip()
            if inner:
                out.append(("p", inner))
            continue

        # Fejlécek
        if el.name in ("h2", "h3", "h4", "h5", "h6"):
            txt = el.get_text(" ", strip=True)
            if txt:
                out.append((el.name, txt))
            continue

        # Kód blokk
        if el.name == "pre":
            out.append(("code", el.get_text("\n", strip=False)))
            continue

        # Lista
        if el.name in ("ul", "ol"):
            items = []
            for li in el.find_all("li", recursive=False):
                inner = "".join(str(c) for c in li.children).strip()
                if inner:
                    items.append(inner)
            if items:
                out.append(("list", {"ordered": el.name == "ol", "items": items}))
            continue

        # Idézet
        if el.name == "blockquote":
            inner = "".join(str(c) for c in el.children).strip()
            if inner:
                out.append(("quote", inner))
            continue

    return out
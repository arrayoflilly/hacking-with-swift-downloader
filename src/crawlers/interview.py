import hashlib
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

BASE = "https://www.hackingwithswift.com"


def _stable_id(text: str, prefix: str) -> str:
    """Ugyanaz az algoritmus, mint a chapter_id_injector._stable_id().
    Szükséges, hogy a Related questions belső linkjei
    a helyes section anchor ID-ra mutassanak."""
    h = hashlib.sha1(text.encode("utf-8")).hexdigest()[:10]
    return f"{prefix}-{h}"


def get_links_interview(html: str) -> list:
    """
    Főoldal: https://www.hackingwithswift.com/interview-questions

    Valódi DOM struktúra:
      div.col-md-12
        p                       ← intro szöveg (több p)
          p.text-center         ← EGYETLEN p.text-center tartalmazza az ÖSSZES
            h2.title            ← kategória neve (chapter)
            p.lead              ← kategória leírás (kihagyjuk)
            ul                  ← linkek
            h2.title
            p.lead
            ul
            ...

    A h2.title és ul elemek a p.text-center közvetlen gyerekei.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Az összes kategória és link egyetlen p.text-center-ben van
    p_center = soup.select_one("p.text-center")
    if not p_center:
        return []

    seen = set()
    items = []

    for el in p_center.children:
        if not isinstance(el, Tag):
            continue

        # h2.title → chapter (kategória fejléc)
        if el.name == "h2" and "title" in (el.get("class") or []):
            txt = el.get_text(strip=True)
            if txt:
                items.append(("chapter", txt))
            continue

        # ul → linkek
        if el.name == "ul":
            for li in el.find_all("li", recursive=False):
                a = li.find("a", href=True)
                if not a:
                    continue

                href = str(a.get("href", ""))
                if "/interview-questions/" not in href:
                    continue

                full = urljoin(BASE, href)
                if full in seen:
                    continue

                seen.add(full)
                items.append(("link", a.get_text(strip=True), full))

    return items


def extract_interview(html: str, url: str, cache) -> list:
    """
    Aloldal struktúrája (div.col-md-12 közvetlen gyerekei):

      h2.title          → "iOS Developer Interview Questions" — kihagyjuk
      h1.title          → a kérdés szövege — kihagyjuk (run.py injektálja section_title-ként)
      div[margin:40px]  → "Suggested approach" bekezdés — kell
      p (badge+diff)    → difficulty szöveg, badge eltávolítva — kell
      p.text-center.lead (/plus/ link) → "Watch solution (subscribers only)" link — kell
      p.text-center.lead (list link)   → "See the full list..." — kihagyjuk
      h2 "Important notes" + ul        → ismétlődő minden oldalon — kihagyjuk
      h2 "Related questions" + ul      → belső anchor linkekként — kell
      p.text-center.lead (list, ismétlés) → kihagyjuk
    """
    soup = BeautifulSoup(html, "html.parser")

    container = soup.select_one("div.col-md-12")
    if not container:
        return []

    out = []
    in_important_notes = False

    children = [el for el in container.children if isinstance(el, Tag)]

    i = 0
    while i < len(children):
        el = children[i]
        classes = el.get("class") or []

        # h2.title → vezérlő elem
        if el.name == "h2" and "title" in classes:
            txt = el.get_text(strip=True)

            if "important notes" in txt.lower():
                in_important_notes = True
                i += 1
                continue

            if "related questions" in txt.lower():
                in_important_notes = False
                i += 1
                if i < len(children) and children[i].name == "ul":
                    related = _extract_related_questions(children[i])
                    if related:
                        out.append(("similar_articles", {
                            "title": "Related questions",
                            "items": related,
                        }))
                    i += 1
                continue

            # "iOS Developer Interview Questions" és bármely más h2 — kihagyjuk
            in_important_notes = False
            i += 1
            continue

        # h1 → a kérdés szövege, run.py injektálja section_title-ként — kihagyjuk
        if el.name == "h1":
            in_important_notes = False
            i += 1
            continue

        # ul az "Important notes" után — kihagyjuk
        if el.name == "ul" and in_important_notes:
            in_important_notes = False
            i += 1
            continue

        # div[style*="margin: 40px"] → Suggested approach bekezdés
        if el.name == "div":
            style = el.get("style") or ""
            if "margin: 40px" in style or "margin:40px" in style:
                for p in el.find_all("p"):
                    inner = "".join(str(c) for c in p.children).strip()
                    if inner:
                        out.append(("p", inner))
                i += 1
                continue

        # p → difficulty, plus link, vagy "See the full list" (kihagyandó)
        if el.name == "p":
            text = el.get_text(strip=True)

            # "See the full list of iOS interview questions" → kihagyjuk
            if "see the full list" in text.lower():
                i += 1
                continue

            # /plus/ link → "Watch solution (subscribers only)" egyszerű link
            plus_link = el.find("a", href=re.compile(r"/plus/"))
            if plus_link:
                href = str(plus_link.get("href", ""))
                full_url = urljoin(BASE, href)
                out.append(("p", f'<a href="{full_url}">Watch solution (subscribers only)</a>'))
                i += 1
                continue

            # Difficulty sor: tartalmaz badge span-t → eltávolítjuk, szöveget megtartjuk
            badge_span = el.find("span", class_=re.compile(r"badge-"))
            if badge_span:
                badge_span.decompose()
                difficulty_text = el.get_text(" ", strip=True)
                if difficulty_text:
                    out.append(("p", f"<strong>{difficulty_text}</strong>"))
                i += 1
                continue

            # Bármilyen más p → kihagyjuk
            i += 1
            continue

        i += 1

    return out


def _extract_related_questions(ul_tag: Tag) -> list:
    """
    A Related questions ul-ból belső anchor linkeket generálunk.
    Az anchor ID-t a link szövegéből számítjuk, ugyanúgy mint
    a chapter_id_injector._stable_id() — így a TOC és a Related questions
    linkjei konzisztensek lesznek.

    Visszatér: [{"title": "...", "url": "#sec-{hash}"}]
    """
    items = []
    for li in ul_tag.find_all("li", recursive=False):
        a = li.find("a", href=True)
        if not a:
            continue
        title = a.get_text(strip=True)
        if not title:
            continue
        anchor = _stable_id(title, "sec")
        items.append({
            "title": title,
            "url": f"#{anchor}",
        })
    return items
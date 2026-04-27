# chapter_id_injector.py

from typing import List, Dict, Any, Tuple
import hashlib

Node = Dict[str, Any]


def _stable_id(text: str, prefix: str) -> str:
    h = hashlib.sha1(text.encode("utf-8")).hexdigest()[:10]
    return f"{prefix}-{h}"


def inject_chapter_ids(ast: List[Node]) -> Tuple[List[Node], List[tuple]]:
    """
    Single-pass:
    - Assigns stable IDs to chapter, section_title, subsection_title,
      sub_subsection_title, heading nodes
    - Derives TOC from chapter, section_title, subsection_title,
      sub_subsection_title nodes
    - heading nodes never appear in TOC
    - glossary section_title nodes get special flag
    """

    updated: List[Node] = []
    toc: List[tuple] = []

    chapter_index = 0
    section_index = 0
    heading_index = 0

    for node in ast:
        ntype = node.get("type")
        node.setdefault("meta", {})

        # chapter → TOC entry, stabil ID
        if ntype == "chapter":
            if not node["meta"].get("id"):
                node["meta"]["id"] = f"chapter-{chapter_index}"
            chapter_index += 1
            updated.append(node)
            toc.append(("chapter", node.get("content"), node["meta"]["id"]))
            continue

        # section_title → TOC entry, stabil ID
        if ntype == "section_title":
            if not node["meta"].get("id"):
                content = node.get("content") or ""
                node["meta"]["id"] = _stable_id(content, "sec")
            section_index += 1

            # glossary detektálás
            content = (node.get("content") or "").lower()
            if "glossary" in content:
                node["meta"]["special"] = "glossary"

            updated.append(node)
            toc.append(("section", node.get("content"), node["meta"]["id"]))
            continue

        # subsection_title → stabil ID, passthrough (TOC a builder._build_toc()-ban kezeli)
        if ntype == "subsection_title":
            if not node["meta"].get("id"):
                content = node.get("content") or ""
                node["meta"]["id"] = _stable_id(content, "subsec")
            updated.append(node)
            continue

        # sub_subsection_title → stabil ID, passthrough (TOC a builder._build_toc()-ban kezeli)
        if ntype == "sub_subsection_title":
            if not node["meta"].get("id"):
                content = node.get("content") or ""
                node["meta"]["id"] = _stable_id(content, "subsubsec")
            updated.append(node)
            continue

        # heading → stabil ID, NEM kerül TOC-ba
        if ntype == "heading":
            if not node["meta"].get("id"):
                content = node.get("content") or ""
                node["meta"]["id"] = _stable_id(content, f"h{heading_index}")
                heading_index += 1
            # level biztosítása
            if "level" not in node["meta"] or node["meta"]["level"] is None:
                node["meta"]["level"] = 2
            updated.append(node)
            continue

        # link → glossary detektálás
        if ntype == "link":
            content = (node.get("content") or "").lower()
            url = (node.get("meta") or {}).get("url", "")
            if "glossary" in content or "/glossary" in url:
                node["meta"]["special"] = "glossary"
            updated.append(node)
            continue

        # default passthrough
        updated.append(node)

    return updated, toc
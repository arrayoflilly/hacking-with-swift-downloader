
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
    - assigns stable IDs
    - derives TOC
    - enforces "first heading per chapter" rule
    """

    updated: List[Node] = []
    toc: List[tuple] = []

    chapter_open = False
    chapter_id = None
    heading_used_in_chapter = False

    chapter_index = 0

    for node in ast:
        ntype = node.get("type")

        # -------------------------
        # chapter = page boundary
        # -------------------------
        if ntype == "chapter":
            chapter_id = f"chapter-{chapter_index}"
            chapter_index += 1

            node.setdefault("meta", {})
            node["meta"]["id"] = chapter_id

            updated.append(node)

            toc.append(("chapter", node.get("content"), chapter_id))

            chapter_open = True
            heading_used_in_chapter = False
            continue

        # -------------------------
        # heading
        # -------------------------
        if ntype == "heading":
            node.setdefault("meta", {})

            # ensure stable id
            if not node["meta"].get("id"):
                node["meta"]["id"] = _stable_id(node.get("content", ""), "h")

            updated.append(node)

            # only first heading per chapter goes to TOC
            if chapter_open and not heading_used_in_chapter:
                toc.append(("link", node.get("content"), node["meta"]["id"]))
                heading_used_in_chapter = True

            continue

        # -------------------------
        # default passthrough
        # -------------------------
        updated.append(node)

    return updated, toc
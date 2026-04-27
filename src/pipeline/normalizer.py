# Normalizer

import ast
from typing import Any, Dict, List

Node = Dict[str, Any]


def _base_node(node_type: str, content=None, layout=None, meta=None):
    return {
        "type": node_type,
        "layout": layout,
        "content": content,
        "meta": meta or {},
    }


def _coerce(item: Any):
    """
    Egységesíti a bemenetet:
    - tuple -> tuple marad
    - dict -> dict marad
    - string dict -> dict-é parse-oljuk
    """
    if isinstance(item, dict):
        return item

    if isinstance(item, tuple):
        return item

    if isinstance(item, str):
        s = item.strip()
        if s.startswith("{") and s.endswith("}"):
            try:
                return ast.literal_eval(s)
            except Exception:
                pass

    return item


# heading level string → int
_HEADING_LEVEL_MAP = {
    "h1": 1,
    "h2": 2,
    "h3": 3,
    "h4": 4,
    "h5": 5,
    "h6": 6,
}


def normalize(extracted_items: List[Any]) -> List[Node]:
    ast_nodes: List[Node] = []

    for item in extracted_items:
        item = _coerce(item)

        # dict node (builderből jön, már normalizált)
        if isinstance(item, dict):
            ast_nodes.append(item)
            continue

        # tuple node (extractből jön)
        if isinstance(item, tuple):

            # chapter
            if item[0] == "chapter":
                ast_nodes.append(_base_node("chapter", item[1], "block"))
                continue

            # section_title
            if item[0] == "section_title":
                _, title, meta = item
                ast_nodes.append(_base_node(
                    "section_title",
                    content=title,
                    layout="block",
                    meta=meta if isinstance(meta, dict) else {"id": meta},
                ))
                continue

            # subsection_title
            if item[0] == "subsection_title":
                _, title, meta = item
                ast_nodes.append(_base_node(
                    "subsection_title",
                    content=title,
                    layout="block",
                    meta=meta if isinstance(meta, dict) else {"id": meta},
                ))
                continue

            # sub_subsection_title
            if item[0] == "sub_subsection_title":
                _, title, meta = item
                ast_nodes.append(_base_node(
                    "sub_subsection_title",
                    content=title,
                    layout="block",
                    meta=meta if isinstance(meta, dict) else {"id": meta},
                ))
                continue

            # heading — három formátum:
            # ("heading", "h2", text)  — hundred.py crawlerből
            # ("heading", level_int, text)  — egyéb
            # ("h1"/"h2"/"h3", text)  — extract() kimenetéből
            if item[0] == "heading":
                if len(item) == 3:
                    _, level_raw, text = item
                    level_int = _HEADING_LEVEL_MAP.get(level_raw, level_raw) if isinstance(level_raw, str) else level_raw
                    ast_nodes.append(_base_node(
                        "heading",
                        content=text,
                        layout="block",
                        meta={
                            "level": level_int,
                            "id": None,
                        }
                    ))
                continue

            if item[0] in ("h1", "h2", "h3", "h4", "h5", "h6"):
                level_int = _HEADING_LEVEL_MAP.get(item[0], 2)
                ast_nodes.append(_base_node(
                    "heading",
                    item[1],
                    "block",
                    {"level": level_int, "id": None}
                ))
                continue

            # paragraph
            if item[0] == "p":
                ast_nodes.append(_base_node("paragraph", item[1], "block"))
                continue

            # code
            if item[0] == "code":
                ast_nodes.append(_base_node("code", item[1], "block"))
                continue

            # list
            if item[0] == "list":
                _, data = item
                ast_nodes.append(_base_node(
                    "list",
                    content=data["items"],
                    layout="block",
                    meta={"ordered": data["ordered"]},
                ))
                continue

            # quote
            if item[0] == "quote":
                ast_nodes.append(_base_node("quote", item[1], "block"))
                continue

            # link
            if item[0] == "link":
                _, title, url = item
                meta = {"url": url}
                if "glossary" in title.lower():
                    meta["special"] = "glossary"
                ast_nodes.append(_base_node(
                    "link",
                    title,
                    "inline",
                    meta,
                ))
                continue

            # inline_code
            if item[0] == "inline_code":
                _, code = item
                ast_nodes.append(_base_node(
                    "inline_code",
                    content=code,
                    layout="inline",
                    meta={},
                ))
                continue

            # image
            if item[0] == "image":
                ast_nodes.append(_base_node(
                    "image",
                    None,
                    "block",
                    item[1]
                ))
                continue

            # video_frame
            if item[0] == "video_frame":
                ast_nodes.append(_base_node(
                    "video_frame",
                    None,
                    "block",
                    item[1]
                ))
                continue

            # similar_articles
            if item[0] == "similar_articles":
                data = item[1]
                node = _base_node("similar_articles", None, "block")
                node["title"] = data.get("title", "")
                node["items"] = data.get("items", [])
                ast_nodes.append(node)
                continue

        # fallback
        ast_nodes.append(_base_node(
            "unknown",
            str(item),
            "block"
        ))

    return ast_nodes
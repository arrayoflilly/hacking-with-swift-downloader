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


def normalize(extracted_items: List[Any]) -> List[Node]:
    ast_nodes: List[Node] = []

    for item in extracted_items:
        item = _coerce(item)

        # dict node (builderből jön)
        if isinstance(item, dict):
            ast_nodes.append(item)
            continue

        # tuple node (extractből jön)
        if isinstance(item, tuple):

            if item[0] == "chapter":
                ast_nodes.append(_base_node("chapter", item[1], "block"))
                continue
            
            # section title (run.py source)
            if item[0] == "section_title":
                _, title, meta = item

                ast_nodes.append(_base_node(
                    "section_title",
                    content=title,
                    layout="block",
                    meta=meta if isinstance(meta, dict) else {"id": meta},
                ))
            
            if item[0] == "heading":
                _, level, text = item

                ast_nodes.append(_base_node(
                    "heading",
                    content=text,
                    layout="block",
                    meta={
                        "level": level,
                        "id": None  # később fixáljuk
                    }
                ))

            if item[0] in ("h1", "h2", "h3"):
                ast_nodes.append(_base_node(
                    "heading",
                    item[1],
                    "block",
                    {"level": item[0]}
                ))
                continue

            if item[0] == "p":
                ast_nodes.append(_base_node("paragraph", item[1], "block"))
                continue

            if item[0] == "code":
                ast_nodes.append(_base_node("code", item[1], "block"))
                continue

            if item[0] == "list":
                _, data = item
                items = data["items"]

                ast_nodes.append(_base_node(
                    "list",
                    content=items,
                    layout="block",
                    meta={
                        "ordered": data["ordered"],
                    },
                ))

            if item[0] == "quote":
                ast_nodes.append(_base_node("quote", item[1], "block"))
                continue

            if item[0] == "link":
                _, title, url = item
                ast_nodes.append(_base_node(
                    "link",
                    title,
                    "inline",
                    {"url": url}
                ))
                continue
            
            if item[0] == "inline_code":
                _, code = item

                ast_nodes.append(_base_node(
                    "inline_code",
                    content=code,
                    layout="inline",
                    meta={},
                ))

            if item[0] == "image":
                ast_nodes.append(_base_node(
                    "image",
                    None,
                    "block",
                    item[1]
                ))
                continue

            if item[0] == "video_frame":
                ast_nodes.append(_base_node(
                    "video_frame",
                    None,
                    "block",
                    item[1]
                ))
                continue
            
            # -------------------------
            # SIMILAR ARTICLES
            # -------------------------
            if item[0] == "similar_articles":
                data = item[1]

                node = _base_node("similar_articles", None, "block")
                node["title"] = item[1].get("title", "")
                node["items"] = item[1].get("items", [])
                ast_nodes.append(node)
                continue
        

        # fallback
        ast_nodes.append(_base_node(
            "unknown",
            str(item),
            "block"
        ))

    return ast_nodes
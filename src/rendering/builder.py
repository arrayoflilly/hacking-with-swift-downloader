# builder.py

from typing import Any, Dict, List

from pygments.formatters.html import HtmlFormatter

from src.config.config import IMG_PATH
from src.rendering.inline_parser import split_inline
from src.rendering.renderers import (
    render_code,
    render_image,
    render_inline,
    render_video_frames,
    render_video_link,
)
from src.utils.utils import load_image_base64
from src.rendering.write_css import get_styles_css


def _render_cover(title: str, date_str: str, author: str) -> str:
    img_base64 = load_image_base64(IMG_PATH)
    return f"""
<div class="cover">
    <img src="data:image/png;base64,{img_base64}" />
    <h1>{title}</h1>
    <div class="meta">{author}<br>{date_str}</div>
</div>
"""


def _build_toc(nodes: List[Dict[str, Any]]) -> str:
    toc: List[tuple] = []
    last_chapter_idx = None  # az aktuális chapter pozíciója a toc listában

    for node in nodes:
        ntype = node.get("type")
        meta = node.get("meta") or {}
        content = node.get("content") or ""

        if ntype == "chapter":
            last_chapter_idx = len(toc)
            toc.append(("chapter", content, None, None))  # (type, text, anchor, paragraph)
            continue

        if ntype == "paragraph" and last_chapter_idx is not None:
            # Az utolsó chapter-hez tartozó paragrafust hozzáfűzzük
            ch_type, ch_text, ch_anchor, _ = toc[last_chapter_idx]
            toc[last_chapter_idx] = (ch_type, ch_text, ch_anchor, content)
            last_chapter_idx = None  # csak az első paragrafust vesszük fel
            continue

        # Bármilyen nem-paragraph node megszakítja a chapter→paragraph kapcsolatot
        if ntype not in ("chapter", "paragraph"):
            last_chapter_idx = None

        if ntype == "section_title":
            anchor = meta.get("id")
            if anchor:
                toc.append(("section", content, anchor, None))
            continue

        if ntype == "subsection_title":
            anchor = meta.get("id")
            if anchor:
                toc.append(("subsection", content, anchor, None))
            continue

        if ntype == "sub_subsection_title":
            anchor = meta.get("id")
            if anchor:
                toc.append(("sub_subsection", content, anchor, None))
            continue

    parts = ["<div class='toc' id='toc'><h2>Table of Contents</h2>"]

    for item in toc:
        item_type = item[0]
        text = item[1] or ""
        anchor = item[2]
        paragraph = item[3] if len(item) > 3 else None

        if item_type == "chapter":
            parts.append(f"<h3 class='toc-chapter'>{text}</h3>")
            if paragraph:
                parts.append(f"<p class='toc-chapter-desc'>{paragraph}</p>")

        elif item_type == "section":
            parts.append(
                f"<div class='toc-section'>"
                f"<a href='#{anchor}'>{text}</a>"
                f"</div>"
            )

        elif item_type == "subsection":
            parts.append(
                f"<div class='toc-subsection'>"
                f"<a href='#{anchor}'>{text}</a>"
                f"</div>"
            )

        elif item_type == "sub_subsection":
            parts.append(
                f"<div class='toc-sub-subsection'>"
                f"<a href='#{anchor}'>{text}</a>"
                f"</div>"
            )

    parts.append("</div>")
    return "\n".join(parts)


def _render_heading(content: str, meta: Dict[str, Any]) -> str:
    level = meta.get("level", "h2")
    anchor = meta.get("id")

    tag_map = {
        "h1": "h2",
        "h2": "h3",
        "h3": "h4",
    }
    tag = tag_map.get(level, "h3")

    id_attr = f" id='{anchor}'" if anchor else ""
    return f"<{tag}{id_attr}>{content}</{tag}>"


def _render_list(content: List[str], meta: Dict[str, Any]) -> str:
    ordered = bool(meta.get("ordered"))
    open_tag = "<ol>" if ordered else "<ul>"
    close_tag = "</ol>" if ordered else "</ul>"

    html = [open_tag]
    for li in content:
        tokens = split_inline(li)
        html.append(f"<li>{render_inline(tokens)}</li>")
    html.append(close_tag)
    return "\n".join(html)


def _render_video(meta: Dict[str, Any]) -> str:
    provider = (meta.get("provider") or "").lower()

    if provider in {"youtube", "vimeo"}:
        return render_video_link(meta)

    if provider == "mp4":
        frames_html = render_video_frames(meta)
        if frames_html:
            return frames_html

        url = meta.get("url") or ""
        if url:
            return f'<div class="asset video-link"><a href="{url}">{url}</a></div>'

    src = meta.get("src") or meta.get("url") or ""
    if not src:
        return ""

    return f'<div class="asset video-link"><a href="{src}">{src}</a></div>'


def _render_similar_articles(node: Dict[str, Any]) -> str:
    title = node.get("title", "")
    items = node.get("items", [])

    html = ["<div class='similar-section'>"]
    if title:
        html.append(f"<h3>{title}</h3>")

    if items:
        html.append("<ul>")
        for it in items:
            text = it.get("title", "")
            url = it.get("url", "")
            if url:
                html.append(f'<li><a href="{url}">{text}</a></li>')
            else:
                html.append(f"<li>{text}</li>")
        html.append("</ul>")

    html.append("</div>")
    return "\n".join(html)


def _render_node(node: Dict[str, Any], idx: int) -> str:
    t = node.get("type")
    c = node.get("content")
    m = node.get("meta") or {}
    c_str = c if isinstance(c, str) else ""

    if t == "chapter":
        return f'<h2 class="chapter-page">{c_str}</h2>'

    if t == "section_title":
        anchor = m.get("id") or f"sec-{idx}"
        m["id"] = anchor
        return f"<div class='page-break'></div>\n<h1 class='section-title' id='{anchor}'>{c_str}</h1>"

    if t == "subsection_title":
        anchor = m.get("id") or f"subsec-{idx}"
        m["id"] = anchor
        return f"<h2 class='subsection-title' id='{anchor}'>{c_str}</h2>"

    if t == "sub_subsection_title":
        anchor = m.get("id") or f"subsubsec-{idx}"
        m["id"] = anchor
        return f"<h3 class='sub-subsection-title' id='{anchor}'>{c_str}</h3>"

    if t == "heading":
        return _render_heading(c_str, m)

    if t == "paragraph":
        tokens = split_inline(c_str)
        cls = " class='has-link'" if "<a " in c_str.lower() else ""
        return f"<p{cls}>{render_inline(tokens)}</p>"

    if t == "quote":
        return f"<blockquote><p>{c_str}</p></blockquote>"

    if t == "list":
        list_content = c if isinstance(c, list) else []
        return _render_list([str(item) for item in list_content], m)

    if t == "image":
        return render_image(m)

    if t == "video_frame":
        return _render_video(m)

    if t == "code":
        return render_code(c_str)

    if t == "inline_code":
        return f"<code>{c_str}</code>"

    if t == "similar_articles":
        return _render_similar_articles(node)

    return ""


def build_html(all_sections, title, date_str, author):
    formatter = HtmlFormatter(style="material", cssclass="code")
    base_css = formatter.get_style_defs(".code")
    inline_css = get_styles_css(base_css) or ""

    nodes = all_sections

    html = [
        """
<html>
<head>
<meta charset="utf-8">
<style>
""",
        inline_css,
        """
</style>
</head>
<body>
""",
        "<a class='toc-float' href='#toc'>Contents</a>",
        _render_cover(title, date_str, author),
        _build_toc(nodes),
    ]

    for idx, node in enumerate(nodes):
        rendered = _render_node(node, idx)
        if rendered:
            html.append(rendered)

    html.append("</body></html>")
    return "\n".join(html)
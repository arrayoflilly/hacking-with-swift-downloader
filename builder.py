from pygments import highlight
from pygments.lexers import SwiftLexer # type: ignore
from pygments.formatters.html import HtmlFormatter

from utils import load_image_base64
from config import IMG_PATH, FONT_ROBOTO, FONT_ROBOTO_ITALIC, FONT_SLAB, FONT_MONTSERRAT

# -------------------------
# HTML builder
# -------------------------

from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters.html import HtmlFormatter


def build_html(all_sections, toc_items, title, date_str, author):
    formatter = HtmlFormatter(style="nord", cssclass="code")
    base_css = formatter.get_style_defs(".code")

    img_base64 = load_image_base64(IMG_PATH)

    custom_css = f"""
    @font-face {{
        font-family: 'Roboto';
        src: url('{FONT_ROBOTO}');
        font-weight: 100 900;
    }}

    @font-face {{
        font-family: 'Roboto';
        src: url('{FONT_ROBOTO_ITALIC}');
        font-style: italic;
        font-weight: 100 900;
    }}

    @font-face {{
        font-family: 'Roboto Slab';
        src: url('{FONT_SLAB}');
        font-weight: 100 900;
    }}

    @font-face {{
        font-family: 'Montserrat';
        src: url('{FONT_MONTSERRAT}');
        font-weight: 100 900;
    }}

    """ + base_css + """

    body {
        font-family: 'Roboto', sans-serif;
        margin: 0;
        padding: 0;
        line-height: 1.4;
        font-size: 12pt;
    }

    @page {
        margin: 20mm;
    }

    .cover {
        width: 100%;
        height: 100vh;
        background: #363636;
        color: white;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
        page-break-after: always;
    }

    .cover img {
        width: 300px;
        height: auto;
        margin-bottom: 20px;
        display: block;
    }

    .cover h1 {
        font-size: 34pt;
        margin: 0;
    }

    .cover .meta {
        margin-top: 10px;
        font-size: 11pt;
        color: #ddd;
    }

    .chapter-page {
        height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
        page-break-before: always;
        page-break-after: always;
        text-align: center;
    }

    .chapter-page h2 {
        font-size: 26pt;
    }

    .toc {
        page-break-after: always;
    }

    .toc h3 {
        margin-top: 16px;
    }

    .toc a {
        display: block;
        margin: 4px 0 4px 12px;
        font-size: 11pt;
        color: #4ea1ff;
        text-decoration: none;
    }

    .section-title {
        page-break-before: always;
        font-size: 20pt;
        margin-bottom: 2em;
    }
    
    a {
        font-size: 11pt;
        color: #4ea1ff;
        text-decoration: none;
    }

    p {
        text-align: justify;
    }
    
    code {
        font-family: "JetBrains Mono", monospace;        
        background: #ececec;
        color: #2d2d2d;
        padding: 1px 3px;
        margin: 0 2px;
        border-radius: 2px;
        font-size: 0.9em;
        font-weight: 500;
    }

    .code {
        background: #363636 !important;
        border-radius: 10px;
        overflow-wrap: break-word;
        padding: 0;
        margin: 10px 0;
    }

    .code,
    .code .highlight,
    .code pre {
        -webkit-box-decoration-break: clone;
        box-decoration-break: clone;
    }

    .code pre {
        background: transparent !important;
        margin: 0;
        padding: 20px;
        font-size: 8pt;
        line-height: 1.4;
    }

    blockquote {
        border-left: 4px solid #363636;
        background: #f0f0f0;
        padding: 12px;
        margin: 20px 0;
    }

    """

    html = []
    html.append(f"""
<html>
<head>
<meta charset="utf-8">
<style>{custom_css}</style>
</head>
<body>
""")

    # COVER
    html.append(f"""
<div class="cover">
<img src="data:image/png;base64,{img_base64}" />
<h1>{title}</h1>
<div class="meta">{author}<br>{date_str}</div>
</div>
""")

    # TOC
    html.append("<div class='toc'><h2>Table of Contents</h2>")

    for item in toc_items:
        if item[0] == "chapter":
            html.append(f"<h3>{item[1]}</h3>")
        else:
            _, name, anchor = item
            html.append(f"<a href='#{anchor}'>{name}</a>")

    html.append("</div>")

    # CONTENT
    in_list = False

    for section in all_sections:
        kind = section[0]

        if kind == "chapter":
            if in_list:
                html.append("</ul>")
                in_list = False

            html.append(f"""
<div class="chapter-page">
<h2>{section[1]}</h2>
</div>
""")

        elif kind == "h_main":            
            if in_list:
                html.append("</ul>")
                in_list = False
                
            html.append(f"<h1 class='section-title' id='{section[2]}'>{section[1]}</h1>")
            
        elif kind == "h1":
            html.append(f"<h2>{section[1]}</h2>")

        elif kind == "h2":
            html.append(f"<h3>{section[1]}</h3>")

        elif kind == "h3":
            html.append(f"<h4>{section[1]}</h4>")


        elif kind == "p":
            if in_list:
                html.append("</ul>")
                in_list = False
            html.append(f"<p>{section[1]}</p>")

        elif kind == "quote":
            if in_list:
                html.append("</ul>")
                in_list = False
            html.append(f"<blockquote>{section[1]}</blockquote>")

        elif kind == "li":
            if not in_list:
                html.append("<ul>")
                in_list = True
            html.append(f"<li>{section[1]}</li>")

        elif kind == "code":
            if in_list:
                html.append("</ul>")
                in_list = False

            highlighted = highlight(
                section[1],
                get_lexer_by_name("swift"),
                formatter
            )
            html.append(f"<div class='code'>{highlighted}</div>")

    if in_list:
        html.append("</ul>")

    html.append("</body></html>")
    return "\n".join(html)

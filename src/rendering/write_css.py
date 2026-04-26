# write_css.py

from src.config.config import FONT_MONTSERRAT, FONT_ROBOTO, FONT_ROBOTO_ITALIC, FONT_SLAB, CSS_PATH


def _build_css(base_css: str) -> str:
    return f"""
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
body {{ font-family: 'Roboto', sans-serif; margin: 0; padding: 0; line-height: 1.4; font-size: 12pt; }}
@page {{ margin: 20mm; }}
.cover {{ width: 100%; height: 100vh; background: #363636; color: white; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; page-break-after: always; }}
.cover img {{ width: 200px; height: auto;   margin-bottom: 20px; display: block; }}
.cover h1 {{ font-size: 26pt; margin: 0; }}
.cover .meta {{ margin-top: 10px; font-size: 11pt; color: #ddd; }}
.chapter-page {{ display: flex; align-items: center; justify-content: center; page-break-before: always; text-align: center; padding-top: 40vh;}}
.chapter-page h2 {{ font-size: 26pt; }}
.toc {{ page-break-after: always; }}
.toc h3 {{ margin-top: 16px; }}
.toc a {{ display: block; margin: 4px 0 4px 12px; font-size: 11pt; color: #4ea1ff; text-decoration: none; }}
.section-title {{ page-break-before: always; font-size: 20pt; margin-bottom: 2em; }}
a {{ font-size: 11pt; color: #4ea1ff; text-decoration: none; }}
p {{ text-align: justify; }}
p.has-link {{ text-align: left; }}
p.has-link a {{ white-space: nowrap; }}
.toc-float {{
    position: fixed;
    right: 0mm;
    bottom: 0mm;
    color: #4ea1ff;
    font-size: 11pt;
    text-decoration: none;
    z-index: -1;
}}
code {{ font-family: "JetBrains Mono", monospace; background: #ececec; color: #2d2d2d; padding: 1px 3px; margin: 0 2px; border-radius: 2px; font-size: 0.9em; font-weight: 500; }}
.code {{ background: #363636 !important; border-radius: 10px; overflow-wrap: break-word; padding: 0; margin: 10px 0; }}
.code, .code .highlight, .code pre {{ -webkit-box-decoration-break: clone; box-decoration-break: clone; }}
.code pre {{ background: transparent !important; margin: 0; padding: 20px; font-size: 8pt; line-height: 1.4; }}
blockquote {{ border-left: 4px solid #363636; background: #f0f0f0; padding: 12px; margin: 20px 0; }}
.asset {{
    margin: 16px 0;
    text-align: center;
    display: block;
    break-inside: avoid;
    page-break-inside: avoid;
    overflow: hidden;
}}
.asset img {{
    max-width: 88%;
    max-height: 62vh;
    width: auto;
    height: auto;
    object-fit: contain;
    border: 1px solid #98a1ab;
    border-radius: 6px;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
    break-inside: avoid;
    page-break-inside: avoid;
}}
.video-frames img {{
    max-width: 92%;
    max-height: 48vh;
    margin: 6px 0;
}}
.video-link img.thumb-rounded {{
    border-radius: 12px;
}}
.similar-section {{
    margin-top: 48px;
}}
{base_css}
"""


def write_styles_css(base_css: str):
    """CSS-t fájlba irja (fejleszteshez)."""
    with open(CSS_PATH, "w", encoding="utf-8") as f:
        f.write(_build_css(base_css))


def get_styles_css(base_css: str) -> str:
    """CSS stringkent adja vissza inline style tagbe agyazashoz."""
    return _build_css(base_css)

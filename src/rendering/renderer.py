# renderer.py

from __future__ import annotations

import math
import tempfile
from pathlib import Path

from playwright.sync_api import Error, sync_playwright
from pypdf import PdfWriter

from src.config.config import TITLE
from src.core.logger import log


# -------------------------
# Config
# -------------------------

CHUNK_SIZE = 20

CHROMIUM_ARGS = [
    "--js-flags=--max-old-space-size=8192",
]


# -------------------------
# PDF render
# -------------------------

def _render_pdf(page, html_str: str, out_path: str):
    page.set_content(
        html_str,
        wait_until="domcontentloaded",
        timeout=1200000,
    )

    page.pdf(
        path=out_path,
        format="A4",
        prefer_css_page_size=True,
        print_background=True,
        scale=1.3,
        margin={
            "top": "25mm",
            "bottom": "25mm",
            "left": "20mm",
            "right": "20mm",
        },
        display_header_footer=True,
        header_template=f"""
        <div style="width:100%; font-size:12px; text-align:center; font-family:'Roboto', sans-serif; color:#000;">
            <span>{TITLE} - Hacking with Swift</span>
            <hr style="border:none; border-top:1px solid #ccc; margin:20px 15%;" />
        </div>
        """,
        footer_template="""
        <div style="width:100%; font-size:12px; text-align:center; font-family:'Roboto', sans-serif; color:#000;">
            <hr style="border:none; border-top:1px solid #ccc; margin:20px 15%;" />
            <div style="position:relative; padding:0 20mm; min-height:14px;">
                <div style="text-align:center;">
                    <span class="pageNumber"></span> / <span class="totalPages"></span>
                </div>
            </div>
        </div>
        """,
    )


# -------------------------
# HTML chunking
# -------------------------

def _split_html_by_h1(
    html: str,
    chunk_size: int = CHUNK_SIZE,
) -> list[str]:

    parts = html.split("<h1")

    # No article tags found.
    if len(parts) <= 1:
        return [html]

    head = parts[0]

    sections = [
        "<h1" + part
        for part in parts[1:]
    ]

    chunks: list[str] = []

    for i in range(0, len(sections), chunk_size):
        subset = sections[i:i + chunk_size]

        chunk_html = head + "".join(subset)

        # Safety fallback.
        if "</body>" not in chunk_html:
            chunk_html += "</body>"

        if "</html>" not in chunk_html:
            chunk_html += "</html>"

        chunks.append(chunk_html)

    return chunks


# -------------------------
# Main API
# -------------------------

def html_to_pdf(html_str: str, out_path: str):

    out_path = str(Path(out_path).resolve())
    
    log(f'articles: {html_str.count("<article")}')
    log(f'sections: {html_str.count("<section")}')
    log(f'divs: {html_str.count("<div")}')
    log(f'h1s: {html_str.count("<h1")}')

    chunks = _split_html_by_h1(html_str)

    print(f"Generated {len(chunks)} HTML chunks.")

    with tempfile.TemporaryDirectory() as temp_dir:

        temp_dir_path = Path(temp_dir)

        with sync_playwright() as p:

            browser = p.chromium.launch(
                headless=True,
                args=CHROMIUM_ARGS,
            )

            try:

                partial_pdfs: list[str] = []

                total_chunks = len(chunks)

                for chunk_index, chunk_html in enumerate(chunks):

                    print(
                        f"Rendering chunk "
                        f"{chunk_index + 1}/{total_chunks}"
                    )

                    page = browser.new_page()

                    partial_pdf_path = (
                        temp_dir_path /
                        f"chunk-{chunk_index:04d}.pdf"
                    )

                    page.emulate_media(media="print")
                    _render_pdf(
                        page,
                        chunk_html,
                        str(partial_pdf_path),
                    )

                    page.close()

                    partial_pdfs.append(str(partial_pdf_path))

                print("Merging PDFs...")

                writer = PdfWriter()

                for pdf_path in partial_pdfs:
                    writer.append(pdf_path)

                with open(out_path, "wb") as f:
                    writer.write(f)

                writer.close()

                print(f"Final PDF written to: {out_path}")

            except Error as e:
                print(f"PDF rendering failed: {e}")
                raise

            finally:
                browser.close()
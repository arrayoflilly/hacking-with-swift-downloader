# renderer.py

from playwright.sync_api import Error, sync_playwright
from src.config.config import TITLE

# -------------------------
# PDF render
# -------------------------

def _render_pdf(page, html_str: str, out_path: str):
    page.set_content(html_str, wait_until="domcontentloaded", timeout=1200000)
    page.pdf(
        path=out_path,
        format="A4",
        print_background=True,
        scale=1.3,
        margin={
            "top": "25mm",
            "bottom": "25mm",
            "left": "20mm",
            "right": "20mm"
        },
        display_header_footer=True,
        header_template=f"""
        <div style="width:100%; font-size:12px; text-align:center; font-family: 'Roboto', sans-serif; color: #000;">
            <span>{TITLE} - Hacking with Swift</span>
            <hr style="border: none; border-top: 1px solid #ccc; margin: 20px 15%;" />
        </div>
        """,
        footer_template="""
        <div style="width:100%; font-size:12px; text-align:center; font-family: 'Roboto', sans-serif; color: #000;">
            <hr style="border: none; border-top: 1px solid #ccc; margin: 20px 15%;" />
            <div style="position: relative; padding: 0 20mm; min-height: 14px;">
                <div style="text-align: center;">
                    <span class="pageNumber"></span> / <span class="totalPages"></span>
                </div>
            </div>
        </div>
        """
    )


def html_to_pdf(html_str: str, out_path: str):
    with sync_playwright() as p:
        # First attempt: standard settings.
        try:
            browser = p.chromium.launch()
            page = browser.new_page()
            _render_pdf(page, html_str, out_path)
            browser.close()
            return
        except Error:
            print("Initial PDF rendering attempt failed, retrying with increased timeouts...")
            try:
                browser.close() # type: ignore
            except Exception:
                print("Failed to close browser.")

        # Fallback attempt: start a fresh browser context and try again.
        browser = p.chromium.launch()
        page = browser.new_page()
        _render_pdf(page, html_str, out_path)
        browser.close()

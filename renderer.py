from playwright.sync_api import sync_playwright
from config import TITLE

# -------------------------
# PDF render
# -------------------------

def html_to_pdf(html_str: str, out_path: str):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        page.set_content(html_str, wait_until="networkidle")

        page.pdf(
            path=out_path,
            format="A4",
            print_background=True,
            scale=1.0,
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
                <span class="pageNumber"></span> / <span class="totalPages"></span>
            </div>
            """
        )

        browser.close()
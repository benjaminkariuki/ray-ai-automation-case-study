"""Renders submission.html to the final PDF with headless Chromium (pip install playwright; playwright install chromium)."""
import pathlib
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
SRC, OUT = HERE / "submission.html", HERE / "Benjamin_Kariuki_RAY_Case_Study.pdf"

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(SRC.as_uri(), wait_until="networkidle")
    page.pdf(path=str(OUT), format="A4", print_background=True, prefer_css_page_size=True,
             display_header_footer=True, header_template="<span></span>",
             footer_template='<div style="font-size:8px;width:100%;text-align:center;color:#888;">'
                             'RAY Case Study – Benjamin Kariuki · page <span class="pageNumber"></span> of <span class="totalPages"></span></div>')
    browser.close()
print("Wrote", OUT, f"({OUT.stat().st_size // 1024} KB)")

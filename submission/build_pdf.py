"""Renders submission.html to the final PDF with headless Chromium (pip install playwright; playwright install chromium).

Fills in Task 2 automatically:
  - the public Notion link from ../.secrets/notion.txt (line `public_url=...`), or a clear "pending" note;
  - Notion screenshots from ../task2-travel-planner/docs/images/ when they exist.
"""
import pathlib
import re

from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
SRC, OUT = HERE / "submission.html", HERE / "Benjamin_Kariuki_RAY_Case_Study.pdf"
TMP = HERE / "_rendered.html"
IMAGES = ROOT / "task2-travel-planner" / "docs" / "images"

secrets = ROOT / ".secrets" / "notion.txt"
public_url = ""
if secrets.exists():
    m = re.search(r"^public_url=(\S+)", secrets.read_text(encoding="utf-8"), re.M)
    public_url = m.group(1).strip() if m else ""

html = SRC.read_text(encoding="utf-8")
if public_url:
    html = html.replace("NOTION_PUBLIC_URL_TEXT", public_url.split("?")[0]).replace("NOTION_PUBLIC_URL", public_url)
else:
    html = html.replace('<a href="NOTION_PUBLIC_URL">NOTION_PUBLIC_URL_TEXT</a>',
                        '<span style="color:#b00">PENDING: public link added after "Share to web"</span>')

shots = [("notion-overview.png", "The planner page: a short guide for the EA and the founder, then the Trips database "
                                 "(Upcoming – Timeline view)."),
         ("notion-board.png", "The By status view: Planned / In-Progress / Done."),
         ("notion-brief.png", "A Trip Brief, generated automatically: summary, 🆘 contacts and the day-by-day timeline.")]
parts = []
for file, caption in shots:
    if (IMAGES / file).exists():
        cls = "shot crop-ov" if file == "notion-overview.png" else "shot"
        parts.append(f'<img class="{cls}" src="../task2-travel-planner/docs/images/{file}" alt="{file}">'
                     f'<div class="cap">{caption}</div>')
if (IMAGES / "notion-brief-mobile.png").exists():
    parts.append('<div class="two"><div><img class="phone" src="../task2-travel-planner/docs/images/notion-brief-mobile.png">'
                 '</div><div class="cap" style="padding-top:20px">The same Trip Brief on a phone (390 px wide): '
                 'headings, bullets and callouts only, with no wide tables, so nothing needs side-scrolling.</div></div>')
html = html.replace("TASK2_SCREENSHOTS", "\n".join(parts))
TMP.write_text(html, encoding="utf-8")

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(TMP.as_uri(), wait_until="networkidle")
    page.pdf(path=str(OUT), format="A4", print_background=True, prefer_css_page_size=True,
             display_header_footer=True, header_template="<span></span>",
             footer_template='<div style="font-size:8px;width:100%;text-align:center;color:#888;">'
                             'RAY Case Study – Benjamin Kariuki · page <span class="pageNumber"></span> of '
                             '<span class="totalPages"></span></div>')
    browser.close()
TMP.unlink()
print(f"Wrote {OUT.name}: {OUT.stat().st_size / 1024 / 1024:.2f} MB | Notion link: {'yes' if public_url else 'PENDING'} "
      f"| Task 2 screenshots: {len(parts)}")

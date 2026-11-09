# Requirements check: every line of the brief

Each requirement is quoted from the case-study brief, followed by how it's met and where to verify it.
Status: ✅ met, tested live on 8–9 November 2026.

**Links:**
- Repository: https://github.com/benjaminkariuki/ray-ai-automation-case-study
- Google Sheet: https://docs.google.com/spreadsheets/d/1GwAt8R3_O-h6ivZ_CT_8yD6GMIdybyf2-YgscTQ9hRI (anyone with the link can view and edit)
- Task 1 – Run it now (optional): https://ray-run-now.run-now.workers.dev: a complementary page for extra manual runs; the automatic daily schedule is the default
- Notion (public): https://billowy-target-f39.notion.site/Executive-Travel-Planner-Benjamin-Kariuki-412d73ee564d807d82e8f40be8b6009c

---

## Task 1 – Executive Assistant Job Outreach Automation

| # | Brief says | How it is met | Verify | |
|---|---|---|---|---|
| 1 | "automatically search job platforms (excluding LinkedIn) for relevant postings" | Daily search of **Himalayas, RemoteOK and Jobicy**. LinkedIn is never used. | [sources.py](task1-job-outreach/job_outreach/sources.py); Sheet → *Source* column | ✅ |
| 2 | "verify key criteria (remote work, English requirement, role relevance)" | An LLM returns strict JSON (`is_remote`, `is_english`, `is_relevant`) with a reason. | Sheet → **Rejected** tab (Yes/No for each check, plus the reason) | ✅ |
| 3 | "generate tailored outreach messages using an LLM" | A second LLM call per lead, based on that posting's details. | Sheet → *LLM-Generated Outreach Message* | ✅ |
| 4 | "save everything to a Google Sheet that a sales rep can use as a dashboard" | **Leads** tab with a Status dropdown, colour coding, filters and Notes; a **How to Use** tab; a **Run Log**. Anyone with the link can edit. | The Google Sheet | ✅ |
| 5 | "Build a scraper … pick at least one compliant, non-LinkedIn job board (respect its terms of service, or use available APIs)" | **3 official public JSON APIs**, no HTML scraping. Each row keeps the original URL and its source name (the boards ask for attribution and a link back). Requests are paced (1 s between pages). | [sources.py](task1-job-outreach/job_outreach/sources.py) | ✅ |
| 6 | "Collect for each posting: Job Title, Company Name, Location, Job Description, Job Posting URL, and any language requirements" | Every scraped posting gets all six fields. **Language requirements** are extracted by rules for every posting, and refined by the AI for checked jobs. | [sample-output/latest/](task1-job-outreach/sample-output/latest/) → `*-all-postings.csv` | ✅ |
| 7 | "Store the results in a structured format (CSV, JSON, or a database)" | Each run writes **JSON** (every posting plus every AI decision), **CSVs** (all postings, leads, rejections) and a console **log**. Results also go to the Google Sheet. | [sample-output/](task1-job-outreach/sample-output/) | ✅ |
| 8 | "automatically decide from each description whether the job is remote, English-speaking, and relevant to an Executive/Admin Assistant" | The validation prompt is applied to each description (the first 6,000 characters). An incomplete AI answer is retried rather than treated as a rejection. | [validation_prompt.md](task1-job-outreach/prompts/validation_prompt.md), [ai.py](task1-job-outreach/job_outreach/ai.py) | ✅ |
| 9 | "Only keep postings that meet all three" | `is_lead = remote and english and relevant` (plus a configurable staffing-agency exclusion, since agencies are competitors). Everything else goes to Rejected. | [pipeline.py](task1-job-outreach/job_outreach/pipeline.py); `verify_sheet.py` check "Every rejection failed a check" | ✅ |
| 10 | "generate a genuinely personalized outreach message per posting" | Each message cites duties, tools or team details from that posting. The AI may only state facts about us from `sender_offer`. | `verify_sheet.py`: "39/39 messages reference the specific posting" and "Messages are clean" | ✅ |
| 11 | "The prompt must be easily interchangeable so tone/wording can be tested without rebuilding the workflow" | Prompts live in the Sheet's **Prompts** tab. Changing **Settings → outreach_prompt** switches the prompt on the next run, with no code change. Each lead records **Prompt Used**. | Leads → *Prompt Used* shows `v1_warm` and `v2_direct` (tested live) | ✅ |
| 12 | "Save to Google Sheets — with columns: Job Posting URL, Job Title, Company Name, Location, Job Description, LLM-Generated Outreach Message" | Exactly these 6 columns come first, in this order. Tracking columns follow. | `verify_sheet.py`: "Required columns, in order" | ✅ |
| 13 | "schedule the process to run daily or weekly" | GitHub Actions runs **daily at about 06:07 UTC**. Because GitHub's free scheduler can skip a slot, backup slots every 3 hours and an independent Cloudflare trigger start it later that day if no daily run has succeeded; a failed run is retried 3 times. Editing the cron lines makes it weekly. This automatic schedule is the default; as a complementary extra, anyone can start an additional run manually from the public **Run now** page. | [job-outreach.yml](.github/workflows/job-outreach.yml), [run-now/](task1-job-outreach/run-now/); Sheet → Run Log | ✅ |
| 14 | "README/user guide covering install, how to run, how to adjust filters and the LLM prompt, basic troubleshooting, and how a sales rep uses the Sheet" | README sections 5, 5, 4, 4, 6 and 3 respectively, plus a 5-minute evaluator guide. | [task1-job-outreach/README.md](task1-job-outreach/README.md) | ✅ |
| D1 | Deliverable: "Source code (scrape, validate, LLM, Sheets)" | `sources.py` / `filters.py`, `ai.py` + prompts, `ai.py`, and `sheet.py` + `setup_sheet.py` | [job_outreach/](task1-job-outreach/job_outreach/) | ✅ |
| D2 | Deliverable: "sample data output (CSV/JSON or console)" | All three: CSV, JSON and the console `.log`, refreshed after every run | [sample-output/](task1-job-outreach/sample-output/) | ✅ |
| D3 | Deliverable: "the scheduling setup (or clear documentation of it)" | The workflow file, the Run now Worker, and README section 5 | [job-outreach.yml](.github/workflows/job-outreach.yml) | ✅ |
| D4 | Deliverable: "the README" | ✅ | [README](task1-job-outreach/README.md) | ✅ |
| D5 | Deliverable: "the populated Google Sheet" | 39 leads, 37 rejections and the run history, colour-coded | Google Sheet link above | ✅ |

**Testing.** There are 17 offline unit tests (filtering, language detection, parsing, formatting, AI failover, message quality checks and broken Settings); they run before every run. The live end-to-end runs are on GitHub Actions. After each run, `verify_sheet.py` checks the live Sheet; the latest result is 13/13. Details are in [TEST_REPORT.md](task1-job-outreach/docs/TEST_REPORT.md).

---

## Task 2 – Executive Travel Planner (Notion)

| # | Brief says | How it is met | Verify | |
|---|---|---|---|---|
| 1 | "log trip details, view a clear timeline per journey, and generate a shareable, mobile-friendly Trip Brief" | A Trips database, a day-by-day timeline inside every brief, and list, calendar and timeline views; the brief is generated automatically. | Notion page | ✅ |
| 2 | "Trips Database — one record per trip" (single-database structure) | One **Trips** database. Each trip is one record, with 23 sample trips across Europe and the USA. | Notion → *All trips* view | ✅ |
| 3 | "capturing: trip name, who is traveling, date range" | **Trip** (title), **Traveler**, **Travel Dates** (range) | Any trip | ✅ |
| 4 | "all essential details (flights, hotels, addresses, confirmations, meetings, notes)" | **Flights**, **Hotel**, **Hotel Address**, **Hotel Confirmation**, flight PNRs and other confirmations, meetings in **Itinerary**, **Notes**, plus Ground Transport, Visa / Entry and Visa Notes | Any trip | ✅ |
| 5 | "Trip Brief template — an auto-generated, shareable summary per trip" | Every trip page holds a **✈️ Trip Brief**, written automatically from its fields and refreshed within 15 minutes of any edit (GitHub Actions). | Open *London — Investor Roadshow* | ✅ |
| 6 | "a chronological timeline of key events" | **📅 Day by day**: itinerary events sorted by date and time and grouped by day, with icons and confirmation numbers; while travelling, a **Today** box comes first | Any brief | ✅ |
| 7 | "space to attach documents (tickets, visas)" | The **Documents** files field (3 SAMPLE PDFs attached to each trip), listed in the brief, plus an **📂 Extra files & notes** area that's never overwritten | Any trip | ✅ |
| 8 | "clear emergency/primary contact info" | A red **🆘** box near the top of every brief: primary contact (the EA, benjaminleyian50@gmail.com), emergency contact and hotel | Any brief | ✅ |
| 9 | "Saved views — at least a timeline/calendar view of upcoming trips" | **Upcoming trips** (the default list), **Calendar** and **Timeline**; Done trips are hidden from Upcoming and Timeline | Notion views | ✅ |
| 10 | "an overview grouped by trip status (Planned / In-Progress / Done)" | The **By status** board, grouped by a Status property with exactly these three options | Notion views | ✅ |
| 11 | "Notion 'Share to web' link (anyone with the link can view)" | Published to the web, view-only | Link in the PDF | ✅ |
| 12 | "titled 'Executive Travel Planner – {Your Name}'" | **Executive Travel Planner – Benjamin Kariuki** | Page title | ✅ |
| 13 | "everything is easy to find and the Trip Brief is founder-ready" | Built for zero learning curve: one line at the top plus an automatic **Travelling now / Next trip** box (two taps to any brief); every trip link opens the trip scrolled straight to its brief; views show only trip, brief link, dates and countdown. Briefs lead with where/when/hotel, then any action needed, today, who to call and each day, using phone-friendly blocks only. | Notion page | ✅ |
| 14 | "Optional bonus: a short note … explaining your design choices" | "Design choices" in the PDF (Task 2 section) and the "Design" section of the Task 2 README | [task2-travel-planner/README.md](task2-travel-planner/README.md) | ✅ |

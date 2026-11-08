"""
One-time setup of the Google Sheet dashboard used by the n8n workflow.

Creates (or repairs) these tabs: How to Use, Leads, Rejected, Settings, Prompts, Run Log.
Safe to re-run: existing Leads/Rejected/Run Log rows are never touched; Settings and Prompts
are only seeded when empty (use --reset-settings to overwrite them with the defaults).

Usage:
    pip install -r requirements.txt
    python setup_sheet.py --sheet-id <SPREADSHEET_ID> --key <service-account.json> [--public] [--reset-settings]
"""
import argparse
import pathlib

import gspread
from google.oauth2.service_account import Credentials

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROMPTS = ROOT / "prompts"

LEADS_HEADERS = [
    "Job Posting URL", "Job Title", "Company Name", "Location", "Job Description",
    "LLM-Generated Outreach Message", "Language Requirements", "Source", "Date Posted",
    "Date Found", "Prompt Used", "AI Model", "Status", "Notes",
]
REJECTED_HEADERS = [
    "Job Posting URL", "Job Title", "Company Name", "Location", "Remote", "English",
    "Relevant", "Agency", "Reason", "Source", "Date Checked", "AI Model",
]
RUNLOG_HEADERS = [
    "Run Time (UTC)", "Trigger", "Fetched", "Passed Keyword Filter", "Already Seen", "Checked by LLM",
    "Leads Added", "Rejected", "LLM Errors", "Backup AI Used",
]
STATUSES = ["New", "Contacted", "Replied", "Meeting Booked", "Not a Fit"]
STATUS_COLORS = {  # soft fills so the sheet stays readable
    "New": (0.85, 0.92, 1.0), "Contacted": (1.0, 0.95, 0.8), "Replied": (0.85, 0.95, 0.85),
    "Meeting Booked": (0.72, 0.88, 0.72), "Not a Fit": (0.93, 0.93, 0.93),
}

SETTINGS = [
    ["Setting", "Value", "What it does"],
    ["search_queries", "executive assistant, administrative assistant, admin assistant, personal assistant",
     "Comma-separated searches sent to Himalayas (RemoteOK uses its 'assistant' tag, Jobicy its 'Admin & Support' category)."],
    ["himalayas_pages_per_query", "3", "Result pages per search (20 jobs per page)."],
    ["title_include_keywords",
     "executive assistant, administrative assistant, admin assistant, personal assistant, executive admin, "
     "assistant to the ceo, assistant to the founder, office administrator, administrative coordinator",
     "A job title must contain at least one of these to be considered (case-insensitive)."],
    ["title_exclude_keywords",
     "medical, dental, veterinary, nurse, pharmacy, teaching, research, sales, marketing, engineer, developer, "
     "student, intern, clinical",
     "Jobs whose title contains any of these are skipped before the LLM step."],
    ["excluded_companies",
     "Wing Assistant, Assist World, OurAssistants, Assistant Launch, VirtuHire, Hire Hangar, Globibo, ScaleJet, "
     "Outsource Access Careers, RemoteVA, Hire Overseas, Scale-X Solutions, Job Duck, InsideOutVAS, Pavago, "
     "HireBoost, STAFFVIRTUAL, DCX PH",
     "Companies never to contact (e.g. competitors / VA agencies)."],
    ["exclude_agencies", "TRUE", "TRUE = also drop postings the LLM identifies as staffing/VA agencies."],
    ["max_posting_age_days", "30", "Ignore postings older than this many days."],
    ["max_jobs_per_run", "15", "Cap on new postings sent to the LLM per run (protects free-tier limits)."],
    ["validation_model", "nvidia/nemotron-3-ultra-550b-a55b:free", "OpenRouter model used to check remote / English / relevance."],
    ["outreach_model", "nvidia/nemotron-3-ultra-550b-a55b:free", "OpenRouter model used to write the outreach message."],
    ["fallback_model", "google/gemma-4-31b-it:free", "OpenRouter tries this model if the main model is busy or down."],
    ["backup_model", "@cf/openai/gpt-oss-120b",
     "Cloudflare Workers AI model used automatically if OpenRouter fails or hits its daily limit."],
    ["outreach_prompt", "v1_warm", "Which prompt from the Prompts tab writes the messages (Prompt Name)."],
    ["sender_name", "Benjamin Kariuki", "Signs the outreach message."],
    ["sender_company", "RAY", "Company named in the outreach message."],
    ["sender_offer",
     "RAY provides dedicated, pre-vetted remote Executive Assistants who run founders' inboxes, calendars, "
     "travel and operations, supported by AI and automation tools. Assistants can start within days.",
     "One or two sentences describing what we offer. The LLM uses this as the only facts about us."],
    ["call_to_action", "Would a 15-minute call this week be useful to see if we are a fit?",
     "Closing question the message ends with."],
]

HOW_TO = [
    ["How to use this sheet"],
    [""],
    ["WHAT IT IS"],
    ["Every day at 06:00 UTC an automation finds new remote, English-speaking Executive/Admin Assistant jobs "
     "(Himalayas, RemoteOK, Jobicy), checks them with AI and writes a personalised outreach email for each match."],
    [""],
    ["DAILY ROUTINE FOR SALES REPS"],
    ["1. Open the Leads tab. Filter Status = New."],
    ["2. Read the job (Job Posting URL) and the draft in LLM-Generated Outreach Message. Edit it if needed."],
    ["3. Send it from your own email/LinkedIn, then change Status to Contacted."],
    ["4. Update Status as things progress: Replied, Meeting Booked, or Not a Fit. Use Notes for context."],
    [""],
    ["TABS"],
    ["Leads - qualified jobs with outreach drafts (your dashboard)."],
    ["Rejected - jobs the AI filtered out, with the reason. Check here if you think a good job was missed."],
    ["Settings - search words, filters, AI models and sender details. Changes apply on the next run."],
    ["Prompts - the AI instructions. Add a new row to test a different tone, then set Settings > outreach_prompt to its name."],
    ["Run Log - one row per run with counts, so you can see the automation is healthy."],
    [""],
    ["TIPS"],
    ["- Never delete rows in Leads/Rejected: the automation uses them to avoid duplicates. Use Status = Not a Fit instead."],
    ["- Sort or filter freely; column order must stay as is."],
    ["- Job data comes from Himalayas, RemoteOK and Jobicy; always apply via the original Job Posting URL."],
]


def prompt_rows():
    return [
        ["Prompt Name", "Type", "Prompt Text", "Notes"],
        ["v1_warm", "outreach", (PROMPTS / "outreach_v1_warm.md").read_text(encoding="utf-8").strip(),
         "Default. Warm, specific, 120-160 words."],
        ["v2_direct", "outreach", (PROMPTS / "outreach_v2_direct.md").read_text(encoding="utf-8").strip(),
         "Shorter, bullet points, outcome-focused."],
        ["validation", "validation", (PROMPTS / "validation_prompt.md").read_text(encoding="utf-8").strip(),
         "Decides remote / English / relevant / agency. Must keep the JSON output format."],
    ]


def get_ws(sh, title, rows=1000, cols=20):
    try:
        return sh.worksheet(title)
    except gspread.WorksheetNotFound:
        return sh.add_worksheet(title=title, rows=rows, cols=cols)


def col_width_req(sheet_id, widths):
    return [{"updateDimensionProperties": {
        "range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": i, "endIndex": i + 1},
        "properties": {"pixelSize": w}, "fields": "pixelSize"}} for i, w in enumerate(widths)]


def header_req(sheet_id, ncols, color=(0.13, 0.2, 0.33)):
    return [
        {"repeatCell": {
            "range": {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": ncols},
            "cell": {"userEnteredFormat": {
                "backgroundColor": {"red": color[0], "green": color[1], "blue": color[2]},
                "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
                "verticalAlignment": "MIDDLE", "wrapStrategy": "WRAP"}},
            "fields": "userEnteredFormat(backgroundColor,textFormat,verticalAlignment,wrapStrategy)"}},
        {"updateSheetProperties": {"properties": {"sheetId": sheet_id, "gridProperties": {"frozenRowCount": 1}},
                                   "fields": "gridProperties.frozenRowCount"}},
    ]


def body_format_req(sheet_id, ncols, wrap="CLIP"):
    return [{"repeatCell": {
        "range": {"sheetId": sheet_id, "startRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": ncols},
        "cell": {"userEnteredFormat": {"verticalAlignment": "TOP", "wrapStrategy": wrap}},
        "fields": "userEnteredFormat(verticalAlignment,wrapStrategy)"}}]


def ensure_headers(ws, headers):
    """Writes the header row. If a newer version added columns, inserts them in place so existing data shifts correctly."""
    original = ws.row_values(1)
    current = list(original)
    if current and current != headers:
        for idx, h in enumerate(headers):
            if h not in current:
                if idx < ws.col_count:
                    ws.insert_cols([[]], col=idx + 1)
                else:
                    ws.add_cols(1)
                current.insert(idx, h)
    if original != headers:
        ws.update(range_name="A1", values=[headers])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet-id", required=True)
    ap.add_argument("--key", required=True, help="Path to the Google service-account JSON key")
    ap.add_argument("--public", action="store_true", help="Make the sheet viewable by anyone with the link")
    ap.add_argument("--reset-settings", action="store_true", help="Overwrite Settings and Prompts with defaults")
    args = ap.parse_args()

    creds = Credentials.from_service_account_file(args.key, scopes=[
        "https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(args.sheet_id)

    how = get_ws(sh, "How to Use", rows=60, cols=1)
    leads = get_ws(sh, "Leads", cols=len(LEADS_HEADERS))
    rejected = get_ws(sh, "Rejected", cols=len(REJECTED_HEADERS))
    settings = get_ws(sh, "Settings", rows=50, cols=3)
    prompts = get_ws(sh, "Prompts", rows=50, cols=4)
    runlog = get_ws(sh, "Run Log", cols=len(RUNLOG_HEADERS))

    # Remove the default empty "Sheet1" if present
    for ws in sh.worksheets():
        if ws.title in ("Sheet1", "Hoja 1", "Feuille 1") and len(sh.worksheets()) > 1:
            sh.del_worksheet(ws)

    how.clear()
    how.update(range_name="A1", values=HOW_TO)
    ensure_headers(leads, LEADS_HEADERS)
    ensure_headers(rejected, REJECTED_HEADERS)
    ensure_headers(runlog, RUNLOG_HEADERS)
    if args.reset_settings or not settings.acell("A2").value:
        settings.clear()
        settings.update(range_name="A1", values=SETTINGS)
    if args.reset_settings or not prompts.acell("A2").value:
        prompts.clear()
        prompts.update(range_name="A1", values=prompt_rows())

    status_col = LEADS_HEADERS.index("Status")
    req = []
    # Tab order and colours
    for idx, (ws, color) in enumerate([(how, (0.4, 0.4, 0.4)), (leads, (0.2, 0.5, 0.9)), (rejected, (0.8, 0.3, 0.3)),
                                       (settings, (0.95, 0.6, 0.1)), (prompts, (0.6, 0.3, 0.8)), (runlog, (0.3, 0.7, 0.4))]):
        req.append({"updateSheetProperties": {"properties": {"sheetId": ws.id, "index": idx,
                    "tabColorStyle": {"rgbColor": {"red": color[0], "green": color[1], "blue": color[2]}}},
                    "fields": "index,tabColorStyle"}})
    # How to Use
    req += col_width_req(how.id, [900])
    req += [{"repeatCell": {"range": {"sheetId": how.id, "startRowIndex": 0, "endRowIndex": 1},
             "cell": {"userEnteredFormat": {"textFormat": {"bold": True, "fontSize": 16}}}, "fields": "userEnteredFormat.textFormat"}}]
    for r, row in enumerate(HOW_TO):
        if row[0].isupper() and row[0]:
            req.append({"repeatCell": {"range": {"sheetId": how.id, "startRowIndex": r, "endRowIndex": r + 1},
                        "cell": {"userEnteredFormat": {"textFormat": {"bold": True}}}, "fields": "userEnteredFormat.textFormat"}})
    req.append({"repeatCell": {"range": {"sheetId": how.id}, "cell": {"userEnteredFormat": {"wrapStrategy": "WRAP"}},
                "fields": "userEnteredFormat.wrapStrategy"}})
    # Leads
    req += header_req(leads.id, len(LEADS_HEADERS)) + body_format_req(leads.id, len(LEADS_HEADERS))
    req += col_width_req(leads.id, [220, 200, 150, 140, 260, 420, 160, 90, 95, 95, 90, 170, 120, 200])
    for c in (1, 2, 3, 5, 6, 11, 13):  # Title, Company, Location, Message, Languages, AI Model, Notes wrap; URL + Description stay one line
        req.append({"repeatCell": {"range": {"sheetId": leads.id, "startRowIndex": 1, "startColumnIndex": c, "endColumnIndex": c + 1},
                    "cell": {"userEnteredFormat": {"wrapStrategy": "WRAP"}}, "fields": "userEnteredFormat.wrapStrategy"}})
    req.append({"setDataValidation": {"range": {"sheetId": leads.id, "startRowIndex": 1}}})  # clear old dropdowns
    req.append({"setDataValidation": {
        "range": {"sheetId": leads.id, "startRowIndex": 1, "startColumnIndex": status_col, "endColumnIndex": status_col + 1},
        "rule": {"condition": {"type": "ONE_OF_LIST", "values": [{"userEnteredValue": s} for s in STATUSES]},
                 "showCustomUi": True, "strict": False}}})
    for s, (r, g, b) in STATUS_COLORS.items():
        req.append({"addConditionalFormatRule": {"index": 0, "rule": {
            "ranges": [{"sheetId": leads.id, "startRowIndex": 1, "startColumnIndex": status_col, "endColumnIndex": status_col + 1}],
            "booleanRule": {"condition": {"type": "TEXT_EQ", "values": [{"userEnteredValue": s}]},
                            "format": {"backgroundColor": {"red": r, "green": g, "blue": b}}}}}})
    req.append({"setBasicFilter": {"filter": {"range": {"sheetId": leads.id, "startRowIndex": 0,
                                                         "startColumnIndex": 0, "endColumnIndex": len(LEADS_HEADERS)}}}})
    # Rejected
    req += header_req(rejected.id, len(REJECTED_HEADERS), (0.45, 0.2, 0.2)) + body_format_req(rejected.id, len(REJECTED_HEADERS))
    req += col_width_req(rejected.id, [220, 200, 150, 140, 85, 85, 85, 85, 380, 90, 110, 200])
    req.append({"setBasicFilter": {"filter": {"range": {"sheetId": rejected.id, "startRowIndex": 0,
                                                         "startColumnIndex": 0, "endColumnIndex": len(REJECTED_HEADERS)}}}})
    # Settings / Prompts / Run Log
    req += header_req(settings.id, 3) + body_format_req(settings.id, 3, "WRAP") + col_width_req(settings.id, [210, 520, 420])
    req += header_req(prompts.id, 4) + body_format_req(prompts.id, 4, "WRAP") + col_width_req(prompts.id, [120, 100, 700, 280])
    req += header_req(runlog.id, len(RUNLOG_HEADERS)) + col_width_req(runlog.id, [150, 120] + [120] * 8)

    # Clear old conditional formats on Leads first so re-runs don't stack duplicates
    meta = sh.fetch_sheet_metadata({"fields": "sheets(properties.sheetId,conditionalFormats)"})
    for s in meta["sheets"]:
        if s["properties"]["sheetId"] == leads.id:
            for _ in s.get("conditionalFormats", []):
                req.insert(0, {"deleteConditionalFormatRule": {"sheetId": leads.id, "index": 0}})
    sh.batch_update({"requests": req})

    if args.public:
        sh.share(None, perm_type="anyone", role="reader")
    print(f"Sheet ready: https://docs.google.com/spreadsheets/d/{args.sheet_id}")


if __name__ == "__main__":
    main()

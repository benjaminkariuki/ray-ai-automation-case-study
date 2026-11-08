"""Google Sheet access: reads Settings/Prompts/already-processed URLs, appends Leads/Rejected/Run Log rows.

Rows are written by matching dict keys to the tab's header row, so column order in the Sheet can change
without breaking anything. Values are written RAW (no formula injection from job descriptions).
"""
import json
import os

import gspread
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def _list(value):
    return [s.strip().lower() for s in str(value or "").split(",") if s.strip()]


class Sheet:
    def __init__(self, sheet_id=None, credentials_json=None, credentials_file=None):
        sheet_id = sheet_id or os.environ.get("SHEET_ID")
        credentials_json = credentials_json or os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
        credentials_file = credentials_file or os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE")
        if not sheet_id:
            raise SystemExit("SHEET_ID is not set (see .env.example).")
        if credentials_json:
            creds = Credentials.from_service_account_info(json.loads(credentials_json), scopes=SCOPES)
        elif credentials_file:
            creds = Credentials.from_service_account_file(credentials_file, scopes=SCOPES)
        else:
            raise SystemExit("Set GOOGLE_SERVICE_ACCOUNT_JSON or GOOGLE_SERVICE_ACCOUNT_FILE (see .env.example).")
        self.book = gspread.authorize(creds).open_by_key(sheet_id)
        self.sheet_id = sheet_id

    def load_config(self):
        """Settings tab (Setting | Value) + Prompts tab (Prompt Name | Type | Prompt Text) -> config dict."""
        s = {str(r["Setting"]).strip(): str(r.get("Value", "")).strip()
             for r in self.book.worksheet("Settings").get_all_records() if r.get("Setting")}
        prompts = {str(r["Prompt Name"]).strip(): str(r.get("Prompt Text", ""))
                   for r in self.book.worksheet("Prompts").get_all_records() if r.get("Prompt Name")}
        name = s.get("outreach_prompt") or "v1_warm"
        if name not in prompts:
            raise SystemExit(f'Settings > outreach_prompt is "{name}" but the Prompts tab has no row with that name.')
        if "validation" not in prompts:
            raise SystemExit('The Prompts tab needs a row named "validation".')
        config = {
            "search_queries": _list(s.get("search_queries")),
            "himalayas_pages_per_query": max(1, min(5, int(s.get("himalayas_pages_per_query") or 3))),
            "title_include_keywords": _list(s.get("title_include_keywords")),
            "title_exclude_keywords": _list(s.get("title_exclude_keywords")),
            "excluded_companies": _list(s.get("excluded_companies")),
            "exclude_agencies": s.get("exclude_agencies", "TRUE").upper() != "FALSE",
            "max_posting_age_days": int(s.get("max_posting_age_days") or 30),
            "max_jobs_per_run": int(s.get("max_jobs_per_run") or 15),
            "validation_model": s.get("validation_model") or "nvidia/nemotron-3-ultra-550b-a55b:free",
            "outreach_model": s.get("outreach_model") or "nvidia/nemotron-3-ultra-550b-a55b:free",
            "fallback_model": s.get("fallback_model", ""),
            "backup_model": s.get("backup_model") or "@cf/openai/gpt-oss-120b",
            "outreach_prompt_name": name,
            "outreach_prompt_text": prompts[name],
            "validation_prompt": prompts["validation"],
            "sender": {k: s.get(k, "") for k in ("sender_name", "sender_company", "sender_offer", "call_to_action")},
        }
        if not config["search_queries"]:
            raise SystemExit("Settings > search_queries is empty.")
        return config

    def seen_urls(self):
        urls = set()
        for tab in ("Leads", "Rejected"):
            values = self.book.worksheet(tab).col_values(1)[1:]
            urls.update(v.strip() for v in values if v.strip())
        return urls

    def append(self, tab, rows):
        """Append dict rows, matching keys to the header row of the tab."""
        if not rows:
            return 0
        ws = self.book.worksheet(tab)
        headers = ws.row_values(1)
        missing = sorted({k for r in rows for k in r} - set(headers))
        if missing:
            raise SystemExit(f"Tab '{tab}' is missing columns {missing}. Run: python scripts/setup_sheet.py ...")
        ws.append_rows([[r.get(h, "") for h in headers] for r in rows], value_input_option="RAW",
                       insert_data_option="INSERT_ROWS", table_range="A1")
        return len(rows)

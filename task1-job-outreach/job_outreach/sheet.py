"""Google Sheet access: reads Settings/Prompts/already-processed URLs, appends Leads/Rejected/Run Log rows.

Rows are written by matching dict keys to the tab's header row, so column order in the Sheet can change
without breaking anything. Values are written RAW (no formula injection from job descriptions).
"""
import json
import os
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"

# Used when a Settings value is empty or invalid (keep in sync with scripts/setup_sheet.py).
DEFAULTS = {
    "search_queries": "executive assistant, administrative assistant, admin assistant, personal assistant",
    "himalayas_pages_per_query": "3",
    "title_include_keywords": "executive assistant, administrative assistant, admin assistant, personal assistant, "
                              "executive admin, assistant to the ceo, assistant to the founder, office administrator, "
                              "administrative coordinator",
    "exclude_agencies": "TRUE",
    "max_posting_age_days": "30",
    "max_jobs_per_run": "15",
    "validation_model": "nvidia/nemotron-3-ultra-550b-a55b:free",
    "outreach_model": "nvidia/nemotron-3-ultra-550b-a55b:free",
    "fallback_model": "google/gemma-4-31b-it:free",
    "backup_model": "@cf/openai/gpt-oss-120b",
    "outreach_prompt": "v1_warm",
    "sender_name": "Benjamin Kariuki",
    "sender_company": "RAY",
    "sender_offer": "RAY provides dedicated, pre-vetted remote Executive Assistants who run founders' inboxes, "
                    "calendars, travel and operations, supported by AI and automation tools. Assistants can start "
                    "within days.",
    "call_to_action": "Would a 15-minute call this week be useful to see if we are a fit?",
}


def _file_prompt(name):
    return (PROMPTS_DIR / name).read_text(encoding="utf-8").strip()


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
        """Settings tab (Setting | Value) + Prompts tab (Prompt Name | Type | Prompt Text) -> config dict.

        Anyone with the link may edit the Sheet, so a broken value never stops the daily run: it falls back to the
        default (prompts/ folder or DEFAULTS above) and the problem is listed in config["warnings"] and the run log."""
        warnings = []
        s, prompts = {}, {}
        try:
            s = {str(r.get("Setting", "")).strip(): str(r.get("Value", "")).strip()
                 for r in self.book.worksheet("Settings").get_all_records() if str(r.get("Setting", "")).strip()}
        except Exception as exc:  # noqa: BLE001 - tab deleted or headers renamed
            warnings.append(f"Settings tab unreadable ({str(exc)[:80]}): using default settings")
        try:
            prompts = {str(r.get("Prompt Name", "")).strip(): str(r.get("Prompt Text", ""))
                       for r in self.book.worksheet("Prompts").get_all_records()
                       if str(r.get("Prompt Name", "")).strip() and str(r.get("Prompt Text", "")).strip()}
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"Prompts tab unreadable ({str(exc)[:80]}): using the prompts/ folder")

        def get(key):
            value = s.get(key, "")
            return value if value else DEFAULTS[key]

        def number(key, low, high):
            try:
                return max(low, min(high, int(float(get(key)))))
            except ValueError:
                warnings.append(f'Settings > {key} = "{s.get(key)}" is not a number: using {DEFAULTS[key]}')
                return int(DEFAULTS[key])

        name = get("outreach_prompt")
        if name not in prompts:
            fallback = "v1_warm" if "v1_warm" in prompts else None
            warnings.append(f'Settings > outreach_prompt "{name}" not found in the Prompts tab: using '
                            f'{fallback or "prompts/outreach_v1_warm.md"}')
            name = fallback or "v1_warm"
            prompts.setdefault("v1_warm", _file_prompt("outreach_v1_warm.md"))
        if "validation" not in prompts:
            warnings.append('Prompts tab has no "validation" row: using prompts/validation_prompt.md')
            prompts["validation"] = _file_prompt("validation_prompt.md")
        queries = _list(get("search_queries")) or _list(DEFAULTS["search_queries"])
        config = {
            "search_queries": queries,
            "himalayas_pages_per_query": number("himalayas_pages_per_query", 1, 5),
            "title_include_keywords": _list(get("title_include_keywords")),
            "title_exclude_keywords": _list(s.get("title_exclude_keywords")),
            "excluded_companies": _list(s.get("excluded_companies")),
            "exclude_agencies": get("exclude_agencies").upper() != "FALSE",
            "max_posting_age_days": number("max_posting_age_days", 1, 365),
            "max_jobs_per_run": number("max_jobs_per_run", 1, 40),
            "validation_model": get("validation_model"),
            "outreach_model": get("outreach_model"),
            "fallback_model": s.get("fallback_model", DEFAULTS["fallback_model"]),
            "backup_model": get("backup_model"),
            "outreach_prompt_name": name,
            "outreach_prompt_text": prompts[name],
            "validation_prompt": prompts["validation"],
            "sender": {k: get(k) for k in ("sender_name", "sender_company", "sender_offer", "call_to_action")},
            "warnings": warnings,
        }
        return config

    def seen_urls(self):
        urls = set()
        for tab in ("Leads", "Rejected"):
            values = self._tab(tab).col_values(1)[1:]
            urls.update(v.strip() for v in values if v.strip() and v.strip().startswith("http"))
        return urls

    def _tab(self, tab):
        """The worksheet, recreated with its header row if someone deleted it."""
        try:
            return self.book.worksheet(tab)
        except gspread.WorksheetNotFound:
            return self.book.add_worksheet(title=tab, rows=1000, cols=20)

    def append(self, tab, rows):
        """Append dict rows, matching keys to the header row of the tab."""
        if not rows:
            return 0
        ws = self._tab(tab)
        headers = ws.row_values(1)
        missing = [k for k in rows[0] if k not in headers]
        if missing:  # a column was deleted or renamed: add it back at the end so no data is lost
            headers += missing
            if len(headers) > ws.col_count:
                ws.add_cols(len(headers) - ws.col_count)
            ws.update(range_name="A1", values=[headers])
        ws.append_rows([[r.get(h, "") for h in headers] for r in rows], value_input_option="RAW",
                       insert_data_option="INSERT_ROWS", table_range="A1")
        return len(rows)

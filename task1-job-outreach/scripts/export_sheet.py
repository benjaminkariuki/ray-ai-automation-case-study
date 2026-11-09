"""
Exports the Leads, Rejected and Run Log tabs of the Google Sheet to CSV files in sample-output/
(leads.csv, rejected.csv, run-log.csv). GitHub Actions runs this after every run, so the sample output
in the repository always matches the live Sheet.

Usage (from task1-job-outreach/, with .env filled in):
    python scripts/export_sheet.py
"""
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from job_outreach.__main__ import load_dotenv  # noqa: E402
from job_outreach.sheet import Sheet  # noqa: E402

TABS = {"Leads": "leads.csv", "Rejected": "rejected.csv", "Run Log": "run-log.csv"}


def main():
    load_dotenv(ROOT / ".env")
    sheet = Sheet()
    out = ROOT / "sample-output"
    out.mkdir(exist_ok=True)
    for tab, filename in TABS.items():
        rows = sheet.book.worksheet(tab).get_all_values()
        width = len([h for h in rows[0] if h.strip()]) if rows else 0  # drop empty trailing columns
        rows = [r[:width] for r in rows if any(c.strip() for c in r[:width])]
        with (out / filename).open("w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows(rows)
        print(f"{filename}: {len(rows) - 1} rows")


if __name__ == "__main__":
    main()

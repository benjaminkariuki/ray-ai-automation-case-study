"""Command line:  python -m job_outreach [--dry-run] [--max-jobs N] [--trigger NAME]

Credentials come from environment variables (or a .env file next to this project): see .env.example.
"""
import argparse
import os
from pathlib import Path

from .pipeline import run
from .sheet import Sheet


def load_dotenv(path):
    """Minimal .env loader (KEY=value lines) so no extra package is needed."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def main():
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    ap = argparse.ArgumentParser(description="Find EA/Admin jobs, validate with AI, write outreach, save to Google Sheets.")
    ap.add_argument("--dry-run", action="store_true", help="Do everything except writing to the Google Sheet")
    ap.add_argument("--max-jobs", type=int, help="Override Settings > max_jobs_per_run for this run")
    ap.add_argument("--trigger", default=os.environ.get("RUN_TRIGGER", "Local"), help="Label shown in the Run Log")
    args = ap.parse_args()
    run(Sheet(), trigger=args.trigger, dry_run=args.dry_run, max_jobs=args.max_jobs)


if __name__ == "__main__":
    main()

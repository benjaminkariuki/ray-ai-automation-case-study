"""
Maintenance tool: rewrite the outreach message of existing Leads rows with the CURRENT prompt
(e.g. after improving the prompt). Uses the job details already stored in the Sheet.

Usage (from task1-job-outreach/, with .env filled in):
    python scripts/rewrite_messages.py --model-contains nemotron          # rows written by a given model
    python scripts/rewrite_messages.py --rows 2 3 4                       # specific sheet rows
    python scripts/rewrite_messages.py --model-contains llama --dry-run   # preview only
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from job_outreach.__main__ import load_dotenv  # noqa: E402
from job_outreach.ai import AIClient  # noqa: E402
from job_outreach.sheet import Sheet  # noqa: E402


def main():
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    ap = argparse.ArgumentParser()
    ap.add_argument("--model-contains", help="Rewrite rows whose 'AI Model' contains this text")
    ap.add_argument("--rows", type=int, nargs="*", default=[], help="Sheet row numbers to rewrite")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    sheet = Sheet()
    config = sheet.load_config()
    ai = AIClient(config)
    ws = sheet.book.worksheet("Leads")
    values = ws.get_all_values()
    headers = values[0]
    col = {h: i for i, h in enumerate(headers)}
    done = 0
    for n, row in enumerate(values[1:], start=2):
        if not ((args.model_contains and args.model_contains in row[col["AI Model"]]) or n in args.rows):
            continue
        job = {"title": row[col["Job Title"]], "company": row[col["Company Name"]], "location": row[col["Location"]],
               "description": row[col["Job Description"]].replace(" | ", "\n")}
        verdict = {"languages": row[col["Language Requirements"]] or "English"}
        message, model = ai.write_outreach(job, verdict)
        print(f"row {n}: {job['title'][:50]} @ {job['company'][:25]} -> {model}")
        if not args.dry_run:
            updates = {"LLM-Generated Outreach Message": message, "Prompt Used": config["outreach_prompt_name"],
                       "AI Model": model}
            for name, value in updates.items():
                ws.update_cell(n, col[name] + 1, value)
        done += 1
    print(f"{done} message(s) {'previewed' if args.dry_run else 'rewritten'}.")


if __name__ == "__main__":
    main()

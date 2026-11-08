"""The end-to-end run: settings -> fetch -> filter -> AI validate -> AI outreach -> Sheet -> log + files."""
import csv
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from .ai import AIClient
from .filters import keyword_filter
from .sources import fetch_all

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"


def _yn(value):
    return "Yes" if value else "No"


def run(sheet, *, trigger="Manual", dry_run=False, max_jobs=None, log=print):
    started = datetime.now(timezone.utc)
    config = sheet.load_config()
    if max_jobs is not None:
        config["max_jobs_per_run"] = max_jobs
    log(f"Settings loaded. Prompt: {config['outreach_prompt_name']} | max jobs: {config['max_jobs_per_run']}")

    jobs, source_errors = fetch_all(config)
    by_source = {s: sum(1 for j in jobs if j["source"] == s) for s in ("Himalayas", "RemoteOK", "Jobicy")}
    log(f"Fetched {len(jobs)} postings {by_source}" + (f" | source errors: {source_errors}" if source_errors else ""))

    candidates, stats = keyword_filter(jobs, config, sheet.seen_urls())
    log(f"Keyword filter: {stats['passed_keyword_filter']} matched, {stats['already_seen']} already processed, "
        f"{stats['sent_to_ai']} new -> AI ({stats['deferred_to_next_run']} deferred to next run)")

    ai = AIClient(config)
    today = started.strftime("%Y-%m-%d")
    leads, rejected, errors, decisions = [], [], [], []
    for i, job in enumerate(candidates, 1):
        label = f"[{i}/{len(candidates)}] {job['title'][:60]} @ {job['company'][:30]}"
        posted = job["posted"].strftime("%Y-%m-%d") if job.get("posted") else ""
        try:
            verdict = ai.validate(job)
        except Exception as exc:  # noqa: BLE001 - not saved, so it is retried next run
            errors.append({"url": job["url"], "title": job["title"], "error": str(exc)[:300]})
            log(f"{label} -> AI ERROR (will retry next run)")
            continue
        is_lead = verdict["remote"] and verdict["english"] and verdict["relevant"] and not (
            config["exclude_agencies"] and verdict["agency"])
        decision = {**{k: v for k, v in job.items() if k not in ("description", "posted")}, "posted": posted,
                    "verdict": verdict, "decision": "lead" if is_lead else "rejected"}
        if not is_lead:
            rejected.append({
                "Job Posting URL": job["url"], "Job Title": job["title"], "Company Name": job["company"],
                "Location": job["location"], "Remote": _yn(verdict["remote"]), "English": _yn(verdict["english"]),
                "Relevant": _yn(verdict["relevant"]), "Agency": _yn(verdict["agency"]), "Reason": verdict["reason"],
                "Source": job["source"], "Date Checked": today, "AI Model": verdict["model"]})
            decisions.append(decision)
            log(f"{label} -> rejected: {verdict['reason'][:90]}")
            continue
        try:
            message, model = ai.write_outreach(job, verdict)
        except Exception as exc:  # noqa: BLE001
            errors.append({"url": job["url"], "title": job["title"], "error": str(exc)[:300]})
            log(f"{label} -> passed checks, but message failed (will retry next run)")
            continue
        decision["outreach_message"] = message
        decisions.append(decision)
        leads.append({
            "Job Posting URL": job["url"], "Job Title": job["title"], "Company Name": job["company"],
            "Location": job["location"],
            "Job Description": re.sub(r"\s*\n+\s*", " | ", job["description"]).removeprefix("- ")[:45000],
            "LLM-Generated Outreach Message": message, "Language Requirements": verdict["languages"],
            "Source": job["source"], "Date Posted": posted, "Date Found": today,
            "Prompt Used": config["outreach_prompt_name"], "AI Model": model, "Status": "New", "Notes": ""})
        log(f"{label} -> LEAD ({model})")

    summary = {
        "Run Time (UTC)": started.strftime("%Y-%m-%d %H:%M"), "Trigger": trigger, "Fetched": stats["fetched"],
        "Passed Keyword Filter": stats["passed_keyword_filter"], "Already Seen": stats["already_seen"],
        "Checked by LLM": stats["sent_to_ai"], "Leads Added": len(leads), "Rejected": len(rejected),
        "LLM Errors": len(errors), "Backup AI Used": ai.backup_calls}
    if dry_run:
        log("Dry run: nothing written to the Google Sheet.")
    else:
        sheet.append("Leads", leads)
        sheet.append("Rejected", rejected)
        sheet.append("Run Log", [summary])  # written last, after every other write
        log("Google Sheet updated: Leads, Rejected, Run Log.")

    report = {"run_at": started.isoformat(), "trigger": trigger, "dry_run": dry_run, "summary": summary,
              "stats": stats, "source_errors": source_errors, "errors": errors, "decisions": decisions,
              "scraped": [{**{k: v for k, v in j.items() if k != "posted"},
                           "posted": j["posted"].strftime("%Y-%m-%d") if j.get("posted") else ""} for j in jobs]}
    paths = write_outputs(report, leads, rejected)
    write_github_summary(summary, leads, rejected, errors, sheet.sheet_id)
    log("Run summary: " + json.dumps(summary))
    log("Files: " + ", ".join(str(p) for p in paths))
    return summary


def write_outputs(report, leads, rejected):
    """Structured output of every run: full JSON + CSV of this run's leads and rejections."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M")
    json_path = OUTPUT_DIR / f"run-{stamp}.json"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    paths = [json_path]
    for name, rows in (("leads", leads), ("rejected", rejected)):
        if rows:
            p = OUTPUT_DIR / f"run-{stamp}-{name}.csv"
            with p.open("w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
                w.writeheader()
                w.writerows(rows)
            paths.append(p)
    return paths


def write_github_summary(summary, leads, rejected, errors, sheet_id):
    """When running in GitHub Actions, show a readable summary on the run page."""
    target = os.environ.get("GITHUB_STEP_SUMMARY")
    if not target:
        return
    lines = ["## EA Job Outreach - run summary", "",
             "| " + " | ".join(summary) + " |", "|" + "---|" * len(summary),
             "| " + " | ".join(str(v) for v in summary.values()) + " |", "",
             f"Google Sheet: https://docs.google.com/spreadsheets/d/{sheet_id}", ""]
    esc = lambda s: str(s).replace("|", "/").replace("\n", " ")  # noqa: E731 - keep markdown tables intact
    if leads:
        lines += ["### New leads", "| Job | Company | Location | AI model |", "|---|---|---|---|"]
        lines += [f"| [{esc(l['Job Title'])}]({l['Job Posting URL']}) | {esc(l['Company Name'])} | "
                  f"{esc(l['Location'][:40])} | {esc(l['AI Model'])} |" for l in leads]
    if rejected:
        lines += ["", "### Rejected", "| Job | Company | Reason |", "|---|---|---|"]
        lines += [f"| {esc(r['Job Title'])} | {esc(r['Company Name'])} | {esc(r['Reason'][:120])} |" for r in rejected]
    if errors:
        lines += ["", f"### AI errors ({len(errors)}) - retried automatically next run"]
    with open(target, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

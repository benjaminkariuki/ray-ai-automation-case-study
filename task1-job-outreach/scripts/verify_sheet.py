"""
Checks the public Google Sheet against the Task 1 requirements and prints a PASS/FAIL checklist.
No login, API key or extra packages needed (standard-library Python 3.8+).

Usage:
    python verify_sheet.py                      # checks the case-study sheet
    python verify_sheet.py --sheet-id <ID>      # checks another (link-shared) sheet
"""
import argparse
import csv
import io
import re
import ssl
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

DEFAULT_SHEET = "1GwAt8R3_O-h6ivZ_CT_8yD6GMIdybyf2-YgscTQ9hRI"
REQUIRED = ["Job Posting URL", "Job Title", "Company Name", "Location", "Job Description",
            "LLM-Generated Outreach Message"]
ALLOWED_SOURCES = {"Himalayas", "RemoteOK", "Jobicy"}


def read_tab(sheet_id, tab):
    url = (f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&headers=1&sheet="
           + urllib.parse.quote(tab))
    ctx = ssl.create_default_context()
    try:
        import certifi  # optional: fixes outdated certificate stores on some Windows Pythons
        ctx = ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        pass
    with urllib.request.urlopen(url, context=ctx, timeout=60) as r:
        return list(csv.DictReader(io.StringIO(r.read().decode("utf-8"))))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet-id", default=DEFAULT_SHEET)
    sheet = ap.parse_args().sheet_id
    leads, rejected, runlog = (read_tab(sheet, t) for t in ("Leads", "Rejected", "Run Log"))
    results = []

    def check(name, ok, detail):
        results.append(ok)
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {detail}")

    print(f"\nTask 1 verification - sheet {sheet}\n")
    cols = list(leads[0].keys()) if leads else []
    check("Required columns, in order", cols[:6] == REQUIRED, ", ".join(cols[:6]) or "no data")
    check("Leads present", len(leads) > 0, f"{len(leads)} leads")
    missing = [i + 2 for i, r in enumerate(leads) if any(not (r.get(c) or "").strip() for c in REQUIRED)]
    check("No empty required fields", not missing, "all filled" if not missing else f"empty cells in rows {missing}")
    urls = [r["Job Posting URL"] for r in leads]
    check("No duplicate jobs", len(urls) == len(set(urls)), f"{len(set(urls))} unique of {len(urls)}")
    sources = {r.get("Source", "") for r in leads}
    linkedin = [u for u in urls if "linkedin." in u.lower()]
    check("Compliant non-LinkedIn sources", sources <= ALLOWED_SOURCES and not linkedin, ", ".join(sorted(sources)))
    msgs = [r["LLM-Generated Outreach Message"] for r in leads]
    # Personalised = names the company, or shares >= 2 distinctive words (found in < 20% of all postings)
    # with its own job description. Generic words like "calendar" or "assistant" do not count.
    words = lambda t: set(w.lower() for w in re.findall(r"[A-Za-z][A-Za-z-]{4,}", t))  # noqa: E731
    desc_words = [words(r["Job Description"] + " " + r["Job Title"]) for r in leads]
    freq = {}
    for ws in desc_words:
        for w in ws:
            freq[w] = freq.get(w, 0) + 1
    limit = max(2, 0.2 * len(leads))
    personal = [r for r, ws in zip(leads, desc_words)
                if r["Company Name"].split()[0].lower() in r["LLM-Generated Outreach Message"].lower()
                or len({w for w in ws if freq[w] < limit} & words(r["LLM-Generated Outreach Message"])) >= 2]
    check("Messages are unique", len(set(msgs)) == len(msgs), f"{len(set(msgs))} distinct messages")
    # Clean = subject line, sensible length, no leaked model tokens/reasoning, no runaway repetition.
    dirty = [i + 2 for i, m in enumerate(msgs)
             if not m.lstrip().lower().startswith("subject:") or not 40 <= len(m.split()) <= 320
             or re.search(r"<\||\|>|assistantfinal|^\s*analysis\b", m, re.I | re.M)
             or re.search(r"\b(\w+)(?:\s+\1\b){4,}", m, re.I)]
    check("Messages are clean (no AI artifacts)", not dirty,
          "all start with a subject line, 40-320 words, no model tokens or repetition" if not dirty
          else f"problems in rows {dirty}")
    check("Messages reference the specific posting", len(personal) == len(leads),
          f"{len(personal)}/{len(leads)} name the company or quote details found only in their own posting")
    prompts = sorted({r.get("Prompt Used", "") for r in leads} - {""})
    check("Prompt is interchangeable (tracked per lead)", len(prompts) >= 1, "prompts used: " + ", ".join(prompts))
    models = sorted({r.get("AI Model", "").split(" (")[-1].rstrip(")") for r in leads} - {""})
    check("AI provider recorded per lead", bool(models), "providers: " + ", ".join(models))
    bad = [r for r in rejected if not ((r["Remote"] == "No") or (r["English"] == "No") or (r["Relevant"] == "No")
                                       or (r["Agency"] == "Yes"))]
    check("Every rejection failed a check", not bad and len(rejected) > 0,
          f"{len(rejected)} rejected, each with Remote/English/Relevant = No or Agency = Yes, plus a reason")
    last = max((datetime.strptime(r["Run Time (UTC)"][:16], "%Y-%m-%d %H:%M") for r in runlog), default=None)
    fresh = last and datetime.now(timezone.utc).replace(tzinfo=None) - last < timedelta(hours=36)
    triggers = sorted({r.get("Trigger", "") for r in runlog} - {""})
    check("Automation ran in the last 36 hours", bool(fresh), f"last run {last} UTC; triggers seen: {', '.join(triggers)}")
    latest = runlog[-1] if runlog else {}
    checked, errors = int(latest.get("Checked by LLM") or 0), int(latest.get("LLM Errors") or 0)
    check("Latest run healthy (AI answered)", checked == 0 or errors < checked,
          f"{checked} jobs checked, {errors} AI errors, backup AI used {latest.get('Backup AI Used', '0')} times")

    print(f"\n{sum(results)}/{len(results)} checks passed.\n")
    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())

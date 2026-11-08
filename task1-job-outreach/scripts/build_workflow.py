"""
Builds workflow/job-outreach-workflow.json (the importable n8n workflow) from the
Code-node sources in workflow/code/*.js, so the JavaScript stays readable and versioned.

Usage:  python build_workflow.py [--sheet-id ID] [--google-cred-id ID] [--openrouter-cred-id ID]
Without arguments it writes placeholders that you replace after import (see README).
"""
import argparse
import json
import pathlib
import uuid

ROOT = pathlib.Path(__file__).resolve().parent.parent
CODE = ROOT / "workflow" / "code"
OUT = ROOT / "workflow" / "job-outreach-workflow.json"


def nid(name):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "ray-job-outreach/" + name))


def build(sheet_id, gcred, orcred):
    google_cred = {"googleApi": {"id": gcred, "name": "Google Sheets (service account)"}}
    or_cred = {"httpHeaderAuth": {"id": orcred, "name": "OpenRouter API key"}}
    doc = {"__rl": True, "value": "={{ $('Config').first().json.spreadsheetId }}", "mode": "id"}
    nodes, conns = [], {}

    def node(name, ntype, version, pos, params, **extra):
        n = {"id": nid(name), "name": name, "type": ntype, "typeVersion": version, "position": pos, "parameters": params}
        n.update(extra)
        nodes.append(n)
        return name

    def code(name, file, pos, mode="runOnceForAllItems"):
        js = (CODE / file).read_text(encoding="utf-8")
        p = {"jsCode": js} if mode == "runOnceForAllItems" else {"mode": mode, "jsCode": js}
        return node(name, "n8n-nodes-base.code", 2, pos, p)

    def link(src, dst, out=0, inp=0):
        conns.setdefault(src, {"main": []})
        while len(conns[src]["main"]) <= out:
            conns[src]["main"].append([])
        conns[src]["main"][out].append({"node": dst, "type": "main", "index": inp})

    def sheet_read(name, tab, pos, **extra):
        return node(name, "n8n-nodes-base.googleSheets", 4.7, pos, {
            "authentication": "serviceAccount", "operation": "read", "documentId": doc,
            "sheetName": {"__rl": True, "value": tab, "mode": "name"}, "options": {}},
            credentials=google_cred, **extra)

    def sheet_append(name, tab, pos, **extra):
        return node(name, "n8n-nodes-base.googleSheets", 4.7, pos, {
            "authentication": "serviceAccount", "operation": "append", "documentId": doc,
            "sheetName": {"__rl": True, "value": tab, "mode": "name"},
            "columns": {"mappingMode": "autoMapInputData", "value": {}, "matchingColumns": [], "schema": []},
            "options": {"cellFormat": "RAW"}}, credentials=google_cred, **extra)

    def http_get(name, url, pos, **extra):
        return node(name, "n8n-nodes-base.httpRequest", 4.2, pos, {
            "url": url, "sendHeaders": True,
            "headerParameters": {"parameters": [{"name": "User-Agent", "value": "RAY-Job-Outreach/1.0 (n8n)"}]},
            "options": {"timeout": 30000, "batching": {"batch": {"batchSize": 1, "batchInterval": 1500}}}},
            retryOnFail=True, maxTries=3, waitBetweenTries=5000, onError="continueRegularOutput", **extra)

    def llm(name, field, pos):
        return node(name, "n8n-nodes-base.httpRequest", 4.2, pos, {
            "method": "POST", "url": "https://openrouter.ai/api/v1/chat/completions",
            "authentication": "genericCredentialType", "genericAuthType": "httpHeaderAuth",
            "sendHeaders": True, "headerParameters": {"parameters": [
                {"name": "HTTP-Referer", "value": "https://github.com/ray-job-outreach"},
                {"name": "X-Title", "value": "RAY Job Outreach"}]},
            "sendBody": True, "specifyBody": "json", "jsonBody": "={{ JSON.stringify($json." + field + ") }}",
            "options": {"timeout": 120000, "batching": {"batch": {"batchSize": 1, "batchInterval": 4000}}}},
            credentials=or_cred, retryOnFail=True, maxTries=3, waitBetweenTries=5000, onError="continueRegularOutput")

    # --- Triggers & config -------------------------------------------------
    node("Daily at 06:00 UTC", "n8n-nodes-base.scheduleTrigger", 1.2, [0, 0],
         {"rule": {"interval": [{"field": "days", "daysInterval": 1, "triggerAtHour": 6, "triggerAtMinute": 0}]}})
    node("Run manually", "n8n-nodes-base.manualTrigger", 1, [0, 200], {})
    node("Config", "n8n-nodes-base.set", 3.4, [220, 100], {
        "assignments": {"assignments": [{"id": nid("cfg-sheet"), "name": "spreadsheetId", "value": sheet_id, "type": "string"}]},
        "options": {}}, notes="Paste your Google Sheet ID here (the long code in the sheet URL).", notesInFlow=True)
    link("Daily at 06:00 UTC", "Config")
    link("Run manually", "Config")

    sheet_read("Read Settings", "Settings", [440, 100])
    sheet_read("Read Prompts", "Prompts", [660, 100], executeOnce=True)
    sheet_read("Read Leads", "Leads", [880, 100], executeOnce=True, alwaysOutputData=True)
    sheet_read("Read Rejected", "Rejected", [1100, 100], executeOnce=True, alwaysOutputData=True)
    code("Build Search Plan", "01_build_search_plan.js", [1320, 100])
    for a, b in [("Config", "Read Settings"), ("Read Settings", "Read Prompts"), ("Read Prompts", "Read Leads"),
                 ("Read Leads", "Read Rejected"), ("Read Rejected", "Build Search Plan")]:
        link(a, b)

    # --- Fetch job boards --------------------------------------------------
    http_get("Fetch Himalayas", "=https://himalayas.app/jobs/api/search?q={{ encodeURIComponent($json.q) }}&page={{ $json.page }}&sort=recent", [1560, -100])
    http_get("Fetch RemoteOK", "https://remoteok.com/api?tag=assistant", [1560, 100], executeOnce=True)
    http_get("Fetch Jobicy", "https://jobicy.com/api/v2/remote-jobs?count=100&industry=admin-support", [1560, 300], executeOnce=True)
    node("Combine Sources", "n8n-nodes-base.merge", 3.2, [1800, 100], {"numberInputs": 3})
    for i, src in enumerate(["Fetch Himalayas", "Fetch RemoteOK", "Fetch Jobicy"]):
        link("Build Search Plan", src)
        link(src, "Combine Sources", inp=i)
    code("Normalize & Filter", "02_normalize_filter.js", [2020, 100])
    link("Combine Sources", "Normalize & Filter")

    # --- AI branch (top) ---------------------------------------------------
    node("Split Jobs", "n8n-nodes-base.splitOut", 1, [2240, 0], {"fieldToSplitOut": "candidates", "options": {}})
    code("Prepare AI Check", "03_prepare_ai_check.js", [2460, 0], mode="runOnceForEachItem")
    llm("AI: Validate Job", "validationRequest", [2680, 0])
    code("Parse AI Check", "04_parse_ai_check.js", [2900, 0], mode="runOnceForEachItem")
    node("Is it a match?", "n8n-nodes-base.if", 2.2, [3120, 0], {
        "conditions": {"options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict", "version": 2},
                       "conditions": [{"id": nid("if-lead"), "leftValue": "={{ $json.decision }}", "rightValue": "lead",
                                       "operator": {"type": "string", "operation": "equals"}}],
                       "combinator": "and"}, "options": {}})
    llm("AI: Write Outreach", "outreachRequest", [3360, -100])
    code("Format Lead", "05_format_lead.js", [3580, -100])
    sheet_append("Add to Leads", "Leads", [3800, -100])
    code("Format Rejection", "06_format_rejection.js", [3360, 120])
    sheet_append("Add to Rejected", "Rejected", [3580, 120])
    for a, b in [("Normalize & Filter", "Split Jobs"), ("Split Jobs", "Prepare AI Check"), ("Prepare AI Check", "AI: Validate Job"),
                 ("AI: Validate Job", "Parse AI Check"), ("Parse AI Check", "Is it a match?"),
                 ("AI: Write Outreach", "Format Lead"), ("Format Lead", "Add to Leads"), ("Format Rejection", "Add to Rejected")]:
        link(a, b)
    link("Is it a match?", "AI: Write Outreach", out=0)
    link("Is it a match?", "Format Rejection", out=1)

    # --- Logging branch (bottom: runs after the AI branch finishes) ----------
    code("Summarize Run", "07_summarize_run.js", [2240, 400])
    sheet_append("Log Run", "Run Log", [2460, 400])
    code("Build Run Report", "08_build_run_report.js", [2680, 400])
    node("Convert to JSON File", "n8n-nodes-base.convertToFile", 1.1, [2900, 400], {
        "operation": "toJson", "mode": "once",
        "options": {"fileName": "=job-run-{{ $now.toFormat('yyyy-MM-dd_HHmm') }}.json", "format": True}})
    node("Save Run File", "n8n-nodes-base.readWriteFile", 1, [3120, 400], {
        "operation": "write", "fileName": "=/files/job-run-{{ $now.toFormat('yyyy-MM-dd_HHmm') }}.json",
        "dataPropertyName": "data", "options": {}}, onError="continueRegularOutput")
    for a, b in [("Normalize & Filter", "Summarize Run"), ("Summarize Run", "Log Run"), ("Log Run", "Build Run Report"),
                 ("Build Run Report", "Convert to JSON File"), ("Convert to JSON File", "Save Run File")]:
        link(a, b)

    stickies = [
        ("1. Load settings from the Google Sheet", [-80, -280], 1540, 640, 7,
         "## 1. Trigger + load settings\nRuns daily at 06:00 UTC (or manually). Reads **Settings**, **Prompts** and "
         "already-processed URLs from the Google Sheet. Edit the sheet, not this workflow, to change filters, models or prompts."),
        ("2. Fetch + filter jobs", [1500, -280], 680, 760, 5,
         "## 2. Fetch + filter jobs\nPublic APIs: Himalayas (search), RemoteOK, Jobicy. "
         "Normalised to one schema, then keyword / company / age filter and duplicate check."),
        ("3. AI check + outreach", [2220, -280], 1780, 600, 4,
         "## 3. AI (OpenRouter)\nLLM 1 verifies **remote + English + relevant** (and not an agency). "
         "Matches get a personalised message from LLM 2 and go to **Leads**; the rest go to **Rejected** with the reason."),
        ("4. Log the run", [2220, 340], 1120, 260, 3,
         "## 4. Log + save\nAdds a row to **Run Log** and saves the full run as JSON on the server (/files)."),
    ]
    for title, pos, w, h, color, text in stickies:
        nodes.append({"id": nid("sticky-" + title), "name": title, "type": "n8n-nodes-base.stickyNote", "typeVersion": 1,
                      "position": pos, "parameters": {"content": text, "width": w, "height": h, "color": color}})

    return {"name": "RAY - EA Job Outreach (daily)", "nodes": nodes, "connections": conns, "active": False,
            "settings": {"executionOrder": "v1", "timezone": "UTC", "saveManualExecutions": True,
                         "callerPolicy": "workflowsFromSameOwner"},
            "pinData": {}, "meta": {"templateCredsSetupCompleted": False}, "tags": []}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet-id", default="PASTE_YOUR_GOOGLE_SHEET_ID")
    ap.add_argument("--google-cred-id", default="google-sheets-sa")
    ap.add_argument("--openrouter-cred-id", default="openrouter-key")
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args()
    wf = build(a.sheet_id, a.google_cred_id, a.openrouter_cred_id)
    pathlib.Path(a.out).write_text(json.dumps(wf, indent=2), encoding="utf-8")
    print("Wrote", a.out)

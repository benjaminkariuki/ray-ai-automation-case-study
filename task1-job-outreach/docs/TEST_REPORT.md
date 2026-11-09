# Task 1 – Test Report

All live tests used real job-board APIs, real AI providers and the real Google Sheet.
Every live run has public logs in [GitHub Actions](https://github.com/benjaminkariuki/ray-ai-automation-case-study/actions/workflows/job-outreach.yml) and a row in the Sheet's **Run Log**.

## Summary

| # | Test | How | Result |
|---|---|---|---|
| 1 | Offline unit tests: filtering, HTML cleanup, language detection, AI-answer parsing, message formatting, failover logic, quality checks, broken Settings | `pytest` (17 tests), also run before every run | ✅ 17/17 |
| 2 | Full run on GitHub Actions: fetch → filter → AI → Sheet → log → output files | Manual run of the workflow | ✅ Pass |
| 3 | Automatic failover to the backup AI (Cloudflare) when OpenRouter is rate-limited | Live (OpenRouter's daily limit was exhausted) + unit tests | ✅ Pass |
| 4 | Primary AI path (OpenRouter) | Unit test + live run on 8 Nov (same API call) | ✅ Pass |
| 5 | Swapping the prompt from the Sheet, without code changes | Live: `v1_warm` → `v2_direct` | ✅ Pass |
| 6 | No duplicate jobs across runs | Live, every run | ✅ Pass |
| 7 | Validation quality: remote, English, relevant, agency | Reading the Leads and Rejected tabs | ✅ Pass (after prompt fixes) |
| 8 | No invented claims in outreach messages | Reading the messages | ✅ Pass (after prompt fixes) |
| 9 | Incomplete AI answers never cause a false rejection | Unit test + live case | ✅ Pass (after fix) |
| 10 | Requirement checklist on the live Sheet | `verify_sheet.py`, also run after every run | ✅ 13/13 |
| 11 | Dry run writes nothing to the Sheet | Local `--dry-run` | ✅ Pass |
| 12 | Language requirements collected for **every** scraped posting | `*-all-postings.csv` of each run (344 postings: 103 English, 19 English + Spanish, …) | ✅ Pass |
| 13 | Older messages rewritten with the final prompt | `scripts/rewrite_messages.py` (17 rows) | ✅ Pass |
| 14 | Leaked model reasoning removed; bad drafts regenerated | Unit tests + the 2 affected rows rewritten | ✅ Pass (after fix) |
| 15 | One run every day even if GitHub skips a slot | Gated backup slots + Cloudflare trigger; gate query tested on real run history | ✅ Pass |
| 16 | Public Run now page (cooldown, one run at a time) | Local + deployed tests | ✅ Pass |
| 17 | Sheet edits by evaluators can't stop a run | Unit tests (bad prompt name, non-numeric value, deleted tabs) | ✅ Pass |
| 18 | `sample-output/*.csv` match the live Sheet after every run | Workflow run 9 Nov 15:49 (39 / 37 / 6 rows) | ✅ Pass |

## Details

**1. Unit tests** (`tests/`, 17 tests):
- HTML cleanup, including double-escaped HTML.
- Language-requirement detection.
- The keyword, company and age filters, de-duplication and the per-run cap.
- Parsing complete and incomplete AI answers.
- Message endings normalised across 4 real model-output variants: misplaced or duplicated call-to-action, non-breaking hyphens, missing blank lines.
- Failover: OpenRouter works; OpenRouter is rate-limited; OpenRouter's reply is unusable; both providers fail.
- Safeguards: leaked reasoning stripped, bad drafts detected, verdicts parsed after leaked reasoning, invalid Settings and deleted tabs fall back to defaults.

**2. Full GitHub Actions run** ([run 42527110100](https://github.com/benjaminkariuki/ray-ai-automation-case-study/actions/runs/42527110100)):
- Fetched 344 postings: 240 from Himalayas, 99 from RemoteOK, 5 from Jobicy.
- 82 matched the keywords, 81 had already been processed, and 1 new job went to the AI, which made it a lead.
- The Sheet was updated, the Run Log row written, the output committed to `sample-output/latest/`, and the Sheet check passed.

**3. Failover.**
- During testing, OpenRouter's free daily limit ran out (HTTP 429). Every AI call then went to Cloudflare `gpt-oss-120b` automatically, with **0 errors**.
- These rows show `(Cloudflare)` in the **AI Model** column, and the Run Log counts **Backup AI Used**.

**4. Primary path.**
- On 8 November, a run with the same OpenRouter request produced 10 leads, all from `nvidia/nemotron-3-ultra-550b-a55b:free`. Their messages were later rewritten with the improved prompt (`scripts/rewrite_messages.py`), so they now show the model that rewrote them.
- OpenRouter's free quota resets daily at 00:00 UTC, so each daily run (about 06:07 UTC) tries OpenRouter first. The Run Log's *Backup AI Used* column shows when Cloudflare had to step in.

**5. Prompt swap** ([run 42527434553](https://github.com/benjaminkariuki/ray-ai-automation-case-study/actions/runs/42527434553)):
- With *Settings → outreach_prompt* set to `v2_direct`, two re-checked jobs (Pearson, Naples Jet Center) received the shorter 3-bullet style.
- Each lead records **Prompt Used**. Both prompts appear in the Leads tab.

**6. Duplicates.**
- The *Already Seen* count rises run after run.
- The Sheet holds 34 leads with 34 unique URLs, and no URL appears in both Leads and Rejected (checked by `verify_sheet.py`).

**7. Validation quality.**
- Correct rejections include staffing and VA agencies (Hire Overseas, Pavago, FreedUp, Pearl Talent), a hybrid role, a recruiter role, a marine-engineering "admin" role, and a Korean-speaking role that wasn't remote.
- *Fixes made during testing:*
  - Time-zone or working-hours limits now count as remote.
  - A posting written in English counts as English-speaking unless it names another working language.

**8. No invented claims.**
- Early messages claimed "our assistants are bilingual in Spanish" and "already fluent in Navan".
- The prompts now allow facts about us only from `sender_offer`, require "we would only propose assistants who meet [language]", and forbid claiming tool knowledge.

**9. Incomplete AI answers.**
- *Problem found:* a model once returned its reasoning instead of JSON. Missing fields were read as "No", which falsely rejected a job (Performacentric).
- *Fix:* answers missing any field or the reason are treated as errors and retried. That job was re-checked and is now correctly a lead.

**10. `verify_sheet.py`.**
- It reads the public Sheet without credentials and checks: column order, no empty required fields, no duplicates, compliant sources, unique, clean and posting-specific messages, prompt tracking, AI provider recorded, every rejection failing a check, a run in the last 36 hours, and the latest run being healthy.
- Result: **13/13**.

**11. Dry run.**
- `python -m job_outreach --dry-run` ran the whole pipeline, including the AI calls, and wrote the JSON and CSV output, but made no changes to the Sheet.

## Second review (9 November): problems found and fixed

| Found | Fix |
|---|---|
| GitHub skipped the first scheduled 06:00 UTC run (its free scheduler drops cron runs when busy) | Daily slot moved to 06:07 UTC; backup slots every 3 hours and an independent Cloudflare cron trigger, each running only if no daily run has succeeded that day; failed runs retried 3 times |
| Evaluators can't press GitHub's "Run workflow" (it needs write access) | Public **Run now** page (Cloudflare Worker, fine-grained token limited to Actions on this repo, 15-minute cooldown) |
| 2 messages (rows 8 and 37) from the backup model contained its hidden reasoning (`analysis: …<\|end\|>…assistantfinal`) and runaway repetition | Replies are cleaned; drafts without a subject, of the wrong length, with model tokens or repetition are regenerated; `verify_sheet.py` has a new "Messages are clean" check; both rows rewritten |
| One rejection said English = No only because English wasn't mentioned | Validation prompt made explicit ("do NOT set false just because English is not mentioned"); the job was re-checked: English = Yes, still correctly rejected as an agency |
| `sample-output/*.csv` lagged behind the live Sheet | `scripts/export_sheet.py` refreshes them after every run |
| Sheet looked plain | Alternating row colours, yellow message column, red/green checks, coloured Run Log triggers |
| Evaluators couldn't edit the Sheet | Anyone with the link can edit; header rows warn before changes; invalid values fall back to defaults with a `SETTINGS WARNING` |

## Sources
- RemoteOK's `assistant` feed is fetched every run. It currently contains EA roles (16VC, Jasper, Propel and others), but its newest one is from July 2026, so the 30-day freshness filter correctly skips them.
- Leads come from Himalayas and Jobicy for now. RemoteOK will contribute as soon as it publishes fresh EA roles, or if `max_posting_age_days` is raised.

## History: why the pipeline moved from n8n to Python + GitHub Actions
The first version was an n8n workflow on a self-hosted Azure VM. It worked, and its testing produced most of the fixes above. It was replaced for resilience: a VM depends on cloud credits and uptime, while GitHub Actions needs no server, costs nothing and makes every run's logs public. The same Google Sheet, prompts, settings and logic were carried over unchanged.

## Known limits
- **Free AI tiers** cover about 50 jobs a day on OpenRouter and about 70 on Cloudflare. Normal daily volume is 5–20 new jobs.
- **Schedule delays.** GitHub may start scheduled runs a few minutes late at busy times.
- **AI judgement on edge cases.** Borderline roles depend on the AI's judgement. Each rejection's reason is visible so the rules can be tuned in the Prompts tab.

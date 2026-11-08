# Task 1 – Test Report

All live tests used real job-board APIs, real AI providers and the real Google Sheet.
Every live run has public logs in [GitHub Actions](https://github.com/benjaminkariuki/ray-ai-automation-case-study/actions/workflows/job-outreach.yml) and a row in the Sheet's **Run Log**.

## Summary

| # | Test | How | Result |
|---|---|---|---|
| 1 | Offline unit tests: filtering, HTML cleanup, AI-answer parsing, message formatting, failover logic | `pytest` (11 tests), also run before every scheduled run | ✅ 11/11 |
| 2 | Full run on GitHub Actions: fetch → filter → AI → Sheet → log → output files | Manual run of the workflow | ✅ Pass |
| 3 | Automatic failover to the backup AI (Cloudflare) when OpenRouter is rate-limited | Live (OpenRouter's daily limit was exhausted) + unit tests | ✅ Pass |
| 4 | Primary AI path (OpenRouter) | Unit test + live runs on 8 Nov (n8n version, same API call) | ✅ Pass |
| 5 | Swapping the prompt from the Sheet, without code changes | Live: `v1_warm` → `v2_direct` | ✅ Pass |
| 6 | No duplicate jobs across runs | Live, every run | ✅ Pass |
| 7 | Validation quality: remote, English, relevant, agency | Reading the Leads and Rejected tabs | ✅ Pass (after prompt fixes) |
| 8 | No invented claims in outreach messages | Reading the messages | ✅ Pass (after prompt fixes) |
| 9 | Incomplete AI answers never cause a false rejection | Unit test + live case | ✅ Pass (after fix) |
| 10 | Requirement checklist on the live Sheet | `verify_sheet.py`, also run after every scheduled run | ✅ 12/12 |
| 11 | Dry run writes nothing to the Sheet | Local `--dry-run` | ✅ Pass |

## Details

**1. Unit tests** (`tests/`):
- HTML cleanup, including double-escaped HTML.
- The keyword, company and age filters, de-duplication and the per-run cap.
- Parsing complete and incomplete AI answers.
- Message endings normalised across 4 real model-output variants: misplaced or duplicated call-to-action, non-breaking hyphens, missing blank lines.
- Failover: OpenRouter works; OpenRouter is rate-limited; OpenRouter's reply is unusable; both providers fail.

**2. Full GitHub Actions run** ([run 42527110100](https://github.com/benjaminkariuki/ray-ai-automation-case-study/actions/runs/42527110100)):
- Fetched 344 postings: 240 from Himalayas, 99 from RemoteOK, 5 from Jobicy.
- 82 matched the keywords, 81 had already been processed, and 1 new job went to the AI, which made it a lead.
- The Sheet was updated, the Run Log row written, the output committed to `sample-output/latest/`, and the Sheet check passed.

**3. Failover.**
- During testing, OpenRouter's free daily limit ran out (HTTP 429). Every AI call then went to Cloudflare `gpt-oss-120b` automatically, with **0 errors**.
- These rows show `(Cloudflare)` in the **AI Model** column, and the Run Log counts **Backup AI Used**.

**4. Primary path.**
- On 8 November, a run with the same OpenRouter request produced 10 leads, all from `nvidia/nemotron-3-ultra-550b-a55b:free`. They're still in the Sheet and show `(OpenRouter)`.
- The daily 06:00 UTC run uses OpenRouter first every day.

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
- It reads the public Sheet without credentials and checks: column order, no empty required fields, no duplicates, compliant sources, unique and posting-specific messages, prompt tracking, AI provider recorded, every rejection failing a check, a run in the last 30 hours, and the latest run being healthy.
- Result: **12/12**.

**11. Dry run.**
- `python -m job_outreach --dry-run` ran the whole pipeline, including the AI calls, and wrote the JSON and CSV output, but made no changes to the Sheet.

## Sources
- RemoteOK's `assistant` feed is fetched every run. It currently contains EA roles (16VC, Jasper, Propel and others), but its newest one is from July 2026, so the 30-day freshness filter correctly skips them.
- Leads come from Himalayas and Jobicy for now. RemoteOK will contribute as soon as it publishes fresh EA roles, or if `max_posting_age_days` is raised.

## History: why the pipeline moved from n8n to Python + GitHub Actions
The first version was an n8n workflow on a self-hosted Azure VM. It worked, and its testing produced most of the fixes above. It was replaced for resilience: a VM depends on cloud credits and uptime, while GitHub Actions needs no server, costs nothing and makes every run's logs public. The same Google Sheet, prompts, settings and logic were carried over unchanged.

## Known limits
- **Free AI tiers** cover about 50 jobs a day on OpenRouter and about 70 on Cloudflare. Normal daily volume is 5–20 new jobs.
- **Schedule delays.** GitHub may start scheduled runs a few minutes late at busy times.
- **AI judgement on edge cases.** Borderline roles depend on the AI's judgement. Each rejection's reason is visible so the rules can be tuned in the Prompts tab.

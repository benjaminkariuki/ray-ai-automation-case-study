# Task 1 – Test Report

All tests ran against the live system: the n8n server on Azure, real job-board APIs, real AI providers and the real Google Sheet.
Execution numbers refer to the n8n **Executions** list. Every run also has a row in the Sheet's **Run Log** tab.

## Summary

| # | Test | Result |
|---|---|---|
| 1 | End-to-end run with the primary AI (OpenRouter) | ✅ Pass |
| 2 | Automatic failover to the backup AI (Cloudflare) | ✅ Pass |
| 3 | "Run now" link (for evaluators) | ✅ Pass |
| 4 | Swapping the prompt from the Sheet, without editing the workflow | ✅ Pass |
| 5 | No duplicate jobs across runs | ✅ Pass |
| 6 | Run Log written last, with correct counts, in every scenario | ✅ Pass (after fix) |
| 7 | Validation quality: remote, English, relevant, agency | ✅ Pass (after prompt fixes) |
| 8 | No invented claims in outreach messages | ✅ Pass (after prompt fixes) |
| 9 | Incomplete AI answers never cause a false rejection | ✅ Pass (after fix) |
| 10 | Message formatting is consistent across AI models | ✅ Pass |
| 11 | All three job sources are fetched and filtered correctly | ✅ Pass |
| 12 | Requirement checklist on the live Sheet (`verify_sheet.py`) | ✅ 12/12 |
| 13 | Server recovers after a reboot | ✅ Pass (configuration check) |

## Details

**1. Primary AI path (executions 3–4).**
- A run fetched 359 postings; 47–58 passed the keyword filter.
- 15 went to the AI, giving **10 leads** (GitLab, Pearson, Thrivent and others) and 4 rejections.
- Every answer came from `nvidia/nemotron-3-ultra-550b-a55b:free` via OpenRouter.

**2. Backup failover (execution 7).**
- OpenRouter's free daily limit had run out (HTTP 429). Every OpenRouter call left through the node's *error* output to the Cloudflare backup.
- 10/10 validations and 7/7 messages were answered by Cloudflare, giving 7 leads, 3 rejections and **0 errors**.
- These rows show `(Cloudflare)` in the **AI Model** column, and the Run Log shows **Backup AI Used = 17**.

**3. Run-now link (executions 7 and 14).**
- Opening the link returned *"Run started. New results appear in the Google Sheet … in about 3 minutes."*
- The run completed, and the Run Log recorded **Trigger = Run-now link**.

**4. Prompt swap (executions 11 and 16).**
- Changing *Settings → outreach_prompt* from `v1_warm` to `v2_direct` switched the message style on the next run: shorter, with 3 bullet points.
- Each lead records **Prompt Used**. Both prompts now appear in the Leads tab.

**5. Duplicate protection (every run).**
- *Already Seen* in the Run Log grew from 0 to 64 across runs.
- The Sheet holds 33 leads with 33 unique URLs, and no URL appears in both Leads and Rejected.

**6. Logging order.**
- *Problem found:* in execution 7 the log branch ran before the AI branch finished, because n8n defers merge nodes, so the Run Log showed 0 leads.
- *Fix:* a 3-input **All done** merge now waits for the filter step and both sheet writes before logging.
- *Proven* on test workflows for 3 scenarios (leads and rejections; rejections only; no new jobs) and on the live execution 11 (3 leads and 2 rejections logged correctly).

**7. Validation quality.**
- Correct rejections included staffing and VA agencies (Hire Overseas, Pavago, FreedUp, Pearl Talent), a hybrid role (Irth), a recruiter role (Magic), a marine-engineering "admin" role, and a Korean-speaking role that wasn't remote.
- *Fixes made during testing:*
  - Time-zone or working-hours limits now count as remote. A Jobicy role had been wrongly marked non-remote.
  - A posting written in English counts as English-speaking unless it names another working language.

**8. No invented claims.**
- Early messages claimed "our assistants are bilingual in Spanish" and "already fluent in Navan".
- The prompts now allow facts about us only from `sender_offer`, require "we would only propose assistants who meet [language]", and never claim tool knowledge. Messages generated afterwards were checked by reading them.

**9. Incomplete AI answers (execution 16).**
- *Problem found:* gpt-oss once returned its reasoning instead of JSON. Missing fields were read as "No", which falsely rejected a job.
- *Fix:* answers missing any field or the reason are now treated as **errors**. The job isn't saved and is retried next run. The false rejection was removed so the job gets re-checked.

**10. Message formatting.**
- Different models placed the call-to-action and signature differently, sometimes used non-breaking hyphens, and once repeated the call-to-action.
- *Format Lead* now rebuilds the ending the same way every time: body, call-to-action, signature. This was unit-tested with Node.js on 4 real failure cases, and existing rows were cleaned up.

**11. Sources.**
- The first version used RemoteOK's and Jobicy's general feeds, which had no EA roles. These were switched to RemoteOK's `assistant` tag and Jobicy's `admin-support` category.
- A typical run now fetches about 240 Himalayas, 99 RemoteOK and 5 Jobicy postings. Leads come from **Himalayas and Jobicy**.
- RemoteOK's feed currently contains EA roles (16VC, Jasper, Propel and others), but its newest one is from July 2026. The 30-day freshness filter correctly skips them, so they'd appear as soon as RemoteOK publishes fresh EA roles. To include older postings, raise `max_posting_age_days`.

**12. `verify_sheet.py`.**
- It reads the public Sheet and checks: column order, no empty required fields, no duplicates, compliant sources, unique and posting-specific messages, prompt tracking, AI provider recorded, every rejection failing a check, a run in the last 30 hours, and the latest run being healthy.
- Result: **12/12**. It also runs daily in GitHub Actions.

**13. Reboot recovery.**
- The Docker service is enabled at boot, and both containers use `restart: unless-stopped`. Caddy renews the HTTPS certificate automatically; it's currently valid until February 2027.

## Known limits
- **Free AI tiers** cover about 50 jobs a day on OpenRouter and about 70 on Cloudflare. Normal daily volume is 5–20 new jobs.
- **AI judgement on edge cases.** Borderline roles, such as hospice or legal administrative assistants, depend on the AI's judgement. Each rejection's reason is visible so the rules can be tuned in the Prompts tab.
- **Server cost.** The n8n server runs on Azure student credits. If they run out, the server stops. The Sheet, repository and PDF are hosted by Google and GitHub, so they stay available regardless.

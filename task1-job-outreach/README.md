# Task 1 – Executive Assistant Job Outreach Automation

An n8n workflow that runs every day and does four things:

1. Finds new Executive Assistant and Admin Assistant jobs on three job boards. LinkedIn is not used.
2. Uses AI to check that each job is **remote**, **English-speaking** and **relevant**.
3. Writes a personalised outreach email for every job that passes.
4. Saves everything to a Google Sheet that sales reps use as their dashboard.

| What | Link |
|---|---|
| Google Sheet (dashboard) | https://docs.google.com/spreadsheets/d/1GwAt8R3_O-h6ivZ_CT_8yD6GMIdybyf2-YgscTQ9hRI |
| n8n workflow export | [workflow/job-outreach-workflow.json](workflow/job-outreach-workflow.json) |
| Sample output (CSV + JSON) | [sample-output/](sample-output/) |
| Live n8n server (private login) | https://ray-n8n-bk.southafricanorth.cloudapp.azure.com |

![n8n workflow](docs/images/n8n-workflow.png)

---

## 1. How it works

| Step | What happens | Where |
|---|---|---|
| **1. Trigger + settings** | Runs daily at 06:00 UTC, or when you click Execute. Loads the settings, prompts and already-processed job URLs from the Google Sheet. | Grey section |
| **2. Fetch + filter** | Calls the public APIs of **Himalayas**, **RemoteOK** and **Jobicy**. Converts every job to one format (title, company, location, description, URL, date). Removes jobs with the wrong title keywords, excluded companies, postings older than 30 days, and duplicates. | Blue section |
| **3. AI check** | LLM call 1 returns `is_remote`, `is_english`, `is_relevant`, `is_agency` and `language_requirements`, with a one-line reason. A job is kept only if all three checks pass and it isn't a staffing or VA agency. | Green section |
| **4. AI outreach** | LLM call 2 writes a short, personalised email using details from that specific posting. The prompt comes from the Sheet's **Prompts** tab. | Green section |
| **5. Save + log** | Matches go to **Leads**. Rejections go to **Rejected** with the reason. Each run adds a row to **Run Log**, and the full run is saved as JSON on the server. | Red section |

**Built-in safeguards**
- **No duplicates.** A job already in Leads or Rejected is never processed again, so the AI never gets paid to re-check it.
- **Self-healing.** If the AI fails (busy model, rate limit), the job is *not* saved, so the next run retries it automatically.
- **Fallback model.** If the main model is down, OpenRouter switches to the fallback model automatically.
- **Cost cap.** `max_jobs_per_run` limits how many jobs go to the AI in one run.
- **Fault-tolerant sources.** If one job board fails, the others still run.

---

## 2. For sales reps: using the Sheet

1. Open the **Leads** tab and filter **Status = New**.
2. Open the **Job Posting URL** and read the draft in **LLM-Generated Outreach Message**. Edit it if needed.
3. Send the message from your own email, then set **Status → Contacted**.
4. Keep the status up to date as things progress: **Replied**, **Meeting Booked** or **Not a Fit**. Use **Notes** for context.

| Tab | Purpose |
|---|---|
| **How to Use** | One-page guide inside the Sheet |
| **Leads** | Your dashboard. The 6 required columns, then Language Requirements, Source, Date Posted, Date Found, Prompt Used, Status and Notes |
| **Rejected** | Jobs the AI filtered out, with Yes/No for each check and the reason |
| **Settings** | Search terms, filters, AI models and sender details |
| **Prompts** | The AI instructions, editable as plain text |
| **Run Log** | One row per run: jobs fetched, filtered, checked, added, rejected and errors |

> Don't delete rows in Leads or Rejected. The automation uses them to avoid duplicates. Set **Not a Fit** instead.

![Leads tab](docs/images/sheet-leads.png)

---

## 3. Changing filters and the AI prompt (no n8n needed)

Everything you'd want to tune is in the Google Sheet. Changes apply on the **next run**.

### Filters (Settings tab)
| Setting | Example | Effect |
|---|---|---|
| `search_queries` | `executive assistant, admin assistant` | Searches sent to Himalayas |
| `title_include_keywords` | `executive assistant, office administrator` | A title must contain at least one of these |
| `title_exclude_keywords` | `medical, dental, sales` | Titles containing these are skipped |
| `excluded_companies` | `Wing Assistant, Hire Overseas` | Never contact these companies (competitors, agencies) |
| `exclude_agencies` | `TRUE` | Also drop jobs the AI identifies as staffing or VA agencies |
| `max_posting_age_days` | `30` | Ignore older postings |
| `max_jobs_per_run` | `15` | Maximum jobs sent to the AI per run |

### Prompt and tone
- The **Prompts** tab has two outreach prompts, `v1_warm` and `v2_direct`, plus the `validation` prompt.
- **To test a new tone:** add a row to Prompts (for example `v3_short`), paste your prompt and set **Settings → `outreach_prompt`** to `v3_short`.
- Every lead records the **Prompt Used**, so you can compare reply rates by prompt.
- Available placeholders: `{{job_title}}`, `{{company_name}}`, `{{location}}`, `{{job_description}}`, `{{language_requirements}}`, `{{sender_name}}`, `{{sender_company}}`, `{{sender_offer}}` and `{{call_to_action}}`.
- **Sender details** (`sender_name`, `sender_company`, `sender_offer`, `call_to_action`) live in Settings. The AI may only state facts about us that appear in `sender_offer`.

### AI model
`validation_model`, `outreach_model` and `fallback_model` accept any model ID from [OpenRouter](https://openrouter.ai/models). Free models end in `:free`.

---

## 4. Install

### What you need
- An n8n instance, version 2.x. n8n Cloud and self-hosted both work, or use option B below for a ready-made server.
- A Google account, plus a Google Cloud **service account** with the Sheets API and Drive API enabled.
- An **OpenRouter API key** from https://openrouter.ai/settings/keys. A free account works.

### Option A: use an existing n8n
1. **Create the Sheet.** Create a blank Google Sheet and share it as **Editor** with your service-account email. Then run:
   ```bash
   cd scripts
   pip install -r requirements.txt
   python setup_sheet.py --sheet-id <SHEET_ID> --key <service-account.json>
   ```
   This creates every tab, header, dropdown and default setting. It's safe to re-run.
2. **Import the workflow.** In n8n, go to **Workflows → Import from file** and choose `workflow/job-outreach-workflow.json`.
3. **Add the credentials** in n8n under **Credentials → New**:
   - **Google API (Service Account):** paste the service-account email and private key.
   - **Header Auth:** Name `Authorization`, Value `Bearer <your OpenRouter key>`.

   Then open each Google Sheets node and each **AI:** node, and pick these credentials.
4. **Set the Sheet ID.** Open the **Config** node and paste your Sheet ID. It's the long code in the Sheet URL.
5. **Test.** Click **Execute workflow** and check the Leads, Rejected and Run Log tabs.
6. **Schedule it.** Click **Publish**, top right. The workflow then runs every day at 06:00 UTC.

### Option B: deploy your own server (Azure)
`deploy/deploy-azure.sh` creates an Ubuntu VM with Docker, n8n 2.47.2 and Caddy, which provides free automatic HTTPS. SSH access is limited to your IP address.
```bash
az login
bash deploy/deploy-azure.sh my-n8n-name      # → https://my-n8n-name.southafricanorth.cloudapp.azure.com
```
Open the URL, create the owner account, then follow option A from step 2.
Monthly cost is about $30 (Standard_B2als_v2 with 4 GB RAM). The 1 GB size is too small for n8n.

### Rebuilding the workflow from source
The JavaScript in each Code node is kept as readable files in `workflow/code/`. After editing one, run:
```bash
python scripts/build_workflow.py        # regenerates workflow/job-outreach-workflow.json
```

---

## 5. Running and scheduling

| Task | How |
|---|---|
| Run now | Open the workflow in n8n and click **Execute workflow** |
| Change the schedule | Open the **Daily at 06:00 UTC** node, change the hour or frequency (for example weekly), then **Publish** |
| Pause | Click **Unpublish** |
| See past runs | Check the **Executions** tab in n8n, or the **Run Log** tab in the Sheet |
| Raw data per run | `/opt/n8n/files/job-run-<date>.json` on the server. A sample is in `sample-output/` |

A typical run takes 2–3 minutes. It fetches about 260–360 postings, of which about 50 pass the keyword filter. Up to 15 new ones go to the AI, and roughly half become leads.

---

## 6. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Run Log shows **LLM Errors** > 0 | Free model rate-limited (HTTP 429) or temporarily down | Nothing to do: those jobs retry next run. If it happens daily, lower `max_jobs_per_run`, switch model, or add $10 OpenRouter credit (raises the free limit from 50 to 1,000 requests/day) |
| **Leads Added = 0**, Checked by LLM = 0 | No *new* matching jobs (all already seen) | Normal on quiet days. Broaden `search_queries` / `title_include_keywords` |
| Good job ended up in **Rejected** | AI judged it non-remote, non-English or an agency | Read the Reason column; adjust the `validation` prompt or settings. Delete that row to have it re-checked |
| Error: *"outreach_prompt is … but no row with that Prompt Name exists"* | Typo in Settings → `outreach_prompt` | Use the exact Prompt Name from the Prompts tab |
| Google Sheets node: *permission denied / 404* | Sheet not shared with the service account, or wrong ID in **Config** | Share the sheet as Editor with the service-account email; check the ID |
| OpenRouter *401* | Wrong/expired key | Update the **OpenRouter API key** credential (`Bearer sk-or-…`) |
| A job board returns nothing | API down or changed | The other sources still run; check the node output in **Executions** |
| Messages too long / wrong tone | Prompt | Edit or add a prompt in the Prompts tab — no workflow change needed |

---

## 7. Design decisions

- **Compliant sources.** All three boards publish free public JSON APIs intended for reuse. No HTML scraping, no LinkedIn. Each lead links to the original posting and keeps its source name, as the boards' terms ask.
- **Cheap filter first, AI second.** Keyword rules remove about 85% of postings before any AI call. This keeps the workflow inside the free LLM tier.
- **Strict JSON from the AI.** The validator must return booleans plus a reason, so every decision can be audited in the Rejected tab.
- **Agency detection.** Many remote EA postings come from VA and staffing agencies, which are competitors rather than leads. They're excluded both by name and by the AI check.
- **No made-up claims.** The outreach prompt allows facts about the company only from the posting, and facts about us only from `sender_offer`.
- **Configuration in the Sheet.** Non-technical users can change search terms, filters, models and tone without opening n8n.

## 8. Repository layout
```
task1-job-outreach/
├── workflow/job-outreach-workflow.json   # import this into n8n
├── workflow/code/*.js                    # source of every Code node
├── prompts/*.md                          # default prompts (copied into the Sheet)
├── scripts/setup_sheet.py                # creates/formats the Google Sheet
├── scripts/build_workflow.py             # builds the workflow JSON from source
├── deploy/                               # Azure VM + Docker + HTTPS setup
├── sample-output/                        # leads.csv, rejected.csv, run-log.csv, job-run-sample.json
└── docs/images/                          # screenshots
```

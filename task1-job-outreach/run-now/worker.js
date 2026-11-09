// Public "Run now" page for Task 1 (Cloudflare Worker, free plan).
//
// GET  /      -> a page showing the latest runs and a "Run the automation now" button
// POST /run   -> starts the GitHub Actions workflow (15-minute cooldown, never two runs at once)
// cron        -> independent backup for GitHub's scheduler: if no daily run has succeeded today, start one
//
// Secret: GITHUB_TOKEN = fine-grained GitHub token limited to this one repository, permission "Actions: read and write".
// It can only start/read workflow runs: it cannot read code secrets or change any code.

const REPO = "benjaminkariuki/ray-ai-automation-case-study";
const WORKFLOW = "job-outreach.yml";
const ACTIONS_URL = `https://github.com/${REPO}/actions/workflows/${WORKFLOW}`;
const SHEET_URL = "https://docs.google.com/spreadsheets/d/1GwAt8R3_O-h6ivZ_CT_8yD6GMIdybyf2-YgscTQ9hRI/edit";
const REPO_URL = `https://github.com/${REPO}/tree/main/task1-job-outreach`;
const COOLDOWN_MINUTES = 15;
const ACTIVE = ["queued", "in_progress", "waiting", "requested", "pending"];

async function github(env, path, init = {}) {
  return fetch(`https://api.github.com/repos/${REPO}${path}`, {
    ...init,
    headers: {
      Authorization: `Bearer ${env.GITHUB_TOKEN}`,
      Accept: "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28",
      "User-Agent": "ray-run-now",
      ...(init.headers || {}),
    },
  });
}

async function recentRuns(env, count = 8) {
  const r = await github(env, `/actions/workflows/${WORKFLOW}/runs?per_page=${count}`);
  if (!r.ok) throw new Error(`GitHub API returned ${r.status}`);
  return (await r.json()).workflow_runs || [];
}

async function startRun(env, trigger) {
  const r = await github(env, `/actions/workflows/${WORKFLOW}/dispatches`, {
    method: "POST",
    body: JSON.stringify({ ref: "main", inputs: { trigger } }),
  });
  if (r.status !== 204) throw new Error(`GitHub API returned ${r.status}: ${(await r.text()).slice(0, 200)}`);
}

const minutesAgo = (iso) => (Date.now() - Date.parse(iso)) / 60000;
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

function statusBadge(run) {
  if (ACTIVE.includes(run.status)) return `<span class="b run">⏳ running</span>`;
  if (run.conclusion === "success") return `<span class="b ok">✓ success</span>`;
  if (run.conclusion === "skipped" || run.conclusion === "cancelled") return `<span class="b grey">${esc(run.conclusion)}</span>`;
  return `<span class="b bad">✗ ${esc(run.conclusion || run.status)}</span>`;
}

function page({ runs, notice, error }) {
  const active = runs.some((r) => ACTIVE.includes(r.status));
  // Refresh while a run is going, or just after "Run now" until the new run shows up (it takes a few seconds).
  const waitingForNewRun = notice === NOTICES.started && !runs.some((r) => minutesAgo(r.created_at) < 2);
  const refresh = active ? 20 : waitingForNewRun ? 4 : 0;
  const rows = runs
    .map((r) => `<tr><td>${esc(r.created_at.replace("T", " ").slice(0, 16))} UTC</td><td>${esc(r.display_title)}</td>
      <td>${statusBadge(r)}</td><td><a href="${esc(r.html_url)}" target="_blank" rel="noopener">details</a></td></tr>`)
    .join("");
  return `<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
${refresh ? `<meta http-equiv="refresh" content="${refresh}">` : ""}
<title>Run now – RAY Task 1</title>
<style>
  :root{--bg:#f6f7fb;--card:#fff;--ink:#1d2433;--mute:#5b6475;--line:#e3e6ee;--brand:#1f4fd1;--ok:#e3f5e6;--okt:#16692a;--bad:#fde4e4;--badt:#9b1c1c;--run:#fff4d6;--runt:#7a5300}
  @media (prefers-color-scheme:dark){:root{--bg:#12151c;--card:#1b1f29;--ink:#e8ebf2;--mute:#a3abbb;--line:#2c3240;--brand:#7aa2ff;--ok:#173a22;--okt:#8fe0a5;--bad:#43191c;--badt:#ffaaaa;--run:#3d3216;--runt:#ffd98a}}
  *{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
  main{max-width:820px;margin:0 auto;padding:28px 16px 48px}h1{font-size:1.5rem;margin:0 0 4px}p{margin:.4rem 0}
  .card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:20px;margin:18px 0}
  .mute{color:var(--mute);font-size:.92rem}a{color:var(--brand)}
  button{background:var(--brand);color:#fff;border:0;border-radius:10px;padding:13px 22px;font-size:1.05rem;font-weight:600;cursor:pointer}
  button:hover{filter:brightness(1.1)}
  .notice{border-radius:10px;padding:12px 14px;margin:12px 0;background:var(--run);color:var(--runt)}
  .notice.ok{background:var(--ok);color:var(--okt)}.notice.bad{background:var(--bad);color:var(--badt)}
  table{width:100%;border-collapse:collapse;font-size:.93rem}td,th{padding:8px 6px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
  .b{display:inline-block;border-radius:999px;padding:1px 9px;font-size:.85rem;white-space:nowrap}
  .ok{background:var(--ok);color:var(--okt)}.bad{background:var(--bad);color:var(--badt)}.run{background:var(--run);color:var(--runt)}.grey{background:var(--line)}
  ol{padding-left:20px;margin:.4rem 0}.wrap{overflow-x:auto}
</style></head><body><main>
<h1>RAY Task 1 – run the job-outreach automation</h1>
<p class="mute">For evaluators: start the same GitHub Actions run that happens every day, without a GitHub account.</p>
${notice ? `<div class="notice ${notice.kind}">${notice.html}</div>` : ""}
${error ? `<div class="notice bad">${esc(error)}</div>` : ""}
<div class="card">
  <form method="post" action="/run"><button type="submit">▶ Run the automation now</button></form>
  <p class="mute" style="margin-top:12px">What happens: it fetches new Executive/Admin Assistant jobs, checks each with AI
  (remote + English + relevant), writes outreach for the ones that pass and adds them to the Google Sheet.
  A run takes about 3–6 minutes. To protect the free AI limits there is a ${COOLDOWN_MINUTES}-minute cooldown between runs,
  and jobs already in the Sheet are skipped, so a run soon after another may add few or no new leads.</p>
</div>
<div class="card">
  <strong>Then check the result</strong>
  <ol>
    <li><a href="${SHEET_URL}" target="_blank" rel="noopener">Google Sheet</a> → <b>Run Log</b> tab: a new row with Trigger
      “Run now (public link)”. New leads appear at the bottom of <b>Leads</b>, rejections in <b>Rejected</b>.</li>
    <li><a href="${ACTIONS_URL}" target="_blank" rel="noopener">GitHub run history</a>: the run and its summary.</li>
  </ol>
  <p class="mute">Tip: anyone with the link can edit the Sheet. Set <b>Settings → outreach_prompt</b> to <code>v2_direct</code>
  before running to see the other prompt in action.</p>
</div>
<div class="card wrap"><strong>Latest runs</strong>${active ? ' <span class="mute">(this page refreshes every 20 s)</span>' : ""}
  <table><thead><tr><th>Started</th><th>Run</th><th>Status</th><th></th></tr></thead><tbody>${rows ||
    '<tr><td colspan="4">No runs found.</td></tr>'}</tbody></table>
</div>
<p class="mute">Source code of this page: <a href="${REPO_URL}/run-now" target="_blank" rel="noopener">run-now/worker.js</a> ·
  <a href="${REPO_URL}" target="_blank" rel="noopener">Task 1 README</a></p>
</main></body></html>`;
}

const html = (body, status = 200) =>
  new Response(body, { status, headers: { "content-type": "text/html; charset=utf-8", "cache-control": "no-store" } });

// Returns the notice to show: "busy", "cooldown" or "started".
async function handleRun(env) {
  const runs = await recentRuns(env, 5);
  if (runs.some((r) => ACTIVE.includes(r.status))) return "busy";
  if (runs.some((r) => minutesAgo(r.created_at) < COOLDOWN_MINUTES)) return "cooldown";
  await startRun(env, "run-now");
  return "started";
}

const NOTICES = {
  started: { kind: "ok", html: "✓ Started. The new run appears in the table below within a few seconds and takes about 3–6 minutes." },
  busy: { kind: "", html: "A run is already in progress – watch it in the table below." },
  cooldown: { kind: "", html: `A run started less than ${COOLDOWN_MINUTES} minutes ago. Please wait a little and try again.` },
};

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    try {
      if (url.pathname === "/run" && request.method === "POST") {
        const state = await handleRun(env);
        return Response.redirect(`${url.origin}/?state=${state}`, 303); // POST-redirect-GET: refresh never re-runs
      }
      if (url.pathname !== "/") return html("Not found", 404);
      const runs = await recentRuns(env);
      return html(page({ runs, notice: NOTICES[url.searchParams.get("state")] }));
    } catch (err) {
      return html(page({ runs: [], error: `Could not reach GitHub (${err.message}). Please try again in a minute.` }), 502);
    }
  },

  // Independent backup for GitHub's cron: start the daily run if none has succeeded today and none is running.
  async scheduled(event, env, ctx) {
    const today = new Date().toISOString().slice(0, 10);
    const runs = await recentRuns(env, 30);
    const todays = runs.filter((r) => r.created_at.startsWith(today) && r.display_title.startsWith("Daily run"));
    if (todays.some((r) => r.conclusion === "success" || ACTIVE.includes(r.status))) return;
    await startRun(env, "daily-backup");
  },
};

// Build Run Report
// Creates the structured JSON record of this run (every scraped posting + every AI decision)
// which the next nodes save to disk as /files/job-run-<timestamp>.json

const safe = (node) => { try { return $(node).all().map((i) => i.json); } catch (e) { return []; } };
const norm = $('Normalize & Filter').first().json;

const decisions = safe('Parse AI Check').map(({ outreachRequest, outreachBackup, description, ...j }) => j);
const messages = Object.fromEntries(safe('Format Lead').map((l) => [l['Job Posting URL'], l['LLM-Generated Outreach Message']]));
for (const d of decisions) if (messages[d.url]) d.outreachMessage = messages[d.url];

return [{
  json: {
    runAt: new Date().toISOString(),
    summary: $('Summarize Run').first().json,
    stats: norm.stats,
    decisions,
    scraped: norm.scraped,
  },
}];

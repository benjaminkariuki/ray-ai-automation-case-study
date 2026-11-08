// Parse AI Check  (runs once per job)
// Reads the LLM's JSON verdict and decides: "lead" (all checks pass), "rejected", or "error"
// (LLM failed -> job is NOT saved, so it is retried automatically on the next run).
// For leads it also prepares the outreach prompt.

const config = $('Build Search Plan').first().json.config;
const job = $('Prepare AI Check').item.json;
const fill = (tpl, vars) => tpl.replace(/\{\{\s*(\w+)\s*\}\}/g, (m, k) => (k in vars ? String(vars[k]) : m));
const bool = (v) => v === true || String(v).toLowerCase() === 'true';

const { validationRequest, ...base } = job;
const raw = $json.choices?.[0]?.message?.content;
let check = null;
if (raw) {
  const text = String(raw).replace(/<think>[\s\S]*?<\/think>/g, '');
  const match = text.match(/\{[\s\S]*\}/);
  try { check = match ? JSON.parse(match[0]) : null; } catch (e) { check = null; }
}

if (!check) {
  const why = $json.error ? JSON.stringify($json.error).slice(0, 300) : `Unreadable model reply: ${String(raw).slice(0, 200)}`;
  return { json: { ...base, decision: 'error', error: why } };
}

const verdict = {
  remote: bool(check.is_remote),
  english: bool(check.is_english),
  relevant: bool(check.is_relevant),
  agency: bool(check.is_agency),
  languages: String(check.language_requirements || 'English'),
  reason: String(check.reason || ''),
  model: $json.model || '',
};
const isLead = verdict.remote && verdict.english && verdict.relevant && !(config.excludeAgencies && verdict.agency);

const out = { ...base, verdict, decision: isLead ? 'lead' : 'rejected' };
if (isLead) {
  out.outreachRequest = {
    models: [config.outreachModel, config.fallbackModel].filter(Boolean),
    temperature: 0.7,
    messages: [{
      role: 'user',
      content: fill(config.outreachPrompt, {
        ...config.sender,
        job_title: job.title, company_name: job.company, location: job.location,
        language_requirements: verdict.languages, job_description: job.description.slice(0, 6000),
      }),
    }],
  };
}
return { json: out };

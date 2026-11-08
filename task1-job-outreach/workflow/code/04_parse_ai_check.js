// Parse AI Check  (runs once per job)
// Reads the LLM's JSON verdict (from OpenRouter, or from the Cloudflare backup if OpenRouter failed)
// and decides: "lead" (all checks pass), "rejected", or "error" (both AI providers failed -> the job
// is NOT saved, so it is retried automatically on the next run).
// For leads it also prepares the outreach requests (primary + backup).

const config = $('Build Search Plan').first().json.config;
const job = $('Prepare AI Check').item.json;
const fill = (tpl, vars) => tpl.replace(/\{\{\s*(\w+)\s*\}\}/g, (m, k) => (k in vars ? String(vars[k]) : m));
const bool = (v) => v === true || String(v).toLowerCase() === 'true';
const provider = (model) => (String(model).startsWith('@cf/') ? 'Cloudflare' : 'OpenRouter');

const { validationRequest, validationBackup, ...base } = job;
const raw = $json.choices?.[0]?.message?.content;
let check = null;
if (raw) {
  const text = String(raw).replace(/<think>[\s\S]*?<\/think>/g, '');
  const match = text.match(/\{[\s\S]*\}/);
  try { check = match ? JSON.parse(match[0]) : null; } catch (e) { check = null; }
}

// An incomplete answer (missing fields or no reason) is treated as an error, never as a rejection,
// so a good job is never dropped because a model cut its reply short. It is retried next run.
const REQUIRED_KEYS = ['is_remote', 'is_english', 'is_relevant', 'is_agency', 'reason'];
if (check && (REQUIRED_KEYS.some((k) => !(k in check)) || !String(check.reason).trim())) check = null;

if (!check) {
  const why = $json.error ? JSON.stringify($json.error).slice(0, 300) : `Unreadable or incomplete model reply: ${String(raw).slice(0, 200)}`;
  return { json: { ...base, decision: 'error', error: why } };
}

const model = $json.model || config.backupModel;
const verdict = {
  remote: bool(check.is_remote),
  english: bool(check.is_english),
  relevant: bool(check.is_relevant),
  agency: bool(check.is_agency),
  languages: String(check.language_requirements || 'English'),
  reason: String(check.reason || ''),
  model: `${model} (${provider(model)})`,
};
const isLead = verdict.remote && verdict.english && verdict.relevant && !(config.excludeAgencies && verdict.agency);

const out = { ...base, verdict, decision: isLead ? 'lead' : 'rejected' };
if (isLead) {
  const messages = [{
    role: 'user',
    content: fill(config.outreachPrompt, {
      ...config.sender,
      job_title: job.title, company_name: job.company, location: job.location,
      language_requirements: verdict.languages, job_description: job.description.slice(0, 6000),
    }),
  }];
  out.outreachRequest = { models: [config.outreachModel, config.fallbackModel].filter(Boolean), temperature: 0.7, messages };
  out.outreachBackup = { model: config.backupModel, temperature: 0.7, max_tokens: 2500, messages };
}
return { json: out };

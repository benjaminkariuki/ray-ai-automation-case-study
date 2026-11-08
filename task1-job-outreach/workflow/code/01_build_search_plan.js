// Build Search Plan
// Reads the Settings tab into a config object and emits one item per Himalayas search page.
// The config travels on every item so later nodes can read it via $('Build Search Plan').first().json.config

const list = (v) => String(v || '').split(',').map((s) => s.trim().toLowerCase()).filter(Boolean);

const s = {};
for (const { json } of $('Read Settings').all()) {
  if (json.Setting) s[String(json.Setting).trim()] = String(json.Value ?? '').trim();
}

const prompts = {};
for (const { json } of $('Read Prompts').all()) {
  if (json['Prompt Name']) prompts[String(json['Prompt Name']).trim()] = String(json['Prompt Text'] || '');
}

const outreachPromptName = s.outreach_prompt || 'v1_warm';
if (!prompts[outreachPromptName]) {
  throw new Error(`Settings > outreach_prompt is "${outreachPromptName}" but no row with that Prompt Name exists in the Prompts tab.`);
}
if (!prompts.validation) throw new Error('The Prompts tab needs a row named "validation".');

const config = {
  searchQueries: list(s.search_queries),
  pagesPerQuery: Math.max(1, Math.min(5, parseInt(s.himalayas_pages_per_query, 10) || 2)),
  includeKeywords: list(s.title_include_keywords),
  excludeKeywords: list(s.title_exclude_keywords),
  excludedCompanies: list(s.excluded_companies),
  excludeAgencies: String(s.exclude_agencies || 'TRUE').toUpperCase() !== 'FALSE',
  maxAgeDays: parseInt(s.max_posting_age_days, 10) || 30,
  maxJobsPerRun: parseInt(s.max_jobs_per_run, 10) || 15,
  validationModel: s.validation_model || 'nvidia/nemotron-3-ultra-550b-a55b:free',
  outreachModel: s.outreach_model || 'nvidia/nemotron-3-ultra-550b-a55b:free',
  fallbackModel: s.fallback_model || '',
  backupModel: s.backup_model || '@cf/openai/gpt-oss-120b',
  outreachPromptName,
  outreachPrompt: prompts[outreachPromptName],
  validationPrompt: prompts.validation,
  sender: {
    sender_name: s.sender_name || '',
    sender_company: s.sender_company || '',
    sender_offer: s.sender_offer || '',
    call_to_action: s.call_to_action || '',
  },
};

if (!config.searchQueries.length) throw new Error('Settings > search_queries is empty.');

const out = [];
for (const q of config.searchQueries) {
  for (let page = 1; page <= config.pagesPerQuery; page++) out.push({ json: { q, page, config } });
}
return out;

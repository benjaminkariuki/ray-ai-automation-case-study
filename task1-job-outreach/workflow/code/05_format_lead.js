// Format Lead
// Pairs each generated message (from OpenRouter or the Cloudflare backup) with its job and maps it
// to the Leads tab columns. If both AI providers failed, the job is skipped and retried next run.

const config = $('Build Search Plan').first().json.config;
const today = new Date().toISOString().slice(0, 10);
const provider = (model) => (String(model).startsWith('@cf/') ? 'Cloudflare' : 'OpenRouter');

const clean = (t) => String(t || '')
  .replace(/<think>[\s\S]*?<\/think>/g, '')
  .replace(/[‐‑]/g, '-').replace(/[  ]/g, ' ') // non-breaking hyphens/spaces some models emit
  .replace(/^```[a-z]*\n?|```$/gim, '')
  .replace(/\*\*(.*?)\*\*/g, '$1')
  .trim();

return $input.all().flatMap((item, i) => {
  const job = $('Is it a match?').itemMatching(i).json;
  let message = clean(item.json.choices?.[0]?.message?.content);
  if (!message || message.length < 80) return [];
  // Same ending whatever the model wrote: body, blank line, call to action, blank line, signature.
  const { call_to_action: cta, sender_name: name, sender_company: company } = config.sender;
  if (cta) message = message.split(cta).join('');
  const signatureLines = [name, company].filter(Boolean).map((s) => s.trim());
  message = message.split('\n').map((l) => l.trimEnd()).filter((l) => !signatureLines.includes(l.trim()))
    .join('\n').replace(/\n{3,}/g, '\n\n').trim();
  message = [message, cta, signatureLines.join('\n')].filter(Boolean).join('\n\n');
  const model = item.json.model || config.backupModel;
  return [{
    json: {
      'Job Posting URL': job.url,
      'Job Title': job.title,
      'Company Name': job.company,
      'Location': job.location,
      // One line keeps rows compact in the sheet; the full formatted text is in the run JSON.
      'Job Description': job.description.replace(/\s*\n+\s*/g, ' | ').replace(/^- /, ''),
      'LLM-Generated Outreach Message': message,
      'Language Requirements': job.verdict.languages,
      'Source': job.source,
      'Date Posted': job.datePosted,
      'Date Found': today,
      'Prompt Used': config.outreachPromptName,
      'AI Model': `${model} (${provider(model)})`,
      'Status': 'New',
      'Notes': '',
    },
  }];
});

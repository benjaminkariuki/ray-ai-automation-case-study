// Format Lead
// Pairs each generated message with its job and maps it to the Leads tab columns.
// If the LLM failed to write a message the job is skipped (and retried next run).

const config = $('Build Search Plan').first().json.config;
const today = new Date().toISOString().slice(0, 10);

const clean = (t) => String(t || '')
  .replace(/<think>[\s\S]*?<\/think>/g, '')
  .replace(/^```[a-z]*\n?|```$/gim, '')
  .replace(/\*\*(.*?)\*\*/g, '$1')
  .trim();

return $input.all().flatMap((item, i) => {
  const job = $('Is it a match?').itemMatching(i).json;
  const message = clean(item.json.choices?.[0]?.message?.content);
  if (!message || message.length < 80) return [];
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
      'Status': 'New',
      'Notes': '',
    },
  }];
});

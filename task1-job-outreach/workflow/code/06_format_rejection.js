// Format Rejection
// Maps jobs the AI rejected to the Rejected tab columns. LLM errors are dropped here
// (not saved), so those jobs are automatically retried on the next run.

const today = new Date().toISOString().slice(0, 10);
const yn = (b) => (b ? 'Yes' : 'No');

return $input.all()
  .filter((i) => i.json.decision === 'rejected')
  .map(({ json: j }) => ({
    json: {
      'Job Posting URL': j.url,
      'Job Title': j.title,
      'Company Name': j.company,
      'Location': j.location,
      'Remote': yn(j.verdict.remote),
      'English': yn(j.verdict.english),
      'Relevant': yn(j.verdict.relevant),
      'Agency': yn(j.verdict.agency),
      'Reason': j.verdict.reason,
      'Source': j.source,
      'Date Checked': today,
    },
  }));

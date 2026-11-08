// Summarize Run
// Runs last (bottom branch). Counts what happened and builds the Run Log row.
// Uses try/catch because branches with zero jobs never execute.

const count = (node, filter = () => true) => {
  try { return $(node).all().filter(filter).length; } catch (e) { return 0; }
};
const stats = $('Normalize & Filter').first().json.stats;
const cfOk = (i) => !i.json.error;

return [{
  json: {
    'Run Time (UTC)': new Date().toISOString().replace('T', ' ').slice(0, 16),
    'Trigger': $('Config').first().json.trigger || 'Manual',
    'Fetched': stats.fetched,
    'Passed Keyword Filter': stats.passedKeyword,
    'Already Seen': stats.alreadySeen,
    'Checked by LLM': stats.sentToLLM,
    'Leads Added': count('Add to Leads'),
    'Rejected': count('Add to Rejected'),
    'LLM Errors': count('Parse AI Check', (i) => i.json.decision === 'error'),
    'Backup AI Used': count('Backup AI: Validate', cfOk) + count('Backup AI: Write Outreach', cfOk),
  },
}];

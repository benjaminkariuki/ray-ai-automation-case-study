// Prepare AI Check  (runs once per job)
// Fills the validation prompt template from the Prompts tab with this job's details.

const config = $('Build Search Plan').first().json.config;
const fill = (tpl, vars) => tpl.replace(/\{\{\s*(\w+)\s*\}\}/g, (m, k) => (k in vars ? String(vars[k]) : m));

const job = $json;
return {
  json: {
    ...job,
    validationRequest: {
      models: [config.validationModel, config.fallbackModel].filter(Boolean),
      temperature: 0,
      response_format: { type: 'json_object' },
      messages: [{
        role: 'user',
        content: fill(config.validationPrompt, {
          job_title: job.title, company_name: job.company, location: job.location,
          job_description: job.description.slice(0, 6000),
        }),
      }],
    },
  },
};

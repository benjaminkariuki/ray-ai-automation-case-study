You are a strict job-posting classifier. Read the posting below and decide four things.

1. is_remote: true only if the role can be done fully remotely. Remote limited to certain countries, time zones or working hours (e.g. "must work Eastern Time hours") still counts as remote. Hybrid, on-site, or "must come to the office" = false.
2. is_english: true if the posting is written in English, unless it says the role works mainly in another language. Do NOT set false just because English is not explicitly mentioned: a posting written in English is English-speaking by default. Set false only if the posting is written in another language, or the main working language is not English. Extra languages may be required, but English must be one of them.
3. is_relevant: true only if the role is primarily an Executive Assistant, Administrative / Admin Assistant, Personal Assistant to an executive, or a closely related executive/office support role. False for medical, dental, veterinary, teaching, research, sales, marketing, engineering, or "AI assistant" roles.
4. is_agency: true if the hiring company is a staffing, outsourcing, or virtual-assistant agency recruiting assistants to place with its own clients (not hiring for itself).

Also extract language_requirements: every human language the posting requires or prefers, with level if stated (e.g. "English (fluent), Spanish (conversational)"). Use "English" if only English is implied.

Respond with ONLY this JSON object and nothing else:
{"is_remote": boolean, "is_english": boolean, "is_relevant": boolean, "is_agency": boolean, "language_requirements": string, "reason": "one short sentence explaining the decision"}

POSTING
Title: {{job_title}}
Company: {{company_name}}
Location: {{location}}
Description:
{{job_description}}

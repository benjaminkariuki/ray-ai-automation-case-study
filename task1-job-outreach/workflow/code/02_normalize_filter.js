// Normalize & Filter
// 1. Converts the three job-board formats into one schema.
// 2. Applies the cheap keyword / company / age filters from Settings.
// 3. Skips jobs already in the Leads or Rejected tabs (no duplicates, no wasted LLM calls).
// Outputs ONE item: { stats, candidates[], scraped[] }.

const config = $('Build Search Plan').first().json.config;
const now = Date.now();

const decode = (t) => String(t || '')
  .replace(/&nbsp;/g, ' ').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>')
  .replace(/&quot;/g, '"').replace(/&#0?39;|&apos;|&#8217;/g, "'")
  .replace(/&#(\d+);/g, (_, n) => String.fromCharCode(Number(n)));
const htmlToText = (html) => decode(decode(html)
  .replace(/<\s*br\s*\/?>/gi, '\n')
  .replace(/<\s*li[^>]*>/gi, '\n- ')
  .replace(/<\/(p|div|h[1-6]|ul|ol|li)>/gi, '\n')
  .replace(/<[^>]+>/g, ''))
  .replace(/[ \t]+/g, ' ').replace(/\n\s*\n\s*\n+/g, '\n\n').trim();
const asList = (v) => {
  if (Array.isArray(v)) return v;
  if (typeof v === 'string' && v.startsWith('[')) { try { return JSON.parse(v.replace(/'/g, '"')); } catch (e) { /* fall through */ } }
  return v ? [v] : [];
};
const iso = (d) => (d && !isNaN(d) ? new Date(d).toISOString().slice(0, 10) : '');

const scraped = [];
const sourceErrors = [];
for (const { json } of $input.all()) {
  if (json.error) { sourceErrors.push(String(json.error.message || json.error).slice(0, 200)); continue; }
  // Himalayas: { totalCount, jobs: [...] }
  if (Array.isArray(json.jobs) && json.totalCount !== undefined) {
    for (const j of json.jobs) {
      const locs = asList(j.locationRestrictions);
      scraped.push({
        source: 'Himalayas', url: j.guid || j.applicationLink, title: j.title, company: j.companyName,
        location: locs.length ? `Remote (${locs.join(', ')})` : 'Remote (Worldwide)',
        description: htmlToText(j.description), postedMs: Number(j.pubDate) * 1000,
      });
    }
  // Jobicy: { apiVersion, jobs: [...] }
  } else if (Array.isArray(json.jobs) && json.apiVersion) {
    for (const j of json.jobs) {
      scraped.push({
        source: 'Jobicy', url: j.url, title: decode(j.jobTitle), company: decode(j.companyName),
        location: `Remote (${j.jobGeo || 'Worldwide'})`,
        description: htmlToText(j.jobDescription), postedMs: Date.parse(j.pubDate),
      });
    }
  // RemoteOK: one item per job (first item is the legal notice and has no position)
  } else if (json.position && json.url) {
    scraped.push({
      source: 'RemoteOK', url: json.url, title: decode(json.position), company: decode(json.company),
      location: json.location ? `Remote (${json.location})` : 'Remote',
      description: htmlToText(json.description), postedMs: Number(json.epoch) * 1000,
    });
  }
}

// Already processed URLs (Leads + Rejected tabs)
const seen = new Set();
for (const node of ['Read Leads', 'Read Rejected']) {
  for (const { json } of $(node).all()) if (json['Job Posting URL']) seen.add(String(json['Job Posting URL']).trim());
}

const hasAny = (text, words) => words.some((w) => text.includes(w));
const unique = new Map();
let passedKeyword = 0, alreadySeen = 0;
for (const j of scraped) {
  if (!j.url || !j.title || unique.has(j.url)) continue;
  const title = j.title.toLowerCase();
  const company = String(j.company || '').toLowerCase();
  const ageDays = (now - j.postedMs) / 86400000;
  if (!hasAny(title, config.includeKeywords)) continue;
  if (hasAny(title, config.excludeKeywords)) continue;
  if (config.excludedCompanies.some((c) => company.includes(c))) continue;
  if (j.postedMs && ageDays > config.maxAgeDays) continue;
  passedKeyword++;
  if (seen.has(j.url)) { alreadySeen++; continue; }
  unique.set(j.url, j);
}

const ready = [...unique.values()].sort((a, b) => (b.postedMs || 0) - (a.postedMs || 0));
const candidates = ready.slice(0, config.maxJobsPerRun).map((j) => ({
  url: j.url, title: j.title, company: j.company || 'Unknown', location: j.location, source: j.source,
  datePosted: iso(j.postedMs), description: j.description.slice(0, 30000),
}));

return [{
  json: {
    stats: {
      fetched: scraped.length, passedKeyword, alreadySeen,
      sentToLLM: candidates.length, deferredToNextRun: Math.max(0, ready.length - candidates.length),
      sourceErrors,
    },
    candidates,
    scraped: scraped.map((j) => ({ ...j, datePosted: iso(j.postedMs), postedMs: undefined })),
  },
}];

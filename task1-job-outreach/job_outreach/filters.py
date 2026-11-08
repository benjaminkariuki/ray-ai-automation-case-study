"""Cheap rule-based filtering that runs before any AI call."""
from datetime import datetime, timedelta, timezone


def keyword_filter(jobs, config, seen_urls, now=None):
    """Keep jobs whose title matches the include keywords, not the exclude keywords or excluded companies,
    posted within max_posting_age_days, and not already processed. Returns (candidates, stats)."""
    now = now or datetime.now(timezone.utc)
    max_age = timedelta(days=config["max_posting_age_days"])
    unique, passed, already_seen = {}, 0, 0
    for job in jobs:
        url, title = job.get("url"), (job.get("title") or "").lower()
        company = (job.get("company") or "").lower()
        if not url or not title or url in unique:
            continue
        if not any(k in title for k in config["title_include_keywords"]):
            continue
        if any(k in title for k in config["title_exclude_keywords"]):
            continue
        if any(c in company for c in config["excluded_companies"]):
            continue
        if job.get("posted") and now - job["posted"] > max_age:
            continue
        passed += 1
        if url in seen_urls:
            already_seen += 1
            continue
        unique[url] = job
    ready = sorted(unique.values(), key=lambda j: j.get("posted") or datetime.min.replace(tzinfo=timezone.utc),
                   reverse=True)
    candidates = ready[: config["max_jobs_per_run"]]
    stats = {"fetched": len(jobs), "passed_keyword_filter": passed, "already_seen": already_seen,
             "sent_to_ai": len(candidates), "deferred_to_next_run": max(0, len(ready) - len(candidates))}
    return candidates, stats

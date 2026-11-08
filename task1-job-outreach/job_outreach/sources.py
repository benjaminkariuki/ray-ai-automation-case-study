"""Job sources: official public JSON APIs of Himalayas, RemoteOK and Jobicy (no HTML scraping, no LinkedIn).

Every fetcher returns a list of jobs in one common shape:
    {source, url, title, company, location, description, posted (datetime, UTC)}
"""
import html
import json
import re
import time
from datetime import datetime, timezone

import requests

USER_AGENT = "RAY-Job-Outreach/2.0 (+https://github.com/benjaminkariuki/ray-ai-automation-case-study)"


def html_to_text(raw):
    """Turn job-description HTML (sometimes double-escaped) into clean plain text."""
    text = html.unescape(html.unescape(str(raw or "")))
    text = re.sub(r"<\s*br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"<\s*li[^>]*>", "\n- ", text, flags=re.I)
    text = re.sub(r"</(p|div|h[1-6]|ul|ol|li)>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"[ \t ]+", " ", text)
    return re.sub(r"\n\s*\n\s*\n+", "\n\n", text).strip()


def _as_list(value):
    if isinstance(value, list):
        return value
    if isinstance(value, str) and value.startswith("["):
        try:
            return json.loads(value.replace("'", '"'))
        except ValueError:
            pass
    return [value] if value else []


def _from_epoch(value):
    try:
        return datetime.fromtimestamp(int(value), tz=timezone.utc)
    except (TypeError, ValueError):
        return None


def _from_iso(value):
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _get_json(url, params=None, retries=3):
    for attempt in range(retries):
        try:
            r = requests.get(url, params=params, headers={"User-Agent": USER_AGENT}, timeout=30)
            r.raise_for_status()
            return r.json()
        except (requests.RequestException, ValueError):
            if attempt == retries - 1:
                raise
            time.sleep(3 * (attempt + 1))


def fetch_himalayas(queries, pages):
    jobs = []
    for q in queries:
        for page in range(1, pages + 1):
            data = _get_json("https://himalayas.app/jobs/api/search", {"q": q, "page": page, "sort": "recent"})
            for j in data.get("jobs", []):
                locs = _as_list(j.get("locationRestrictions"))
                jobs.append({
                    "source": "Himalayas",
                    "url": j.get("guid") or j.get("applicationLink"),
                    "title": html.unescape(j.get("title") or ""),
                    "company": html.unescape(j.get("companyName") or ""),
                    "location": f"Remote ({', '.join(locs)})" if locs else "Remote (Worldwide)",
                    "description": html_to_text(j.get("description")),
                    "posted": _from_epoch(j.get("pubDate")),
                })
            time.sleep(1)
    return jobs


def fetch_remoteok():
    data = _get_json("https://remoteok.com/api", {"tag": "assistant"})
    jobs = []
    for j in data:
        if not isinstance(j, dict) or not j.get("position"):
            continue  # first element is the API's legal notice
        jobs.append({
            "source": "RemoteOK",
            "url": j.get("url"),
            "title": html.unescape(j.get("position") or ""),
            "company": html.unescape(j.get("company") or ""),
            "location": f"Remote ({j['location']})" if j.get("location") else "Remote",
            "description": html_to_text(j.get("description")),
            "posted": _from_epoch(j.get("epoch")),
        })
    return jobs


def fetch_jobicy():
    data = _get_json("https://jobicy.com/api/v2/remote-jobs", {"count": 100, "industry": "admin-support"})
    return [{
        "source": "Jobicy",
        "url": j.get("url"),
        "title": html.unescape(j.get("jobTitle") or ""),
        "company": html.unescape(j.get("companyName") or ""),
        "location": f"Remote ({j.get('jobGeo') or 'Worldwide'})",
        "description": html_to_text(j.get("jobDescription")),
        "posted": _from_iso(j.get("pubDate")),
    } for j in data.get("jobs", [])]


def fetch_all(config):
    """Fetch every source. A failing source is reported but never stops the others."""
    jobs, errors = [], []
    fetchers = [
        ("Himalayas", lambda: fetch_himalayas(config["search_queries"], config["himalayas_pages_per_query"])),
        ("RemoteOK", fetch_remoteok),
        ("Jobicy", fetch_jobicy),
    ]
    for name, fetch in fetchers:
        try:
            jobs.extend(fetch())
        except Exception as exc:  # noqa: BLE001 - one bad source must not stop the run
            errors.append(f"{name}: {exc}")
    return jobs, errors

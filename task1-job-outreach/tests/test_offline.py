"""Offline unit tests (no network, no credentials): run with  pytest -q"""
from datetime import datetime, timedelta, timezone

from job_outreach.ai import fill, format_message, parse_verdict, provider_of
from job_outreach.filters import keyword_filter
from job_outreach.sources import html_to_text

SENDER = {"sender_name": "Benjamin Kariuki", "sender_company": "RAY",
          "call_to_action": "Would a 15-minute call this week be useful to see if we are a fit?"}
CTA = SENDER["call_to_action"]
NOW = datetime(2026, 11, 9, tzinfo=timezone.utc)
CONFIG = {"title_include_keywords": ["executive assistant", "admin assistant"],
          "title_exclude_keywords": ["medical"], "excluded_companies": ["wing assistant"],
          "max_posting_age_days": 30, "max_jobs_per_run": 2}


def job(url, title, company="Acme", days_old=1):
    return {"url": url, "title": title, "company": company, "posted": NOW - timedelta(days=days_old)}


def test_html_to_text_handles_double_escaped_html():
    assert html_to_text("&lt;p&gt;Hello &amp;amp; welcome&lt;/p&gt;&lt;ul&gt;&lt;li&gt;One&lt;/li&gt;&lt;/ul&gt;") == \
        "Hello & welcome\n\n- One"


def test_keyword_filter_rules_and_dedupe():
    jobs = [job("1", "Executive Assistant"), job("2", "Medical Admin Assistant"),
            job("3", "Executive Assistant", company="Wing Assistant"), job("4", "Software Engineer"),
            job("5", "Admin Assistant", days_old=60), job("6", "Executive Assistant to CEO"),
            job("7", "Admin Assistant"), job("1", "Executive Assistant")]
    candidates, stats = keyword_filter(jobs, CONFIG, seen_urls={"6"}, now=NOW)
    assert [c["url"] for c in candidates] == ["1", "7"]  # 2 = excluded word, 3 = excluded company, 4 = no keyword,
    assert stats["already_seen"] == 1                      # 5 = too old, 6 = already processed, dup "1" ignored
    assert stats["passed_keyword_filter"] == 3


def test_keyword_filter_caps_jobs_per_run():
    jobs = [job(str(i), "Executive Assistant", days_old=i) for i in range(5)]
    candidates, stats = keyword_filter(jobs, CONFIG, set(), now=NOW)
    assert [c["url"] for c in candidates] == ["0", "1"] and stats["deferred_to_next_run"] == 3


def test_parse_verdict_complete_answer():
    v = parse_verdict('Sure: {"is_remote": true, "is_english": "true", "is_relevant": true, "is_agency": false, '
                      '"language_requirements": "English, Spanish", "reason": "Fully remote EA role."}')
    assert v == {"remote": True, "english": True, "relevant": True, "agency": False,
                 "languages": "English, Spanish", "reason": "Fully remote EA role."}


def test_parse_verdict_incomplete_answer_is_error_not_rejection():
    assert parse_verdict("analysis: need to evaluate criteria. remote? yes ...") is None
    assert parse_verdict('{"is_remote": true, "is_english": true}') is None
    assert parse_verdict('{"is_remote": true, "is_english": true, "is_relevant": true, "is_agency": false, '
                         '"reason": ""}') is None


def test_format_message_normalises_endings_from_any_model():
    raw_variants = [
        "Subject: X\n\nBody.\n- a\n- Ad hoc support. " + CTA + "\n\nBenjamin Kariuki\nRAY",
        "Subject: X\n\nBody.\n- a\n- Ad hoc support.\n\nBenjamin Kariuki\nRAY\n\n" + CTA,
        "Subject: X\n\nBody.\n- a\n- Ad hoc support.\n\n" + CTA.replace("-", "‑") + "\n\n" + CTA + "\nBenjamin Kariuki\nRAY",
        "**Subject: X**\n\nBody.\n- a\n- Ad hoc support.",
    ]
    for raw in raw_variants:
        msg = format_message(raw, SENDER)
        assert msg.endswith("\n\n" + CTA + "\n\nBenjamin Kariuki\nRAY"), msg
        assert msg.count(CTA) == 1 and msg.startswith("Subject: X")


def test_fill_and_provider():
    assert fill("Hi {{ company_name }} - {{unknown}}", {"company_name": "Acme"}) == "Hi Acme - {{unknown}}"
    assert provider_of("@cf/openai/gpt-oss-120b") == "Cloudflare"
    assert provider_of("nvidia/nemotron-3-ultra-550b-a55b:free") == "OpenRouter"

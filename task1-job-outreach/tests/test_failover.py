"""Offline tests of the AI failover logic (OpenRouter primary -> Cloudflare backup), with the HTTP calls stubbed."""
import pytest

from job_outreach import ai as ai_module
from job_outreach.ai import AIClient

GOOD_JSON = ('{"is_remote": true, "is_english": true, "is_relevant": true, "is_agency": false, '
             '"language_requirements": "English", "reason": "Remote EA role."}')
CONFIG = {"fallback_model": "google/gemma-4-31b-it:free", "backup_model": "@cf/openai/gpt-oss-120b",
          "validation_model": "nvidia/nemotron-3-ultra-550b-a55b:free", "outreach_model": "x",
          "validation_prompt": "Check {{job_title}}", "outreach_prompt_text": "Write",
          "sender": {"sender_name": "B", "sender_company": "RAY", "call_to_action": "Call?"}}
JOB = {"title": "EA", "company": "Acme", "location": "Remote", "description": "Remote EA role"}


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr(ai_module.time, "sleep", lambda s: None)


def client(openrouter, cloudflare):
    c = AIClient(CONFIG, openrouter_key="k", cf_account="a", cf_token="t")
    c._openrouter = openrouter
    c._cloudflare = cloudflare
    return c


def fail(*_a, **_k):
    raise RuntimeError("429 Too Many Requests")


def test_primary_used_when_openrouter_works():
    c = client(lambda *a: (GOOD_JSON, "nvidia/nemotron-3-ultra-550b-a55b:free"), fail)
    v = c.validate(JOB)
    assert v["model"].endswith("(OpenRouter)") and c.backup_calls == 0


def test_backup_used_when_openrouter_rate_limited():
    c = client(fail, lambda *a: (GOOD_JSON, "@cf/openai/gpt-oss-120b"))
    v = c.validate(JOB)
    assert v["model"] == "@cf/openai/gpt-oss-120b (Cloudflare)" and c.backup_calls == 1


def test_backup_used_when_openrouter_reply_is_unusable():
    c = client(lambda *a: ("analysis: thinking...", "nvidia/x"), lambda *a: (GOOD_JSON, "@cf/openai/gpt-oss-120b"))
    assert c.validate(JOB)["remote"] is True and c.backup_calls == 1


def test_error_raised_when_both_providers_fail():
    c = client(fail, fail)
    with pytest.raises(RuntimeError, match="OpenRouter.*Cloudflare"):
        c.validate(JOB)

"""Offline tests for the safeguards added after the first evaluation pass:
leaked model reasoning, bad drafts, and Settings edited by someone else."""
from job_outreach.ai import clean_text, message_problems, parse_verdict
from job_outreach.sheet import Sheet

GOOD = ("Subject: Support for your CEO's calendar\n\n" + "I noticed the role owns the CEO's calendar end to end. " * 6
        + "\n\nWould a 15-minute call this week be useful?\n\nBenjamin Kariuki\nRAY")


def test_leaked_reasoning_is_removed():
    raw = ("analysis: we need to craft email subject max 8 words... Let's produce.<|end|><|start|>assistantfinal:"
           + GOOD)
    assert clean_text(raw).startswith("Subject: Support for your CEO")
    assert "<|" not in clean_text(raw)


def test_bad_drafts_are_detected():
    assert message_problems(clean_text(GOOD)) == []
    assert "no subject line" in message_problems("analysis: need subject... " + "word " * 60)
    assert "repeated words" in message_problems("Subject: hi\n\n" + "ex " * 80)
    assert any("words" in p for p in message_problems("Subject: hi\n\nToo short."))
    assert "unfilled placeholder" in message_problems(GOOD.replace("Benjamin", "{{sender_name}}"))


def test_verdict_parsed_after_leaked_reasoning():
    raw = ('analysis: decide...<|end|><|start|>assistantfinal:{"is_remote": true, "is_english": true, '
           '"is_relevant": true, "is_agency": false, "reason": "Remote EA role."}')
    assert parse_verdict(raw)["remote"] is True


class FakeTab:
    def __init__(self, records):
        self.records = records

    def get_all_records(self):
        return self.records


class FakeBook:
    def __init__(self, tabs):
        self.tabs = tabs

    def worksheet(self, name):
        if name not in self.tabs:
            raise KeyError(name)
        return self.tabs[name]


def sheet_with(settings, prompts):
    sheet = Sheet.__new__(Sheet)  # skip Google login
    sheet.book = FakeBook({"Settings": FakeTab(settings), "Prompts": FakeTab(prompts)})
    return sheet


def test_broken_settings_fall_back_to_defaults_instead_of_stopping():
    settings = [{"Setting": "outreach_prompt", "Value": "does_not_exist"},
                {"Setting": "max_jobs_per_run", "Value": "lots"},
                {"Setting": "search_queries", "Value": ""}]
    config = sheet_with(settings, [{"Prompt Name": "v1_warm", "Prompt Text": "Write {{job_title}}"}]).load_config()
    assert config["outreach_prompt_name"] == "v1_warm"
    assert config["max_jobs_per_run"] == 15
    assert config["search_queries"]  # default searches
    assert "is_english" in config["validation_prompt"]  # missing row -> prompts/validation_prompt.md
    assert len(config["warnings"]) == 3


def test_deleted_tabs_still_give_a_working_config():
    sheet = Sheet.__new__(Sheet)
    sheet.book = FakeBook({})
    config = sheet.load_config()
    assert config["outreach_prompt_text"] and config["validation_prompt"]
    assert config["sender"]["sender_name"] == "Benjamin Kariuki"

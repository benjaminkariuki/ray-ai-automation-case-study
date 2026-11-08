"""Offline tests for the Trip Brief generator: pytest -q"""
from datetime import datetime, timezone

from planner.brief import build_brief, icon_for, needs_refresh, parse_itinerary


def plain(segments):
    return "".join(s["text"]["content"] for s in segments or [])


def rt(value):
    return {"type": "rich_text", "rich_text": [{"plain_text": value}]}


def page(**overrides):
    props = {
        "Trip": {"type": "title", "title": [{"plain_text": "London"}]},
        "Status": {"type": "status", "status": {"name": "Planned"}},
        "Travel Dates": {"type": "date", "date": {"start": "2026-11-08", "end": "2026-11-12"}},
        "Destination": rt("London, UK"), "Traveler": rt("Alex"), "Purpose": {"type": "select", "select": None},
        "Itinerary": rt("2026-11-09 11:00 | Meeting | Northzone | Priya\n2026-11-08 23:35 | Flight | KQ100 | PNR X\n"
                        "bad line\n2026-11-09 | Free | Rest day"),
        "Hotel Address": rt("199 High Holborn, London"), "Hotel Phone": {"type": "phone_number", "phone_number": None},
        "Documents": {"type": "files", "files": [{"name": "eticket.pdf"}]},
        "Rebuild Brief": {"type": "checkbox", "checkbox": False},
        "Brief Updated": {"type": "date", "date": None},
    }
    props.update(overrides)
    return {"id": "p1", "properties": props, "last_edited_time": "2026-11-09T10:00:00.000Z"}


def test_itinerary_is_sorted_and_bad_lines_are_kept():
    events, unparsed = parse_itinerary(page()["properties"]["Itinerary"]["rich_text"][0]["plain_text"])
    assert [e["kind"] for e in events] == ["Flight", "Free", "Meeting"]  # all-day before timed events that day
    assert unparsed == ["bad line"]


def test_brief_contains_timeline_contacts_documents_and_map_link():
    blocks = build_brief(page(), now=datetime(2026, 11, 9, tzinfo=timezone.utc))
    texts = [plain(b[b["type"]].get("rich_text")) for b in blocks if b["type"] != "divider"]
    joined = "\n".join(texts)
    assert "Sun 8 Nov 2026 → Thu 12 Nov 2026  (4 nights)" in joined
    assert texts.index("Sun 8 Nov 2026") < texts.index("Mon 9 Nov 2026")
    assert "Emergency contact" in joined and "📄 eticket.pdf" in joined and "bad line" in joined
    maps = [s for b in blocks if b["type"] == "bulleted_list_item" for s in b["bulleted_list_item"]["rich_text"]
            if s["text"].get("link")]
    assert maps and "google.com/maps" in maps[0]["text"]["link"]["url"]


def test_needs_refresh_rules():
    assert needs_refresh(page())  # never built
    built = {"type": "date", "date": {"start": "2026-11-09T09:59:30+00:00"}}
    assert not needs_refresh(page(**{"Brief Updated": built}))  # our own write, within tolerance
    old = {"type": "date", "date": {"start": "2026-11-09T09:00:00+00:00"}}
    assert needs_refresh(page(**{"Brief Updated": old}))  # edited after the last build
    assert needs_refresh(page(**{"Brief Updated": built, "Rebuild Brief": {"type": "checkbox", "checkbox": True}}))


def test_icons():
    assert icon_for("Flight") == "✈️" and icon_for("Dinner") == "🍽️" and icon_for("Something") == "📌"

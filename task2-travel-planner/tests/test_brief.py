"""Offline tests for the Trip Brief generator: pytest -q"""
from datetime import datetime, timezone

from planner.brief import build_brief, icon_for, needs_refresh, parse_itinerary
from planner.workspace import home_text


def plain(segments):
    return "".join(s.get("text", {}).get("content", "@link") for s in segments or [])


def rt(value):
    return {"type": "rich_text", "rich_text": [{"plain_text": value}]}


def page(pid="p1", **overrides):
    props = {
        "Trip": {"type": "title", "title": [{"plain_text": "London"}]},
        "Status": {"type": "status", "status": {"name": "Planned"}},
        "Travel Dates": {"type": "date", "date": {"start": "2026-11-08", "end": "2026-11-12"}},
        "Destination": rt("London, UK"), "Traveler": rt("Alex"), "Purpose": {"type": "select", "select": None},
        "Itinerary": rt("2026-11-09 11:00 | Meeting | Northzone | Priya\n2026-11-08 23:35 | Flight | KQ100 | PNR X\n"
                        "bad line\n2026-11-09 | Free | Rest day"),
        "Hotel": rt("The Hoxton"), "Hotel Address": rt("199 High Holborn, London"),
        "Hotel Phone": {"type": "phone_number", "phone_number": None},
        "Documents": {"type": "files", "files": [{"name": "eticket.pdf"}]},
        "Rebuild Brief": {"type": "checkbox", "checkbox": False},
        "Brief Updated": {"type": "date", "date": None},
    }
    props.update(overrides)
    return {"id": pid, "properties": props, "last_edited_time": "2026-11-09T10:00:00.000Z"}


def texts_of(blocks):
    return [plain(b[b["type"]].get("rich_text")) for b in blocks if b["type"] != "divider"]


NOW = datetime(2026, 11, 9, 12, tzinfo=timezone.utc)


def test_itinerary_is_sorted_and_bad_lines_are_kept():
    events, unparsed = parse_itinerary(page()["properties"]["Itinerary"]["rich_text"][0]["plain_text"])
    assert [e["kind"] for e in events] == ["Flight", "Free", "Meeting"]  # all-day before timed events that day
    assert unparsed == ["bad line"]


def test_brief_puts_essentials_first_and_keeps_every_detail():
    blocks = build_brief(page(), now=NOW)
    texts = texts_of(blocks)
    joined = "\n".join(texts)
    # first box: where, when, where I sleep (with a map link)
    assert "London, UK" in texts[0] and "Sun 8 Nov 2026 → Thu 12 Nov 2026  (4 nights)" in texts[0]
    assert "The Hoxton" in texts[0]
    links = [s["text"]["link"]["url"] for s in blocks[0]["callout"]["rich_text"] if s["text"].get("link")]
    assert links and "google.com/maps" in links[0]
    # contacts come before the day-by-day plan, which is sorted
    assert texts.index("📅 Day by day") > next(i for i, t in enumerate(texts) if "Emergency contact" in t)
    assert texts.index("Sun 8 Nov 2026") < texts.index("Mon 9 Nov 2026")
    assert "Documents: eticket.pdf" in joined and "bad line" in joined
    assert "Today," not in joined  # only while travelling


def test_today_box_and_visa_warning():
    blocks = build_brief(page(**{"Status": {"type": "status", "status": {"name": "In-Progress"}},
                                 "Visa / Entry": {"type": "select", "select": {"name": "Action needed"}},
                                 "Visa Notes": rt("Renew passport")}), now=NOW)
    texts = texts_of(blocks)
    assert texts[1].startswith("Visa / entry: Action needed") and "Renew passport" in texts[1]
    assert blocks[1]["callout"]["color"] == "red_background"
    assert texts[2].startswith("Today, Mon 9 Nov 2026") and "Northzone" in texts[2] and "KQ100" not in texts[2]


def test_needs_refresh_rules():
    assert needs_refresh(page(), now=NOW)  # never built
    built = {"type": "date", "date": {"start": "2026-11-09T09:59:30+00:00"}}
    assert not needs_refresh(page(**{"Brief Updated": built}), now=NOW)  # our own write, within tolerance
    old = {"type": "date", "date": {"start": "2026-11-09T09:00:00+00:00"}}
    assert needs_refresh(page(**{"Brief Updated": old}), now=NOW)  # edited after the last build
    assert needs_refresh(page(**{"Brief Updated": built, "Rebuild Brief": {"type": "checkbox", "checkbox": True}}),
                         now=NOW)
    travelling = {"Brief Updated": built, "Status": {"type": "status", "status": {"name": "In-Progress"}}}
    assert not needs_refresh(page(**travelling), now=NOW)  # same day
    assert needs_refresh(page(**travelling), now=datetime(2026, 11, 10, 6, tzinfo=timezone.utc))  # new day


def test_home_box_shows_current_and_next_trip():
    def trip(pid, status, start, end):
        return page(pid, **{"Status": {"type": "status", "status": {"name": status}},
                            "Travel Dates": {"type": "date", "date": {"start": start, "end": end}},
                            "Brief Link": {"type": "url", "url": f"https://x.notion.site/{pid}#brief"},
                            "Countdown": {"type": "formula", "formula": {"type": "string", "string": "5 days to go"}}})
    pages = [trip("done", "Done", "2026-10-01", "2026-10-03"), trip("later", "Planned", "2026-12-01", "2026-12-03"),
             trip("soon", "Planned", "2026-11-14", "2026-11-16"), trip("now", "In-Progress", "2026-11-08", "2026-11-12")]
    rich = home_text(pages, NOW)
    links = [r["text"]["link"]["url"] for r in rich if r["text"].get("link")]
    assert links == ["https://x.notion.site/now#brief", "https://x.notion.site/soon#brief"]  # straight to the brief
    assert "until Thu 12 Nov 2026" in plain(rich) and "Sat 14 Nov 2026" in plain(rich)
    assert plain(home_text([], NOW)) == "No upcoming trips."


def test_icons():
    assert icon_for("Flight") == "✈️" and icon_for("Dinner") == "🍽️" and icon_for("Something") == "📌"

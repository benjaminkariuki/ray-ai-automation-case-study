"""Builds the whole Notion workspace under one page: guide, Trips database, views and sample trips."""
from datetime import datetime, timezone

from .notion import text

STATUS_OPTIONS = [
    {"name": "Planned", "color": "blue", "group": "To-do"},
    {"name": "In-Progress", "color": "yellow", "group": "In progress"},
    {"name": "Done", "color": "green", "group": "Complete"},
]

ITINERARY_HELP = "One event per line:  YYYY-MM-DD HH:MM | Type | Details | Confirmation"

PROPERTIES = {
    "Trip": {"type": "title", "title": {}},
    "Status": {"type": "status", "status": {"options": STATUS_OPTIONS}},
    "Travel Dates": {"type": "date", "date": {}},
    "Traveler": {"type": "rich_text", "rich_text": {}},
    "Destination": {"type": "rich_text", "rich_text": {}},
    "Purpose": {"type": "select", "select": {"options": [
        {"name": "Investor meetings", "color": "purple"}, {"name": "Board meeting", "color": "red"},
        {"name": "Conference", "color": "orange"}, {"name": "Customer / partner", "color": "blue"},
        {"name": "Team offsite", "color": "green"}, {"name": "Personal", "color": "gray"}]}},
    "Countdown": {"type": "formula", "formula": {"expression":
        'if(empty(prop("Travel Dates")), "Dates TBC", '
        'if(prop("Status") == "Done", "✓ Completed", '
        'if(dateBetween(dateStart(prop("Travel Dates")), today(), "days") > 0, '
        'format(dateBetween(dateStart(prop("Travel Dates")), today(), "days")) + " days to go", '
        'if(dateBetween(dateEnd(prop("Travel Dates")), today(), "days") >= 0, "✈️ Travelling now", "Trip ended"))))'}},
    "Visa / Entry": {"type": "select", "select": {"options": [
        {"name": "Not required", "color": "green"}, {"name": "eVisa / ETA approved", "color": "green"},
        {"name": "Visa approved", "color": "green"}, {"name": "Pending", "color": "yellow"},
        {"name": "Action needed", "color": "red"}]}},
    "Itinerary": {"type": "rich_text", "rich_text": {}},
    "Flights": {"type": "rich_text", "rich_text": {}},
    "Hotel": {"type": "rich_text", "rich_text": {}},
    "Hotel Address": {"type": "rich_text", "rich_text": {}},
    "Hotel Phone": {"type": "phone_number", "phone_number": {}},
    "Hotel Confirmation": {"type": "rich_text", "rich_text": {}},
    "Ground Transport": {"type": "rich_text", "rich_text": {}},
    "Visa Notes": {"type": "rich_text", "rich_text": {}},
    "Documents": {"type": "files", "files": {}},
    "Primary Contact": {"type": "rich_text", "rich_text": {}},
    "Emergency Contact": {"type": "rich_text", "rich_text": {}},
    "Notes": {"type": "rich_text", "rich_text": {}},
    "Rebuild Brief": {"type": "checkbox", "checkbox": {}},
    "Brief Updated": {"type": "date", "date": {}},
}

HOME_ICON = "📍"  # marks the auto-updated "Travelling now / Next trip" box on the main page

# Which fields each view shows: only what is needed to pick a trip. Everything else is in the brief.
VIEW_FIELDS = {
    "Upcoming trips": ["Travel Dates", "Countdown"],
    "Calendar": [],
    "Timeline": ["Countdown"],
    "By status": ["Travel Dates", "Countdown"],
    "All trips": ["Status", "Travel Dates", "Countdown", "Destination", "Traveler", "Purpose", "Visa / Entry"],
}


def guide_blocks():
    """Top of the planner page: one line on how to use it, then the auto-updated 'now / next' box."""
    return [
        {"type": "callout", "callout": {"icon": {"type": "emoji", "emoji": "🧳"}, "color": "blue_background",
         "rich_text": text("Tap any trip to open its Trip Brief: ", bold=True) + text(
             "where and when, who to call, and the plan for each day.")}},
        {"type": "callout", "callout": {"icon": {"type": "emoji", "emoji": HOME_ICON}, "color": "yellow_background",
         "rich_text": text("Your next trip appears here automatically.")}},
    ]


def home_text(pages, now):
    """Rich text for the 'now / next' box: the trip in progress (if any) and the next planned trip."""
    from .brief import fmt_day, prop

    def start(pg):
        return ((prop(pg, "Travel Dates") or {}).get("start") or "")[:10]

    def link(pg):
        return [{"type": "mention", "mention": {"type": "page", "page": {"id": pg["id"]}}}]

    today = now.date().isoformat()
    current = sorted((pg for pg in pages if prop(pg, "Status") == "In-Progress"), key=start)
    upcoming = sorted((pg for pg in pages if prop(pg, "Status") == "Planned" and start(pg) >= today), key=start)
    out = []
    for pg in current[:1]:
        end = ((prop(pg, "Travel Dates") or {}).get("end") or start(pg))[:10]
        out += text("Travelling now: ", bold=True) + link(pg) + text(
            f"  ·  until {fmt_day(datetime.fromisoformat(end))}\n")
    for pg in upcoming[:1]:
        out += text("Next trip: ", bold=True) + link(pg) + text(
            f"  ·  {fmt_day(datetime.fromisoformat(start(pg)))}  ·  {prop(pg, 'Countdown')}")
    return out or text("No upcoming trips.")


def _signature(rich):
    return [((r.get("mention") or {}).get("page", {}).get("id", "").replace("-", ""),
             (r.get("text") or {}).get("content", "")) for r in rich]


def update_home(notion, database_id, pages, now=None):
    """Refresh the 'now / next' box on the main page (only writes when it changed)."""
    now = now or datetime.now(timezone.utc)
    page_id = notion.call("GET", f"/databases/{database_id}")["parent"].get("page_id")
    box = next((b for b in notion.children(page_id) if b["type"] == "callout"
                and (b["callout"].get("icon") or {}).get("emoji") == HOME_ICON), None)
    if not box:
        return False
    new = home_text(pages, now)
    if _signature(box["callout"]["rich_text"]) == _signature(new):
        return False
    notion.call("PATCH", f"/blocks/{box['id']}", {"callout": {"rich_text": new}})
    return True


def create_views(notion, database_id, data_source_id):
    """Create the views in the order they are needed (the first one opens by default)."""
    ds = notion.call("GET", f"/data_sources/{data_source_id}")
    pid = {name: p["id"] for name, p in ds["properties"].items()}

    def fields(name):
        shown = VIEW_FIELDS[name]
        return [{"property_id": pid[n], "visible": True} for n in shown] + \
               [{"property_id": i, "visible": False} for n, i in pid.items() if n not in shown and n != "Trip"]

    def view(name, vtype, configuration, **extra):
        return notion.call("POST", "/views", {"data_source_id": data_source_id, "database_id": database_id,
                                              "name": name, "type": vtype, "configuration": {
                                                  "type": vtype, "properties": fields(name), **configuration},
                                              **extra})
    not_done = {"property": "Status", "status": {"does_not_equal": "Done"}}
    by_date = [{"property": "Travel Dates", "direction": "ascending"}]
    return [
        view("Upcoming trips", "table", {"wrap_cells": False}, filter=not_done, sorts=by_date),
        view("Calendar", "calendar", {"date_property_id": pid["Travel Dates"], "view_range": "month"}),
        view("Timeline", "timeline", {"date_property_id": pid["Travel Dates"], "show_table": False},
             filter=not_done, sorts=by_date),
        view("By status", "board",
             {"group_by": {"type": "status", "property_id": pid["Status"], "group_by": "option",
                           "sort": {"type": "manual"}, "hide_empty_groups": False}}, sorts=by_date),
        view("All trips", "table", {"wrap_cells": False},
             sorts=[{"property": "Travel Dates", "direction": "descending"}]),
    ]


def create_workspace(notion, page_id):
    """Create guide + inline Trips database + views under the given page. Returns ids."""
    notion.append(page_id, guide_blocks())
    db = notion.call("POST", "/databases", {
        "parent": {"type": "page_id", "page_id": page_id},
        "title": text("Trips"),
        "is_inline": True,
        "initial_data_source": {"properties": PROPERTIES},
    })
    data_source_id = db["data_sources"][0]["id"]
    default_views = notion.call("GET", "/views", params={"database_id": db["id"]}).get("results", [])
    views = create_views(notion, db["id"], data_source_id)
    for v in default_views:  # remove the blank default table view Notion creates
        notion.call("DELETE", f"/views/{v['id']}")
    return {"database_id": db["id"], "data_source_id": data_source_id, "views": [v["id"] for v in views]}

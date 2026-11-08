"""Builds the whole Notion workspace under one page: guide, Trips database, views and sample trips."""
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

def guide_blocks():
    """Short guide at the top of the planner page (who does what)."""
    def b(*segs):
        return {"type": "bulleted_list_item", "bulleted_list_item": {"rich_text": [s for seg in segs for s in seg]}}
    return [
        {"type": "callout", "callout": {"icon": {"type": "emoji", "emoji": "🧳"}, "color": "blue_background",
         "rich_text": text("One place for every trip. ", bold=True) + text(
             "Open any trip to see its Trip Brief — a day-by-day timeline, hotel, transport, visa status, "
             "documents and emergency contacts, readable on a phone.")}},
        {"type": "heading_3", "heading_3": {"rich_text": text("For the Executive Assistant")}},
        b(text("Add a trip: ", bold=True), text("click New in the trips table, fill in the fields "
          "(dates, traveler, flights, hotel, contacts) and attach tickets/visas in Documents.")),
        b(text("Itinerary: ", bold=True), text(ITINERARY_HELP + "  — e.g. 2026-11-20 21:30 | Flight | "
          "BA178 New York (JFK) → London (LHR) | PNR ABC123")),
        b(text("Trip Brief: ", bold=True), text("built automatically inside the trip page within ~15 minutes of any "
          "change. Tick “Rebuild Brief” to force a refresh. Notes below “📂 Extra files & notes” are never overwritten.")),
        b(text("Status: ", bold=True), text("Planned → In-Progress → Done (drag cards on the Board view).")),
        {"type": "heading_3", "heading_3": {"rich_text": text("For the founder")}},
        b(text("Upcoming trips are on the Timeline and Calendar views. Tap a trip to open its brief — the red box "
               "at the top has who to call.")),
        {"type": "divider", "divider": {}},
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
    ds = notion.call("GET", f"/data_sources/{data_source_id}")
    pid = {name: p["id"] for name, p in ds["properties"].items()}
    default_views = notion.call("GET", "/views", params={"database_id": db["id"]}).get("results", [])

    def view(name, vtype, configuration, **extra):
        return notion.call("POST", "/views", {"data_source_id": data_source_id, "database_id": db["id"],
                                              "name": name, "type": vtype,
                                              "configuration": {"type": vtype, **configuration}, **extra})

    views = [
        view("Upcoming – Timeline", "timeline",
             {"date_property_id": pid["Travel Dates"], "show_table": True},
             filter={"property": "Status", "status": {"does_not_equal": "Done"}},
             sorts=[{"property": "Travel Dates", "direction": "ascending"}]),
        view("By status", "board",
             {"group_by": {"type": "status", "property_id": pid["Status"], "group_by": "option",
                           "sort": {"type": "manual"}, "hide_empty_groups": False}}),
        view("Calendar", "calendar", {"date_property_id": pid["Travel Dates"], "view_range": "month"}),
        view("All trips", "table", {"wrap_cells": False},
             sorts=[{"property": "Travel Dates", "direction": "descending"}]),
    ]
    for v in default_views:  # remove the blank default table view Notion creates
        notion.call("DELETE", f"/views/{v['id']}")
    notion.append(page_id, [
        {"type": "toggle", "toggle": {"rich_text": text("How the Trip Brief is generated"), "children": [
            {"type": "paragraph", "paragraph": {"rich_text": text(
                "A small script (GitHub Actions, every 15 minutes) reads each trip and rewrites its "
                "“✈️ Trip Brief” section from the fields above: a summary, emergency contacts, the itinerary sorted "
                "by date and time, hotel with a map link, transport, visa status and documents. "
                "Source: github.com/benjaminkariuki/ray-ai-automation-case-study (task2-travel-planner).")}}]}}])
    return {"database_id": db["id"], "data_source_id": data_source_id, "views": [v["id"] for v in views]}

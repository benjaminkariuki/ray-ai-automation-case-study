"""Turns a trip's properties into a founder-ready Trip Brief (Notion blocks), and keeps it up to date.

The brief lives inside each trip page between the "✈️ Trip Brief" heading and the
"📂 Extra files & notes" heading. Only that section is rewritten; anything the EA adds below
"📂 Extra files & notes" is never touched.
"""
import re
import urllib.parse
from datetime import datetime, timedelta, timezone

from .notion import plain, text

BRIEF_HEADING = "✈️ Trip Brief"
KEPT_HEADING = "📂 Extra files & notes"
ICONS = {"flight": "✈️", "hotel": "🏨", "check-in": "🏨", "check-out": "🏨", "meeting": "🤝", "transfer": "🚗",
         "car": "🚗", "train": "🚆", "dinner": "🍽️", "lunch": "🍽️", "breakfast": "🍽️", "event": "🎤",
         "talk": "🎤", "keynote": "🎤", "call": "📞", "free": "🌴", "visa": "🛂"}
LINE = re.compile(r"^\s*(\d{4}-\d{2}-\d{2})(?:[ T](\d{1,2}:\d{2}))?\s*\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*(?:\|\s*(.*?)\s*)?$")


# ---------- reading properties ----------------------------------------------------------------
def prop(page, name):
    p = page["properties"].get(name)
    if not p:
        return ""
    t = p["type"]
    if t in ("title", "rich_text"):
        return plain(p[t]).strip()
    if t in ("select", "status"):
        return (p[t] or {}).get("name", "")
    if t == "date":
        return p["date"] or {}
    if t == "phone_number":
        return p["phone_number"] or ""
    if t == "files":
        return [(f.get("name") or "file") for f in p["files"]]
    if t == "checkbox":
        return p["checkbox"]
    if t == "formula":
        f = p["formula"]
        return f.get(f.get("type"), "") or ""
    return ""


def parse_itinerary(raw):
    """'2026-11-09 08:15 | Flight | KQ100 NBO → LHR | Conf ABC123' per line -> sorted events.
    Lines that don't match the format are returned separately so nothing is silently lost."""
    events, unparsed = [], []
    for line in str(raw or "").splitlines():
        if not line.strip():
            continue
        m = LINE.match(line)
        if not m:
            unparsed.append(line.strip())
            continue
        day, clock, kind, details, conf = m.groups()
        try:
            when = datetime.strptime(f"{day} {clock or '00:00'}", "%Y-%m-%d %H:%M")
        except ValueError:
            unparsed.append(line.strip())
            continue
        events.append({"when": when, "has_time": bool(clock), "kind": kind.strip(), "details": details.strip(),
                       "confirmation": (conf or "").strip()})
    return sorted(events, key=lambda e: (e["when"], not e["has_time"])), unparsed


def icon_for(kind):
    k = kind.lower()
    return next((v for key, v in ICONS.items() if key in k), "📌")


def fmt_day(d):
    return d.strftime("%a %d %b %Y").replace(" 0", " ")


# ---------- building blocks -------------------------------------------------------------------
def heading(level, content):
    return {"type": f"heading_{level}", f"heading_{level}": {"rich_text": text(content)}}


def para(segments):
    return {"type": "paragraph", "paragraph": {"rich_text": segments}}


def bullet(segments):
    return {"type": "bulleted_list_item", "bulleted_list_item": {"rich_text": segments}}


def callout(emoji, color, segments):
    return {"type": "callout", "callout": {"icon": {"type": "emoji", "emoji": emoji}, "color": color,
                                           "rich_text": segments}}


def labelled(label, value, link=None):
    return text(f"{label}: ", bold=True) + text(value or "—", link=link)


def build_brief(page, now=None):
    """Return the list of blocks that make up the brief for one trip page."""
    now = now or datetime.now(timezone.utc)
    dates = prop(page, "Travel Dates") or {}
    start, end = dates.get("start"), dates.get("end")
    date_txt = "Dates not set"
    if start:
        s = datetime.fromisoformat(start[:10])
        e = datetime.fromisoformat((end or start)[:10])
        nights = (e - s).days
        date_txt = f"{fmt_day(s)} → {fmt_day(e)}" + (f"  ({nights} night{'s' if nights != 1 else ''})" if nights else "")
    events, unparsed = parse_itinerary(prop(page, "Itinerary"))
    status = prop(page, "Status") or "Planned"
    status_color = {"Planned": "blue_background", "In-Progress": "yellow_background", "Done": "green_background"}

    blocks = [
        callout("🧭", status_color.get(status, "gray_background"),
                text(f"{prop(page, 'Destination') or 'Destination TBC'}\n", bold=True)
                + text(f"{date_txt}\n")
                + text(f"Traveler: {prop(page, 'Traveler') or '—'}   ·   Purpose: {prop(page, 'Purpose') or '—'}\n")
                + text(f"Status: {status}   ·   Visa / entry: {prop(page, 'Visa / Entry') or '—'}")),
    ]

    # Contacts first: what the founder needs in a hurry
    contacts = [labelled("Primary contact", prop(page, "Primary Contact")),
                labelled("Emergency contact", prop(page, "Emergency Contact"))]
    if prop(page, "Hotel Phone"):
        contacts.append(labelled("Hotel", f"{prop(page, 'Hotel')} · {prop(page, 'Hotel Phone')}"))
    blocks.append(callout("🆘", "red_background", sum(([*c, *text("\n")] for c in contacts[:-1]), []) + contacts[-1]))

    # Chronological timeline, grouped by day
    blocks.append(heading(2, "📅 Timeline"))
    if not events:
        blocks.append(para(text("No itinerary yet — add lines to the Itinerary property, e.g. "
                                "2026-11-20 08:15 | Flight | KQ100 Nairobi → London | Conf ABC123", color="gray")))
    current_day = None
    for ev in events:
        if ev["when"].date() != current_day:
            current_day = ev["when"].date()
            blocks.append(heading(3, fmt_day(ev["when"])))
        seg = text(f"{ev['when'].strftime('%H:%M') if ev['has_time'] else 'All day'}  ", bold=True)
        seg += text(f"{icon_for(ev['kind'])} {ev['kind']} — {ev['details']}")
        if ev["confirmation"]:
            seg += text(f"  ·  {ev['confirmation']}", color="gray")
        blocks.append(bullet(seg))
    if unparsed:
        blocks.append(callout("⚠️", "yellow_background",
                              text("Itinerary lines not in the expected format (shown as written):\n" + "\n".join(unparsed))))

    # Stay & logistics
    blocks.append(heading(2, "🏨 Stay & getting around"))
    address = prop(page, "Hotel Address")
    maps = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(address)}" if address else None
    blocks += [bullet(labelled("Hotel", prop(page, "Hotel"))),
               bullet(labelled("Address", address, link=maps)),
               bullet(labelled("Booking", prop(page, "Hotel Confirmation"))),
               bullet(labelled("Flights", prop(page, "Flights"))),
               bullet(labelled("Ground transport", prop(page, "Ground Transport")))]

    blocks.append(heading(2, "🛂 Visa & entry"))
    blocks.append(bullet(labelled(prop(page, "Visa / Entry") or "Status", prop(page, "Visa Notes"))))

    blocks.append(heading(2, "📎 Documents"))
    files = prop(page, "Documents") or []
    if files:
        blocks += [bullet(text(f"📄 {name}")) for name in files]
        blocks.append(para(text("Open them from the Documents field at the top of this page.", color="gray")))
    else:
        blocks.append(para(text("No documents attached yet — add tickets and visas in the Documents field at the top.",
                                color="gray")))

    if prop(page, "Notes"):
        blocks.append(heading(2, "📝 Notes"))
        blocks.append(para(text(prop(page, "Notes"))))

    blocks.append(para(text(f"Brief generated automatically {now.strftime('%d %b %Y, %H:%M')} UTC from the trip details.",
                            color="gray")))
    blocks.append({"type": "divider", "divider": {}})
    return blocks


# ---------- writing / refreshing --------------------------------------------------------------
def _heading_text(block):
    t = block["type"]
    return plain(block[t].get("rich_text")) if t.startswith("heading_") else None


def write_brief(notion, page, now=None):
    """Replace the brief section of a trip page (creating the section the first time)."""
    page_id = page["id"]
    existing = notion.children(page_id)
    anchor = next((b for b in existing if _heading_text(b) == BRIEF_HEADING), None)
    kept = next((b for b in existing if _heading_text(b) == KEPT_HEADING), None)
    blocks = build_brief(page, now)
    if anchor is None:
        notion.append(page_id, [heading(1, BRIEF_HEADING)] + blocks + [
            heading(2, KEPT_HEADING),
            para(text("Drop extra files or notes here — this section is never overwritten.", color="gray"))])
    else:
        start = existing.index(anchor) + 1
        stop = existing.index(kept) if kept in existing else len(existing)
        for old in existing[start:stop]:
            notion.call("DELETE", f"/blocks/{old['id']}")
        notion.append(page_id, blocks, after=anchor["id"])
    notion.call("PATCH", f"/pages/{page_id}", {"properties": {
        "Brief Updated": {"date": {"start": (now or datetime.now(timezone.utc)).isoformat()}},
        "Rebuild Brief": {"checkbox": False}}})


def needs_refresh(page):
    """A brief is rebuilt when: never built, 'Rebuild Brief' ticked, or the trip was edited after the last build."""
    if prop(page, "Rebuild Brief"):
        return True
    updated = (prop(page, "Brief Updated") or {}).get("start")
    if not updated:
        return True
    edited = datetime.fromisoformat(page["last_edited_time"].replace("Z", "+00:00"))
    built = datetime.fromisoformat(updated.replace("Z", "+00:00"))
    if built.tzinfo is None:
        built = built.replace(tzinfo=timezone.utc)
    return edited > built + timedelta(minutes=2)  # our own write also bumps last_edited_time

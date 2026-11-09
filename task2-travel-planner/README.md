# Task 2 – Executive Travel Planner (Notion)

[![Task 2 - Trip Briefs](https://github.com/benjaminkariuki/ray-ai-automation-case-study/actions/workflows/trip-briefs.yml/badge.svg)](https://github.com/benjaminkariuki/ray-ai-automation-case-study/actions/workflows/trip-briefs.yml)

A Notion workspace where an Executive Assistant logs every trip in **one database**. It's populated with **23 sample trips to Europe and the USA** for a New York-based founder. Each trip gets an **automatically generated Trip Brief**: a mobile-friendly summary the founder can use before and during travel.

| | |
|---|---|
| **Notion workspace (public link)** | https://billowy-target-f39.notion.site/Executive-Travel-Planner-Benjamin-Kariuki-412d73ee564d807d82e8f40be8b6009c |
| **Builder + brief generator (Python)** | [planner/](planner/) |
| **Brief refresh schedule** | [.github/workflows/trip-briefs.yml](../.github/workflows/trip-briefs.yml) (every 15 minutes) |

---

## 1. For evaluators: what to look at

**Check it in 3 minutes:** open the Notion link. The yellow box at the top shows the trip in progress (*London — Investor Roadshow*) and the next trip. Tap London to open its brief, then go back and try each view tab.

| # | Requirement | Where |
|---|---|---|
| 1 | **Single Trips database** | The **Trips** database on the main page: one record per trip |
| 2 | Trip name, who is traveling, date range | The **Trip**, **Traveler** and **Travel Dates** fields |
| 3 | Flights, hotels, addresses, confirmations, meetings, notes | **Flights**, **Hotel**, **Hotel Address**, **Hotel Phone**, **Hotel Confirmation**, **Ground Transport**, **Itinerary** (meetings and every timed event) and **Notes** |
| 4 | **Trip Brief**, auto-generated per trip | Open any trip (e.g. *London — Investor Roadshow*, In-Progress this week) and read the **✈️ Trip Brief** |
| 5 | Chronological timeline of key events | Brief → **📅 Day by day**: grouped by day and sorted by time. While a trip is in progress, a **Today** box at the top shows the current day |
| 6 | Space to attach documents (tickets, visas) | The **Documents** field (file uploads), listed in the brief, plus the **📂 Extra files & notes** area that's never overwritten |
| 7 | Emergency and primary contact info | The red **🆘** box near the top of every brief |
| 8 | Timeline/calendar view of upcoming trips | **Upcoming trips** (the default), **Calendar** and **Timeline** |
| 9 | Overview grouped by status (Planned / In-Progress / Done) | The **By status** board view |
| 10 | Shareable, mobile-friendly, founder-ready | Published to the web. Briefs use headings, bullets and coloured boxes only (no wide tables), so they read well on a phone |

---

## 2. Design

### The rule: zero learning curve for the founder
The founder opens one link and finds what they need in one or two taps, without reading instructions or scrolling through data meant for the assistant.

1. **Two taps to anything.** The page starts with one line ("Tap any trip to open its Trip Brief") and a box that always shows **Travelling now** and **Next trip**. Every trip link (in that box and the **Brief** column, "Open the Trip Brief ↓") opens the trip **scrolled straight to its brief**, skipping the assistant's raw fields. The box updates itself.
2. **The brief answers questions in the order a traveller asks them.** Where am I going, when, and where do I sleep (with a Google Maps link)? Is there anything I must do? (A visa problem shows in red.) What's on today? (Only while travelling.) Who do I call? Then the plan for each day. The remaining details (flights, transport, booking numbers, documents) are in one short list at the end.
3. **Only what's needed is shown.** The default view, **Upcoming trips**, is a simple table: trip, an *Open the Trip Brief* link, dates and countdown, soonest first. The other views show just as little. The raw fields the assistant types into stay on the trip page (that's where the assistant edits them), but the founder's links jump past them to the brief.
4. **Always current, with no effort.** The assistant only fills in fields. The brief is rewritten automatically whenever the trip changes, and once a day during a trip so that **Today** stays current.
5. **Made for a phone.** Headings, bullets and coloured boxes only, with no wide tables.

The assistant's instructions are in this README (section 3) rather than on the page, so the founder never sees them.

### One database, every detail
| Field | Type | Purpose |
|---|---|---|
| Trip | Title | e.g. "London — Investor Roadshow" |
| Status | Status | **Planned → In-Progress → Done** (drives the board) |
| Travel Dates | Date range | Drives the timeline and calendar |
| Traveler, Destination | Text | Who goes where |
| Purpose | Select | Investor meetings, Board meeting, Conference, … |
| Countdown | Formula | "15 days to go", "✈️ Travelling now" or "✓ Completed" |
| Visa / Entry | Select | Not required / eVisa approved / Visa approved / **Pending** / **Action needed** |
| **Itinerary** | Text | One event per line: `YYYY-MM-DD HH:MM \| Type \| Details \| Confirmation` |
| Flights, Hotel, Hotel Address, Hotel Phone, Hotel Confirmation, Ground Transport | Text / phone | Logistics |
| Visa Notes, Notes | Text | Details |
| **Documents** | Files | Tickets, boarding passes, visas |
| Primary Contact, Emergency Contact | Text | Who to call |
| Rebuild Brief, Brief Updated, Brief Link, Brief | Checkbox / date / URL / formula | Brief automation (see below). **Brief** shows "Open the Trip Brief ↓", a link that opens the trip scrolled straight to its brief |

### The Trip Brief, generated automatically
Every 15 minutes, a GitHub Action runs `python -m planner briefs`. It rebuilds the brief of any trip that is **new**, was **edited** since its last brief, has **Rebuild Brief** ticked, or is **In-Progress** and was last built on an earlier day. The same run updates the **Travelling now / Next trip** box on the main page. Each brief contains, in this order:
1. **At a glance:** destination, dates and nights, hotel with a **Google Maps link**, traveler, purpose and status. The box is coloured by status.
2. **Action needed** (only when the visa is *Pending* or *Action needed*): a yellow or red box with the visa notes.
3. **Today** (only while the trip is in progress): today's events.
4. **🆘 Contacts:** primary contact, emergency contact and hotel phone.
5. **📅 Day by day:** every itinerary line, sorted by date and time and grouped by day, with icons (✈️ 🚗 🏨 🤝 🍽️ 🎤) and confirmation numbers. Lines in the wrong format are shown in a ⚠️ box, so nothing is silently lost.
6. **🧳 Travel details:** flights, ground transport, hotel booking, visa / entry, documents and notes.

Only the brief section is rewritten. Anything below **📂 Extra files & notes** is never touched.

Why generate it rather than use a Notion template? A Notion page can't display its own properties as a formatted, sorted timeline, and templates are only filled once, when the page is created. Generating the brief keeps it **always in sync** with the trip's fields. The EA only maintains the fields.

### Views
Each view shows only the fields needed to pick a trip; everything else is in the brief.

| View | Type | Shows |
|---|---|---|
| Upcoming trips (default) | Table | Planned and In-Progress trips, soonest first: trip, *Open the Trip Brief* link, dates, countdown |
| Calendar | Calendar (month) | Trips across their date range |
| Timeline | Timeline | Planned and In-Progress trips on a timeline |
| By status | Board | Columns for Planned / In-Progress / Done; drag cards to change status |
| All trips | Table | Every trip with status, dates, countdown, city, traveler, purpose and visa status |

---

## 3. For the Executive Assistant

1. In **Trips**, click **New** and fill in the fields. Attach tickets and visas in **Documents**.
2. Write the itinerary one line per event:
   ```
   2026-11-20 21:30 | Flight | BA178 New York (JFK) → London (LHR) | PNR ABC123
   2026-11-20 16:00 | Meeting | Investor meeting, 20 Air St | Contact: Priya
   2026-11-21 | Free | Rest day
   ```
   Type words such as *Flight, Transfer, Hotel, Meeting, Lunch, Dinner, Keynote, Call* get matching icons.
3. The **Trip Brief appears inside the trip within about 15 minutes**. Tick **Rebuild Brief** to force a refresh.
4. Move the trip through **Planned → In-Progress → Done** on the board.

## 4. For the founder
Open the link on any device. Tap the trip in the yellow box at the top, or **Open the Trip Brief** next to any trip in the list. Its brief opens with where you're going and where you sleep, then today's plan, who to call and each day.

---

## 5. Setup (to rebuild this in another Notion workspace)
1. Create an internal integration at https://www.notion.so/profile/integrations with Read, Update and Insert capabilities, and copy the secret.
2. Create an empty page, then use **••• → Connections** to add the integration.
3. Run:
   ```bash
   cd task2-travel-planner
   pip install -r requirements.txt
   cp .env.example .env          # set NOTION_TOKEN and NOTION_PAGE_URL
   python -m planner build --with-samples
   ```
   This creates the page header, the Trips database, the 5 views, the 23 sample trips (Europe and USA) and their briefs, and saves the ids to `workspace.json`. Add `--reset` to rebuild the page from scratch.
4. **Share → Publish → Publish to web** in Notion. This is the one step the API can't do.
5. Optional, for automatic briefs: add the GitHub secret `NOTION_TOKEN` and the variable `NOTION_DATA_SOURCE_ID`. The schedule is in `.github/workflows/trip-briefs.yml`. To refresh by hand, run `python -m planner briefs` (or add `--all`).

Tests: `python -m pytest -q tests` covers itinerary parsing and sorting, the brief order and contents, the Today and visa boxes, the refresh rules, the Travelling now / Next trip box and the icons.

## 6. Test results
| Test | Result |
|---|---|
| Offline unit tests | ✅ 6/6 |
| Build via the API: database, status groups, formula, 5 views, 23 trips, 23 complete briefs (each checked for timeline, 🆘 contacts, travel details, visa, documents) | ✅ |
| Founder-first update (9 Nov), applied in place: same page and database, views recreated with minimal fields, all 23 briefs rebuilt, Travelling now / Next trip box live | ✅ |
| Sample itineraries: every event falls between arrival and the flight home (0 conflicts in 23 trips) | ✅ |
| Only Europe and USA destinations; statuses: 7 Done, 1 In-Progress, 15 Planned | ✅ |
| Countdown formula: "15 days to go", "✈️ Travelling now", "✓ Completed" | ✅ |
| Timeline sorted by date and time and grouped by day; bad lines kept in a ⚠️ box | ✅ |
| Nothing changed → 0 briefs rebuilt; one trip edited → only that brief rebuilt | ✅ |
| An EA note under "📂 Extra files & notes" survives a rebuild | ✅ |
| GitHub Actions run of the refresher | ✅ |

### Sample data
23 trips (September 2026 – April 2027): 7 Done, 1 In-Progress (London, this week) and 15 Planned. Hotels and addresses are real; people, partner companies, booking numbers and `555` phone numbers are fictional. The attached PDFs are watermarked **SAMPLE**. The EA contact on every trip is Benjamin Kariuki (benjaminleyian50@gmail.com).

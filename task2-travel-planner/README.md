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

| # | Requirement | Where |
|---|---|---|
| 1 | **Single Trips database** | The **Trips** table on the main page: one record per trip |
| 2 | Trip name, who is traveling, date range | The **Trip**, **Traveler** and **Travel Dates** fields |
| 3 | Flights, hotels, addresses, confirmations, meetings, notes | **Flights**, **Hotel**, **Hotel Address**, **Hotel Phone**, **Hotel Confirmation**, **Ground Transport**, **Itinerary** (meetings and every timed event) and **Notes** |
| 4 | **Trip Brief**, auto-generated per trip | Open any trip (e.g. *London — Investor Roadshow*, In-Progress this week) and read the **✈️ Trip Brief** section |
| 5 | Chronological timeline of key events | Brief → **📅 Timeline**: grouped by day and sorted by time, with an icon for each event type |
| 6 | Space to attach documents (tickets, visas) | The **Documents** field (file uploads), listed in the brief under **📎 Documents**, plus the **📂 Extra files & notes** area that's never overwritten |
| 7 | Emergency and primary contact info | The red **🆘** box near the top of every brief |
| 8 | Timeline/calendar view of upcoming trips | The **Upcoming – Timeline** view (hides Done trips) and the **Calendar** view |
| 9 | Overview grouped by status (Planned / In-Progress / Done) | The **By status** board view |
| 10 | Shareable, mobile-friendly, founder-ready | The page is published to the web. Briefs use headings, bullets and callouts only (no wide tables), so they read well on a phone |

---

## 2. Design

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
| Rebuild Brief, Brief Updated | Checkbox / date | Brief automation (see below) |

### The Trip Brief, generated automatically
Every 15 minutes, a GitHub Action runs `python -m planner briefs`. It rebuilds the brief of any trip that is **new**, was **edited** since its last brief, or has **Rebuild Brief** ticked. Each brief contains:
1. **At a glance:** destination, dates and nights, traveler, purpose, status and visa status. The box is coloured by status.
2. **🆘 Contacts:** primary contact, emergency contact and hotel phone.
3. **📅 Timeline:** every itinerary line, sorted by date and time and grouped by day, with icons (✈️ 🚗 🏨 🤝 🍽️ 🎤) and confirmation numbers. Lines in the wrong format are shown in a ⚠️ box, so nothing is silently lost.
4. **🏨 Stay & getting around:** hotel with a **Google Maps link**, booking reference, flights and ground transport.
5. **🛂 Visa & entry**, **📎 Documents** and **📝 Notes**.

Only the brief section is rewritten. Anything below **📂 Extra files & notes** is never touched.

Why generate it rather than use a Notion template? A Notion page can't display its own properties as a formatted, sorted timeline, and templates are only filled once, when the page is created. Generating the brief keeps it **always in sync** with the trip's fields. The EA only maintains the fields.

### Views
| View | Type | Shows |
|---|---|---|
| Upcoming – Timeline | Timeline (with table) | Planned and In-Progress trips on a timeline, sorted by date |
| By status | Board | Columns for Planned / In-Progress / Done; drag cards to change status |
| Calendar | Calendar (month) | Trips across their date range |
| All trips | Table | Everything, newest first |

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
Open the published page on any device, and tap a trip on the **Timeline** or **Calendar**. The brief opens with where and when, then who to call, then the day-by-day plan.

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
   This creates the guide, the Trips database, the 4 views, the 23 sample trips (Europe and USA) and their briefs, and saves the ids to `workspace.json`. Add `--reset` to rebuild the page from scratch.
4. **Share → Publish → Publish to web** in Notion. This is the one step the API can't do.
5. Optional, for automatic briefs: add the GitHub secret `NOTION_TOKEN` and the variable `NOTION_DATA_SOURCE_ID`. The schedule is in `.github/workflows/trip-briefs.yml`. To refresh by hand, run `python -m planner briefs` (or add `--all`).

Tests: `python -m pytest -q tests` covers itinerary parsing and sorting, the brief contents, the refresh rules and the icons.

## 6. Test results
| Test | Result |
|---|---|
| Offline unit tests | ✅ 4/4 |
| Build via the API: database, status groups, formula, 4 views, 23 trips, 23 complete briefs (each checked for timeline, 🆘 contacts, stay, visa, documents) | ✅ |
| Sample itineraries: every event falls between arrival and the flight home (0 conflicts in 23 trips) | ✅ |
| Only Europe and USA destinations; statuses: 7 Done, 1 In-Progress, 15 Planned | ✅ |
| Countdown formula: "15 days to go", "✈️ Travelling now", "✓ Completed" | ✅ |
| Timeline sorted by date and time and grouped by day; bad lines kept in a ⚠️ box | ✅ |
| Nothing changed → 0 briefs rebuilt; one trip edited → only that brief rebuilt | ✅ |
| An EA note under "📂 Extra files & notes" survives a rebuild | ✅ |
| GitHub Actions run of the refresher | ✅ |

### Sample data
23 trips (September 2026 – April 2027): 7 Done, 1 In-Progress (London, this week) and 15 Planned. Hotels and addresses are real; people, partner companies, booking numbers and `555` phone numbers are fictional. The attached PDFs are watermarked **SAMPLE**. The EA contact on every trip is Benjamin Kariuki (benjaminleyian50@gmail.com).

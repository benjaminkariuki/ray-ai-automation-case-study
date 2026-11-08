"""23 sample trips (Europe + USA only) for a New York-based founder.

Hotels and addresses are real places; people, partner companies, bookings and 555 phone numbers are fictional.
Sample documents are clearly watermarked "SAMPLE" PDFs hosted in this repository.
"""
from datetime import date, timedelta

from .notion import text

EA = "Benjamin Kariuki (EA) · benjaminleyian50@gmail.com · +1 (555) 010-2040 (WhatsApp, 24/7)"
EMERGENCY = "Jordan Morgan (spouse) · +1 (555) 010-7788"
FOUNDER = "Alex Morgan (Founder & CEO)"
DOCS_BASE = "https://raw.githubusercontent.com/benjaminkariuki/ray-ai-automation-case-study/main/task2-travel-planner/sample-docs/"
DOCUMENTS = [("SAMPLE e-ticket.pdf", "sample-e-ticket.pdf"),
             ("SAMPLE hotel confirmation.pdf", "sample-hotel-confirmation.pdf"),
             ("SAMPLE travel insurance.pdf", "sample-travel-insurance.pdf")]

EU_VISA = ("Not required", "US passport: visa-free short stay (up to 90 days in any 180). Passport valid to 2031.")
US_VISA = ("Not required", "Domestic trip — no travel documents beyond ID.")
UK_VISA = ("eVisa / ETA approved", "UK ETA approved 14 Oct 2026 (ref UKETA-55821), valid 2 years.")

# city: (destination, airport, hotel, hotel address, ground transport, US domestic?)
CITIES = {
    "London": ("London, United Kingdom", "LHR", "The Hoxton, Holborn", "199-206 High Holborn, London WC1V 7BD",
               "Addison Lee account (arrival pickup booked); Holborn Tube 2 min walk", False),
    "Paris": ("Paris, France", "CDG", "Hôtel National des Arts et Métiers", "243 Rue Saint-Martin, 75003 Paris",
              "G7 taxi booked from CDG; Métro Arts et Métiers next door", False),
    "Berlin": ("Berlin, Germany", "BER", "Hotel Zoo Berlin", "Kurfürstendamm 25, 10719 Berlin",
               "Blacklane chauffeur from BER", False),
    "Amsterdam": ("Amsterdam, Netherlands", "AMS", "Pulitzer Amsterdam", "Prinsengracht 323, 1016 GZ Amsterdam",
                  "Train Schiphol → Centraal (17 min), then taxi", False),
    "Lisbon": ("Lisbon, Portugal", "LIS", "Memmo Príncipe Real", "Rua Dom Pedro V 56J, 1250-094 Lisboa",
               "Conference shuttle from hotel; Uber for evenings", False),
    "Madrid": ("Madrid, Spain", "MAD", "Only YOU Boutique Hotel", "Calle del Barquillo 21, 28004 Madrid",
               "Cabify booked from MAD T4", False),
    "Barcelona": ("Barcelona, Spain", "BCN", "Hotel Casa Fuster", "Passeig de Gràcia 132, 08008 Barcelona",
                  "Taxi from BCN; Metro to the venue", False),
    "Zurich": ("Zurich, Switzerland", "ZRH", "Hotel Storchen", "Weinplatz 2, 8001 Zürich",
               "SBB train ZRH → Zürich HB (10 min), 5 min walk", False),
    "Stockholm": ("Stockholm, Sweden", "ARN", "Hotel Diplomat", "Strandvägen 7C, 114 56 Stockholm",
                  "Arlanda Express (18 min) then taxi", False),
    "Copenhagen": ("Copenhagen, Denmark", "CPH", "Hotel Sanders", "Tordenskjoldsgade 15, 1055 København",
                   "Metro M2 from CPH to Kongens Nytorv (15 min)", False),
    "Dublin": ("Dublin, Ireland", "DUB", "The Shelbourne", "27 St Stephen's Green, Dublin 2",
               "Free Now taxi from DUB", False),
    "Milan": ("Milan, Italy", "MXP", "Room Mate Giulia", "Via Silvio Pellico 4, 20121 Milano",
              "Malpensa Express to Cadorna, then taxi", False),
    "Munich": ("Munich, Germany", "MUC", "Hotel Bayerischer Hof", "Promenadeplatz 2-6, 80333 München",
               "Hotel limousine from MUC (booked)", False),
    "Vienna": ("Vienna, Austria", "VIE", "Hotel Sacher Wien", "Philharmoniker Str. 4, 1010 Wien",
               "City Airport Train to Wien Mitte (16 min)", False),
    "San Francisco": ("San Francisco, CA, USA", "SFO", "Hotel Nikko San Francisco", "222 Mason St, San Francisco, CA 94102",
                      "Uber Black from SFO", True),
    "Boston": ("Boston, MA, USA", "BOS", "The Liberty Hotel", "215 Charles St, Boston, MA 02114",
               "Uber from Logan", True),
    "Austin": ("Austin, TX, USA", "AUS", "Hotel Van Zandt", "605 Davis St, Austin, TX 78701",
               "Hotel shuttle from AUS", True),
    "Miami": ("Miami Beach, FL, USA", "MIA", "1 Hotel South Beach", "2341 Collins Ave, Miami Beach, FL 33139",
              "Car service booked from MIA", True),
    "Chicago": ("Chicago, IL, USA", "ORD", "The Langham, Chicago", "330 N Wabash Ave, Chicago, IL 60611",
                "Uber from O'Hare", True),
    "Seattle": ("Seattle, WA, USA", "SEA", "Thompson Seattle", "110 Stewart St, Seattle, WA 98101",
                "Link light rail to Westlake, 3 min walk", True),
    "Washington": ("Washington, DC, USA", "DCA", "The Hay-Adams", "800 16th St NW, Washington, DC 20006",
                   "Taxi from DCA (15 min)", True),
    "Los Angeles": ("Los Angeles, CA, USA", "LAX", "The Hoxton, Downtown LA", "1060 S Broadway, Los Angeles, CA 90015",
                    "Car service booked from LAX", True),
    "Las Vegas": ("Las Vegas, NV, USA", "LAS", "ARIA Resort & Casino", "3730 S Las Vegas Blvd, Las Vegas, NV 89158",
                  "Hotel shuttle from LAS", True),
}
AIRLINE = {"LHR": "BA", "CDG": "AF", "BER": "LH", "AMS": "KL", "LIS": "TP", "MAD": "IB", "BCN": "DL", "ZRH": "LX",
           "ARN": "SK", "CPH": "SK", "DUB": "EI", "MXP": "AZ", "MUC": "LH", "VIE": "OS"}

# (city, title, purpose, start, nights, status, agenda[(day, time, type, details)], extra)
TRIPS = [
    ("Boston", "Customer Advisory Board", "Customer / partner", "2026-09-14", 2, "Done",
     [(1, "09:00", "Event", "Customer Advisory Board, Seaport office (6 customers)"), (1, "19:00", "Dinner", "CAB dinner, Oyster bar")]),
    ("Paris", "Investor Meetings", "Investor meetings", "2026-09-21", 4, "Done",
     [(1, "10:00", "Meeting", "Lumen Capital — Series B intro"), (2, "14:00", "Meeting", "Seine Ventures — partner meeting"),
      (3, "12:30", "Lunch", "Founders lunch, Le Marais")]),
    ("Austin", "Tech Conference Panel", "Conference", "2026-10-05", 3, "Done",
     [(1, "11:00", "Talk", "Panel: 'AI in operations' — Main hall"), (2, "18:00", "Event", "Speaker reception")]),
    ("Berlin", "Partner Workshop", "Customer / partner", "2026-10-13", 3, "Done",
     [(1, "09:30", "Meeting", "Kiezbank — integration workshop (full day)"), (2, "19:30", "Dinner", "Partner dinner, Mitte")]),
    ("Chicago", "Customer Visits", "Customer / partner", "2026-10-20", 2, "Done",
     [(1, "10:00", "Meeting", "Lakeshore Logistics — QBR"), (1, "15:00", "Meeting", "Windy City Retail — renewal")]),
    ("Amsterdam", "Payments Summit Panel", "Conference", "2026-10-26", 3, "Done",
     [(1, "13:00", "Talk", "Payments Summit panel, RAI Amsterdam"), (2, "10:00", "Meeting", "Canal Pay — partnership call")]),
    ("Washington", "Policy Roundtable", "Customer / partner", "2026-11-02", 2, "Done",
     [(1, "10:00", "Meeting", "Fintech policy roundtable, Dupont Circle"), (1, "18:30", "Dinner", "Dinner with policy advisers")]),
    ("London", "Investor Roadshow", "Investor meetings", "2026-11-08", 4, "In-Progress",
     [(1, "11:00", "Meeting", "Thames Ventures — partner meeting, 20 Air St"), (2, "09:30", "Meeting", "Crown Capital — Series B intro"),
      (2, "13:00", "Lunch", "Founders lunch, Covent Garden"), (3, "15:00", "Meeting", "Albion Partners — follow-up"),
      (3, "19:30", "Dinner", "Investor dinner, Rules Restaurant")]),
    ("Lisbon", "Conference Keynote", "Conference", "2026-11-23", 3, "Planned",
     [(1, "09:00", "Event", "Speaker check-in, Hall 1 backstage (bring passport)"),
      (1, "10:30", "Keynote", "'Building AI-first operations' — Centre Stage (20 min)"),
      (2, "16:00", "Meeting", "Tejo Partners — booth C42")]),
    ("San Francisco", "Board Meeting", "Board meeting", "2026-12-01", 2, "Planned",
     [(1, "09:00", "Meeting", "Q4 board meeting, investor office, Market St"), (1, "18:30", "Dinner", "Board dinner")]),
    ("Zurich", "Banking Partner Meetings", "Customer / partner", "2026-12-07", 2, "Planned",
     [(1, "10:00", "Meeting", "Alpine Bank — custody partnership"), (2, "09:00", "Meeting", "Limmat Insurance — pilot review")],
     {"visa": ("Action needed", "Passport expires 15 Mar 2027: Schengen needs 3 months' validity after departure. "
                                "Renewal appointment booked 20 Nov — EA to confirm new passport before booking flights.")}),
    ("Miami", "Investor Summit", "Investor meetings", "2026-12-14", 2, "Planned",
     [(1, "09:30", "Event", "Investor summit, Miami Beach Convention Center"), (2, "11:00", "Meeting", "Biscayne Capital — 1:1")]),
    ("Las Vegas", "Tech Expo", "Conference", "2027-01-06", 3, "Planned",
     [(1, "10:00", "Event", "Tech Expo — booth walk with product team"), (2, "14:00", "Meeting", "Partner meetings, Venetian Expo")]),
    ("Copenhagen", "Customer Visit", "Customer / partner", "2027-01-11", 2, "Planned",
     [(1, "10:00", "Meeting", "Nordhavn Retail — executive sponsor meeting"), (1, "18:00", "Dinner", "Team dinner, Nyhavn")]),
    ("Stockholm", "Partner Meetings", "Customer / partner", "2027-01-18", 2, "Planned",
     [(1, "09:30", "Meeting", "Gamla Payments — roadmap session"), (2, "11:00", "Meeting", "Söder Health — pilot kickoff")]),
    ("Seattle", "Cloud Partner Review", "Customer / partner", "2027-01-25", 2, "Planned",
     [(1, "10:00", "Meeting", "Cloud partner quarterly review, South Lake Union")]),
    ("Dublin", "EU Office Visit", "Team offsite", "2027-02-01", 3, "Planned",
     [(1, "09:30", "Event", "All-hands, Dublin office"), (2, "14:00", "Meeting", "1:1s with EU leadership team")]),
    ("Madrid", "Sales Kickoff", "Team offsite", "2027-02-15", 3, "Planned",
     [(1, "09:00", "Keynote", "Sales kickoff opening keynote"), (2, "19:30", "Dinner", "Team awards dinner")]),
    ("Los Angeles", "Media Day", "Customer / partner", "2027-02-22", 2, "Planned",
     [(1, "10:00", "Event", "Podcast recordings x3, Arts District studio"), (1, "16:00", "Meeting", "Press interviews")]),
    ("Munich", "Industry Fair", "Conference", "2027-03-01", 3, "Planned",
     [(1, "10:00", "Event", "Industry fair — stand B3, Messe München"), (2, "12:30", "Lunch", "Partner lunch")],
     {"visa": ("Pending", "Depends on passport renewal (see Zurich trip). EA to update once the new passport arrives.")}),
    ("Milan", "Retail Partner Meetings", "Customer / partner", "2027-03-15", 2, "Planned",
     [(1, "10:30", "Meeting", "Brera Retail Group — expansion plan"), (1, "20:00", "Dinner", "Dinner with partners, Navigli")]),
    ("Vienna", "Leadership Offsite", "Team offsite", "2027-03-22", 4, "Planned",
     [(1, "09:00", "Event", "Leadership offsite day 1 — 2027 strategy"), (2, "09:00", "Event", "Offsite day 2 — org design"),
      (3, "19:00", "Dinner", "Offsite dinner, Heuriger")]),
    ("Barcelona", "Mobile Conference", "Conference", "2027-04-06", 3, "Planned",
     [(1, "11:00", "Talk", "Fireside chat, Hall 8"), (2, "15:00", "Meeting", "Telco partner meetings")]),
]


def _iso(d):
    return d.isoformat()


def build_trip(entry):
    city, title, purpose, start_s, nights, status, agenda, *extra = entry
    extra = extra[0] if extra else {}
    destination, airport, hotel, address, ground, domestic = CITIES[city]
    start = date.fromisoformat(start_s)
    end = start + timedelta(days=nights)
    seed = sum(map(ord, city + title))
    if domestic:
        carrier, out_no, back_no = "DL", 400 + seed % 400, 401 + seed % 400
        out_time, arr_day, back_time = "07:15", 0, "17:30"
    else:
        carrier = AIRLINE[airport]
        out_no, back_no = 100 + seed % 80, 101 + seed % 80
        out_time, arr_day, back_time = "21:30", 1, "12:15"
    pnr = f"{carrier}{(seed * 7919) % 46656:04X}"[:6]
    word = next(w for w in hotel.replace(",", "").split() if w not in ("The", "Hotel", "Hôtel", "1", "Only", "Room"))
    conf = f"{word[:3].upper()}-{(seed * 31) % 90000 + 10000}"
    out_flight = f"{carrier}{out_no} New York (JFK) → {city} ({airport})"
    back_flight = f"{carrier}{back_no} {city} ({airport}) → New York (JFK)"
    arrive = start + timedelta(days=arr_day)
    lines = [
        f"{_iso(start)} {out_time} | Flight | {out_flight} | PNR {pnr}",
        f"{_iso(arrive)} {'10:05' if not domestic else '10:20'} | Transfer | {ground.split(';')[0]} | ",
        f"{_iso(arrive)} {'12:00' if not domestic else '11:30'} | Hotel | Check-in, {hotel} | {conf}",
    ]
    busy_last_day = False
    for i, (day, clock, kind, details) in enumerate(agenda):
        if not domestic and day == arr_day and clock < "14:00":
            clock = f"{14 + i}:00"  # overnight flight lands ~10:00: first meeting after lunch
        if day == nights:
            busy_last_day = True
        lines.append(f"{_iso(start + timedelta(days=day))} {clock} | {kind} | {details} | ")
    if busy_last_day:
        back_time = "18:30"  # leave time for last-day meetings before the flight home
    lines += [f"{_iso(end)} 09:30 | Hotel | Check-out, {hotel} (luggage stored) | {conf}",
              f"{_iso(end)} {back_time} | Flight | {back_flight} | PNR {pnr}"]
    visa = extra.get("visa") or (US_VISA if domestic else UK_VISA if city == "London" else EU_VISA)
    trip = {
        "Trip": f"{city} — {title}", "Status": status, "dates": (_iso(start), _iso(end)), "Destination": destination,
        "Purpose": purpose, "Visa / Entry": visa[0], "Visa Notes": visa[1],
        "Traveler": FOUNDER if seed % 4 else f"{FOUNDER} + Sam Lee (COO)",
        "Flights": f"Out: {out_flight}, {start:%d %b} {out_time}. Back: {back_flight}, {end:%d %b} {back_time}. PNR {pnr}.",
        "Hotel": hotel, "Hotel Address": address, "Hotel Confirmation": f"{conf} · {nights} night{'s' if nights > 1 else ''}",
        "Ground Transport": ground, "Primary Contact": EA, "Emergency Contact": EMERGENCY,
        "Itinerary": "\n".join(lines),
        "Notes": "Expenses: photograph receipts into the Expensify app. " + (
            "Travel insurance covers the whole trip (policy in Documents)." if not domestic else "Corporate card covers hotel."),
    }
    return trip


def all_trips():
    return [build_trip(t) for t in TRIPS]


def page_properties(trip):
    props = {
        "Trip": {"title": text(trip["Trip"])},
        "Status": {"status": {"name": trip["Status"]}},
        "Travel Dates": {"date": {"start": trip["dates"][0], "end": trip["dates"][1]}},
        "Purpose": {"select": {"name": trip["Purpose"]}},
        "Visa / Entry": {"select": {"name": trip["Visa / Entry"]}},
        "Documents": {"files": [{"type": "external", "name": name, "external": {"url": DOCS_BASE + file}}
                                for name, file in DOCUMENTS]},
    }
    for key in ("Traveler", "Destination", "Itinerary", "Flights", "Hotel", "Hotel Address", "Hotel Confirmation",
                "Ground Transport", "Visa Notes", "Primary Contact", "Emergency Contact", "Notes"):
        if trip.get(key):
            props[key] = {"rich_text": text(trip[key])}
    return props

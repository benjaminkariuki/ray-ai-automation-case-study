"""Realistic sample trips (fictional founder "Alex Morgan"; 555 phone numbers are fictional)."""
from .notion import text

EA = "Benjamin Kariuki (EA) · +1 (555) 010-2040 · WhatsApp 24/7"
TRAVELER = "Alex Morgan (Founder & CEO)"

TRIPS = [
    {
        "Trip": "London — Investor Roadshow", "Status": "In-Progress", "dates": ("2026-11-08", "2026-11-12"),
        "Destination": "London, United Kingdom", "Purpose": "Investor meetings", "Visa / Entry": "eVisa / ETA approved",
        "Visa Notes": "UK ETA approved 14 Oct 2026 (ref UKETA-55821), valid 2 years. Passport valid to 2031.",
        "Flights": "Out: KQ100 NBO→LHR, 8 Nov 23:35, seat 2A, PNR KQ7XT2. Back: KQ101 LHR→NBO, 12 Nov 18:40, seat 2A.",
        "Hotel": "The Hoxton, Holborn", "Hotel Address": "199-206 High Holborn, London WC1V 7BD",
        "Hotel Phone": "+44 20 7661 3000", "Hotel Confirmation": "HX-448210 · 4 nights · late checkout 14:00 confirmed",
        "Ground Transport": "Addison Lee account #AL-3391 (arrival pickup booked). Tube: Holborn station 2 min walk.",
        "Primary Contact": EA, "Emergency Contact": "Jordan Morgan (spouse) · +1 (555) 010-7788",
        "Notes": "Bring the Q3 board deck on the iPad. Dress code for Thursday dinner: smart casual.",
        "Itinerary": "\n".join([
            "2026-11-08 23:35 | Flight | KQ100 Nairobi (NBO) → London Heathrow (LHR), T4 | PNR KQ7XT2",
            "2026-11-09 06:20 | Transfer | Addison Lee driver meets at Arrivals, name board 'MORGAN' | Job AL-90812",
            "2026-11-09 08:00 | Hotel | Early check-in, The Hoxton Holborn | HX-448210",
            "2026-11-09 11:00 | Meeting | Northzone — partner meeting, 2nd floor, 20 Air St | Contact: Priya",
            "2026-11-10 09:30 | Meeting | Balderton Capital — Series B intro, 20 Balderton St | Contact: Tom",
            "2026-11-10 13:00 | Lunch | Founders lunch at Dishoom Covent Garden | Table for 4",
            "2026-11-11 15:00 | Meeting | Index Ventures — follow-up, 5-8 Lower John St | Contact: Elena",
            "2026-11-11 19:30 | Dinner | Investor dinner, Rules Restaurant | Booking R-2219",
            "2026-11-12 14:00 | Hotel | Check-out (late checkout confirmed) | HX-448210",
            "2026-11-12 15:30 | Transfer | Addison Lee to Heathrow T4 | Job AL-90813",
            "2026-11-12 18:40 | Flight | KQ101 London Heathrow (LHR) → Nairobi (NBO) | PNR KQ7XT2"]),
    },
    {
        "Trip": "Lisbon — Tech Conference Keynote", "Status": "Planned", "dates": ("2026-11-23", "2026-11-26"),
        "Destination": "Lisbon, Portugal", "Purpose": "Conference", "Visa / Entry": "Visa approved",
        "Visa Notes": "Schengen visa approved (sticker in passport), multiple entry, valid 20 Nov – 20 Dec 2026.",
        "Flights": "Out: TP1302 LHR→LIS 23 Nov 07:15. Back: TP1351 LIS→LHR 26 Nov 19:05. Booking TPX9Q4.",
        "Hotel": "Memmo Príncipe Real", "Hotel Address": "Rua Dom Pedro V 56J, 1250-094 Lisboa",
        "Hotel Phone": "+351 21 901 6800", "Hotel Confirmation": "MPR-77120 · 3 nights",
        "Ground Transport": "Conference shuttle from hotel every 30 min (08:00–10:00). Uber for evenings.",
        "Primary Contact": EA, "Emergency Contact": "Jordan Morgan (spouse) · +1 (555) 010-7788",
        "Notes": "Keynote slides due to organisers by 18 Nov. Speaker check-in at Hall 1 backstage.",
        "Itinerary": "\n".join([
            "2026-11-23 07:15 | Flight | TP1302 London (LHR) → Lisbon (LIS) | Booking TPX9Q4",
            "2026-11-23 11:00 | Hotel | Check-in, Memmo Príncipe Real | MPR-77120",
            "2026-11-24 09:00 | Event | Speaker check-in, Hall 1 backstage | Badge pickup with passport",
            "2026-11-24 10:30 | Keynote | 'Building AI-first operations' — Centre Stage (20 min) | Producer: Marta",
            "2026-11-24 13:00 | Lunch | Speakers lunch | ",
            "2026-11-25 16:00 | Meeting | Partner meeting with LX Partners, booth C42 | Contact: Rui",
            "2026-11-26 19:05 | Flight | TP1351 Lisbon (LIS) → London (LHR) | Booking TPX9Q4"]),
    },
    {
        "Trip": "Dubai — Partner Meetings", "Status": "Planned", "dates": ("2026-12-07", "2026-12-10"),
        "Destination": "Dubai, United Arab Emirates", "Purpose": "Customer / partner", "Visa / Entry": "Pending",
        "Visa Notes": "UAE eVisa application submitted 2 Nov — decision expected by 20 Nov. EA to confirm.",
        "Flights": "EK722 NBO→DXB 7 Dec 16:25 (Business). Return EK719 DXB→NBO 10 Dec 10:30. PNR EK4LM8.",
        "Hotel": "Address Downtown", "Hotel Address": "Sheikh Mohammed bin Rashid Blvd, Downtown Dubai",
        "Hotel Phone": "+971 4 436 8888", "Hotel Confirmation": "ADD-55102 · 3 nights",
        "Ground Transport": "Emirates chauffeur drive included (book 48h ahead).",
        "Primary Contact": EA, "Emergency Contact": "Jordan Morgan (spouse) · +1 (555) 010-7788",
        "Itinerary": "\n".join([
            "2026-12-07 16:25 | Flight | EK722 Nairobi (NBO) → Dubai (DXB) | PNR EK4LM8",
            "2026-12-07 23:00 | Hotel | Check-in, Address Downtown | ADD-55102",
            "2026-12-08 10:00 | Meeting | Majid Al Futtaim — retail pilot review | Contact: Aisha",
            "2026-12-09 14:00 | Meeting | DIFC FinTech Hive — partnership workshop | Contact: Omar",
            "2026-12-10 10:30 | Flight | EK719 Dubai (DXB) → Nairobi (NBO) | PNR EK4LM8"]),
    },
    {
        "Trip": "New York — Board Meeting", "Status": "Planned", "dates": ("2027-01-18", "2027-01-21"),
        "Destination": "New York, USA", "Purpose": "Board meeting", "Visa / Entry": "Visa approved",
        "Visa Notes": "US B1/B2 visa valid to 2029.", "Flights": "To be booked (hold: KQ002 NBO→JFK 17 Jan).",
        "Hotel": "Arlo SoHo", "Hotel Address": "231 Hudson St, New York, NY 10013", "Hotel Phone": "+1 212-342-7000",
        "Hotel Confirmation": "Hold until 20 Dec", "Ground Transport": "TBC",
        "Primary Contact": EA, "Emergency Contact": "Jordan Morgan (spouse) · +1 (555) 010-7788",
        "Itinerary": "\n".join([
            "2027-01-18 | Flight | KQ002 Nairobi (NBO) → New York (JFK) — to be confirmed | Hold",
            "2027-01-19 09:00 | Meeting | Q4 board meeting, investor offices, 5th Ave | Agenda in Documents",
            "2027-01-20 18:30 | Dinner | Board dinner | Booking TBC"]),
    },
    {
        "Trip": "Nairobi — Team Offsite", "Status": "Done", "dates": ("2026-10-12", "2026-10-15"),
        "Destination": "Nairobi, Kenya", "Purpose": "Team offsite", "Visa / Entry": "Not required",
        "Flights": "No flights (local).", "Hotel": "Hemingways Nairobi", "Hotel Address": "Mbagathi Ridge, Karen, Nairobi",
        "Hotel Phone": "+254 20 513 0000", "Hotel Confirmation": "HEM-3310", "Ground Transport": "Team bus from office",
        "Primary Contact": EA, "Emergency Contact": "Jordan Morgan (spouse) · +1 (555) 010-7788",
        "Itinerary": "\n".join([
            "2026-10-12 09:00 | Transfer | Team bus departs office | ",
            "2026-10-12 11:00 | Event | 2027 planning workshop | Facilitator: Grace",
            "2026-10-14 18:00 | Dinner | Team dinner | ",
            "2026-10-15 15:00 | Transfer | Bus back to office | "]),
    },
]


def page_properties(trip):
    props = {
        "Trip": {"title": text(trip["Trip"])},
        "Status": {"status": {"name": trip["Status"]}},
        "Travel Dates": {"date": {"start": trip["dates"][0], "end": trip["dates"][1]}},
        "Traveler": {"rich_text": text(TRAVELER)},
        "Purpose": {"select": {"name": trip["Purpose"]}},
        "Visa / Entry": {"select": {"name": trip["Visa / Entry"]}},
        "Hotel Phone": {"phone_number": trip.get("Hotel Phone") or None},
    }
    for key in ("Destination", "Itinerary", "Flights", "Hotel", "Hotel Address", "Hotel Confirmation",
                "Ground Transport", "Visa Notes", "Primary Contact", "Emergency Contact", "Notes"):
        if trip.get(key):
            props[key] = {"rich_text": text(trip[key])}
    return props

"""'werken'-afspraken uit een Google Agenda (iCal-link of .ics-bestand) halen."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import icalendar
import recurring_ical_events
import requests

TZ = ZoneInfo("Europe/Amsterdam")


def haal_ics(url: str) -> bytes:
    # Google toont webcal://; requests kan alleen http(s).
    if url.startswith("webcal://"):
        url = "https://" + url[len("webcal://"):]
    antwoord = requests.get(url, timeout=15)
    antwoord.raise_for_status()
    return antwoord.content


def werkblokken(ics: bytes, begin: date, eind: date,
                zoekwoord: str = "werken") -> list[tuple[datetime, datetime]]:
    """Start/eind van alle afspraken tussen begin en eind (inclusief) met het
    zoekwoord in de titel. Hele-dag-afspraken tellen niet mee."""
    agenda = icalendar.Calendar.from_ical(ics)
    afspraken = recurring_ical_events.of(agenda).between(begin, eind + timedelta(days=1))
    zoek = zoekwoord.strip().lower()
    blokken = []
    for a in afspraken:
        if zoek not in str(a.get("SUMMARY", "")).lower():
            continue
        start, stop = a["DTSTART"].dt, a["DTEND"].dt
        if not isinstance(start, datetime):
            continue
        blokken.append((_lokaal(start), _lokaal(stop)))
    return sorted(blokken)


def _lokaal(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=TZ)
    return dt.astimezone(TZ).replace(tzinfo=None)

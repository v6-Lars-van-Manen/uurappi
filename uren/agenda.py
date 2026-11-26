"""'werken'-afspraken uit een Google- of iCloud-agenda (iCal-link of .ics-bestand) halen."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import icalendar
import recurring_ical_events
import requests

TZ = ZoneInfo("Europe/Amsterdam")


def maak_https(url: str) -> str:
    """Agenda-apps geven vaak een webcal://-link (Google, iCloud: 'Openbare agenda');
    requests kan alleen http(s). Werkt ook voor WEBCAL://, webcals:// en een link
    zonder begin."""
    url = url.strip()
    schema, _, rest = url.partition("://")
    if not rest:
        return "https://" + url
    if schema.lower() in ("webcal", "webcals"):
        return "https://" + rest
    return url


def haal_ics(url: str) -> bytes:
    # iCloud stuurt soms door naar een andere pXX-caldav-server; requests volgt dat.
    antwoord = requests.get(maak_https(url), timeout=20,
                            headers={"User-Agent": "Mozilla/5.0 (uurappi)"})
    if antwoord.status_code in (403, 404):
        raise ValueError("de agenda-link werkt niet (meer). Staat 'Openbare agenda' "
                         "(iCloud) of het geheime adres (Google) nog aan?")
    antwoord.raise_for_status()
    if b"BEGIN:VCALENDAR" not in antwoord.content[:2000]:
        raise ValueError("deze link geeft geen agenda terug. Kopieer de link opnieuw.")
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

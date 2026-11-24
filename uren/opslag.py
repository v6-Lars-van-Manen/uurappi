"""Werkdagen en instellingen van één gebruiker, als JSON.

De app bewaart deze JSON in de browser van de gebruiker (zie uren/browser.py),
zodat iedere collega alleen zijn eigen uren en agenda-link ziet.
"""

from __future__ import annotations

import json
from datetime import date

from .core import Werkdag

STANDAARD_INSTELLINGEN = {
    "ical_url": "",
    "zoekwoord": "werken",
    "aanhef": "Beste Marinus",
    "naam": "",
    "ontvanger": "marinus@horlogerievanmanen.nl",
    "pauze_aan": True,
    "pauze_van": "12:00",
    "pauze_tot": "13:00",
    "pauze_weekdagen": [5],
    "laatst_gemeld": None,
}


class Opslag:
    def __init__(self, tekst: str = ""):
        self.dagen: dict[date, Werkdag] = {}
        self.instellingen = dict(STANDAARD_INSTELLINGEN)
        if tekst.strip():
            self.laad(tekst)

    def laad(self, tekst: str) -> None:
        data = json.loads(tekst)
        self.dagen = {w.datum: w for w in map(Werkdag.uit_dict, data.get("dagen", []))}
        self.instellingen = {**STANDAARD_INSTELLINGEN, **data.get("instellingen", {})}

    def als_json(self) -> str:
        return json.dumps({
            "dagen": [d.naar_dict() for d in sorted(self.dagen.values(), key=lambda d: d.datum)],
            "instellingen": self.instellingen,
        }, indent=2, ensure_ascii=False)

    def in_periode(self, begin: date, eind: date) -> list[Werkdag]:
        return sorted((d for d in self.dagen.values() if begin <= d.datum <= eind),
                      key=lambda d: d.datum)

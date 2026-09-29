"""Werkdagen en instellingen bewaren in een JSON-bestand."""

from __future__ import annotations

import json
import os
from datetime import date
from pathlib import Path

from .core import Werkdag

STANDAARD_PAD = Path(os.environ.get("UURAPPI_DATA", Path(__file__).parent.parent / "data" / "uren.json"))

STANDAARD_INSTELLINGEN = {
    "ical_url": "",
    "zoekwoord": "werken",
    "aanhef": "Beste oom Marinus",
    "naam": "Lars van Manen",
    "ontvanger": "marinus@horlogerievanmanen.nl",
    "pauze_aan": True,
    "pauze_van": "12:00",
    "pauze_tot": "13:00",
    "pauze_weekdagen": [5],
    "laatst_gemeld": "2026-09-25",  # laatste dag in de urenmail van september 2026
}


class Opslag:
    def __init__(self, pad: Path = STANDAARD_PAD):
        self.pad = Path(pad)
        self.dagen: dict[date, Werkdag] = {}
        self.instellingen = dict(STANDAARD_INSTELLINGEN)
        if self.pad.exists():
            self.laad(self.pad.read_text(encoding="utf-8"))

    def laad(self, tekst: str) -> None:
        data = json.loads(tekst)
        self.dagen = {w.datum: w for w in map(Werkdag.uit_dict, data.get("dagen", []))}
        self.instellingen = {**STANDAARD_INSTELLINGEN, **data.get("instellingen", {})}

    def als_json(self) -> str:
        return json.dumps({
            "dagen": [d.naar_dict() for d in sorted(self.dagen.values(), key=lambda d: d.datum)],
            "instellingen": self.instellingen,
        }, indent=2, ensure_ascii=False)

    def bewaar(self) -> None:
        self.pad.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.pad.with_suffix(".tmp")
        tmp.write_text(self.als_json(), encoding="utf-8")
        tmp.replace(self.pad)

    def in_periode(self, begin: date, eind: date) -> list[Werkdag]:
        return sorted((d for d in self.dagen.values() if begin <= d.datum <= eind),
                      key=lambda d: d.datum)

    def vervang_periode(self, begin: date, eind: date, dagen: list[Werkdag]) -> None:
        for datum in [d for d in self.dagen if begin <= d <= eind]:
            del self.dagen[datum]
        for dag in dagen:
            self.dagen[dag.datum] = dag

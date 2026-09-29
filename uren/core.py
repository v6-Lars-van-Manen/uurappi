"""Werkdagen, urenberekening en de tekst voor de maandelijkse urenmail."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta

DAGEN = ["Ma", "Di", "Wo", "Do", "Vr", "Za", "Zo"]
MAANDEN_KORT = ["jan", "feb", "mrt", "april", "mei", "juni",
                "juli", "aug", "sep", "okt", "nov", "dec"]
MAANDEN_LANG = ["januari", "februari", "maart", "april", "mei", "juni", "juli",
                "augustus", "september", "oktober", "november", "december"]


@dataclass
class Werkdag:
    datum: date
    begin: time
    eind: time
    pauze_van: time | None = None
    pauze_tot: time | None = None
    bron: str = "handmatig"  # "agenda" of "handmatig"

    def heeft_pauze(self) -> bool:
        return self.pauze_van is not None and self.pauze_tot is not None

    def uren(self) -> float:
        totaal = _minuten(self.eind) - _minuten(self.begin)
        if self.heeft_pauze():
            totaal -= _minuten(self.pauze_tot) - _minuten(self.pauze_van)
        return totaal / 60

    def fouten(self) -> list[str]:
        f = []
        if self.eind <= self.begin:
            f.append("eindtijd ligt niet na begintijd")
        if (self.pauze_van is None) != (self.pauze_tot is None):
            f.append("vul zowel begin als eind van de pauze in")
        elif self.heeft_pauze():
            if self.pauze_tot <= self.pauze_van:
                f.append("pauze eindigt niet na het begin")
            elif self.pauze_van <= self.begin or self.pauze_tot >= self.eind:
                f.append("pauze valt niet binnen de werktijd")
        return f

    def regel(self) -> str:
        """Regel zoals in de mail, bijv. 'Za 29 aug 9.00-12.00 13.00-17.00 = 7'."""
        d = self.datum
        kop = f"{DAGEN[d.weekday()]} {d.day} {MAANDEN_KORT[d.month - 1]}"
        if self.heeft_pauze():
            tijden = (f"{tijd_tekst(self.begin)}-{tijd_tekst(self.pauze_van)} "
                      f"{tijd_tekst(self.pauze_tot)}-{tijd_tekst(self.eind)}")
        else:
            tijden = f"{tijd_tekst(self.begin)}-{tijd_tekst(self.eind)}"
        return f"{kop} {tijden} = {uren_tekst(self.uren())}"

    def naar_dict(self) -> dict:
        return {
            "datum": self.datum.isoformat(),
            "begin": self.begin.strftime("%H:%M"),
            "eind": self.eind.strftime("%H:%M"),
            "pauze_van": self.pauze_van.strftime("%H:%M") if self.pauze_van else None,
            "pauze_tot": self.pauze_tot.strftime("%H:%M") if self.pauze_tot else None,
            "bron": self.bron,
        }

    @classmethod
    def uit_dict(cls, d: dict) -> "Werkdag":
        def t(s):
            return datetime.strptime(s, "%H:%M").time() if s else None
        return cls(date.fromisoformat(d["datum"]), t(d["begin"]), t(d["eind"]),
                   t(d.get("pauze_van")), t(d.get("pauze_tot")), d.get("bron", "handmatig"))


@dataclass
class PauzeRegel:
    """Standaardpauze die een concept uit de agenda krijgt."""
    aan: bool = True
    van: time = time(12, 0)
    tot: time = time(13, 0)
    weekdagen: list[int] = field(default_factory=lambda: [5])  # 5 = zaterdag

    def pas_toe(self, dag: Werkdag) -> None:
        if (self.aan and not dag.heeft_pauze()
                and dag.datum.weekday() in self.weekdagen
                and dag.begin < self.van and dag.eind > self.tot):
            dag.pauze_van, dag.pauze_tot = self.van, self.tot


def _minuten(t: time) -> int:
    return t.hour * 60 + t.minute


def tijd_tekst(t: time) -> str:
    return f"{t.hour}.{t.minute:02d}"


def uren_tekst(uren: float) -> str:
    return f"{uren:.2f}".rstrip("0").rstrip(".")


def dagen_uit_agenda(blokken: list[tuple[datetime, datetime]],
                     pauze: PauzeRegel | None = None) -> list[Werkdag]:
    """Voeg agenda-blokken per datum samen tot werkdagen.

    Twee blokken op één dag (bijv. 9-12 en 13-17) worden één dag met het gat
    als pauze. Zonder gat krijgt de dag eventueel de standaardpauze.
    """
    per_dag: dict[date, list[tuple[time, time]]] = {}
    for start, eind in blokken:
        per_dag.setdefault(start.date(), []).append((start.time(), eind.time()))

    dagen = []
    for datum, tijden in sorted(per_dag.items()):
        tijden.sort()
        dag = Werkdag(datum, tijden[0][0], max(e for _, e in tijden), bron="agenda")
        for (_, eind_a), (begin_b, _) in zip(tijden, tijden[1:]):
            if begin_b > eind_a:
                dag.pauze_van, dag.pauze_tot = eind_a, begin_b
                break
        if pauze:
            pauze.pas_toe(dag)
        dagen.append(dag)
    return dagen


def mail_onderwerp(maand: int) -> str:
    return f"Uren {MAANDEN_LANG[maand - 1]}"


def mail_tekst(dagen: list[Werkdag], maand: int, aanhef: str, naam: str) -> str:
    dagen = sorted(dagen, key=lambda d: d.datum)
    regels = "\n".join(d.regel() for d in dagen)
    totaal = uren_tekst(sum(d.uren() for d in dagen))
    return (f"{aanhef},\n\n"
            f"Bij deze mijn uren van de maand {MAANDEN_LANG[maand - 1]}\n\n"
            f"{regels}\n\n"
            f"Totaal aantal dagen = {len(dagen)}\n"
            f"Totaal aantal uren = {totaal}\n\n"
            f"Met vriendelijke groet,\n\n"
            f"{naam}")


def standaard_periode(laatst_gemeld: date | None, vandaag: date) -> tuple[date, date]:
    """Periode vanaf de dag na de laatst gemelde werkdag t/m het einde van de maand.

    Zonder eerdere melding is het de huidige maand. Valt het begin in de laatste
    tien dagen van de maand, dan loopt de periode door tot het eind van de
    volgende maand (je mailt vaak al rond de 25e).
    """
    begin = laatst_gemeld + timedelta(days=1) if laatst_gemeld else vandaag.replace(day=1)
    eind = _einde_maand(max(begin, vandaag))
    if (eind - begin).days < 10:
        eind = _einde_maand(eind + timedelta(days=1))
    return begin, eind


def _einde_maand(d: date) -> date:
    volgende = (d.replace(day=28) + timedelta(days=4)).replace(day=1)
    return volgende - timedelta(days=1)

from datetime import date, datetime, time

from uren.agenda import werkblokken
from uren.core import (PauzeRegel, Werkdag, dagen_uit_agenda, mail_tekst,
                       standaard_periode)

SEPTEMBER = """Beste oom Marinus,

Bij deze mijn uren van de maand september

Za 29 aug 9.00-12.00 13.00-17.00 = 7
Vr 4 sep 14.00-22.00 = 8
Za 5 sep 8.30-12.00 = 3.5
Za 12 sep 8.30-12.00 13.00-17.00 = 7.5
Vr 18 sep 14.00-21.00 = 7
Za 19 sep 9.00-12.00 13.00-17.00 = 7
Vr 25 sep 14.00-21.00 = 7

Totaal aantal dagen = 7
Totaal aantal uren = 47

Met vriendelijke groet,

Lars van Manen"""


def d(dag, maand, b, e, pv=None, pt=None):
    t = lambda s: time(*map(int, s.split(":"))) if s else None
    return Werkdag(date(2026, maand, dag), t(b), t(e), t(pv), t(pt))


def test_mail_zoals_september():
    dagen = [
        d(29, 8, "9:00", "17:00", "12:00", "13:00"),
        d(4, 9, "14:00", "22:00"),
        d(5, 9, "8:30", "12:00"),
        d(12, 9, "8:30", "17:00", "12:00", "13:00"),
        d(18, 9, "14:00", "21:00"),
        d(19, 9, "9:00", "17:00", "12:00", "13:00"),
        d(25, 9, "14:00", "21:00"),
    ]
    assert mail_tekst(dagen, 9, "Beste oom Marinus", "Lars van Manen") == SEPTEMBER


def test_uren_en_kwartieren():
    assert d(1, 9, "9:15", "17:00", "12:00", "12:30").uren() == 7.25
    assert d(1, 9, "9:15", "17:00").regel() == "Di 1 sep 9.15-17.00 = 7.75"


def test_fouten():
    assert d(1, 9, "17:00", "9:00").fouten() == ["eindtijd ligt niet na begintijd"]
    assert d(1, 9, "9:00", "17:00", "8:00", "9:30").fouten() == ["pauze valt niet binnen de werktijd"]
    assert d(1, 9, "9:00", "17:00", "12:00").fouten() == ["vul zowel begin als eind van de pauze in"]
    assert d(1, 9, "9:00", "17:00", "12:00", "13:00").fouten() == []


def test_agenda_blokken_samenvoegen_en_standaardpauze():
    dt = lambda m, dg, h, mi=0: datetime(2026, m, dg, h, mi)
    blokken = [
        (dt(9, 12, 13), dt(9, 12, 17)), (dt(9, 12, 8, 30), dt(9, 12, 12)),  # za, gesplitst
        (dt(9, 19, 9), dt(9, 19, 17)),   # za, één blok -> standaardpauze
        (dt(9, 18, 14), dt(9, 18, 21)),  # vr, geen pauze
        (dt(9, 5, 8, 30), dt(9, 5, 12)),  # za, alleen ochtend -> geen pauze
    ]
    regels = [w.regel() for w in dagen_uit_agenda(blokken, PauzeRegel())]
    assert regels == [
        "Za 5 sep 8.30-12.00 = 3.5",
        "Za 12 sep 8.30-12.00 13.00-17.00 = 7.5",
        "Vr 18 sep 14.00-21.00 = 7",
        "Za 19 sep 9.00-12.00 13.00-17.00 = 7",
    ]


def test_ics_filter_en_herhaling():
    ics = b"""BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:1
SUMMARY:Werken
DTSTART;TZID=Europe/Amsterdam:20260904T140000
DTEND;TZID=Europe/Amsterdam:20260904T220000
RRULE:FREQ=WEEKLY;COUNT=3
END:VEVENT
BEGIN:VEVENT
UID:2
SUMMARY:Huisavond
DTSTART:20260906T180000Z
DTEND:20260906T190000Z
END:VEVENT
BEGIN:VEVENT
UID:3
SUMMARY:werken
DTSTART:20260905T063000Z
DTEND:20260905T100000Z
END:VEVENT
END:VCALENDAR"""
    blokken = werkblokken(ics, date(2026, 9, 1), date(2026, 9, 11))
    assert blokken == [
        (datetime(2026, 9, 4, 14), datetime(2026, 9, 4, 22)),
        (datetime(2026, 9, 5, 8, 30), datetime(2026, 9, 5, 12)),
        (datetime(2026, 9, 11, 14), datetime(2026, 9, 11, 22)),
    ]


def test_standaard_periode():
    # vorige mail t/m 25 sep, vandaag 29 sep -> 26 sep t/m eind oktober
    assert standaard_periode(date(2026, 9, 25), date(2026, 9, 29)) == (date(2026, 9, 26), date(2026, 10, 31))
    assert standaard_periode(None, date(2026, 10, 3)) == (date(2026, 10, 1), date(2026, 10, 31))

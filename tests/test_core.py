from datetime import date, datetime, time

from uren.agenda import werkblokken
from uren.core import (PauzeRegel, Werkdag, dagen_uit_agenda, huidige_maand,
                       laatste_vrijdag, maand_periode, mail_tekst)

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


def test_laatste_vrijdag():
    assert laatste_vrijdag(2026, 11) == date(2026, 11, 27)
    assert laatste_vrijdag(2026, 10) == date(2026, 10, 30)
    assert laatste_vrijdag(2026, 7) == date(2026, 7, 31)  # maand eindigt op vrijdag


def test_maand_periode():
    assert maand_periode(2026, 11) == (date(2026, 10, 31), date(2026, 11, 27))
    assert maand_periode(2027, 1) == (date(2026, 12, 26), date(2027, 1, 29))


def test_huidige_maand():
    assert huidige_maand(date(2026, 11, 25)) == (2026, 11)
    assert huidige_maand(date(2026, 11, 27)) == (2026, 11)  # inleverdag zelf
    assert huidige_maand(date(2026, 11, 28)) == (2026, 12)
    assert huidige_maand(date(2026, 12, 31)) == (2027, 1)


def test_echte_agenda_oktober():
    # 'Werken '-afspraken zoals ze in de agenda staan (titel met spatie erachter)
    tijden = [("20260926T090000", "20260926T170000"), ("20261002T130000", "20261002T170000"),
              ("20261030T180000", "20261030T210000")]
    ics = ("BEGIN:VCALENDAR\nVERSION:2.0\n" + "".join(
        f"BEGIN:VEVENT\nUID:{i}\nSUMMARY:Werken \nDTSTART;TZID=Europe/Amsterdam:{s}\n"
        f"DTEND;TZID=Europe/Amsterdam:{e}\nEND:VEVENT\n" for i, (s, e) in enumerate(tijden))
        + "END:VCALENDAR\n").encode()
    dagen = dagen_uit_agenda(werkblokken(ics, date(2026, 9, 26), date(2026, 10, 31)), PauzeRegel())
    assert [d.regel() for d in dagen] == [
        "Za 26 sep 9.00-12.00 13.00-17.00 = 7",
        "Vr 2 okt 13.00-17.00 = 4",
        "Vr 30 okt 18.00-21.00 = 3",  # na de wintertijd
    ]


def test_opslag_heen_en_terug():
    from uren.opslag import Opslag
    leeg = Opslag("")
    assert leeg.dagen == {} and leeg.instellingen["naam"] == ""
    leeg.dagen[date(2026, 11, 7)] = d(7, 11, "9:00", "17:00", "12:00", "13:00")
    leeg.instellingen["naam"] = "Collega"
    terug = Opslag(leeg.als_json())
    assert terug.instellingen["naam"] == "Collega"
    assert terug.in_periode(date(2026, 11, 1), date(2026, 11, 30))[0].uren() == 7


ICLOUD_ICS = b"""BEGIN:VCALENDAR\r
VERSION:2.0\r
PRODID:-//Apple Inc.//iPhone OS 18.0//EN\r
X-WR-CALNAME:Werk\r
BEGIN:VTIMEZONE\r
TZID:Europe/Amsterdam\r
BEGIN:STANDARD\r
DTSTART:19961027T030000\r
RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=-1SU\r
TZOFFSETFROM:+0200\r
TZOFFSETTO:+0100\r
END:STANDARD\r
BEGIN:DAYLIGHT\r
DTSTART:19810329T020000\r
RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU\r
TZOFFSETFROM:+0100\r
TZOFFSETTO:+0200\r
END:DAYLIGHT\r
END:VTIMEZONE\r
BEGIN:VEVENT\r
UID:a@icloud\r
DTSTART;TZID=Europe/Amsterdam:20261107T090000\r
DURATION:PT8H\r
SUMMARY:Werken\r
END:VEVENT\r
BEGIN:VEVENT\r
UID:b@icloud\r
DTSTART:20261113T140000\r
DTEND:20261113T220000\r
SUMMARY:WERKEN \r
END:VEVENT\r
BEGIN:VEVENT\r
UID:c@icloud\r
DTSTART:20261114T080000Z\r
DTEND:20261114T160000Z\r
SUMMARY:Werken\r
END:VEVENT\r
BEGIN:VEVENT\r
UID:d@icloud\r
DTSTART;VALUE=DATE:20261115\r
DTEND;VALUE=DATE:20261116\r
SUMMARY:Werken\r
END:VEVENT\r
END:VCALENDAR\r
"""


def test_icloud_agenda():
    # iCloud: TZID met eigen VTIMEZONE, DURATION i.p.v. DTEND, zwevende tijden, UTC
    blokken = werkblokken(ICLOUD_ICS, date(2026, 11, 1), date(2026, 11, 30))
    assert blokken == [
        (datetime(2026, 11, 7, 9), datetime(2026, 11, 7, 17)),
        (datetime(2026, 11, 13, 14), datetime(2026, 11, 13, 22)),
        (datetime(2026, 11, 14, 9), datetime(2026, 11, 14, 17)),
    ]


def test_webcal_links():
    from uren.agenda import maak_https
    assert maak_https(" webcal://p52-caldav.icloud.com/published/2/abc ") == \
        "https://p52-caldav.icloud.com/published/2/abc"
    assert maak_https("WEBCAL://x.nl/a.ics") == "https://x.nl/a.ics"
    assert maak_https("webcals://x.nl/a.ics") == "https://x.nl/a.ics"
    assert maak_https("p52-caldav.icloud.com/published/2/abc") == \
        "https://p52-caldav.icloud.com/published/2/abc"
    assert maak_https("https://calendar.google.com/x/basic.ics") == \
        "https://calendar.google.com/x/basic.ics"

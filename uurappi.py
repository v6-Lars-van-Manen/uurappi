"""Urenregistratie: concept uit de agenda, aanpassen, en de urenmail voor Marinus."""

from datetime import date, datetime, time
from urllib.parse import quote

import pandas as pd
import streamlit as st

from uren import agenda
from uren.core import (DAGEN, PauzeRegel, Werkdag, dagen_uit_agenda, mail_onderwerp,
                       mail_tekst, standaard_periode, uren_tekst)
from uren.opslag import Opslag

st.set_page_config(page_title="Uren", page_icon="🕘", layout="centered")

opslag = Opslag()
inst = opslag.instellingen


def tijd(s: str) -> time:
    return datetime.strptime(s, "%H:%M").time()


def pauzeregel() -> PauzeRegel:
    return PauzeRegel(inst["pauze_aan"], tijd(inst["pauze_van"]), tijd(inst["pauze_tot"]),
                      inst["pauze_weekdagen"])


def ververs_editor():
    st.session_state["editor_versie"] = st.session_state.get("editor_versie", 0) + 1


# ---------------------------------------------------------------- zijbalk
with st.sidebar:
    st.header("Instellingen")
    with st.form("instellingen"):
        ical_url = st.text_input(
            "Geheime iCal-link van je Google Agenda", inst["ical_url"], type="password",
            help="Google Agenda → Instellingen → je agenda → 'Geheim adres in iCal-indeling'.")
        zoekwoord = st.text_input("Titel van werkafspraken", inst["zoekwoord"])
        aanhef = st.text_input("Aanhef", inst["aanhef"])
        naam = st.text_input("Ondertekening", inst["naam"])
        ontvanger = st.text_input("Mail naar", inst["ontvanger"])
        st.markdown("**Standaardpauze in het concept**")
        pauze_aan = st.checkbox("Pauze toevoegen als de agenda er geen heeft", inst["pauze_aan"])
        c1, c2 = st.columns(2)
        pauze_van = c1.time_input("Van", tijd(inst["pauze_van"]), step=900)
        pauze_tot = c2.time_input("Tot", tijd(inst["pauze_tot"]), step=900)
        weekdagen = st.multiselect("Op", list(range(7)), inst["pauze_weekdagen"],
                                   format_func=lambda i: DAGEN[i])
        if st.form_submit_button("Opslaan"):
            inst.update(ical_url=ical_url.strip(), zoekwoord=zoekwoord, aanhef=aanhef,
                        naam=naam, ontvanger=ontvanger, pauze_aan=pauze_aan,
                        pauze_van=pauze_van.strftime("%H:%M"),
                        pauze_tot=pauze_tot.strftime("%H:%M"), pauze_weekdagen=weekdagen)
            opslag.bewaar()
            st.success("Opgeslagen")

    st.header("Back-up")
    st.download_button("Download alle uren (JSON)", opslag.als_json(),
                       file_name=f"uren-{date.today().isoformat()}.json", mime="application/json")
    backup = st.file_uploader("Zet een back-up terug", type="json")
    if backup and st.button("Terugzetten"):
        opslag.laad(backup.getvalue().decode("utf-8"))
        opslag.bewaar()
        ververs_editor()
        st.rerun()

# ---------------------------------------------------------------- periode
st.title("Werkuren")

laatst = date.fromisoformat(inst["laatst_gemeld"]) if inst["laatst_gemeld"] else None
std_begin, std_eind = standaard_periode(laatst, date.today())
c1, c2 = st.columns(2)
begin = c1.date_input("Van", std_begin, format="DD-MM-YYYY")
eind = c2.date_input("Tot en met", std_eind, format="DD-MM-YYYY")
if laatst:
    st.caption(f"Laatst gemelde werkdag: {laatst.strftime('%d-%m-%Y')}")
if eind < begin:
    st.error("De einddatum ligt voor de begindatum.")
    st.stop()

# ---------------------------------------------------------------- concept uit agenda
with st.expander("Concept uit je agenda halen", expanded=not opslag.in_periode(begin, eind)):
    ics_bestand = None
    if not inst["ical_url"]:
        st.info("Zet je geheime iCal-link in de instellingen, of upload hier een .ics-export.")
        ics_bestand = st.file_uploader("Agenda-export (.ics)", type="ics")
    overschrijf = st.checkbox("Dagen die ik al heb aangepast ook vervangen", False)
    if st.button(f"Haal '{inst['zoekwoord']}' uit de agenda", type="primary",
                 disabled=not (inst["ical_url"] or ics_bestand)):
        try:
            ics = ics_bestand.getvalue() if ics_bestand else agenda.haal_ics(inst["ical_url"])
            blokken = agenda.werkblokken(ics, begin, eind, inst["zoekwoord"])
        except Exception as fout:  # netwerk of kapot bestand
            st.error(f"Agenda lezen lukte niet: {fout}")
        else:
            nieuw = dagen_uit_agenda(blokken, pauzeregel())
            toegevoegd = 0
            for dag in nieuw:
                if overschrijf or dag.datum not in opslag.dagen:
                    opslag.dagen[dag.datum] = dag
                    toegevoegd += 1
            opslag.bewaar()
            ververs_editor()
            st.success(f"{len(nieuw)} werkdagen in de agenda gevonden, {toegevoegd} toegevoegd.")

# ---------------------------------------------------------------- dagen bewerken
st.subheader("Gewerkte dagen")
st.caption("Pas tijden aan in de tabel. Pauze weg: maak beide pauzevelden leeg. "
           "Dag erbij: klik op + onder de tabel. Dag weg: vink de rij aan en klik op het prullenbakje.")

KOLOMMEN = ["Datum", "Begin", "Eind", "Pauze van", "Pauze tot", "Bron"]
editor_key = f"editor-{begin}-{eind}-{st.session_state.get('editor_versie', 0)}"
basis_key = "basis-" + editor_key
if basis_key not in st.session_state:
    st.session_state[basis_key] = pd.DataFrame(
        [[d.datum, d.begin, d.eind, d.pauze_van, d.pauze_tot, d.bron]
         for d in opslag.in_periode(begin, eind)],
        columns=KOLOMMEN).astype(object)

tijd_kolom = lambda label: st.column_config.TimeColumn(label, format="HH:mm", step=900)
bewerkt = st.data_editor(
    st.session_state[basis_key],
    key=editor_key,
    num_rows="dynamic",
    hide_index=True,
    use_container_width=True,
    column_config={
        "Datum": st.column_config.DateColumn("Datum", format="DD-MM-YYYY", required=True,
                                             min_value=begin, max_value=eind),
        "Begin": tijd_kolom("Begin"),
        "Eind": tijd_kolom("Eind"),
        "Pauze van": tijd_kolom("Pauze van"),
        "Pauze tot": tijd_kolom("Pauze tot"),
        "Bron": st.column_config.TextColumn("Bron", disabled=True, default="handmatig"),
    },
)


def leeg(v) -> bool:
    return v is None or (isinstance(v, float) and pd.isna(v)) or v is pd.NaT


dagen, fouten = [], []
for rij in bewerkt.itertuples(index=False):
    datum, b, e, pv, pt, bron = rij
    if all(leeg(v) for v in (datum, b, e, pv, pt)):
        continue
    if leeg(datum) or leeg(b) or leeg(e):
        fouten.append("Een rij mist een datum, begin- of eindtijd.")
        continue
    if isinstance(datum, datetime):
        datum = datum.date()
    dag = Werkdag(datum, b, e, None if leeg(pv) else pv, None if leeg(pt) else pt,
                  "handmatig" if leeg(bron) else bron)
    fouten += [f"{dag.datum.strftime('%d-%m')}: {f}" for f in dag.fouten()]
    if not begin <= dag.datum <= eind:
        fouten.append(f"{dag.datum.strftime('%d-%m')}: valt buiten de gekozen periode")
    dagen.append(dag)

gezien = set()
for dag in dagen:
    if dag.datum in gezien:
        fouten.append(f"{dag.datum.strftime('%d-%m')}: staat er twee keer in")
    gezien.add(dag.datum)

if fouten:
    st.error("Nog niet opgeslagen:\n\n" + "\n".join(f"- {f}" for f in dict.fromkeys(fouten)))
else:
    oud = [d.naar_dict() for d in opslag.in_periode(begin, eind)]
    if sorted((d.naar_dict() for d in dagen), key=lambda d: d["datum"]) != oud:
        opslag.vervang_periode(begin, eind, dagen)
        opslag.bewaar()

# ---------------------------------------------------------------- overzicht en mail
dagen.sort(key=lambda d: d.datum)
totaal = sum(d.uren() for d in dagen if not d.fouten())
c1, c2 = st.columns(2)
c1.metric("Dagen", len(dagen))
c2.metric("Uren", uren_tekst(totaal))

if dagen and not fouten:
    st.subheader("Mail aan Marinus")
    maand = eind.month if eind <= date.today() else date.today().month
    onderwerp = mail_onderwerp(maand)
    tekst = mail_tekst(dagen, maand, inst["aanhef"], inst["naam"])
    st.text_input("Onderwerp", onderwerp)
    st.code(tekst, language=None)
    mailto = f"mailto:{inst['ontvanger']}?subject={quote(onderwerp)}&body={quote(tekst)}"
    c1, c2 = st.columns(2)
    c1.link_button("Open in je mailprogramma", mailto, use_container_width=True)
    if c2.button("Markeer als verstuurd", use_container_width=True,
                 help="De volgende periode begint dan na de laatste dag in deze lijst."):
        inst["laatst_gemeld"] = dagen[-1].datum.isoformat()
        opslag.bewaar()
        ververs_editor()
        st.rerun()

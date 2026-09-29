"""Urenregistratie: concept uit de agenda, aanpassen, en de urenmail voor Marinus."""

from datetime import date, datetime, time
from urllib.parse import quote

import streamlit as st

from uren import agenda
from uren.core import (DAGEN, MAANDEN_KORT, PauzeRegel, Werkdag, dagen_uit_agenda,
                       mail_onderwerp, mail_tekst, standaard_periode, uren_tekst)
from uren.opslag import Opslag

st.set_page_config(page_title="Werkuren", page_icon="🕘", layout="centered",
                   initial_sidebar_state="collapsed")

st.markdown("""
<style>
.block-container {padding-top: 2rem; padding-bottom: 4rem; max-width: 720px;}
@media (max-width: 640px) {
  .block-container {padding: 1rem 0.9rem 4rem;}
  /* Twee velden naast elkaar houden op je telefoon (begin/eind, pauze van/tot). */
  [data-testid="stHorizontalBlock"] {flex-wrap: nowrap !important; gap: 0.75rem;}
  [data-testid="stColumn"] {min-width: 0 !important; flex: 1 1 0 !important; width: auto !important;}
}
.hero {background: linear-gradient(135deg, #0f766e, #134e4a); color: #fff;
       border-radius: 18px; padding: 1.2rem 1.4rem; margin-bottom: 1rem;}
.hero .titel {font-size: 0.85rem; opacity: 0.8; letter-spacing: 0.04em; text-transform: uppercase;}
.hero .periode {font-size: 1.25rem; font-weight: 600; margin: 0.15rem 0 0.9rem;}
.hero .stats {display: flex; gap: 2.2rem;}
.hero .num {font-size: 2.2rem; font-weight: 700; line-height: 1;}
.hero .lbl {font-size: 0.85rem; opacity: 0.8; margin-left: 0.35rem;}
[data-testid="stExpander"] details {border-radius: 12px;}
[data-testid="stExpander"] summary p {font-size: 1rem;}
.stTabs [data-baseweb="tab-list"] {gap: 0.5rem;}
.stTabs [data-baseweb="tab"] {font-size: 1rem; padding: 0.4rem 0.2rem;}
</style>
""", unsafe_allow_html=True)

opslag = Opslag()
inst = opslag.instellingen


def geheim(naam: str) -> str:
    try:
        return st.secrets.get(naam, "")
    except Exception:  # geen secrets.toml
        return ""


ical_url = geheim("ICAL_URL") or inst["ical_url"]


def tijd(s: str) -> time:
    return datetime.strptime(s, "%H:%M").time()


def pauzeregel() -> PauzeRegel:
    return PauzeRegel(inst["pauze_aan"], tijd(inst["pauze_van"]), tijd(inst["pauze_tot"]),
                      inst["pauze_weekdagen"])


def versie() -> int:
    return st.session_state.get("versie", 0)


def nieuwe_versie():
    """Laat alle formulieren opnieuw beginnen met de bewaarde waarden."""
    st.session_state["versie"] = versie() + 1


def bewaar_en_ververs():
    opslag.bewaar()
    nieuwe_versie()
    st.rerun()


def korte_datum(d: date) -> str:
    return f"{d.day} {MAANDEN_KORT[d.month - 1]}"


# ---------------------------------------------------------------- periode en overzicht
laatst = date.fromisoformat(inst["laatst_gemeld"]) if inst["laatst_gemeld"] else None
std_begin, std_eind = standaard_periode(laatst, date.today())
begin = st.session_state.get("begin", std_begin)
eind = st.session_state.get("eind", std_eind)
dagen = opslag.in_periode(begin, eind)
totaal = sum(d.uren() for d in dagen)

st.markdown(f"""
<div class="hero">
  <div class="titel">Werkuren</div>
  <div class="periode">{korte_datum(begin)} t/m {korte_datum(eind)} {eind.year}</div>
  <div class="stats">
    <div><span class="num">{len(dagen)}</span><span class="lbl">dagen</span></div>
    <div><span class="num">{uren_tekst(totaal)}</span><span class="lbl">uur</span></div>
  </div>
</div>
""", unsafe_allow_html=True)

tab_dagen, tab_mail, tab_inst = st.tabs(["Dagen", "Mail", "Instellingen"])

# ---------------------------------------------------------------- dagen
with tab_dagen:
    with st.expander("Periode wijzigen", icon=":material/date_range:"):
        c1, c2 = st.columns(2)
        st.session_state["begin"] = c1.date_input("Van", begin, format="DD-MM-YYYY")
        st.session_state["eind"] = c2.date_input("Tot en met", eind, format="DD-MM-YYYY")
        if laatst:
            st.caption(f"Laatst gemelde werkdag: {korte_datum(laatst)} {laatst.year}")
        if (st.session_state["begin"], st.session_state["eind"]) != (begin, eind):
            st.rerun()

    ics_bestand = None
    if not ical_url:
        st.info("Koppel je agenda bij **Instellingen**, of upload hieronder een .ics-export.",
                icon=":material/link:")
        ics_bestand = st.file_uploader("Agenda-export (.ics)", type="ics")
    if st.button("Concept uit agenda halen", type="primary", icon=":material/event_upcoming:",
                 use_container_width=True, disabled=not (ical_url or ics_bestand)):
        try:
            ics = ics_bestand.getvalue() if ics_bestand else agenda.haal_ics(ical_url)
            blokken = agenda.werkblokken(ics, begin, eind, inst["zoekwoord"])
        except Exception as fout:  # netwerk of kapot bestand
            st.error(f"Agenda lezen lukte niet: {fout}")
        else:
            nieuw = [d for d in dagen_uit_agenda(blokken, pauzeregel())
                     if d.datum not in opslag.dagen]
            for dag in nieuw:
                opslag.dagen[dag.datum] = dag
            st.session_state["melding"] = (
                f"{len(nieuw)} {'dag' if len(nieuw) == 1 else 'dagen'} uit je agenda toegevoegd."
                if nieuw else "Geen nieuwe werkdagen in je agenda gevonden.")
            bewaar_en_ververs()
    if melding := st.session_state.pop("melding", None):
        st.toast(melding, icon=":material/check_circle:")
    st.caption("Dagen die al in de lijst staan worden niet overschreven.")

    if not dagen:
        st.markdown("Nog geen dagen in deze periode.")

    def dag_formulier(dag: Werkdag | None):
        """Formulier om een dag aan te passen, of een nieuwe toe te voegen (dag=None)."""
        sleutel = f"{dag.datum if dag else 'nieuw'}-{versie()}"
        with st.form(f"form-{sleutel}", border=False):
            datum = st.date_input("Datum", dag.datum if dag else date.today(),
                                  format="DD-MM-YYYY", key=f"datum-{sleutel}")
            c1, c2 = st.columns(2)
            b = c1.time_input("Begin", dag.begin if dag else time(9), step=900, key=f"b-{sleutel}")
            e = c2.time_input("Eind", dag.eind if dag else time(17), step=900, key=f"e-{sleutel}")
            met_pauze = st.toggle("Pauze", dag.heeft_pauze() if dag else False, key=f"p-{sleutel}")
            c1, c2 = st.columns(2)
            pv = c1.time_input("Pauze van", dag.pauze_van if dag and dag.pauze_van else time(12),
                               step=900, key=f"pv-{sleutel}")
            pt = c2.time_input("Pauze tot", dag.pauze_tot if dag and dag.pauze_tot else time(13),
                               step=900, key=f"pt-{sleutel}")
            c1, c2 = st.columns(2)
            opslaan = c1.form_submit_button("Opslaan" if dag else "Toevoegen", type="primary",
                                            icon=":material/check:", use_container_width=True)
            weg = dag and c2.form_submit_button("Verwijderen", icon=":material/delete:",
                                                use_container_width=True)
        if weg:
            del opslag.dagen[dag.datum]
            st.session_state["melding"] = f"{dag.kop()} verwijderd."
            bewaar_en_ververs()
        if opslaan:
            nieuw = Werkdag(datum, b, e, pv if met_pauze else None, pt if met_pauze else None,
                            dag.bron if dag else "handmatig")
            fouten = nieuw.fouten()
            if datum in opslag.dagen and (not dag or datum != dag.datum):
                fouten.append(f"{nieuw.kop()} staat er al in; pas die dag aan")
            if fouten:
                st.error("Niet opgeslagen: " + "; ".join(fouten) + ".")
                return
            if dag:
                del opslag.dagen[dag.datum]
            opslag.dagen[datum] = nieuw
            st.session_state["melding"] = f"{nieuw.kop()} opgeslagen."
            bewaar_en_ververs()

    for dag in dagen:
        label = f"**{dag.kop()}**  ·  {dag.tijden().replace(' ', ', ')}  ·  **{uren_tekst(dag.uren())} u**"
        icoon = ":material/event:" if dag.bron == "agenda" else ":material/edit:"
        with st.expander(label, icon=icoon):
            dag_formulier(dag)

    with st.expander("Dag toevoegen", icon=":material/add:"):
        dag_formulier(None)

# ---------------------------------------------------------------- mail
with tab_mail:
    if not dagen:
        st.markdown("Voeg eerst dagen toe.")
    else:
        maand = dagen[-1].datum.month
        onderwerp = mail_onderwerp(maand)
        tekst = mail_tekst(dagen, maand, inst["aanhef"], inst["naam"])
        st.markdown(f"**Aan:** {inst['ontvanger']}  \n**Onderwerp:** {onderwerp}")
        st.code(tekst, language=None, wrap_lines=True)
        st.caption("Kopieer de tekst met het knopje rechtsboven, of open hem direct in je mail.")
        mailto = f"mailto:{inst['ontvanger']}?subject={quote(onderwerp)}&body={quote(tekst)}"
        st.link_button("Open in je mail-app", mailto, type="primary", icon=":material/mail:",
                       use_container_width=True)
        if st.button("Markeer als verstuurd", icon=":material/done_all:", use_container_width=True,
                     help="De volgende periode begint dan na de laatste dag in deze lijst."):
            inst["laatst_gemeld"] = dagen[-1].datum.isoformat()
            st.session_state.pop("begin", None)
            st.session_state.pop("eind", None)
            st.session_state["melding"] = "Gemarkeerd als verstuurd. De volgende periode staat klaar."
            bewaar_en_ververs()

# ---------------------------------------------------------------- instellingen
with tab_inst:
    with st.form("instellingen"):
        st.markdown("**Agenda**")
        if geheim("ICAL_URL"):
            st.caption("Je agenda-link is ingesteld via de secrets van de app.")
            url = inst["ical_url"]
        else:
            url = st.text_input(
                "Geheime iCal-link", inst["ical_url"], type="password",
                help="Google Agenda → Instellingen → je agenda → 'Geheim adres in iCal-indeling'.")
        zoekwoord = st.text_input("Titel van werkafspraken", inst["zoekwoord"])
        st.markdown("**Mail**")
        aanhef = st.text_input("Aanhef", inst["aanhef"])
        naam = st.text_input("Ondertekening", inst["naam"])
        ontvanger = st.text_input("Mail naar", inst["ontvanger"])
        st.markdown("**Standaardpauze in het concept**")
        pauze_aan = st.toggle("Pauze toevoegen als de agenda er geen heeft", inst["pauze_aan"])
        c1, c2 = st.columns(2)
        pauze_van = c1.time_input("Van", tijd(inst["pauze_van"]), step=900)
        pauze_tot = c2.time_input("Tot", tijd(inst["pauze_tot"]), step=900)
        weekdagen = st.multiselect("Op", list(range(7)), inst["pauze_weekdagen"],
                                   format_func=lambda i: DAGEN[i])
        if st.form_submit_button("Opslaan", type="primary", use_container_width=True):
            inst.update(ical_url=url.strip(), zoekwoord=zoekwoord, aanhef=aanhef,
                        naam=naam, ontvanger=ontvanger, pauze_aan=pauze_aan,
                        pauze_van=pauze_van.strftime("%H:%M"),
                        pauze_tot=pauze_tot.strftime("%H:%M"), pauze_weekdagen=weekdagen)
            st.session_state["melding"] = "Instellingen opgeslagen."
            bewaar_en_ververs()

    st.markdown("**Back-up**")
    st.download_button("Download alle uren", opslag.als_json(), icon=":material/download:",
                       file_name=f"uren-{date.today().isoformat()}.json",
                       mime="application/json", use_container_width=True)
    backup = st.file_uploader("Zet een back-up terug", type="json")
    if backup and st.button("Terugzetten", use_container_width=True):
        opslag.laad(backup.getvalue().decode("utf-8"))
        st.session_state["melding"] = "Back-up teruggezet."
        bewaar_en_ververs()

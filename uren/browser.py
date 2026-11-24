"""Gegevens bewaren in de browser (localStorage) van de gebruiker.

Zo heeft iedereen die de app opent zijn eigen uren en instellingen, zonder
account. Ze blijven bewaard als de app op de server herstart, maar alleen op
het apparaat en in de browser waarin ze zijn ingevoerd.
"""

from __future__ import annotations

import streamlit as st

_JS = """
export default function(component) {
  const { data, setStateValue } = component;
  const SLEUTEL = "uurappi";
  if (!data) return;
  if (data.bewaar !== null && data.bewaar !== undefined
      && window.__uurappiVersie !== data.versie) {
    try {
      if (data.bewaar === "") localStorage.removeItem(SLEUTEL);
      else localStorage.setItem(SLEUTEL, data.bewaar);
      window.__uurappiVersie = data.versie;
    } catch (e) { /* privévenster of opslag geblokkeerd */ }
  }
  if (data.laden) {
    let inhoud = "", ok = true;
    try { inhoud = localStorage.getItem(SLEUTEL) || ""; } catch (e) { ok = false; }
    setStateValue("geladen", { inhoud: inhoud, ok: ok, t: Date.now() });
  }
}
"""

_component = st.components.v2.component("uurappi_browseropslag", js=_JS)


def _niets():
    pass


def synchroniseer(inhoud: str | None, versie: int) -> dict | None:
    """Plaats de opslag-component; precies één keer per run aanroepen.

    Met inhoud=None vraagt hij de bewaarde gegevens op. Het resultaat
    ({"inhoud": str, "ok": bool}) komt na een automatische herhaling van het
    script; tot die tijd geeft hij None terug. Met een inhoud schrijft hij die
    naar de browser zodra versie verandert; "" wist de gegevens.
    """
    resultaat = _component(key="uurappi_opslag",
                           data={"laden": inhoud is None, "bewaar": inhoud, "versie": versie},
                           on_geladen_change=_niets)
    return resultaat.geladen if inhoud is None else None

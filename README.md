# Uurappi

Streamlit-app om je gewerkte uren bij te houden en de maandelijkse urenmail voor Marinus te maken.

## Zo werkt het

1. **Concept uit je agenda.** De app haalt alle afspraken met `werken` in de titel uit je Google Agenda
   voor de gekozen maand (van de dag na de laatste vrijdag van vorige maand t/m de laatste vrijdag
   van deze maand, want dan lever je je uren in). Twee afspraken op één dag (bijv. 9-12 en 13-17) worden één dag met pauze.
   Op zaterdag komt er standaard een pauze van 12:00 tot 13:00 bij (aan te passen in de instellingen).
2. **Aanpassen.** In de tabel pas je tijden aan, haal je een pauze weg (beide pauzevelden leeg),
   voeg je een dag toe (+ onder de tabel) of verwijder je er een. Fouten, zoals een eindtijd voor de
   begintijd of een dubbele datum, worden meteen gemeld.
3. **Mail.** Onderaan staat de mail in hetzelfde formaat als je altijd stuurt. Kopieer hem, of open hem
   in je mailprogramma.

## Agenda koppelen

Google Agenda → Instellingen → kies je agenda → *Geheim adres in iCal-indeling*. Plak die link bij
*Instellingen* in de app. Zonder link kun je ook een `.ics`-export uploaden.

## Delen met collega's

Iedereen gebruikt dezelfde link. Bij het eerste bezoek vult iemand zijn naam, ontvanger en eigen
iCal-link in. Alles wordt bewaard in de browser van die persoon (`localStorage`, zie `uren/browser.py`),
niet op de server, dus niemand ziet de uren of agenda van een ander. Uitleg voor collega's staat in
[HANDLEIDING.md](HANDLEIDING.md).

## Online zetten (Streamlit Community Cloud)

1. Ga naar [share.streamlit.io](https://share.streamlit.io) en log in met GitHub.
2. Klik op *Create app*, kies repo `v6-Lars-van-Manen/uurappi`, branch `main` en bestand `uurappi.py`.
3. Zet onder *Settings → Sharing* de app op **Public**, zodat collega's hem zonder account kunnen openen.
   Zet geen persoonlijke agenda-link in de secrets: de app gebruikt die niet meer, omdat iedereen met de
   link hem anders zou krijgen.
4. Optioneel: kies onder *Settings → General* een makkelijk adres, bijv. `werkuren-hvm.streamlit.app`.
5. Open het adres op je telefoon en kies *Zet op beginscherm* (iPhone: deelknop; Android: menu ⋮).

## Opslag

Uren en instellingen staan in de browser van de gebruiker, per apparaat. Ze blijven bewaard als de app
op de server herstart, maar gaan verloren als je browsergegevens wist. Download daarom af en toe een
back-up via *Instellingen*.

## Draaien en testen

```
pip install -r requirements.txt
streamlit run uurappi.py
pip install pytest && pytest
```

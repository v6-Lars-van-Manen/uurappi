# Uurappi

Streamlit-app om je gewerkte uren bij te houden en de maandelijkse urenmail voor Marinus te maken.

## Zo werkt het

1. **Concept uit je agenda.** De app haalt alle afspraken met `werken` in de titel uit je Google Agenda
   voor de gekozen periode. Twee afspraken op één dag (bijv. 9-12 en 13-17) worden één dag met pauze.
   Op zaterdag komt er standaard een pauze van 12:00 tot 13:00 bij (aan te passen in de instellingen).
2. **Aanpassen.** In de tabel pas je tijden aan, haal je een pauze weg (beide pauzevelden leeg),
   voeg je een dag toe (+ onder de tabel) of verwijder je er een. Fouten, zoals een eindtijd voor de
   begintijd of een dubbele datum, worden meteen gemeld.
3. **Mail.** Onderaan staat de mail in hetzelfde formaat als je altijd stuurt. Kopieer hem, of open hem
   in je mailprogramma. Klik daarna op *Markeer als verstuurd*: de volgende periode begint dan vanzelf
   op de dag na de laatste dag in de lijst.

## Agenda koppelen

Google Agenda → Instellingen → kies je agenda → *Geheim adres in iCal-indeling*. Plak die link in de
instellingen van de app. Zonder link kun je ook een `.ics`-export uploaden.

## Opslag

Alles wordt bewaard in `data/uren.json` (pad aan te passen met `UURAPPI_DATA`). Op Streamlit Community
Cloud gaat dat bestand verloren bij een herstart, dus download af en toe een back-up via de zijbalk.

## Draaien en testen

```
pip install -r requirements.txt
streamlit run uurappi.py
pip install pytest && pytest
```

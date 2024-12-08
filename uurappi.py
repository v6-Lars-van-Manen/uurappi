import streamlit as st
from datetime import datetime

# Initialiseer session state
if "totaal_uren_maand" not in st.session_state:
    st.session_state["totaal_uren_maand"] = 0.0
if "lijst" not in st.session_state:
    st.session_state["lijst"] = []
if "dag_naam" not in st.session_state:
    st.session_state["dag_naam"] = None
if "dagen" not in st.session_state:
    st.session_state["dagen"] = 0

# Functie om uren te tonen
def show_uren():
    if st.session_state["lijst"]:
        for i in st.session_state["lijst"]:
            st.write(i)
        st.session_state["dagen"] = len(st.session_state["lijst"])
        st.write("")
        st.write("Totaal aantal uren = ", st.session_state["totaal_uren_maand"])  # Correcte sleutelnaam
        st.write(f"Totaal aantal dagen = {st.session_state['dagen']}")
    else:
        st.write("Nog geen uren toegevoegd.")

# Functie om een datum te kiezen
def dag():
    st.write("Kies een datum:")
    datum_input = st.date_input("Selecteer een datum", key="datum_input")
    if datum_input:
        st.session_state["dag_naam"] = datum_input.strftime("%A %d %b")
        st.write(f"Gekozen datum: {st.session_state['dag_naam']}")

# Functie om alles te resetten
def reset_data():
    st.session_state["totaal_uren_maand"] = 0.0
    st.session_state["lijst"] = []
    st.session_state["dag_naam"] = None
    st.session_state["dagen"] = 0
    st.success("Alle gegevens zijn gewist!")

# Streamlit interface
st.title("Werkuren Berekening")


# Keuze tussen met of zonder pauze
st.header("Werkdag invoeren:")
dag_type = st.radio("Kies het type werkdag:", ["Met pauze", "Zonder pauze"], key="dag_type")
dag()

# Dynamische invoervelden afhankelijk van keuze
if dag_type == "Met pauze":
    begin_tijd = st.slider("Begin tijd:", 7.0, 21.0, 9.0, 0.5, key="begin_tijd_p")
    pauze_start = st.slider("Pauze begint om:", 11.0, 20.0, 12.0, 0.5, key="pauze_start")
    pauze_eind = st.slider("Pauze eindigt om:", 11.0, 20.0, 13.0, 0.5, key="pauze_eind")
    eind_tijd = st.slider("Eind tijd:", 7.0, 22.0, 17.0, 0.5, key="eind_tijd_p")

    if st.button("Voeg uren toe"):
        if st.session_state["dag_naam"]:
            gewerkte_uren = (eind_tijd - begin_tijd) - (pauze_eind - pauze_start)
            st.session_state["lijst"].append(
                f"{st.session_state['dag_naam']} {begin_tijd:.2f}-{eind_tijd:.2f} "
                f"Pauze {pauze_start:.2f}-{pauze_eind:.2f} = {gewerkte_uren:.2f} uur"
            )
            st.session_state["totaal_uren_maand"] += gewerkte_uren
            st.success("Uren toegevoegd!")
        else:
            st.error("Selecteer eerst een datum!")
else:
    begin_tijd = st.slider("Begin tijd:", 7.0, 21.0, 15.0, 0.5, key="begin_tijd_np")
    eind_tijd = st.slider("Eind tijd:", 7.0, 21.0, 22.0, 0.5, key="eind_tijd_np")

    if st.button("Voeg uren toe"):
        if st.session_state["dag_naam"]:
            gewerkte_uren = eind_tijd - begin_tijd
            st.session_state["lijst"].append(
                f"{st.session_state['dag_naam']} {begin_tijd:.2f}-{eind_tijd:.2f} = {gewerkte_uren:.2f} uur"
            )
            st.session_state["totaal_uren_maand"] += gewerkte_uren
            st.success("Uren toegevoegd!")
        else:
            st.error("Selecteer eerst een datum!")

# Toon uren
st.header("Gewerkte Uren")
show_uren()


# Reset gegevens
st.header("Reset gegevens")
if st.button("Wis alle gegevens"):
    reset_data()

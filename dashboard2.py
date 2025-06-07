import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os
from datetime import datetime

st.set_page_config(layout="wide")

DATA_PATH = "Waterkwaliteit.csv"

# ---------- 1. Data inladen ----------
@st.cache_data
def load_data():
    if os.path.exists(DATA_PATH):
        df = pd.read_csv(DATA_PATH)
        df['Datum'] = pd.to_datetime(df['Meetdag'], format='%Y-%m-%d', errors='coerce')
    else:
        df = pd.DataFrame()
    return df

# ---------- 2. Hoofdpagina met kaart ----------
def kaartpagina(df):
    st.sidebar.header("Filter opties")
    if df.empty:
        st.warning("Nog geen meetdata beschikbaar.")
        return

    unieke_dagen = df['Datum'].dropna().dt.date.unique()
    datum_selectie = st.sidebar.date_input("Kies meetdag", min_value=min(unieke_dagen), max_value=max(unieke_dagen))
    waardes = st.sidebar.multiselect("Waardes om te tonen", ['PH', 'Temperatuur', 'ORP', 'EC', 'CF', 'TDS', 'Humidity', 'Buitentemperatuur'])

    filtered_df = df[df['Datum'].dt.date == datum_selectie]

    st.title("Waterkwaliteit Meetdashboard")
    st.markdown(f"### Meetpunten op {datum_selectie.strftime('%d-%m-%Y')}")

    kaart = folium.Map(location=[52.36, 4.9], zoom_start=13)

    for _, row in filtered_df.iterrows():
        try:
            lat, lon = map(float, str(row['Coordinaten']).split(','))
        except:
            continue

        # Bereken kleur op basis van PH
        kleur = "gray"
        try:
            ph = float(row['PH'])
            if 6.5 <= ph <= 8.5:
                kleur = "green"
            elif 6.0 <= ph < 6.5 or 8.5 < ph <= 9.0:
                kleur = "orange"
            else:
                kleur = "red"
        except:
            pass

        popup_text = f"<b>{row['Locatie']}</b><br>"
        for col in waardes:
            if col in row and pd.notna(row[col]):
                popup_text += f"{col}: {row[col]}<br>"

        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_text, max_width=300),
            icon=folium.Icon(color=kleur)
        ).add_to(kaart)

    st_folium(kaart, width=900, height=600)

# ---------- 3. Data toevoegen ----------
def invoerpagina():
    st.title("Voeg nieuwe meting toe")

    with st.form("meet_formulier"):
        meetdag = st.date_input("Meetdag", value=datetime.today())
        tijdstip = st.text_input("Tijdstip (bv. 14.00-14.15)")
        locatie = st.text_input("Locatie")
        coordinaten = st.text_input("Coördinaten (lat, lon)", placeholder="52.36, 4.90")
        ph = st.number_input("pH", step=0.01, format="%.2f")
        temperatuur = st.number_input("Temperatuur (°C)", step=0.1)
        orp = st.number_input("ORP", step=1)
        ec = st.number_input("EC", step=0.01)
        cf = st.number_input("CF", step=0.1)
        tds = st.number_input("TDS", step=1)
        humidity = st.text_input("Luchtvochtigheid (bv. 35%)")
        zon = st.selectbox("Zon / Schaduw", ["zon", "schaduw"])
        meetpunt = st.selectbox("Type meetpunt", ["kade", "steiger"])
        buitentemp = st.number_input("Buitentemperatuur", step=0.1)

        submitted = st.form_submit_button("Opslaan")

        if submitted:
            nieuwe_rij = {
                'Meetdag': meetdag.strftime('%Y-%m-%d'),
                'Tijdstip': tijdstip,
                'Locatie': locatie,
                'Coordinaten': coordinaten,
                'PH': ph,
                'Temperatuur': temperatuur,
                'ORP': orp,
                'EC': ec,
                'CF': cf,
                'TDS': tds,
                'Humidity': humidity,
                'zon/schaduw': zon,
                'meetpunt': meetpunt,
                'Buitentemperatuur': buitentemp
            }

            if os.path.exists(DATA_PATH):
                df = pd.read_csv(DATA_PATH)
                df = pd.concat([df, pd.DataFrame([nieuwe_rij])], ignore_index=True)
            else:
                df = pd.DataFrame([nieuwe_rij])

            df.to_csv(DATA_PATH, index=False)
            st.success("Meting opgeslagen!")

# ---------- 4. Tabs ----------
tab1, tab2 = st.tabs(["📍 Dashboard", "➕ Meting toevoegen"])

with tab1:
    kaartpagina(load_data())

with tab2:
    invoerpagina()

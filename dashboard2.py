import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os

st.set_page_config(layout="wide", page_title="Waterkwaliteit Dashboard")

DATA_FILE = "Waterkwaliteit.xlsx"

# ---------- Data inladen ----------
@st.cache_data
def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_excel(DATA_FILE)
        df['Datum'] = pd.to_datetime(df['Meetdag'], dayfirst=True, errors='coerce')
        df['Datum_only'] = df['Datum'].dt.date  # voor vergelijking met date input
        return df
    else:
        return pd.DataFrame()

# ---------- Data toevoegen ----------
def append_data(new_row):
    df_existing = load_data()
    df_new = pd.DataFrame([new_row])
    df_all = pd.concat([df_existing, df_new], ignore_index=True)
    df_all.to_excel(DATA_FILE, index=False)

# ---------- Tabs ----------
tab1, tab2 = st.tabs(["🌍 Dashboard", "📋 Data toevoegen"])

# ---------- TAB 1: DASHBOARD ----------
with tab1:
    df = load_data()

    if df.empty:
        st.warning("Geen meetdata beschikbaar.")
    else:
        st.sidebar.header("Filter opties")
        unieke_data = sorted(df['Datum_only'].dropna().unique())
        geselecteerde_datum = st.sidebar.date_input(
            "Kies meetdag",
            value=unieke_data[-1] if unieke_data else None,
            min_value=min(unieke_data),
            max_value=max(unieke_data)
        )

        waardes = st.sidebar.multiselect(
            "Waardes om te tonen", 
            ['PH', 'Temperatuur', 'ORP', 'EC', 'CF', 'TDS', 'Humidity', 'Buitentemperatuur'],
            default=['PH']
        )

        df_filtered = df[df['Datum_only'] == geselecteerde_datum]

        st.title("Waterkwaliteit Meetdashboard")
        st.markdown(f"### Meetpunten op {geselecteerde_datum.strftime('%d-%m-%Y')}")

        kaart = folium.Map(location=[52.36, 4.9], zoom_start=13)

        def bepaal_kleur(ph):
            try:
                if pd.isna(ph): return "gray"
                ph = float(ph)
                if 6.5 <= ph <= 8.5:
                    return "green"
                elif 6.0 <= ph < 6.5 or 8.5 < ph <= 9.0:
                    return "orange"
                else:
                    return "red"
            except:
                return "gray"

        for _, row in df_filtered.iterrows():
            try:
                lat_str, lon_str = str(row['Coordinaten']).split(',')
                lat, lon = float(lat_str.strip()), float(lon_str.strip())
            except:
                continue

            popup = f"<b>{row['Locatie']}</b><br>"
            for col in waardes:
                if col in row and pd.notna(row[col]):
                    popup += f"{col}: {row[col]}<br>"

            kleur = bepaal_kleur(row.get('PH'))

            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup, max_width=300),
                icon=folium.Icon(color=kleur)
            ).add_to(kaart)

        st_folium(kaart, width=900, height=600)

# ---------- TAB 2: DATA TOEVOEGEN ----------
with tab2:
    st.header("Nieuwe meetdata toevoegen")

    with st.form("meetdata_form"):
        datum = st.date_input("Meetdag (datum)")
        tijd = st.text_input("Tijdstip")
        locatie = st.text_input("Locatie")
        coordinaten = st.text_input("Coördinaten (lat, lon)")
        ph = st.number_input("PH", step=0.01)
        temp = st.number_input("Temperatuur (°C)", step=0.1)
        orp = st.number_input("ORP", step=1)
        ec = st.number_input("EC", step=0.01)
        cf = st.number_input("CF", step=0.01)
        tds = st.number_input("TDS", step=1)
        humidity = st.text_input("Luchtvochtigheid (%)")
        zon_schaduw = st.selectbox("Zon/schaduw", ["zon", "schaduw"])
        meetpunt = st.selectbox("Meetpunt type", ["kade", "steiger"])
        buitentemp = st.number_input("Buitentemperatuur (°C)", step=0.5)

        submitted = st.form_submit_button("Voeg toe")

        if submitted:
            nieuwe_waarde = {
                "Meetdag": datum.strftime("%d-%m-%Y"),
                "Tijdstip": tijd,
                "Locatie": locatie,
                "Coordinaten": coordinaten,
                "PH": ph,
                "Temperatuur": temp,
                "ORP": orp,
                "EC": ec,
                "CF": cf,
                "TDS": tds,
                "Humidity": humidity,
                "zon/schaduw": zon_schaduw,
                "meetpunt": meetpunt,
                "Buitentemperatuur": buitentemp,
            }
            append_data(nieuwe_waarde)
            st.success("Nieuwe meetdata toegevoegd! Bekijk het in het dashboard-tab.")

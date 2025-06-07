import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import re
from datetime import datetime

st.set_page_config(layout="wide")

CSV_FILE = "Waterkwaliteit_data.csv"

# ---------- 1. Data inladen ----------
@st.cache_data
def load_data():
    try:
        df = pd.read_csv(CSV_FILE)
        # Datum-kolom aanmaken
        df['Datum'] = pd.to_datetime(df['Meetdag'], format='%d-%m', errors='coerce')
    except FileNotFoundError:
        df = pd.DataFrame(columns=[
            'Meetdag', 'Tijdstip', 'Locatie', 'Coordinaten', 'PH', 'Temperatuur',
            'ORP', 'EC', 'CF', 'TDS', 'Humidity', 'zon/schaduw', 'meetpunt', 'Buitentemperatuur', 'Datum'
        ])
    return df


df = load_data()

# ---------- Tabs maken ----------
tab1, tab2 = st.tabs(["Dashboard", "Nieuwe meting toevoegen"])

with tab1:
    # ---------- 2. Sidebar filters ----------
    st.sidebar.header("Filter opties")
    if df.empty:
        st.warning("Er zijn nog geen meetgegevens beschikbaar.")
    else:
        datum_selectie = st.sidebar.date_input("Kies meetdag", df['Datum'].min())
        waardes = st.sidebar.multiselect(
            "Waardes om te tonen",
            ['PH', 'Temperatuur', 'ORP', 'EC', 'CF', 'TDS', 'Humidity', 'Buitentemperatuur'],
            default=['PH', 'Temperatuur']
        )

        # ---------- 3. Filter op geselecteerde datum ----------
        filtered_df = df[df['Datum'] == pd.to_datetime(datum_selectie)]

        # ---------- 4. Kaart bouwen ----------
        st.title("Waterkwaliteit Meetdashboard")
        st.markdown(f"### Meetpunten op {datum_selectie.strftime('%d-%m-%Y')}")

        kaart = folium.Map(location=[52.36, 4.9], zoom_start=13)

        for _, row in filtered_df.iterrows():
            popup_text = f"<b>{row['Locatie']}</b><br>"
            for col in waardes:
                if col in row and pd.notna(row[col]):
                    popup_text += f"{col}: {row[col]}<br>"

            try:
                lat_str, lon_str = re.split(r',\s*', str(row['Coordinaten']))
                lat = float(lat_str)
                lon = float(lon_str)
            except:
                continue

            kleur = "gray"
            try:
                ph_val = float(str(row['PH']).replace(',', '.'))
                if 6.5 <= ph_val <= 8.5:
                    kleur = "green"
                elif 5.5 <= ph_val < 6.5 or 8.5 < ph_val <= 9.5:
                    kleur = "orange"
                else:
                    kleur = "red"
            except:
                kleur = "gray"

            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_text, max_width=300),
                icon=folium.Icon(color=kleur)
            ).add_to(kaart)

        st_folium(kaart, width=900, height=600)

with tab2:
    st.markdown("### Voeg nieuwe meting toe")

    with st.form("meet_data_form"):
        meetdag = st.date_input("Meetdag", datetime.today())
        tijdstip = st.text_input("Tijdstip (bijv. 13.00-13.15)")
        locatie = st.text_input("Locatie")
        coordinaten = st.text_input("Coördinaten (bijv. 52.36, 4.90)")
        ph = st.number_input("pH", min_value=0.0, max_value=14.0, step=0.01, format="%.2f")
        temperatuur = st.number_input("Temperatuur (°C)", format="%.1f")
        orp = st.number_input("ORP", format="%.0f")
        ec = st.number_input("EC", format="%.2f")
        cf = st.number_input("CF", format="%.1f")
        tds = st.number_input("TDS", format="%.0f")
        humidity = st.text_input("Humidity (bijv. 30%)")
        zon_schaduw = st.selectbox("Zon/schaduw", ['zon', 'schaduw'])
        meetpunt = st.selectbox("Meetpunt", ['kade', 'steiger'])
        buitentemp = st.number_input("Buitentemperatuur", format="%.0f")

        submitted = st.form_submit_button("Voeg toe aan dataset")

        if submitted:
            nieuwe_rij = {
                'Meetdag': meetdag.strftime('%d-%m'),
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
                'zon/schaduw': zon_schaduw,
                'meetpunt': meetpunt,
                'Buitentemperatuur': buitentemp,
                'Datum': meetdag
            }

            nieuwe_df = pd.DataFrame([nieuwe_rij])

            try:
                bestaande_df = pd.read_csv(CSV_FILE)
                updated_df = pd.concat([bestaande_df, nieuwe_df], ignore_index=True)
            except FileNotFoundError:
                updated_df = nieuwe_df

            updated_df.to_csv(CSV_FILE, index=False)
            st.success("Nieuwe meting toegevoegd! Ga terug naar het Dashboard om te zien.")


import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import re
import os

st.set_page_config(layout="wide")

EXCEL_PATH = "Waterkwaliteit.xlsx"

# ---------- 1. Data inladen ----------
def load_data():
    if os.path.exists(EXCEL_PATH):
        df = pd.read_excel(EXCEL_PATH)
        df.columns = df.columns.str.strip()
        df['Datum'] = pd.to_datetime(df['Meetdag'], dayfirst=True, errors='coerce')
        return df
    else:
        cols = ['Locatie', 'Meetdag', 'Datum', 'Coordinaten', 'PH', 'Temperatuur', 'ORP', 'EC', 'CF', 'TDS', 'Humidity', 'Buitentemperatuur']
        return pd.DataFrame(columns=cols)

# Data initialiseren
if 'data' not in st.session_state:
    st.session_state['data'] = load_data()

df = st.session_state['data']

tab1, tab2 = st.tabs(["Kaart", "Nieuwe meting"])

with tab1:
    st.sidebar.header("Filter opties")
    min_datum = df['Datum'].min() if not df.empty else pd.Timestamp.today()
    datum_selectie = st.sidebar.date_input("Kies meetdag", min_datum)
    waardes = st.sidebar.multiselect(
        "Waardes om te tonen",
        ['PH', 'Temperatuur', 'ORP', 'EC', 'CF', 'TDS', 'Humidity', 'Buitentemperatuur'],
        default=['PH', 'Temperatuur']
    )

    filtered_df = df[df['Datum'] == pd.to_datetime(datum_selectie)]

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
    st.header("Nieuwe meting toevoegen")

    with st.form("meting_form"):
        locatie = st.text_input("Locatie", max_chars=50)
        datum = st.date_input("Meetdag")
        coordinaten = st.text_input("Coördinaten (lat, lon)", help="Bijv. 52.370216, 4.895168")

        ph = st.text_input("PH", help="Bijv. 7.2")
        temperatuur = st.text_input("Temperatuur", help="Bijv. 20.5")
        orp = st.text_input("ORP")
        ec = st.text_input("EC")
        cf = st.text_input("CF")
        tds = st.text_input("TDS")
        humidity = st.text_input("Humidity")
        buitentemperatuur = st.text_input("Buitentemperatuur")

        submitted = st.form_submit_button("Toevoegen")

        if submitted:
            try:
                lat_str, lon_str = re.split(r',\s*', coordinaten)
                lat = float(lat_str)
                lon = float(lon_str)
            except Exception:
                st.error("Ongeldige coördinaten. Gebruik formaat: lat, lon (bijv. 52.370216, 4.895168)")
                st.stop()

            nieuwe_meting = {
                'Locatie': locatie,
                'Meetdag': datum.strftime('%d-%m-%Y'),
                'Datum': pd.Timestamp(datum),
                'Coordinaten': coordinaten,
                'PH': ph,
                'Temperatuur': temperatuur,
                'ORP': orp,
                'EC': ec,
                'CF': cf,
                'TDS': tds,
                'Humidity': humidity,
                'Buitentemperatuur': buitentemperatuur,
            }

            try:
                df = st.session_state['data']
                df = pd.concat([df, pd.DataFrame([nieuwe_meting])], ignore_index=True)

                df_to_save = df.copy()
                df_to_save['Meetdag'] = df_to_save['Meetdag'].astype(str)
                df_to_save.drop(columns=['Datum'], inplace=True, errors='ignore')
                df_to_save.to_excel(EXCEL_PATH, index=False)

                # Herladen data na opslaan
                st.session_state['data'] = load_data()

                st.success("Nieuwe meting toegevoegd en opgeslagen!")

            except Exception as e:
                st.error(f"Fout bij opslaan: {e}")

import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime
import os

# ---------- Configuratie ----------
ORIGINELE_DATA = "Waterkwaliteit.xlsx"
NIEUWE_METINGEN = "nieuwe_metingen.csv"

st.set_page_config(layout="wide")
st.title("📍 Waterkwaliteit Meetdashboard")

# ---------- Data inladen ----------
@st.cache_data
def load_data():
    df_orig = pd.read_excel(ORIGINELE_DATA)

    # Zet 'Meetdag' om naar volledige datum met standaardjaar
    df_orig['Datum'] = pd.to_datetime(df_orig['Meetdag'].astype(str) + "-2025", format='%d-%b-%Y', errors='coerce')

    if os.path.exists(NIEUWE_METINGEN):
        df_nieuw = pd.read_csv(NIEUWE_METINGEN)
        df_nieuw['Datum'] = pd.to_datetime(df_nieuw['Meetdag'], errors='coerce')
        df = pd.concat([df_orig, df_nieuw], ignore_index=True)
    else:
        df = df_orig

    return df

df = load_data()

# ---------- Tabs ----------
tab1, tab2 = st.tabs(["📊 Dashboard", "➕ Nieuwe meting toevoegen"])

# ---------- TAB 1: Dashboard ----------
with tab1:
    st.sidebar.header("📅 Filter opties")

    # Filteropties
    beschikbare_datums = df['Datum'].dropna().sort_values().unique()
    if len(beschikbare_datums) == 0:
        st.warning("Geen meetdata beschikbaar.")
    else:
        datum_selectie = st.sidebar.date_input(
            "Kies meetdag",
            value=beschikbare_datums[0],
            min_value=beschikbare_datums[0],
            max_value=beschikbare_datums[-1]
        )

        waardes = st.sidebar.multiselect(
            "Welke waardes wil je tonen?",
            ['PH', 'Temperatuur', 'ORP', 'EC', 'CF', 'TDS', 'Humidity', 'Buitentemperatuur'],
            default=['PH', 'Temperatuur']
        )

        filtered_df = df[df['Datum'] == pd.to_datetime(datum_selectie)]

        st.markdown(f"### Meetpunten op {datum_selectie.strftime('%d-%m-%Y')}")
        kaart = folium.Map(location=[52.36, 4.9], zoom_start=13)

        def bepaal_kleur(ph):
            try:
                ph = float(ph)
                if ph < 6.5 or ph > 9.0:
                    return "red"
                elif 6.5 <= ph <= 7.5:
                    return "green"
                else:
                    return "orange"
            except:
                return "gray"

        for _, row in filtered_df.iterrows():
            try:
                lat, lon = map(float, str(row['Coordinaten']).split(','))
                popup_text = f"<b>{row['Locatie']}</b><br>"
                for col in waardes:
                    if col in row and pd.notna(row[col]):
                        popup_text += f"{col}: {row[col]}<br>"

                marker_kleur = bepaal_kleur(row.get('PH', None))
                folium.Marker(
                    location=[lat, lon],
                    popup=folium.Popup(popup_text, max_width=300),
                    icon=folium.Icon(color=marker_kleur)
                ).add_to(kaart)
            except:
                continue

        st_folium(kaart, width=900, height=600)

# ---------- TAB 2: Formulier voor nieuwe meting ----------
with tab2:
    st.subheader("➕ Voeg een nieuwe meting toe")

    with st.form("nieuwe_meting_form"):
        meetdag = st.date_input("Datum")
        tijdstip = st.text_input("Tijdstip (bv. 14.00-14.15)")
        locatie = st.text_input("Locatie")
        coordinaten = st.text_input("Coördinaten (bv. 52.36, 4.9)")
        ph = st.number_input("pH", step=0.01)
        temp = st.number_input("Temperatuur (°C)", step=0.1)
        orp = st.number_input("ORP", step=1)
        ec = st.number_input("EC", step=0.01)
        cf = st.number_input("CF", step=0.01)
        tds = st.number_input("TDS", step=1)
        humidity = st.text_input("Luchtvochtigheid (bv. 40%)")
        zon_schaduw = st.selectbox("Zon/schaduw", ["zon", "schaduw"])
        meetpunt = st.text_input("Meetpunt (bv. steiger, kade)")
        buitentemp = st.number_input("Buitentemperatuur (°C)", step=0.1)

        submitted = st.form_submit_button("Meting opslaan")

        if submitted:
            nieuwe_data = pd.DataFrame([{
                "Meetdag": meetdag.strftime("%Y-%m-%d"),
                "Tijdstip": tijdstip,
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
                "Buitentemperatuur": buitentemp
            }])

            if os.path.exists(NIEUWE_METINGEN):
                bestaande = pd.read_csv(NIEUWE_METINGEN)
                gecombineerde = pd.concat([bestaande, nieuwe_data], ignore_index=True)
            else:
                gecombineerde = nieuwe_data

            gecombineerde.to_csv(NIEUWE_METINGEN, index=False)
            st.success("✅ Meting opgeslagen! Ga naar het dashboard om het resultaat te zien.")

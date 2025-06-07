import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import re

st.set_page_config(layout="wide")

# ---------- 1. Data inladen en voorbereiden ----------
@st.cache_data
def load_data():
    df = pd.read_excel("Waterkwaliteit.xlsx")

    # Datum kolom verwerken
    df['Datum'] = pd.to_datetime(df['Meetdag'], dayfirst=True, errors='coerce')
    return df

df = load_data()

# ---------- 2. Sidebar filters ----------
st.sidebar.header("Filter opties")
datum_selectie = st.sidebar.date_input("Kies meetdag", df['Datum'].min())

# Zoek automatisch welke waardes beschikbaar zijn (en geldig zijn)
mogelijke_waardes = ['pH', 'Temperatuur', 'ORP', 'EC', 'CF', 'TDS', 'Humidity', 'Buitentemperatuur']
beschikbare_waardes = [col for col in mogelijke_waardes if col in df.columns]

waardes = st.sidebar.multiselect("Waardes om te tonen", beschikbare_waardes, default=beschikbare_waardes)

# ---------- 3. Filter op geselecteerde datum ----------
filtered_df = df[df['Datum'] == pd.to_datetime(datum_selectie)]

# ---------- 4. Kaart weergeven ----------
st.title("🌊 Waterkwaliteit Meetdashboard")
st.markdown(f"### Meetpunten op {datum_selectie.strftime('%d-%m-%Y')}")

kaart = folium.Map(location=[52.36, 4.9], zoom_start=13)

for _, row in filtered_df.iterrows():
    popup_text = f"<b>{row['Locatie']}</b><br>"
    for col in waardes:
        if col in row and pd.notna(row[col]):
            popup_text += f"{col}: {row[col]}<br>"
    try:
        # Coördinaten splitsen en converteren
        lat_str, lon_str = re.split(r',\s*', str(row['Coordinaten']))
        lat, lon = float(lat_str.replace(',', '.')), float(lon_str.replace(',', '.'))
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_text, max_width=300)
        ).add_to(kaart)
    except Exception as e:
        st.warning(f"Kon coördinaten niet lezen voor '{row['Locatie']}': {e}")
        continue

# Toon kaart
st_folium(kaart, width=900, height=600)

# ---------- 5. Optionele datatabel ----------
with st.expander("📋 Bekijk meetgegevens"):
    st.dataframe(filtered_df[['Datum', 'Tijdstip', 'Locatie'] + waardes])

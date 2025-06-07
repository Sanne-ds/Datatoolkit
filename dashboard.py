import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import re

st.set_page_config(layout="wide")

# ---------- 1. Data inladen en voorbereiden ----------
@st.cache_data
def load_data():
    df = pd.read_excel("Waterkwaliteit DataToolkit.xlsx")

    # Datum kolom verwerken
    df['Datum'] = pd.to_datetime(df['Meetdag'], dayfirst=True, errors='coerce')

    # Coördinaten scheiden in Lat en Lon (komma's → punten)
    coords = df['Coordinaten'].astype(str).str.replace(",", ".")
    df[['Lat', 'Lon']] = coords.str.extract(r'([0-9.]+)[,\s]+([0-9.]+)').astype(float)

    # pH converteren van reeksen ("8,3-8,7") naar gemiddelde
    def extract_ph_mean(ph_val):
        if isinstance(ph_val, str):
            ph_val = ph_val.replace(",", ".")
            numbers = re.findall(r"[\d.]+", ph_val)
            if len(numbers) == 1:
                return float(numbers[0])
            elif len(numbers) == 2:
                return (float(numbers[0]) + float(numbers[1])) / 2
        return None

    df['pH'] = df['PH'].apply(extract_ph_mean)

    return df

df = load_data()

# ---------- 2. Sidebar filters ----------
st.sidebar.header("Filter opties")
datum_selectie = st.sidebar.date_input("Kies meetdag", df['Datum'].min())
waardes = st.sidebar.multiselect("Waardes om te tonen", ['pH', 'Temperatuur', 'ORP', 'EC', 'CF', 'TDS', 'Humidity', 'Buitentemperatuur'])

# ---------- 3. Filter op geselecteerde datum ----------
filtered_df = df[df['Datum'] == pd.to_datetime(datum_selectie)]

# ---------- 4. Kaart weergeven ----------
st.title("Waterkwaliteit Meetdashboard")
st.markdown(f"### Meetpunten op {datum_selectie.strftime('%d-%m-%Y')}")

kaart = folium.Map(location=[52.36, 4.9], zoom_start=13)

for _, row in filtered_df.iterrows():
    popup_text = f"<b>{row['Locatie']}</b><br>"
    for col in waardes:
        if col in row and pd.notna(row[col]):
            popup_text += f"{col}: {row[col]}<br>"
    folium.Marker(
        location=[row['Lat'], row['Lon']],
        popup=folium.Popup(popup_text, max_width=300)
    ).add_to(kaart)

st_folium(kaart, width=900, height=600)

# ---------- 5. Optionele datatabel ----------
with st.expander("Toon ruwe data"):
    st.dataframe(filtered_df[['Datum', 'Tijdstip', 'Locatie'] + waardes])

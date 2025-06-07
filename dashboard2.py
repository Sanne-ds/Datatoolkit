import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime

st.set_page_config(layout="wide", page_title="Waterkwaliteit Dashboard")

# --- DATA INLADEN ---
@st.cache_data
def load_data():
    df = pd.read_excel("Waterkwaliteit DataToolkit.xlsx")
    
    # Datum omzetten naar datetime
    df['Meetdag'] = pd.to_datetime(df['Meetdag'], format="%d-%b", dayfirst=True, errors='coerce')
    
    # Coördinaten opsplitsen
    df[['Lat', 'Lon']] = df['Coordinaten'].str.extract(r'([0-9.]+)\s*,\s*([0-9.]+)').astype(float)

    # Verwijder ongeldige rijen
    df = df.dropna(subset=['Lat', 'Lon', 'Meetdag'])
    
    return df

df = load_data()

# --- ZIJBALK ---
st.sidebar.title("🔍 Filter")
selected_date = st.sidebar.date_input("Selecteer meetdag", df['Meetdag'].min())
meetwaarden = ['PH', 'Temperatuur', 'ORP', 'EC', 'CF', 'TDS', 'Humidity', 'Buitentemperatuur']
waardes = st.sidebar.multiselect("Waardes om te tonen", meetwaarden, default=meetwaarden)

# --- FILTEREN DATA ---
filtered_df = df[df['Meetdag'] == pd.to_datetime(selected_date)]

# --- KAART AANMAKEN ---
st.title("📍 Waterkwaliteitsmetingen op kaart")
kaart = folium.Map(location=[filtered_df['Lat'].mean(), filtered_df['Lon'].mean()], zoom_start=14)

for _, row in filtered_df.iterrows():
    if pd.notna(row['Lat']) and pd.notna(row['Lon']):
        popup_text = f"<b>{row['Locatie']}</b><br>"
        for col in waardes:
            if col in row and pd.notna(row[col]):
                popup_text += f"{col}: {row[col]}<br>"
        folium.Marker(
            location=[row['Lat'], row['Lon']],
            popup=folium.Popup(popup_text, max_width=300)
        ).add_to(kaart)

st_data = st_folium(kaart, width=1000, height=600)

# --- EXTRA DATA TABEL ---
with st.expander("📊 Toon meetgegevens in tabel"):
    st.dataframe(filtered_df[['Meetdag', 'Tijdstip', 'Locatie'] + waardes])

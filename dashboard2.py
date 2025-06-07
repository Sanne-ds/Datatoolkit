import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import re

st.set_page_config(layout="wide")

# ---------- 1. Data inladen ----------
@st.cache_data
def load_data():
    df = pd.read_excel("Waterkwaliteit.xlsx")

    # Spaties verwijderen uit kolomnamen
    df.columns = df.columns.str.strip()

    # Datum-kolom aanmaken
    df['Datum'] = pd.to_datetime(df['Meetdag'], dayfirst=True, errors='coerce')

    return df


df = load_data()

# ---------- 2. Sidebar filters ----------
st.sidebar.header("Filter opties")

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
    # Popup tekst opbouwen
    popup_text = f"<b>{row['Locatie']}</b><br>"
    for col in waardes:
        if col in row and pd.notna(row[col]):
            popup_text += f"{col}: {row[col]}<br>"

    # Coördinaten splitsen
    try:
        lat_str, lon_str = re.split(r',\s*', str(row['Coordinaten']))
        lat = float(lat_str)
        lon = float(lon_str)
    except:
        continue

    # pH uitlezen voor kleur
    kleur = "gray"
    try:
        ph_val = float(str(row['PH']).replace(',', '.'))
        if 6.5 <= ph_val <= 8.5:
            kleur = "green"     # Veilig
        elif 5.5 <= ph_val < 6.5 or 8.5 < ph_val <= 9.5:
            kleur = "orange"    # Verhoogd risico
        else:
            kleur = "red"       # Onveilig
    except:
        kleur = "gray"

    # Marker toevoegen
    folium.Marker(
        location=[lat, lon],
        popup=folium.Popup(popup_text, max_width=300),
        icon=folium.Icon(color=kleur)
    ).add_to(kaart)

# ---------- 5. Kaart tonen ----------
st_folium(kaart, width=900, height=600)

# ---------- 6. Gegevens toevoegen ----------
st.markdown("### Voeg nieuwe meting toe")

with st.form("meet_data_form"):
    meetdag = st.date_input("Meetdag")
    tijdstip = st.text_input("Tijdstip (bijv. 13.00-13.15)")
    locatie = st.text_input("Locatie")
    coordinaten = st.text_input("Coordinaten (bijv. 52.36, 4.90)")
    ph = st.number_input("pH", min_value=0.0, max_value=14.0, step=0.01)
    temperatuur = st.number_input("Temperatuur (°C)", step=0.1)
    orp = st.number_input("ORP", step=1.0)
    ec = st.number_input("EC", step=0.01)
    cf = st.number_input("CF", step=0.1)
    tds = st.number_input("TDS", step=1.0)
    humidity = st.text_input("Humidity (bijv. 30%)")
    zon_schaduw = st.selectbox("Zon/schaduw", ['zon', 'schaduw'])
    meetpunt = st.selectbox("Meetpunt", ['kade', 'steiger'])
    buitentemp = st.number_input("Buitentemperatuur", step=1.0)

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
            'Buitentemperatuur': buitentemp
        }

        nieuwe_df = pd.DataFrame([nieuwe_rij])

        try:
            bestaande_df = pd.read_csv("Waterkwaliteit_data.csv")
            updated_df = pd.concat([bestaande_df, nieuwe_df], ignore_index=True)
        except FileNotFoundError:
            updated_df = nieuwe_df

        updated_df.to_csv("Waterkwaliteit_data.csv", index=False)
        st.success("Nieuwe meting toegevoegd!")


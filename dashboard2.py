import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import datetime

st.set_page_config(layout="wide")

# ---------- 1. Data inladen en voorbereiden ----------
@st.cache_data
def load_data():
    df = pd.read_excel("Waterkwaliteit.xlsx")
    # Datum kolom omzetten, dayfirst=True omdat Excel dd-mm-yyyy heeft
    df['Datum'] = pd.to_datetime(df['Meetdag'], dayfirst=True, errors='coerce')
    # Alleen datum (zonder tijd)
    df['Datum_only'] = df['Datum'].dt.date
    return df

# Laad data
df = load_data()

# ---------- 2. Sessiestorage voor nieuwe metingen ----------
if "extra_data" not in st.session_state:
    st.session_state.extra_data = pd.DataFrame(columns=df.columns)

# Voeg nieuwe data toe aan de dataset (in sessie)
df = pd.concat([df, st.session_state.extra_data], ignore_index=True)

# ---------- 3. Sidebar filters ----------
st.sidebar.header("Filter opties")

# Unieke datums als date objecten, zonder restricties (geen min/max)
geldige_data = df['Datum_only'].dropna()
unieke_data = sorted(set(geldige_data))

if unieke_data:
    geselecteerde_datum = st.sidebar.date_input(
        "Kies meetdag",
        value=unieke_data[-1]
    )
else:
    geselecteerde_datum = st.sidebar.date_input("Kies meetdag")

waardes = st.sidebar.multiselect(
    "Waardes om te tonen",
    ['PH', 'Temperatuur', 'ORP', 'EC', 'CF', 'TDS', 'Humidity', 'Buitentemperatuur'],
    default=['PH', 'Temperatuur']
)

# ---------- 4. Filter op geselecteerde datum ----------
df_filtered = df[df['Datum_only'] == geselecteerde_datum]

# ---------- 5. Kaart weergeven ----------
st.title("Waterkwaliteit Meetdashboard")
st.markdown(f"### Meetpunten op {geselecteerde_datum.strftime('%d-%m-%Y')}")

kaart = folium.Map(location=[52.36, 4.9], zoom_start=13)

def bepaal_marker_kleur(row):
    # Voorbeeldregels, pas aan per jouw criteria
    ph = row.get('PH', None)
    if ph is None or pd.isna(ph):
        return 'gray'
    if ph < 6.5 or ph > 9:
        return 'red'
    elif 6.5 <= ph <= 7.5:
        return 'green'
    else:
        return 'orange'

for _, row in df_filtered.iterrows():
    popup_text = f"<b>{row['Locatie']}</b><br>"
    for col in waardes:
        if col in row and pd.notna(row[col]):
            popup_text += f"{col}: {row[col]}<br>"

    # Haal lat/lon uit 'Coordinaten' kolom
    try:
        lat_str, lon_str = str(row['Coordinaten']).split(',')
        lat, lon = float(lat_str.strip()), float(lon_str.strip())
    except Exception:
        continue

    kleur = bepaal_marker_kleur(row)
    folium.Marker(
        location=[lat, lon],
        popup=folium.Popup(popup_text, max_width=300),
        icon=folium.Icon(color=kleur)
    ).add_to(kaart)

st_folium(kaart, width=900, height=600)

# ---------- 6. Tab voor toevoegen nieuwe data ----------
tab1, tab2 = st.tabs(["Dashboard", "Nieuwe Meting"])

with tab2:
    st.header("Voeg nieuwe meetdata toe")

    with st.form("meetdata_form"):
        meetdag = st.date_input("Meetdag", value=datetime.date.today())
        tijdstip = st.text_input("Tijdstip (bijv. 12.30-12.45)")
        locatie = st.text_input("Locatie")
        coordinaten = st.text_input("Coördinaten (lat, lon)")
        ph = st.number_input("PH", format="%.2f", step=0.01)
        temperatuur = st.number_input("Temperatuur", format="%.1f")
        orp = st.number_input("ORP", step=1)
        ec = st.number_input("EC", format="%.2f")
        cf = st.number_input("CF", format="%.1f")
        tds = st.number_input("TDS", step=1)
        humidity = st.text_input("Humidity (bijv. 37%)")
        zon_schaduw = st.selectbox("zon/schaduw", ["zon", "schaduw"])
        meetpunt = st.text_input("Meetpunt")
        buitentemperatuur = st.number_input("Buitentemperatuur", format="%.1f")

        submitted = st.form_submit_button("Toevoegen")

    if submitted:
        nieuwe_rij = {
            'Meetdag': meetdag.strftime("%d-%m-%Y"),
            'Datum': pd.to_datetime(meetdag),
            'Datum_only': meetdag,
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
            'Buitentemperatuur': buitentemperatuur
        }

        # Data toevoegen aan sessiestate dataframe
        st.session_state.extra_data = pd.concat([st.session_state.extra_data, pd.DataFrame([nieuwe_rij])], ignore_index=True)
        st.success("Nieuwe meting toegevoegd! Ga terug naar 'Dashboard' tab om de data te zien.")


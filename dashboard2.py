import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import datetime

st.set_page_config(layout="wide")

@st.cache_data
def load_data():
    df = pd.read_excel("Waterkwaliteit.xlsx")
    df['Datum'] = pd.to_datetime(df['Meetdag'], dayfirst=True, errors='coerce')
    df['Datum_only'] = df['Datum'].dt.date
    return df

# Laad originele data
df_orig = load_data()

if "extra_data" not in st.session_state:
    st.session_state.extra_data = pd.DataFrame(columns=df_orig.columns)

# Combineer originele en toegevoegde data
df = pd.concat([df_orig, st.session_state.extra_data], ignore_index=True)

# Tabs maken
tab1, tab2 = st.tabs(["Dashboard", "Nieuwe Meting"])

with tab1:
    st.title("Waterkwaliteit Meetdashboard")

    # Filters in sidebar voor tab1
    st.sidebar.header("Filter opties")
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

    df_filtered = df[df['Datum_only'] == geselecteerde_datum]

    st.markdown(f"### Meetpunten op {geselecteerde_datum.strftime('%d-%m-%Y')}")

    kaart = folium.Map(location=[52.36, 4.9], zoom_start=13)

    def bepaal_marker_kleur(row):
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

        st.session_state.extra_data = pd.concat([st.session_state.extra_data, pd.DataFrame([nieuwe_rij])], ignore_index=True)
        st.success("Nieuwe meting toegevoegd!")
        st.experimental_rerun()  # App herladen om nieuwe data te tonen

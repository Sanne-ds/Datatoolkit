import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import re

st.set_page_config(layout="wide")

# Define the file path for your data
DATA_FILE = "Waterkwaliteit.xlsx" # Or "Waterkwaliteit.csv" if you prefer CSV

# ---------- 1. Data inladen ----------
# Remove @st.cache_data if you want the data to always reflect the latest file content
# However, for performance, you might keep it and add a clear cache button if needed.
# For now, let's keep it to demonstrate how a button could refresh it.
@st.cache_data
def load_data():
    try:
        df = pd.read_excel(DATA_FILE)
    except FileNotFoundError:
        # Create an empty DataFrame with the expected columns if the file doesn't exist
        # This is useful if you start with no file or it gets deleted.
        columns = ['Locatie', 'Meetdag', 'Datum', 'Coordinaten', 'PH', 'Temperatuur', 'ORP', 'EC', 'CF', 'TDS', 'Humidity', 'Buitentemperatuur']
        df = pd.DataFrame(columns=columns)
        
    # Spaties verwijderen uit kolomnamen
    df.columns = df.columns.str.strip()

    # Datum-kolom aanmaken
    # Ensure 'Meetdag' is in datetime format before creating 'Datum'
    if 'Meetdag' in df.columns:
        df['Meetdag'] = pd.to_datetime(df['Meetdag'], dayfirst=True, errors='coerce')
    df['Datum'] = pd.to_datetime(df['Datum'], dayfirst=True, errors='coerce') # Ensure 'Datum' is also datetime

    return df

# Data initialiseren en opslaan in session_state zodat we ze kunnen uitbreiden
if 'data' not in st.session_state:
    st.session_state['data'] = load_data()

df = st.session_state['data']

# --- Add a button to refresh data if using @st.cache_data ---
st.sidebar.button('Ververs Data', on_click=load_data.clear) # This clears the cache for load_data

# Tabs aanmaken
tab1, tab2 = st.tabs(["Kaart", "Nieuwe meting"])

with tab1:
    # ---------- Sidebar filters (kun je ook hier plaatsen voor betere UX) ----------
    st.sidebar.header("Filter opties")
    
    # Ensure 'Datum' column has valid datetime objects before finding min
    if not df['Datum'].dropna().empty:
        datum_selectie = st.sidebar.date_input("Kies meetdag", df['Datum'].min())
    else:
        datum_selectie = st.sidebar.date_input("Kies meetdag")


    waardes = st.sidebar.multiselect(
        "Waardes om te tonen",
        ['PH', 'Temperatuur', 'ORP', 'EC', 'CF', 'TDS', 'Humidity', 'Buitentemperatuur'],
        default=['PH', 'Temperatuur']
    )

    # Filter op geselecteerde datum
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
        
        # Using number_input for numerical values is safer and provides better input validation
        ph = st.number_input("PH", format="%.2f", step=0.1, help="Bijv. 7.2", value=None)
        temperatuur = st.number_input("Temperatuur (°C)", format="%.1f", step=0.1, help="Bijv. 20.5", value=None)
        orp = st.number_input("ORP", value=None)
        ec = st.number_input("EC", value=None)
        cf = st.number_input("CF", value=None)
        tds = st.number_input("TDS", value=None)
        humidity = st.number_input("Humidity (%)", value=None)
        buitentemperatuur = st.number_input("Buitentemperatuur (°C)", value=None)

        submitted = st.form_submit_button("Toevoegen")

        if submitted:
            # Input validation (basic example)
            if not locatie or not coordinaten:
                st.error("Locatie en Coördinaten zijn verplicht.")
            else:
                try:
                    # Validate coordinates format
                    lat_str, lon_str = re.split(r',\s*', coordinaten)
                    float(lat_str)
                    float(lon_str)

                    # Create a new row
                    nieuwe_meting = {
                        'Locatie': locatie,
                        'Meetdag': pd.Timestamp(datum), # Keep 'Meetdag' consistent with 'Datum' if they represent the same
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

                    # Expand DataFrame and save to session_state
                    df = st.session_state['data']
                    updated_df = pd.concat([df, pd.DataFrame([nieuwe_meting])], ignore_index=True)
                    st.session_state['data'] = updated_df

                    # Save the updated DataFrame back to the Excel file
                    # Use index=False to avoid writing the DataFrame index as a column
                    try:
                        updated_df.to_excel(DATA_FILE, index=False)
                        st.success("Nieuwe meting toegevoegd en opgeslagen! Ga terug naar tab 'Kaart' om de update te zien.")
                        # To immediately reflect the change in the map tab without a full refresh,
                        # you might need to clear the cache if @st.cache_data is used on load_data.
                        # However, for simplicity, asking the user to go back to the tab is fine.
                    except Exception as e:
                        st.error(f"Fout bij opslaan van data: {e}")
                except ValueError:
                    st.error("Ongeldig formaat voor coördinaten. Gebruik 'latitude, longitude' (bijv. 52.37, 4.89).")
                except Exception as e:
                    st.error(f"Er is een onverwachte fout opgetreden: {e}")

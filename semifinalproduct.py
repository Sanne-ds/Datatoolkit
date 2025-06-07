import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import re

st.set_page_config(layout="wide")

DATA_FILE = "Waterkwaliteit.xlsx" 

1. Data inladen 
@st.cache_data
def load_data():
    try:
        df = pd.read_excel(DATA_FILE)
        
        df.columns = df.columns.str.strip()
        
        if 'Meetdag' in df.columns:
            df['Meetdag'] = pd.to_datetime(df['Meetdag'], dayfirst=True, errors='coerce')
        else:
            df['Meetdag'] = pd.NaT 

        if 'Datum' in df.columns:
            df['Datum'] = pd.to_datetime(df['Datum'], dayfirst=True, errors='coerce')
        elif 'Meetdag' in df.columns: # If 'Datum' is missing but 'Meetdag' exists, use 'Meetdag'
            df['Datum'] = df['Meetdag']
        else: # If both are missing, create 'Datum' with NaT values
            df['Datum'] = pd.NaT

    except FileNotFoundError:
        # Create an empty DataFrame with ALL expected columns, including 'Datum' and 'Meetdag'
        # This is crucial for consistency when the file doesn't exist yet.
        columns = [
            'Locatie', 'Meetdag', 'Datum', 'Coordinaten', 'PH', 'Temperatuur',
            'ORP', 'EC', 'CF', 'TDS', 'Humidity', 'Buitentemperatuur'
        ]
        df = pd.DataFrame(columns=columns)
        

        df['Meetdag'] = pd.to_datetime(df['Meetdag'])
        df['Datum'] = pd.to_datetime(df['Datum'])
        
    return df


def save_data(df_to_save):
    try:
        df_to_save.to_excel(DATA_FILE, index=False)
        st.success("Data succesvol opgeslagen!")
    except Exception as e:
        st.error(f"Fout bij opslaan van data: {e}")


if 'data' not in st.session_state:
    st.session_state['data'] = load_data()

df = st.session_state['data']

st.sidebar.button('Refresh', on_click=load_data.clear) 


tab1, tab2, tab3 = st.tabs(["🗺️ Kaart", "➕ Meting toevoegen", "⚙️ Metingen beheren"])

with tab1:
    st.sidebar.header("Filter opties")
    
    
    if not df['Datum'].dropna().empty:
        datum_selectie = st.sidebar.date_input("Kies meetdag", df['Datum'].min())
    else:
        # Provide a default date if no valid dates are found
        datum_selectie = st.sidebar.date_input("Kies meetdag", pd.to_datetime('today'))


    waardes = st.sidebar.multiselect(
        "Waardes om te tonen",
        ['PH', 'Temperatuur', 'ORP', 'EC', 'CF', 'TDS', 'Humidity', 'Buitentemperatuur'],
        default=['PH', 'Temperatuur']
    )

 
    filtered_df = df[df['Datum'] == pd.to_datetime(datum_selectie)]

    st.title("🌊 Waterkwaliteit Amsterdam")
    st.markdown(f"### Meetpunten op {datum_selectie.strftime('%d-%m-%Y')}")

    kaart = folium.Map(location=[52.36, 4.9], zoom_start=13)

    for _, row in filtered_df.iterrows():
        popup_text = f"<b>{row['Locatie']}</b><br>"
        for col in waardes:
            if col in row and pd.notna(row[col]):
                popup_text += f"{col}: {row[col]}<br>"

        try:
            coords_str = str(row['Coordinaten'])
            lat_str, lon_str = re.split(r',\s*', coords_str)
            lat = float(lat_str)
            lon = float(lon_str)
        except (ValueError, TypeError): 
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
        except (ValueError, TypeError):
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
                    
                    lat_str, lon_str = re.split(r',\s*', coordinaten)
                    float(lat_str)
                    float(lon_str)

                    
                    nieuwe_meting = {
                        'Locatie': locatie,
                        'Meetdag': pd.Timestamp(datum), 
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

                
                    df = st.session_state['data']
                    updated_df = pd.concat([df, pd.DataFrame([nieuwe_meting])], ignore_index=True)
                    st.session_state['data'] = updated_df

                
                    save_data(updated_df)
                    st.success("Nieuwe meting toegevoegd en opgeslagen! Ga terug naar tab 'Kaart' om de update te zien.")
                    
                except ValueError:
                    st.error("Ongeldig formaat voor coördinaten. Gebruik 'latitude, longitude' (bijv. 52.37, 4.89).")
                except Exception as e:
                    st.error(f"Er is een onverwachte fout opgetreden: {e}")

with tab3:
    st.header("Metingen beheren")

    if not st.session_state['data'].empty:
        st.write("Selecteer de metingen die je wilt verwijderen:")
        
        
       
        df_display = st.session_state['data'].reset_index()
        df_display.rename(columns={'index': 'Originele Index'}, inplace=True)

        selected_rows_indices = []
        for i, row in df_display.iterrows():
            col1, col2 = st.columns([0.1, 0.9])
            with col1:
                if st.checkbox(f"Selecteer", key=f"checkbox_{i}"):
                    selected_rows_indices.append(row['Originele Index'])
            with col2:
                # Display relevant information for the user to identify the row
                st.write(f"**Locatie:** {row['Locatie']} | **Datum:** {row['Datum'].strftime('%d-%m-%Y')} | **Coördinaten:** {row['Coordinaten']}")
                st.write(f"PH: {row['PH']}, Temp: {row['Temperatuur']}")
                st.write("---") # Separator for readability

        if st.button("Geselecteerde metingen verwijderen"):
            if selected_rows_indices:
                df_to_delete_from = st.session_state['data']
                updated_df = df_to_delete_from.drop(selected_rows_indices).reset_index(drop=True)
                st.session_state['data'] = updated_df
                save_data(updated_df)
                st.success(f"{len(selected_rows_indices)} meting(en) succesvol verwijderd en opgeslagen!")
                st.rerun() # Rerun to refresh the displayed data and checkboxes
            else:
                st.warning("Geen metingen geselecteerd om te verwijderen.")
    else:
        st.info("Er zijn nog geen metingen om te beheren.")

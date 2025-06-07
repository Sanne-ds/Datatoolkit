import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import re
import io

st.set_page_config(layout="wide")

DATA_FILE = "Waterkwaliteit.xlsx"  # Of "Waterkwaliteit.csv" als je dat gebruikt

# ---------- 1. Data inladen ----------
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
        elif 'Meetdag' in df.columns:
            df['Datum'] = df['Meetdag']
        else:
            df['Datum'] = pd.NaT
    except FileNotFoundError:
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

def convert_df_to_excel(df_to_convert):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_to_convert.to_excel(writer, index=False, sheet_name='Sheet1')
    processed_data = output.getvalue()
    return processed_data

if 'data' not in st.session_state:
    st.session_state['data'] = load_data()

df = st.session_state['data']

tab1, tab2, tab3, tab4 = st.tabs(["ℹ️ Info", "🗺️ Kaart", "➕ Nieuwe meting", "⚙️ Metingen beheren"])

with tab1:
    st.title("🌍 Dashboard Waterkwaliteit")
    st.markdown("""
        Welkom bij het dashboard voor waterkwaliteitsmetingen in Amsterdam.  
        Hier kun je metingen bekijken op de kaart, nieuwe data toevoegen, of bestaande metingen beheren.  
        
        - Ga naar **'Kaart'** om de waterkwaliteit op een specifieke datum te bekijken.  
        - Voeg zelf metingen toe onder **'Nieuwe meting'**.  
        - Onder **'Metingen beheren'** kun je eerder ingevoerde data verwijderen.  
        
        Veel succes!
    """)

with tab2:
    st.title("🌊 Waterkwaliteit in Amsterdam")

    # Filters direct op het tabblad plaatsen
    if not df['Datum'].dropna().empty:
        datum_selectie = st.date_input("Kies meetdag", df['Datum'].min())
    else:
        datum_selectie = st.date_input("Kies meetdag", pd.to_datetime('today'))

    waardes = st.multiselect(
        "Waardes om te tonen",
        ['PH', 'Temperatuur', 'ORP', 'EC', 'CF', 'TDS', 'Humidity', 'Buitentemperatuur'],
        default=['PH', 'Temperatuur']
    )

    if st.button("Refresh data"):
        load_data.clear()
        st.experimental_rerun()

    filtered_df = df[df['Datum'] == pd.to_datetime(datum_selectie)]

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

with tab3:
    st.header("Nieuwe meting toevoegen")

    with st.form("meting_form"):
        locatie = st.text_input("Locatie", max_chars=50)
        datum = st.date_input("Meetdag")

        col_lat, col_lon = st.columns(2)
        with col_lat:
            lat = st.number_input("Latitude", format="%.6f", help="Bijv. 52.370216", value=None)
        with col_lon:
            lon = st.number_input("Longitude", format="%.6f", help="Bijv. 4.895168", value=None)

        ph = st.number_input("PH", format="%.2f", step=0.1, help="Bijv. 7.2 (mag > 14, met waarschuwing)", value=None)
        temperatuur = st.number_input("Temperatuur (°C)", format="%.1f", step=0.1, help="Bijv. 20.5", value=None)
        orp = st.number_input("ORP", value=None)
        ec = st.number_input("EC", value=None)
        cf = st.number_input("CF", value=None)
        tds = st.number_input("TDS", value=None)
        humidity = st.number_input("Humidity (%)", min_value=0.0, max_value=100.0, format="%.1f", step=0.1, help="Geef een waarde tussen 0 en 100", value=None)
        buitentemperatuur = st.number_input("Buitentemperatuur (°C)", value=None)

        submitted = st.form_submit_button("Toevoegen")

        if submitted:
            fouten = []
            if not locatie:
                fouten.append("Locatie is verplicht.")
            if lat is None or lon is None:
                fouten.append("Zowel latitude als longitude zijn verplicht.")

            if ph is not None and (ph < 0 or ph > 20):
                fouten.append("PH-waarde lijkt onrealistisch hoog/laag.")

            if fouten:
                for fout in fouten:
                    st.error(fout)
            else:
                # Extra waarschuwing bij hoge PH waarde
                if ph is not None and ph > 14:
                    if st.confirm(f"PH waarde is {ph}, dat is hoger dan normaal. Weet je zeker dat dit klopt?"):
                        pass
                    else:
                        st.warning("Voer de meting opnieuw in.")
                        st.stop()

                try:
                    coordinaten = f"{lat}, {lon}"
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
                except Exception as e:
                    st.error(f"Er is een onverwachte fout opgetreden: {e}")

with tab4:
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
                st.write(f"**Locatie:** {row['Locatie']} | **Datum:** {row['Datum'].strftime('%d-%m-%Y')} | **Coördinaten:** {row['Coordinaten']}")
                st.write(f"PH: {row['PH']}, Temp: {row['Temperatuur']}")
                st.write("---")

        if st.button("Geselecteerde metingen verwijderen"):
            if selected_rows_indices:
                df_to_delete_from = st.session_state['data']
                updated_df = df_to_delete_from.drop(selected_rows_indices).reset_index(drop=True)
                st.session_state['data'] = updated_df
                save_data(updated_df)
                st.success(f"{len(selected_rows_indices)} meting(en) succesvol verwijderd en opgeslagen!")
                st.experimental_rerun()
            else:
                st.warning("Geen metingen geselecteerd om te verwijderen.")

        st.markdown("---")
        st.subheader("Data downloaden")

        # Datum selectie voor export
        min_date = df['Datum'].min()
        max_date = df['Datum'].max()

        start_datum = st.date_input("Startdatum (dd-mm-jjjj)", value=min_date)
        eind_datum = st.date_input("Einddatum (dd-mm-jjjj)", value=max_date)

        if start_datum > eind_datum:
            st.error("Startdatum moet vóór of gelijk zijn aan einddatum.")
        else:
            filtered_df = df[
                (df['Datum'] >= pd.to_datetime(start_datum)) &
                (df['Datum'] <= pd.to_datetime(eind_datum))
            ]

            st.write(f"Toon metingen tussen {start_datum.strftime('%d-%m-%Y')} en {eind_datum.strftime('%d-%m-%Y')}")
            st.dataframe(filtered_df)

            if not filtered_df.empty:
                excel_data = convert_df_to_excel(filtered_df)
                st.download_button(
                    label="Download geselecteerde data als Excel",
                    data=excel_data,
                    file_name=f"waterkwaliteit_{start_datum.strftime('%Y%m%d')}_tot_{eind_datum.strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.info("Geen data beschikbaar voor de geselecteerde datumrange.")

    else:
        st.info("Er zijn nog geen metingen om te beheren.")

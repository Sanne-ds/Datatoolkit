import streamlit as st
import pandas as pd
import pydeck as pdk

# Titel
st.title("Metingen in Amsterdam")

# Coördinatenlijst
coordinates = [
    (52.3597533, 4.9070122),
    (52.3406215, 4.9161200),
    (52.3659139, 4.9005303),
    (52.3677279, 4.8938338),
    (52.3674163, 4.8847137),
]

# Zet het om in een DataFrame
df = pd.DataFrame(coordinates, columns=["lat", "lon"])

# Toon de kaart
st.pydeck_chart(pdk.Deck(
    map_style='mapbox://styles/mapbox/streets-v11',
    initial_view_state=pdk.ViewState(
        latitude=df["lat"].mean(),
        longitude=df["lon"].mean(),
        zoom=13,
        pitch=0,
    ),
    layers=[
        pdk.Layer(
            "ScatterplotLayer",
            data=df,
            get_position='[lon, lat]',
            get_color='[200, 30, 0, 160]',
            get_radius=50,
        ),
    ],
))

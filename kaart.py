import streamlit as st
import pandas as pd
import pydeck as pdk

st.title("Meetlocaties")

# Coördinaten
coordinates = [
    (52.3597533, 4.9070122),
    (52.3406215, 4.9161200),  # Spaklerweg
    (52.3659139, 4.9005303),
    (52.3677279, 4.8938338),
    (52.3674163, 4.8847137),
]

# DataFrame
df = pd.DataFrame(coordinates, columns=["lat", "lon"])

# Google-style pin icoon
df["icon_data"] = [{
    "url": "https://maps.gstatic.com/mapfiles/api-3/images/spotlight-poi2_hdpi.png",
    "width": 64,
    "height": 64,
    "anchorY": 64
} for _ in range(len(df))]

# Kaart tonen
st.pydeck_chart(pdk.Deck(
    map_style='mapbox://styles/mapbox/streets-v11',
    initial_view_state=pdk.ViewState(
        latitude=df["lat"].mean(),
        longitude=df["lon"].mean(),
        zoom=12.3,
        pitch=0,
    ),
    layers=[
        pdk.Layer(
            "IconLayer",
            data=df,
            get_icon="icon_data",
            get_size=4,
            size_scale=10,
            get_position='[lon, lat]',
            pickable=True,
        ),
    ],
))

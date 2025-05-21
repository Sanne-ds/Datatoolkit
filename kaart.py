import streamlit as st
import pandas as pd
import pydeck as pdk

st.title("Metingen in Amsterdam – met iconen")

coordinates = [
    (52.3597533, 4.9070122),
    (52.3406215, 4.9161200),  # Spaklerweg
    (52.3659139, 4.9005303),
    (52.3677279, 4.8938338),
    (52.3674163, 4.8847137),
]

labels = ["P1", "Spaklerweg", "P3", "P4", "P5"]

df = pd.DataFrame(coordinates, columns=["lat", "lon"])
df["label"] = labels
df["icon_data"] = [{
    "url": "https://upload.wikimedia.org/wikipedia/commons/e/ec/RedDot.svg",
    "width": 128,
    "height": 128,
    "anchorY": 128
} for _ in range(len(df))]

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
            pickable=True
        ),
        pdk.Layer(
            "TextLayer",
            data=df,
            get_position='[lon, lat]',
            get_text="label",
            get_size=16,
            get_color=[0, 0, 0],
            get_alignment_baseline="'bottom'"
        ),
    ],
))

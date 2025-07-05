import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from PIL import Image
from io import BytesIO
import numpy as np

# Konfiguration
LAT, LON = 46.836, 10.508
TIMEZONE = "Europe/Berlin"
WEBCAM_URL = "https://images-webcams.windy.com/48/1652791148/current/full/1652791148.jpg"

st.set_page_config(page_title="Kite Forecast Reschensee", layout="wide")
st.title("🏄‍♂️ Kite Forecast Reschensee (mit erweiterter Wetter- & Webcam-Analyse)")

# Wetterdaten abrufen
def fetch_weather_data():
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": LAT,
        "longitude": LON,
        "hourly": "windspeed_10m,winddirection_10m,cl

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
        "hourly": "windspeed_10m,winddirection_10m,cloudcover,temperature_2m,precipitation_probability",
        "daily": "uv_index_max,sunshine_duration",
        "forecast_days": 4,
        "timezone": TIMEZONE
    }
    try:
        res = requests.get(url, params=params, timeout=10)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        st.error(f"❌ Wetterdaten konnten nicht geladen werden: {e}")
        return None

# Webcam analysieren
def analyze_webcam_image():
    try:
        res = requests.get(WEBCAM_URL, timeout=10)
        img = Image.open(BytesIO(res.content)).convert("L")  # Graustufen
        np_img = np.array(img)
        brightness = np.mean(np_img)
        return brightness
    except Exception as e:
        st.warning(f"⚠️ Webcam konnte nicht analysiert werden: {e}")
        return None

# Bewertung mit erweitertem Score
def evaluate_day(wind_avg, wind_dir, clouds, rain, uv, brightness):
    score = 0
    notes = {}

    # Windgeschwindigkeit
    if 10 <= wind_avg <= 25:
        score += 2
        notes["Wind"] = "🟢"
    elif 7 <= wind_avg < 10 or 25 < wind_avg <= 30:
        score += 1
        notes["Wind"] = "🟡"
    else:
        notes["Wind"] = "🔴"

    # Windrichtung
    if wind_dir <= 30 or wind_dir >= 340 or (150 <= wind_dir <= 210):
        score += 2
        notes["Richtung"] = "🟢"
    else:
        score -= 1
        notes["Richtung"] = "🔴"

    # Regenwahrscheinlichkeit
    if rain < 30:
        score += 1
        notes["Regen"] = "🟢"
    elif rain < 60:
        notes["Regen"] = "🟡"
    else:
        notes["Regen"] = "🔴"

    # Bewölkung
    if clouds < 50:
        score += 1
        notes["Bewölkung"] = "🟢"
    else:
        notes["Bewölkung"] = "🟡"

    # UV
    if uv > 5:
        score += 1
        notes["UV"] = "🟢"
    else:
        notes["UV"] = "🟡"

    # Webcam-Helligkeit
    if brightness and brightness > 100:
        score += 1
        notes["Webcam"] = "🟢"
    else:
        notes["Webcam"] = "🟡"

    # Ampelstatus
    if score >= 6:
        amp = "🟢 Perfekt"
    elif score >= 3:
        amp = "🟡 Mittel"
    else:
        amp = "🔴 Schlecht"

    return score, amp, notes

# Darstellung Forecast + Ampelgrid
def show_forecast(data, webcam_brightness):
    df = pd.DataFrame(data["hourly"])
    df["time"] = pd.to_datetime(df["time"])
    df.set_index("time", inplace=True)

    st.subheader("📊 Kitevorschau der nächsten 4 Tage")

    for i in range(4):
        day = (datetime.now().date() + pd.Timedelta(days=i)).isoformat()
        daily_uv = data["daily"]["uv_index_max"][i]
        day_data = df[df.index.date == pd.to_datetime(day).date()]
        if day_data.empty:
            continue

        wind_avg = day_data["windspeed_10m"].mean()
        wind_dir = day_data["winddirection_10m"].median()
        clouds = day_data["cloudcover"].mean()
        rain = day_data["precipitation_probability"].max()
        temp = day_data["temperature_2m"].mean()

        score, amp, notes = evaluate_day(wind_avg, wind_dir, clouds, rain, daily_uv, webcam_brightness)

        st.markdown(f"### 📅 {day} — Bewertung: {amp} ({score}/8 Punkte)")
        grid = pd.DataFrame({
            "Faktor": ["Wind", "Richtung", "Regen", "Bewölkung", "UV", "Webcam"],
            "Bewertung": [notes.get(k, "⚪") for k in ["Wind", "Richtung", "Regen", "Bewölkung", "UV", "Webcam"]]
        })
        st.table(grid)

        with st.expander("🔍 Wetterdetails anzeigen"):
            st.write(f"- ⛅ Ø Bewölkung: **{clouds:.1f}%**")
            st.write(f"- 🌬️ Ø Windgeschwindigkeit: **{wind_avg:.1f} km/h**")
            st.write(f"- 🧭 Windrichtung (Median): **{wind_dir:.0f}°**")
            st.write(f"- 🌧️ Regenwahrscheinlichkeit (max): **{rain:.0f}%**")
            st.write(f"- 🌡️ Temperatur: **{temp:.1f}°C**")
            st.write(f"- ☀️ UV-Index: **{daily_uv}**")
            if webcam_brightness:
                st.write(f"- 📷 Webcam-Helligkeit: **{webcam_brightness:.1f}**")

# Hauptlogik
data = fetch_weather_data()
webcam_brightness = analyze_webcam_image()

if data:
    show_forecast(data, webcam_brightness)

    st.markdown("---")
    st.markdown("### ℹ️ Bewertungskriterien")
    st.markdown("""
    - **Windrichtung:** Nord (0°) oder Süd (180°) sind kitebar.
    - **Windgeschwindigkeit:** Optimal: 10–25 km/h
    - **Niederschlag:** Bei Regen über 60% → ⛔
    - **Bewölkung & UV:** Thermik- und Sicht-Indikator
    - **Webcam:** Helligkeit zeigt reales Wetterbild (bewölkt/sonnig)
    """)

    st.markdown("### 🔗 Datenquellen")
    st.markdown("""
    - [🌤️ Open-Meteo Wetterdaten](https://open-meteo.com)
    - [📷 Webcam Reschensee](https://images-webcams.windy.com/48/1652791148/current/full/1652791148.jpg)
    - [🌀 Föhndiagramm Tirol (wetterring.at)](https://wetterring.at/profiwetter/foehndiagramm-tirol)
    """)

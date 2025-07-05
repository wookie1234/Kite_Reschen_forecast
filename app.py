import streamlit as st
import requests
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Kite Forecast Reschensee", layout="wide")

# Parameter
LAT, LON = 46.836, 10.508
TIMEZONE = "Europe/Berlin"

# Open-Meteo API Call
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
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"❌ Wetterdaten konnten nicht geladen werden: {e}")
        return None

# Bewertung pro Tag
def evaluate_day(wind_avg, wind_dir, clouds, rain, uv):
    score = 0
    if 10 <= wind_avg <= 25:
        score += 2
    elif 7 <= wind_avg < 10 or 25 < wind_avg <= 30:
        score += 1

    if wind_dir in range(340, 361) or wind_dir in range(0, 30) or 150 <= wind_dir <= 210:
        score += 2  # Nord oder Südwind
    elif 30 < wind_dir < 150 or 210 < wind_dir < 330:
        score -= 1  # Ost/West ungeeignet

    if rain < 30:
        score += 1

    if uv > 5:
        score += 1

    if clouds < 60:
        score += 1

    if score >= 6:
        return "🟢 Perfekt"
    elif score >= 3:
        return "🟡 Mittel"
    else:
        return "🔴 Schlecht"

# Darstellung
def show_forecast(data):
    df = pd.DataFrame(data["hourly"])
    df["time"] = pd.to_datetime(df["time"])
    df.set_index("time", inplace=True)

    st.subheader("📊 Kitevorschau für die nächsten Tage")

    for i in range(4):
        day = (datetime.now().date() + pd.Timedelta(days=i)).isoformat()
        day_data = df[df.index.date == pd.to_datetime(day).date()]

        if day_data.empty:
            continue

        wind_avg = day_data["windspeed_10m"].mean()
        wind_dir = day_data["winddirection_10m"].median()
        clouds = day_data["cloudcover"].mean()
        rain = day_data["precipitation_probability"].max()
        temp = day_data["temperature_2m"].mean()
        uv = data["daily"]["uv_index_max"][i]

        score = evaluate_day(wind_avg, wind_dir, clouds, rain, uv)

        with st.expander(f"📅 {day} — Bewertung: {score}"):
            st.write(f"- Durchschnittliche Windgeschwindigkeit: **{wind_avg:.1f} km/h**")
            st.write(f"- Vorherrschende Windrichtung: **{wind_dir:.0f}°**")
            st.write(f"- Max. Niederschlagswahrscheinlichkeit: **{rain:.0f}%**")
            st.write(f"- Ø Bewölkung: **{clouds:.0f}%**")
            st.write(f"- Temperatur: **{temp:.1f}°C**")
            st.write(f"- UV-Index: **{uv}**")

# App Start
st.title("🏄‍♂️ Kite Forecast Reschensee (mit erweiterten Wetterdaten)")

data = fetch_weather_data()
if data:
    show_forecast(data)

    st.markdown("---")
    st.markdown("### ℹ️ Bewertungskriterien")
    st.write("""
    - **Windrichtung:** Nur Nord (0°) oder Süd (180°) sind kitebar.
    - **Windstärke:** Optimal zwischen 10–25 km/h.
    - **Regen:** Bei hoher Regenwahrscheinlichkeit ist Vorsicht geboten.
    - **Bewölkung & UV:** Je sonniger, desto besser für Thermik.
    """)

    st.markdown("### 🔗 Datenquellen")
    st.write("""
    - [Open-Meteo.com](https://open-meteo.com)
    - [Webcam Reschenpass](https://images-webcams.windy.com/48/1652791148/current/full/1652791148.jpg)
    - [Wetterring Föhndiagramm](https://wetterring.at/profiwetter/foehndiagramm-tirol)
    """)

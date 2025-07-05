
import streamlit as st
import requests
from datetime import datetime, timedelta

st.set_page_config(page_title="Kite Forecast Reschensee", layout="wide")
st.title("🏄‍♂️ Kite Forecast Reschensee (mit erweiterten Wetterdaten)")

# Load Forecast
def get_forecast():
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": 46.836,
            "longitude": 10.508,
            "hourly": "windspeed_10m,winddirection_10m,cloudcover,temperature_2m,gusts_10m,precipitation_probability",
            "daily": "uv_index_max,sunshine_duration",
            "forecast_days": 4,
            "timezone": "Europe/Berlin"
        }
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            return r.json()
        else:
            st.warning(f"Statuscode {r.status_code}: {r.text}")
    except Exception as e:
        st.error(f"Fehler beim Abrufen der Wetterdaten: {e}")
    return None

forecast_data = get_forecast()

# Simulierte Druckdaten
bozen_pressure = 1012.3
innsbruck_pressure = 1007.9
pressure_diff = bozen_pressure - innsbruck_pressure

# Auswertung pro Tag
def evaluate_day(day_index):
    score = 50
    info = []

    try:
        hour = 14  # Analysezeitpunkt
        h_index = day_index * 24 + hour
        wind = forecast_data["hourly"]["windspeed_10m"][h_index]
        dir = forecast_data["hourly"]["winddirection_10m"][h_index]
        gusts = forecast_data["hourly"]["gusts_10m"][h_index]
        cloud = forecast_data["hourly"]["cloudcover"][h_index]
        precip = forecast_data["hourly"]["precipitation_probability"][h_index]
        temp = forecast_data["hourly"]["temperature_2m"][h_index]
        uv = forecast_data["daily"]["uv_index_max"][day_index]

        direction = "Süd" if 140 <= dir <= 220 else "Nord" if dir >= 330 or dir <= 30 else "unkitebar"
        info.append(f"💨 Windrichtung: {direction} ({dir}°)")
        if direction == "unkitebar": score -= 30
        else: score += 10

        info.append(f"🌬 Wind: {wind} km/h")
        if wind >= 14: score += 10
        elif wind < 8: score -= 15

        info.append(f"💥 Böen: {gusts} km/h")
        if gusts > 35: score -= 5

        info.append(f"🌧 Regenwahrscheinlichkeit: {precip}%")
        if precip > 40: score -= 10

        info.append(f"🔆 UV-Index: {uv}")
        if uv > 6: score += 5

        info.append(f"☁️ Bewölkung: {cloud}%")
        if cloud < 30: score += 5

        if pressure_diff >= 4:
            score += 10
            info.append("🌀 Südföhn erkannt")
        elif pressure_diff <= -4:
            score += 5
            info.append("🌬 Nordföhn erkannt")

    except:
        info.append("⚠️ Daten unvollständig")

    amp = "🟢 Kitebar" if score >= 75 else "🟡 Möglich" if score >= 50 else "🔴 Nicht empfehlenswert"
    return score, amp, info

# UI: Heutige Zusammenfassung
if forecast_data:
    today_score, today_amp, _ = evaluate_day(0)
    st.markdown(f"## {today_amp}")
    st.markdown(f"**Heutiger Score:** {today_score}/100")
else:
    st.error("❌ Wetterdaten konnten nicht geladen werden.")
    st.stop()

# 3-Tages-Vorhersage
st.subheader("📅 3-Tage Kite-Vorhersage")

cols = st.columns(3)
for i in range(3):
    d = datetime.today() + timedelta(days=i)
    s, a, detail = evaluate_day(i)
    with cols[i]:
        st.markdown(f"### {d.strftime('%A, %d.%m.')}")
        st.markdown(a)
        st.markdown(f"Score: **{s}**")
        with st.expander("🔎 Details"):
            for line in detail:
                st.markdown("- " + line)

# Erklärung am Ende
with st.expander("ℹ️ Erklärung & Datenquellen"):
    st.markdown("""
    Die Ampelbewertung ergibt sich aus:
    - **Windrichtung** (nur Nord & Süd)
    - **Windgeschwindigkeit**
    - **Böen, Regen, UV-Index, Bewölkung**
    - **Druckdifferenz (Föhndiagramm-Simulation)**
    - ✅ Ampel = grün: Score > 75 / gelb: > 50 / rot: darunter

    **Datenquellen:**
    - [Open-Meteo](https://open-meteo.com)
    - [Webcam Windy](https://images-webcams.windy.com/48/1652791148/current/full/1652791148.jpg)
    - Druck simuliert für Bozen/Innsbruck
    """)

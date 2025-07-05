import streamlit as st
import requests
from datetime import datetime, timedelta

st.set_page_config(page_title="Kite Forecast Reschensee", layout="wide")
st.title("🏄‍♂️ Kite Forecast Reschensee (mit erweiterten Wetterdaten)")

# Open-Meteo Forecast holen
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
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"❌ Wetterdaten konnten nicht geladen werden: {e}")
        return None

forecast_data = get_forecast()

# Druckdaten simulieren (ersetzbar durch echte Quellen)
bozen_pressure = 1012.3
innsbruck_pressure = 1007.9
pressure_diff = bozen_pressure - innsbruck_pressure

# Tagesbewertung
def evaluate_day(day_index):
    score = 50
    info = []

    try:
        h_index = day_index * 24 + 14  # 14 Uhr
        wind = forecast_data["hourly"]["windspeed_10m"][h_index]
        direction_deg = forecast_data["hourly"]["winddirection_10m"][h_index]
        gusts = forecast_data["hourly"]["gusts_10m"][h_index]
        cloud = forecast_data["hourly"]["cloudcover"][h_index]
        precip = forecast_data["hourly"]["precipitation_probability"][h_index]
        temp = forecast_data["hourly"]["temperature_2m"][h_index]
        uv = forecast_data["daily"]["uv_index_max"][day_index]

        # Windrichtung
        if 140 <= direction_deg <= 220:
            direction = "Süd"
            score += 10
        elif direction_deg >= 330 or direction_deg <= 30:
            direction = "Nord"
            score += 10
        else:
            direction = "unkitebar"
            score -= 30
        info.append(f"💨 Windrichtung: {direction} ({direction_deg}°)")

        # Windgeschwindigkeit
        info.append(f"🌬 Wind: {wind} km/h")
        if wind >= 14: score += 10
        elif wind < 8: score -= 15

        # Böen
        info.append(f"💥 Böen: {gusts} km/h")
        if gusts > 35: score -= 5

        # Regen
        info.append(f"🌧 Regenwahrscheinlichkeit: {precip}%")
        if precip > 40: score -= 10

        # UV
        info.append(f"🔆 UV-Index: {uv}")
        if uv > 6: score += 5

        # Wolken
        info.append(f"☁️ Bewölkung: {cloud}%")
        if cloud < 30: score += 5

        # Föhnlage
        if pressure_diff >= 4:
            score += 10
            info.append("🌀 Südföhn erkannt")
        elif pressure_diff <= -4:
            score += 5
            info.append("🌬 Nordföhn erkannt")

    except Exception as e:
        info.append(f"⚠️ Daten unvollständig oder Fehler: {e}")

    # Ampelbewertung
    if score >= 75:
        amp = "🟢 Kitebar"
    elif score >= 50:
        amp = "🟡 Möglich"
    else:
        amp = "🔴 Nicht empfehlenswert"

    return score, amp, info

# Heutiger Tag
if forecast_data:
    score_today, amp_today, _ = evaluate_day(0)
    st.subheader(f"{amp_today} – Score: {score_today}/100")
else:
    st.stop()

# Tagesübersicht
st.subheader("📅 3-Tage Kite-Vorhersage")

cols = st.columns(3)
for i in range(3):
    d = datetime.today() + timedelta(days=i)
    score, amp, detail = evaluate_day(i)
    with cols[i]:
        st.markdown(f"### {d.strftime('%A, %d.%m.')}")
        st.markdown(amp)
        st.markdown(f"**Score:** {score}/100")
        with st.expander("🔎 Details"):
            for line in detail:
                st.markdown("- " + line)

# Erklärung
with st.expander("ℹ️ Erklärung & Datenquellen"):
    st.markdown("""
    ### Bewertungskriterien:
    - ✅ **Windrichtung**: nur **Nord** oder **Süd** ist kitebar
    - 🌬 **Windstärke**: ideal >14 km/h
    - 💥 **Böen**: >35 km/h = Abwertung
    - 🌧 **Regenrisiko**: >40 % = Abwertung
    - 🔆 **UV-Index** & ☁️ **Sicht**: fließen in Thermikbewertung ein
    - 🌀 **Föhnlage**: berechnet aus Druck Bozen – Innsbruck

    ### Datenquellen:
    - [Open-Meteo Wetterdaten](https://open-meteo.com)
    - [Webcam Windy Reschensee](https://images-webcams.windy.com/48/1652791148/current/full/1652791148.jpg)
    - Druckwerte simuliert
    """)

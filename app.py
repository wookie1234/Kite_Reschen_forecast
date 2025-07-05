import streamlit as st
import requests
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
import streamlit.components.v1 as components

def get_forecast():
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": 46.836,
            "longitude": 10.508,
            "hourly": "windspeed_10m,winddirection_10m,cloudcover,temperature_2m,gusts_10m,precipitation_probability,uv_index",
            "daily": "sunshine_duration",
            "forecast_days": 4,
            "timezone": "Europe/Berlin"
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; KiteForecastBot/1.0)"
        }
        r = requests.get(url, params=params, headers=headers, timeout=10)
        if r.status_code == 200:
            return r.json()
        else:
            st.warning(f"Statuscode {r.status_code}: {r.text}")
    except Exception as e:
        st.error(f"Fehler beim Abrufen der Wetterdaten: {e}")
    return None
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": 46.836,
            "longitude": 10.508,
            "hourly": "windspeed_10m,winddirection_10m,cloudcover,temperature_2m,gusts_10m,precipitation_probability,uv_index",
            "daily": "sunshine_duration",
            "forecast_days": 4,
            "timezone": "Europe/Berlin"
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; KiteForecastBot/1.0)"
        }
        r = requests.get(url, params=params, headers=headers, timeout=10)
        if r.status_code == 200:
            return r.json()
        else:
            st.warning(f"Statuscode {r.status_code}: {r.text}")
    except Exception as e:
        st.error(f"Fehler beim Abrufen der Wetterdaten: {e}")
    return None
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": 46.836,
            "longitude": 10.508,
            "hourly": "windspeed_10m,winddirection_10m,cloudcover,temperature_2m,gusts_10m,precipitation_probability,uv_index",
            "daily": "sunshine_duration",
            "forecast_days": 4,
            "timezone": "Europe/Berlin"
        }
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, params=params, headers=headers, timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        st.error(f"Fehler beim Abrufen der Wetterdaten: {e}")
    return None

def get_mountain_temp():
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": 46.8,
            "longitude": 10.55,
            "elevation": 2100,
            "hourly": "temperature_2m",
            "forecast_days": 1,
            "timezone": "Europe/Berlin"
        }
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, params=params, headers=headers, timeout=10)
        if r.status_code == 200:
            return r.json()['hourly']
    except Exception as e:
        st.error(f"Fehler beim Abrufen der Berg-Temperaturdaten: {e}")
    return {"temperature_2m": []}

def get_pressure(city_name):
    st.info(f"Druckdaten für {city_name} werden simuliert.")
    if city_name == "bozen":
        return 1012.3
    elif city_name == "innsbruck":
        return 1007.9
    return None
    try:
        url = f"https://www.wetterkontor.de/de/wetter/{city_id}"
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        text = soup.find(string=lambda t: "Luftdruck" in t)
        import re
        if text:
            m = re.search(r"(\d{3,4}\.\d)", text)
            if m:
                return float(m.group(1))
    except Exception as e:
        st.warning(f"Fehler beim Abrufen des Luftdrucks für {city_id}: {e}")
    return None

def is_kiteable(wind_dir):
    return (140 <= wind_dir <= 220) or (wind_dir >= 330 or wind_dir <= 30)

st.set_page_config(page_title="Kite Forecast Reschensee+", layout="centered")
st.title("🏄 Kite Forecast Reschensee (mit erweiterten Wetterdaten)")

forecast_data = get_forecast()
st.write("✅ Forecast geladen:", forecast_data is not None)
mountain_temp_data = get_mountain_temp()
st.write("✅ Bergdaten geladen:", mountain_temp_data is not None)
bozen_pressure = get_pressure("bozen")
st.write("🧪 Druck Bozen:", bozen_pressure)
innsbruck_pressure = get_pressure("innsbruck")
st.write("🧪 Druck Innsbruck:", innsbruck_pressure)
diff_pressure = bozen_pressure - innsbruck_pressure if bozen_pressure and innsbruck_pressure else None

# Föhnbewertung
foehn_score = 0
if diff_pressure is not None:
    if diff_pressure <= -6:
        föhn_score = +10
        föhn_status = "Starker Nordföhn"
    elif diff_pressure <= -4:
        föhn_score = +5
        föhn_status = "Leichter Nordföhn"
    elif diff_pressure <= 0:
        föhn_score = 0
        föhn_status = "Neutral"
    elif diff_pressure <= 4:
        föhn_score = +5
        föhn_status = "Leichter Südföhn"
    else:
        föhn_score = +10
        föhn_status = "Starker Südföhn"
else:
    föhn_status = "Unbekannt"

if forecast_data is None:
    st.error("❌ Wetterdaten konnten nicht geladen werden.")
    st.stop()

# Forecast DataFrame
df_data = {
    "Date": [], "Hour": [], "Wind Speed": [], "Wind Dir": [],
    "Cloud Cover": [], "Temp": [], "Temp_Mountain": [],
    "Gusts": [], "Precip": [], "UV": []
}

for i in range(len(forecast_data['hourly']['time'])):
    dt = datetime.fromisoformat(forecast_data['hourly']['time'][i])
    df_data["Date"].append(dt.date())
    df_data["Hour"].append(dt.hour)
    df_data["Wind Speed"].append(forecast_data['hourly']['windspeed_10m'][i])
    df_data["Wind Dir"].append(forecast_data['hourly']['winddirection_10m'][i])
    df_data["Cloud Cover"].append(forecast_data['hourly']['cloudcover'][i])
    df_data["Temp"].append(forecast_data['hourly']['temperature_2m'][i])
    mt = mountain_temp_data['temperature_2m'][i] if i < len(mountain_temp_data['temperature_2m']) else None
    df_data["Temp_Mountain"].append(mt)
    df_data["Gusts"].append(forecast_data['hourly']['gusts_10m'][i])
    df_data["Precip"].append(forecast_data['hourly']['precipitation_probability'][i])
    df_data["UV"].append(forecast_data['hourly']['uv_index'][i])

forecast_df = pd.DataFrame(df_data)

# Tagesbewertung
daily_scores = []
for date, group in forecast_df.groupby("Date"):
    kite_hours = group[((group["Hour"].between(11, 18)) & (group["Wind Dir"].between(140, 220))) |
                       ((group["Hour"].between(8, 12)) & ((group["Wind Dir"] >= 330) | (group["Wind Dir"] <= 30))) &
                       (group["Wind Speed"] >= 6.0)]

    cloud_morning = group[(group["Hour"] >= 6) & (group["Hour"] <= 10)]["Cloud Cover"].mean()
    temp_tal = group[(group["Hour"] >= 9) & (group["Hour"] <= 10)]["Temp"].mean()
    temp_berg = group[(group["Hour"] >= 9) & (group["Hour"] <= 10)]["Temp_Mountain"].mean()
    gust_max = group["Gusts"].max()
    precip_prob = group["Precip"].max()
    uv_index = group["UV"].max()
    delta_temp = temp_tal - temp_berg if temp_tal and temp_berg else None

    score = föhn_score
    if cloud_morning < 30:
        score += 20
    elif cloud_morning < 60:
        score += 10
    else:
        score -= 10

    if delta_temp and delta_temp >= 6:
        score += 25
    elif delta_temp and delta_temp >= 3:
        score += 10
    else:
        score -= 5

    score += len(kite_hours) * 12

    if gust_max and gust_max > 40:
        score -= 15

    if precip_prob > 40:
        score -= 20

    if uv_index > 6:
        score += 5

    
    if brightness:
        if brightness < 80:
            score -= 15
        elif brightness < 150:
            score += 0
        else:
            score += 10

    if score >= 75:
        status = "🟢 Go"
    elif score >= 50:
        status = "🟡 Risky"
    else:
        status = "🔴 No Go"

    daily_scores.append({
        "Date": date,
        "CloudAvg6-10": cloud_morning,
        "TempDiff_Berg-Tal": delta_temp,
        "KiteableHours": len(kite_hours),
        "PressureDiff": diff_pressure,
        "Föhnlage": föhn_status,
        "Max Gust": gust_max,
        "Precip Prob": precip_prob,
        "UV Index": uv_index,
        "Score": score,
        "Status": status
    })

score_df = pd.DataFrame(daily_scores)
st.subheader("📊 Kite Forecast Übersicht")
st.dataframe(score_df)

fig, ax = plt.subplots(figsize=(10, 4))
ax.bar(score_df['Date'].astype(str), score_df['Score'], color='skyblue')
ax.set_title("Kite Score (Reschensee)")
ax.set_ylabel("Score")
ax.set_xlabel("Datum")
ax.grid(True)
st.pyplot(fig)

st.markdown(f"**Bozen Druck:** {bozen_pressure} hPa")
st.markdown(f"**Innsbruck Druck:** {innsbruck_pressure} hPa")
st.markdown(f"**Druckdifferenz:** {diff_pressure:.2f} hPa" if diff_pressure else "Keine Druckdifferenz verfügbar")
st.markdown(f"**Föhnlage:** {föhn_status}")

st.subheader("🌩️ Gewitterradar")
components.iframe("https://www.wetteronline.de/radar/tirol", height=500)

st.subheader("🌤 Live Webcam Reschenpass")


from PIL import Image
from io import BytesIO

def analyze_webcam_image(url):
    try:
        response = requests.get(url, timeout=10)
        image = Image.open(BytesIO(response.content)).convert("L")  # Graustufen
        brightness = sum(image.getdata()) / (image.width * image.height)
        return brightness
    except Exception as e:
        st.warning(f"Webcam nicht analysierbar: {e}")
        return None

# 🌅 Analyse der Webcam-Helligkeit
st.subheader("📷 Webcam Reschensee (Livebild mit Analyse)")
webcam_url = "https://images-webcams.windy.com/48/1652791148/current/full/1652791148.jpg"
brightness = analyze_webcam_image(webcam_url)
st.write("🔎 Webcam-Helligkeit:", brightness)
st.image(webcam_url, caption=f"Live Webcam – Helligkeit: {brightness:.2f}" if brightness else "Live Webcam", use_column_width=True)

if brightness:
    if brightness < 80:
        st.warning("🔴 Das Bild wirkt sehr dunkel – evtl. bewölkt oder zu früh/spät.")
    elif brightness < 150:
        st.info("🟡 Mäßige Helligkeit – eventuell teils bewölkt.")
    else:
        st.success("🟢 Helle Bedingungen – gute Sonnenwahrscheinlichkeit.")





# 🔍 3-Tage-Vorhersage mit Tagesbewertung

st.markdown("## ℹ️ So entsteht die Kite-Vorhersage")

st.markdown("""
Die Ampelbewertung und der Tages-Score basieren auf einer gewichteten Auswertung folgender Wetterfaktoren:

| Faktor                    | Wirkung auf Score              |
|---------------------------|--------------------------------|
| **Windrichtung**         | Nur Nord (330–30°) & Süd (140–220°) sind kitebar (+10) |
| **Windgeschwindigkeit**  | Optimal > 14 km/h (+10), schwach < 8 km/h (–15) |
| **Böenstärke**           | Starke Böen > 35 km/h (–5)     |
| **Regenwahrscheinlichkeit** | > 40 % (–10)                 |
| **UV-Index**             | Hoch > 6 (+5 für Thermikanzeichen) |
| **Bewölkung**            | Gering < 30 % (+5)             |
| **Föhndiagramm (Druck Bozen – Innsbruck)** | > +4 hPa = Südföhn (+10) / < –4 hPa = Nordföhn (+5) |
| **Webcam-Helligkeit**    | Sehr dunkel = –15, sonnig = +10 |

Die Bewertung wird für **heute und die folgenden 2 Tage** berechnet. Zusätzlich kannst du Details pro Tag aufklappen.

### 🧭 Quellen der Wetterdaten

- **Open-Meteo API** (https://open-meteo.com) – Wind, Temperatur, UV, Regen, Wolken, Böen
- **Webcam Reschenpass** (Windy): Live-Bild zur Sonnen- & Helligkeitserkennung
- **Simulierte Druckdaten** (Bozen/Innsbruck): Normalerweise via wetterring.at oder wetterkontor.de
""")

st.header("📅 3-Tage-Kite-Vorhersage")
from datetime import timedelta

# Hilfsfunktion für Tagesbewertung
def evaluate_day(day_index, forecast_data, bozen_pressure, innsbruck_pressure):
    score = 50
    info = []

    wind_speed = forecast_data["hourly"]["windspeed_10m"][day_index * 24 + 14]  # ca. 14 Uhr
    wind_dir = forecast_data["hourly"]["winddirection_10m"][day_index * 24 + 14]
    gusts = forecast_data["hourly"]["gusts_10m"][day_index * 24 + 14]
    precip = forecast_data["hourly"]["precipitation_probability"][day_index * 24 + 14]
    uv = forecast_data["hourly"]["uv_index"][day_index * 24 + 14]
    cloud = forecast_data["hourly"]["cloudcover"][day_index * 24 + 14]

    direction = "Süd" if 140 <= wind_dir <= 220 else "Nord" if wind_dir >= 330 or wind_dir <= 30 else "unkitebar"
    info.append(f"💨 Windrichtung: {direction} ({wind_dir}°)")

    if direction == "unkitebar":
        score -= 30
    else:
        score += 10

    info.append(f"🌬 Wind: {wind_speed} km/h")
    if wind_speed >= 14:
        score += 10
    elif wind_speed < 8:
        score -= 15

    info.append(f"💥 Böen: {gusts} km/h")
    if gusts > 35:
        score -= 5

    info.append(f"🌧 Niederschlag: {precip}%")
    if precip > 40:
        score -= 10

    info.append(f"🔆 UV-Index: {uv}")
    if uv > 6:
        score += 5

    info.append(f"☁️ Bewölkung: {cloud}%")
    if cloud < 30:
        score += 5

    # Druckdifferenz simuliert
    pressure_diff = bozen_pressure - innsbruck_pressure
    if pressure_diff >= 4:
        score += 10
        info.append(f"🌀 Südföhn: +10 (ΔP={pressure_diff:.1f} hPa)")
    elif pressure_diff <= -4:
        score += 5
        info.append(f"🌬 Nordföhn: +5 (ΔP={pressure_diff:.1f} hPa)")

    # Bewertung
    if score >= 75:
        amp = "🟢 Gut kitebar"
    elif score >= 50:
        amp = "🟡 Möglich"
    else:
        amp = "🔴 Nicht empfehlenswert"

    return score, amp, info

# Ausgabe für 3 Tage
for i in range(3):
    date = datetime.today() + timedelta(days=i)
    st.subheader(date.strftime("📅 %A, %d. %B %Y"))
    score, amp, details = evaluate_day(i, forecast_data, bozen_pressure, innsbruck_pressure)
    st.markdown(f"**Tages-Score:** {score} – {amp}")
    with st.expander("🔎 Details anzeigen"):
        for line in details:
            st.markdown(line)

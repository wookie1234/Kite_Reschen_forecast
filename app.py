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

def get_pressure(city_id):
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
mountain_temp_data = get_mountain_temp()
bozen_pressure = get_pressure("stadt.asp?land=IT&id=11560")
innsbruck_pressure = get_pressure("stadt.asp?land=AT&id=11115")
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

st.subheader(" Live Webcam Reschenpass")
components.iframe("https://kiteboarding-reschen.eu/webcam-reschenpass/", height=450)

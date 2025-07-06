import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from PIL import Image
from io import BytesIO
import numpy as np
import os
import time

# Konfiguration
LAT, LON = 46.836, 10.508
TIMEZONE = "Europe/Berlin"
WEBCAM_URL = "https://images-webcams.windy.com/48/1652791148/current/full/1652791148.jpg"

st.set_page_config(page_title="Kite Forecast Reschensee", layout="wide")
st.title("Kite Forecast Reschensee")

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
        st.error(f"Wetterdaten konnten nicht geladen werden: {e}")
        return None

# Webcam analysieren + Anzeige
def analyze_webcam_image():
    try:
        ts = int(time.time())
        url = f"{WEBCAM_URL}?nocache={ts}"
        res = requests.get(url, timeout=10)
        timestamp = datetime.now().strftime("%d.%m.%Y %H:%M Uhr")

        img = Image.open(BytesIO(res.content)).convert("L")
        np_img = np.array(img)
        brightness = np.mean(np_img)

        st.image(img, caption=f"Aktuelles Webcam-Bild (Stand: {timestamp})", use_container_width=True)

        st.markdown("**Bildhelligkeit (Webcam-Analyse):**")
        st.progress(min(int(brightness), 255) / 255)

        if brightness > 130:
            st.info("Helligkeit: **klarer Himmel / gute Sicht**")
        elif brightness > 90:
            st.warning("Helligkeit: **wolkig oder diesig**")
        else:
            st.error("Helligkeit: **sehr dunkel oder schlechte Sicht**")

        return brightness
    except Exception as e:
        st.warning(f"Webcam konnte nicht analysiert werden: {e}")
        return None

# Bewertung Tagesbedingungen
def evaluate_day(wind_avg, wind_dir, clouds, rain, uv, brightness):
    score = 0
    notes = {}

    if 10 <= wind_avg <= 25:
        score += 2
        notes["Windgeschwindigkeit"] = "Gut"
    elif 7 <= wind_avg < 10 or 25 < wind_avg <= 30:
        score += 1
        notes["Windgeschwindigkeit"] = "Grenzwertig"
    else:
        notes["Windgeschwindigkeit"] = "Nicht geeignet"

    if wind_dir <= 30 or wind_dir >= 340 or (150 <= wind_dir <= 210):
        score += 2
        notes["Windrichtung"] = "Gut"
    else:
        score -= 1
        notes["Windrichtung"] = "Nicht geeignet"

    if rain < 30:
        score += 1
        notes["Regenwahrscheinlichkeit"] = "Gering"
    elif rain < 60:
        notes["Regenwahrscheinlichkeit"] = "Mittel"
    else:
        notes["Regenwahrscheinlichkeit"] = "Hoch"

    if clouds < 50:
        score += 1
        notes["Bewölkung"] = "Gering"
    else:
        notes["Bewölkung"] = "Hoch"

    if uv > 5:
        score += 1
        notes["UV-Index"] = "Hoch"
    else:
        notes["UV-Index"] = "Niedrig"

    if brightness and brightness > 100:
        score += 1
        notes["Webcam-Helligkeit"] = "Hell"
    else:
        notes["Webcam-Helligkeit"] = "Dunkel oder nicht verfügbar"

    if score >= 7:
        status = "Sehr gut"
    elif score >= 4:
        status = "Bedingt geeignet"
    else:
        status = "Nicht geeignet"

    return score, status, notes

# Tagesvorschau anzeigen
def show_forecast(data, webcam_brightness):
    df = pd.DataFrame(data["hourly"])
    df["time"] = pd.to_datetime(df["time"])
    df.set_index("time", inplace=True)

    st.subheader("4-Tages-Kitevorschau")

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

        score, status, notes = evaluate_day(wind_avg, wind_dir, clouds, rain, daily_uv, webcam_brightness)

        st.markdown(f"### {day} – Bewertung: **{status}** ({score}/8 Punkte)")
        st.write(pd.DataFrame(notes.items(), columns=["Faktor", "Bewertung"]))

        with st.expander("Details"):
            st.write(f"- Ø Windgeschwindigkeit: {wind_avg:.1f} km/h")
            st.write(f"- Windrichtung (Median): {wind_dir:.0f}°")
            st.write(f"- Regenwahrscheinlichkeit (max): {rain:.0f}%")
            st.write(f"- Bewölkung: {clouds:.0f}%")
            st.write(f"- Temperatur: {temp:.1f}°C")
            st.write(f"- UV-Index: {daily_uv}")
            if webcam_brightness:
                st.write(f"- Webcam-Helligkeit: {webcam_brightness:.0f}")

# Erklärung Bewertung
def show_scoring_explanation():
    st.markdown("### Bewertungskriterien (max. 8 Punkte)")
    st.markdown("""
    - **Windgeschwindigkeit**: 10–25 km/h (2 Pkt), 7–10 oder 25–30 km/h (1 Pkt)
    - **Windrichtung**: Nord/Süd optimal (2 Pkt), andere Richtungen (0 oder -1)
    - **Niederschlag**: <30% = 1 Pkt
    - **Bewölkung**: <50% = 1 Pkt
    - **UV-Index**: >5 = 1 Pkt
    - **Webcam-Helligkeit**: Heller als 100 = 1 Pkt
    """)

# Hauptausführung
data = fetch_weather_data()
webcam_brightness = analyze_webcam_image()

if data:
    show_forecast(data, webcam_brightness)
    show_scoring_explanation()

# --- Feedback-Bereich ---
st.markdown("---")
st.header("Feedback einreichen")

with st.form("feedback_form"):
    st.subheader("Wie waren die Bedingungen für dich?")
    col1, col2 = st.columns(2)

    with col1:
        wind_rating = st.slider("Windbewertung (1 = kein Wind, 5 = zu stark)", 1, 5, 3)
        board_type = st.selectbox("Board-Typ", ["Twintip", "Foilboard", "Waveboard"])
        kite_type = st.selectbox("Kite-Typ", ["Tubekite", "Foilkite"])
    with col2:
        kite_size = st.text_input("Kite-Größe (in m²)", "")
        weight = st.text_input("Körpergewicht (in kg)", "")
        feedback_date = st.date_input("Datum", value=datetime.today().date())

    comment = st.text_area("Kommentar (optional)")
    submitted = st.form_submit_button("Absenden")

    if submitted:
        feedback_data = {
            "Datum": feedback_date,
            "Windbewertung": wind_rating,
            "Board": board_type,
            "Kite-Typ": kite_type,
            "Kite-Größe": kite_size,
            "Gewicht": weight,
            "Kommentar": comment
        }

        feedback_file = "feedback.csv"
        df_new = pd.DataFrame([feedback_data])
        if os.path.exists(feedback_file):
            df_old = pd.read_csv(feedback_file)
            df_all = pd.concat([df_old, df_new], ignore_index=True)
        else:
            df_all = df_new
        df_all.to_csv(feedback_file, index=False)

        st.success("Feedback wurde gespeichert.")

# Anzeige der bisherigen Feedbacks
st.markdown("### Öffentliche Feedbacks")
if os.path.exists("feedback.csv"):
    df_fb = pd.read_csv("feedback.csv")
    st.dataframe(df_fb)
else:
    st.info("Noch kein Feedback vorhanden.")

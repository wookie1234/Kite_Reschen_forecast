import streamlit as st
import requests
import pandas as pd
import os
from datetime import datetime, timedelta
from PIL import Image
from io import BytesIO
import matplotlib.pyplot as plt

# -------------------------------
# SETTINGS
# -------------------------------
LAT, LON = 46.836, 10.508  # Reschensee
FORECAST_URL = (
    "https://api.open-meteo.com/v1/forecast?"
    f"latitude={LAT}&longitude={LON}"
    "&hourly=windspeed_10m,winddirection_10m,cloudcover,temperature_2m,precipitation_probability"
    "&daily=uv_index_max,sunshine_duration"
    "&forecast_days=4&timezone=Europe%2FBerlin"
)
WEBCAM_URL = "https://images-webcams.windy.com/48/1652791148/current/full/1652791148.jpg"

# -------------------------------
# UTILS
# -------------------------------

def load_forecast():
    try:
        response = requests.get(FORECAST_URL)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"❌ Wetterdaten konnten nicht geladen werden: {e}")
        return None

def get_hourly_dataframe(data):
    hourly = data["hourly"]
    df = pd.DataFrame(hourly)
    df["time"] = pd.to_datetime(df["time"])
    return df

def fetch_webcam_image():
    try:
        response = requests.get(WEBCAM_URL)
        response.raise_for_status()
        timestamp = response.headers.get("Date", "Unbekannt")
        return Image.open(BytesIO(response.content)), timestamp
    except:
        return None, "Fehler beim Laden des Webcam-Bildes"

def hourly_evaluation(df_day):
    df_window = df_day[(df_day["time"].dt.hour >= 12) & (df_day["time"].dt.hour <= 17)]
    hourly_scores = []
    for _, row in df_window.iterrows():
        s = 0
        if 135 <= row["winddirection_10m"] <= 225:
            s += 1
            if row["windspeed_10m"] > 15:
                s += 1
        elif (row["winddirection_10m"] >= 315 or row["winddirection_10m"] <= 45) and row["windspeed_10m"] > 10:
            s -= 1
        if row["cloudcover"] < 60:
            s += 1
        if row["temperature_2m"] > 16:
            s += 1
        hourly_scores.append(s)
    return hourly_scores

def analyze_day(df_day):
    hourly_scores = hourly_evaluation(df_day)
    score = sum(hourly_scores)
    details = {
        "Summe der stündlichen Bewertungen (12–17 Uhr)": score
    }
    return score, details, hourly_scores

def show_ampel(score):
    if score >= 12:
        st.success("🟢 Sehr guter Kitetag")
    elif score >= 8:
        st.warning("🟡 Solider Kitetag mit Unsicherheiten")
    elif score >= 4:
        st.info("🟠 Schwacher Kitetag")
    else:
        st.error("🔴 Keine Kitesession zu erwarten")
import cv2
import numpy as np
from PIL import Image
from io import BytesIO

def fetch_and_analyze_foehn_diagram(url="https://static-weather.services.siag.it/sys/pgradient_de.png"):
    try:
        response = requests.get(url)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content)).convert("RGB")
        img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        hsv = cv2.cvtColor(img_cv, cv2.COLOR_BGR2HSV)

        # Rotfilter (zwei Bereiche in HSV)
        lower_red1 = np.array([0, 100, 100])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([160, 100, 100])
        upper_red2 = np.array([179, 255, 255])

        mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        mask = cv2.bitwise_or(mask1, mask2)

        points = np.column_stack(np.where(mask > 0))
        if len(points) == 0:
            return None, "Keine rote Linie erkannt"

        # Extrahiere mittlere y-Position pro x (um glatte Linie zu erzeugen)
        x_coords = points[:, 1]
        y_coords = points[:, 0]
        curve = {}
        for x in range(min(x_coords), max(x_coords)):
            y_vals = y_coords[x_coords == x]
            if len(y_vals) > 0:
                curve[x] = np.mean(y_vals)

        # Werte interpolieren (auf ~12–17 Uhr Zeitfenster normieren)
        sorted_curve = dict(sorted(curve.items()))
        y_vals = list(sorted_curve.values())
        mean_pressure_line = np.mean(y_vals[:100])  # grobe Annahme: links = heute

        # Bewertung:
        if mean_pressure_line < 180:  # je tiefer im Bild, desto stärker der Südföhn (Pixel: oben = 0)
            score = 2  # starker Südföhn
        elif mean_pressure_line < 220:
            score = 1  # moderater Südföhn
        elif mean_pressure_line > 260:
            score = -2  # starker Nordföhn
        elif mean_pressure_line > 240:
            score = -1  # leichter Nordföhn
        else:
            score = 0

        return score, "Föhnscore berechnet"
    except Exception as e:
        return None, f"Föhndiagramm konnte nicht geladen werden: {e}"

# -------------------------------
# UI
# -------------------------------
st.set_page_config(layout="centered")
st.title("Kite Forecast Reschensee - mit Webcam")

foehn_score, foehn_message = fetch_and_analyze_foehn_diagram()
st.markdown(f"### 🧭 Föhndiagramm-Analyse: {foehn_message}")
if foehn_score is not None:
    st.markdown(f"**Föhn-Score für heute:** {foehn_score}")


data = load_forecast()
if data:
    df = get_hourly_dataframe(data)
    today = datetime.now().date()

    for offset in range(3):
        current_day = today + timedelta(days=offset)
        st.markdown(f"## 📅 {current_day.strftime('%A, %d.%m.%Y')}")
        df_day = df[df["time"].dt.date == current_day]

        score, details, hourly_scores = analyze_day(df_day)
        show_ampel(score)

        # Chart anzeigen
        st.markdown("**📊 Bewertung je Stunde (12–17 Uhr)**")
        fig, ax = plt.subplots()
        ax.plot(range(12, 18), hourly_scores, marker="o")
        ax.set_xticks(range(12, 18))
        ax.set_xlabel("Uhrzeit")
        ax.set_ylabel("Score")
        ax.set_title("Stündlicher Bewertungsverlauf")
        st.pyplot(fig)

        with st.expander("Details zur Bewertung anzeigen"):
            for k, v in details.items():
                st.write(f"{k}: {v}")

        if offset == 0:
            st.markdown("#### 📷 Webcam")
            img, ts = fetch_webcam_image()
            if img:
                st.image(img, caption=f"Webcam-Bild (geladen: {ts})", use_container_width=True)
            else:
                st.error("Webcam-Bild konnte nicht geladen werden.")
else:
    st.stop()

def analyze_day(df_day, foehn_score=0):
    ...
    score += foehn_score
    details["Föhndiagramm Einfluss"] = f"{'✅' if foehn_score > 0 else '❌'} ({foehn_score:+})"
    ...


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

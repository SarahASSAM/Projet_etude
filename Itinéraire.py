import streamlit as st
import requests
import os
import folium
import polyline
import certifi
from dotenv import load_dotenv
from streamlit_folium import st_folium
from datetime import datetime, time as dt_time
import time
import hashlib

# Charger la clé API
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Configuration
st.set_page_config(page_title="Itinéraire intelligent", layout="wide")

# En-tête
st.markdown(
    f"""
    <h1 style='text-align: center; color: #2866C1;'>🗺️ Calculateur d'itinéraire avec carte interactive</h1>
    <p style='text-align: center;'>Entrez vos points de départ et d'arrivée pour visualiser votre trajet sur une carte élégante.</p>
    <p style='text-align: center; font-size: 14px;'>🕒 {datetime.now().strftime("%A %d %B %Y à %H:%M:%S")}</p>
    """,
    unsafe_allow_html=True
)

# Session init
if "transit_cache" not in st.session_state:
    st.session_state.transit_cache = {}
    st.session_state.transport_options = []
    st.session_state.standard_route = {}

# Fonctions

def to_unix_timestamp(date, heure):
    dt = datetime.combine(date, heure)
    return int(time.mktime(dt.timetuple()))

def hash_polyline(polyline_str):
    return hashlib.md5(polyline_str.encode()).hexdigest()

def get_directions(origin, destination, mode, departure_time=None):
    url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": origin,
        "destination": destination,
        "mode": mode,
        "key": GOOGLE_API_KEY
    }
    if mode == "transit":
        params["alternatives"] = "true"
        if departure_time:
            params["departure_time"] = departure_time
    return requests.get(url, params=params, verify=certifi.where()).json()

def afficher_carte(points, tiles_style):
    m = folium.Map(location=points[0], zoom_start=13, tiles=tiles_style)
    folium.Marker(points[0], tooltip="Départ", icon=folium.Icon(color="green")).add_to(m)
    folium.Marker(points[-1], tooltip="Arrivée", icon=folium.Icon(color="red")).add_to(m)
    folium.PolyLine(points, color="blue", weight=5).add_to(m)
    return m

# Formulaire
with st.form("formulaire"):
    col1, col2 = st.columns(2)
    with col1:
        origin = st.text_input("📍 Point de départ", "12 Rue Voltaire, Nantes")
        destination = st.text_input("🏁 Point d'arrivée", "Gare de Nantes")
        mode_label = st.selectbox("🚦 Mode de transport", ["Voiture 🚗", "Marche 🚶", "Vélo 🚴", "Transports en commun 🚌🚊"])
    with col2:
        date_depart = st.date_input("📅 Date de départ", datetime.today())
        heure_depart = st.time_input("🕒 Heure de départ", dt_time(hour=9, minute=0))
        theme = st.selectbox("🎨 Style de carte", ["OpenStreetMap", "CartoDB positron", "CartoDB dark_matter"])

    submitted = st.form_submit_button("🚀 Calculer mon itinéraire")

# Traitement
mode_map = {
    "Voiture 🚗": "driving",
    "Marche 🚶": "walking",
    "Vélo 🚴": "bicycling",
    "Transports en commun 🚌🚊": "transit"
}
mode = mode_map.get(mode_label, "driving")

if submitted:
    if mode != "transit":
        response = get_directions(origin, destination, mode)
        if response["status"] == "OK":
            leg = response["routes"][0]["legs"][0]
            points = polyline.decode(response["routes"][0]["overview_polyline"]["points"])
            st.session_state.standard_route = {
                "points": points,
                "distance": leg['distance']['text'],
                "duration": leg['duration']['text']
            }
            st.session_state.transport_options = []
        else:
            st.error("Erreur API")
            st.session_state.standard_route = {}
    else:
        timestamp = to_unix_timestamp(date_depart, heure_depart)
        data = get_directions(origin, destination, mode, timestamp)
        if data["status"] == "OK":
            seen_hashes = set()
            routes = []
            for route in data["routes"]:
                poly_str = route["overview_polyline"]["points"]
                hash_val = hash_polyline(poly_str)
                if hash_val not in seen_hashes:
                    seen_hashes.add(hash_val)
                    routes.append(route)
            options = []
            for idx, route in enumerate(routes):
                leg = route["legs"][0]
                transit = [s for s in leg["steps"] if s["travel_mode"] == "TRANSIT"]
                desc = []
                for step in transit:
                    l = step["transit_details"]["line"]
                    desc.append(f"{l.get('vehicle', {}).get('type', '?')} {l.get('short_name', '?')}")
                label = f"Itinéraire {idx+1} – {' + '.join(desc)} – {leg['duration']['text']}"
                options.append((label, route))
            st.session_state.transport_options = options
            st.session_state.standard_route = {}
        else:
            st.error("Aucun itinéraire trouvé")
            st.session_state.transport_options = []

# Affichage standard
if st.session_state.standard_route:
    r = st.session_state.standard_route
    st.success(f"📏 {r['distance']} – ⏱ {r['duration']}")
    st_folium(afficher_carte(r['points'], theme), width=1000, height=550)

# Affichage transport en commun
if st.session_state.transport_options and mode == "transit":
    st.markdown("### 🚊 Choisissez une option :")
    labels = [opt[0] for opt in st.session_state.transport_options]
    selected = st.radio("Itinéraires disponibles", labels)
    for label, route in st.session_state.transport_options:
        if label == selected:
            leg = route["legs"][0]
            points = polyline.decode(route["overview_polyline"]["points"])
            st.success(f"📏 {leg['distance']['text']} – ⏱ {leg['duration']['text']}")
            steps = [s for s in leg["steps"] if s["travel_mode"] == "TRANSIT"]
            for step in steps:
                t = step["transit_details"]
                l = t["line"]
                st.markdown(
                    f"- 🚌 Ligne **{l.get('short_name', '?')}** ({l.get('vehicle', {}).get('type', '?')}) "
                    f"de **{t['departure_stop']['name']}** → **{t['arrival_stop']['name']}** "
                    f"({t['num_stops']} arrêts) – 🏁 Terminus : **{t['headsign']}**"
                )
            st_folium(afficher_carte(points, theme), width=1000, height=500)

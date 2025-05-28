import streamlit as st

# ➤ Configuration de la page (doit être tout en haut)
st.set_page_config(page_title="Prédictions transport TAN", layout="wide")

import pandas as pd
from sqlalchemy import create_engine
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

# Chargement unique des données et des modèles
@st.cache_resource
def charger_et_preparer():
    engine = create_engine("postgresql+psycopg2://postgres:postgres123@localhost:5432/ml_prediction")
    df = pd.read_sql("SELECT * FROM trafic_arrets", engine)

    # Nettoyage
    df['temps'] = df['temps'].astype(str).str.replace("mn", "").str.strip()
    df['temps'] = pd.to_numeric(df['temps'], errors='coerce')
    df = df.dropna(subset=['temps'])

    cat_cols = ['codeArret', 'LibelleArret', 'terminus', 'numLigne', 'typeLigne', 'codeArret.1', 'ModeTransport']
    encoders = {}
    for col in cat_cols:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col].astype(str))
        encoders[col] = le

    for col in ['dernierDepart', 'tempsReel', 'infotrafic']:
        df[col] = df[col].astype(int)

    df['Date'] = pd.to_datetime(df['Date'])
    df['jour_semaine'] = df['Date'].dt.dayofweek

    features = ['codeArret', 'sens', 'terminus', 'dernierDepart', 'tempsReel', 'infotrafic',
                'numLigne', 'typeLigne', 'ModeTransport', 'jour_semaine']
    X = df[features]

    models = {
        'temps': RandomForestRegressor(n_estimators=100, random_state=42).fit(X, df['temps']),
        'infotrafic': RandomForestClassifier(n_estimators=100, random_state=42).fit(X, df['infotrafic']),
        'tempsReel': RandomForestClassifier(n_estimators=100, random_state=42).fit(X, df['tempsReel']),
        'dernierDepart': RandomForestClassifier(n_estimators=100, random_state=42).fit(X, df['dernierDepart'])
    }

    return df, encoders, models

# Chargement
df, encoders, models = charger_et_preparer()

# === Interface utilisateur ===
st.title("🚌 Application de Prédictions pour le Réseau TAN")
st.markdown("Prédisez différents éléments liés aux arrêts de transport à Nantes : **temps d’attente, incident, temps réel, dernier départ**.")

# === Sidebar pour les paramètres ===
st.sidebar.header("Paramètres de la situation")

mode = st.sidebar.radio("Quel élément voulez-vous prédire ?", [
    "Temps d’attente (en minutes)",
    "Incident trafic (oui/non)",
    "Disponibilité du temps réel",
    "Dernier départ"
])

# Choix utilisateur
def encode(col, val):
    return encoders[col].transform([val])[0]

codeArret = st.sidebar.selectbox("Code arrêt", sorted(encoders['codeArret'].classes_))
sens = st.sidebar.selectbox("Sens", sorted(df['sens'].dropna().unique()))
terminus = st.sidebar.selectbox("Terminus", sorted(encoders['terminus'].classes_))
tempsReel = st.sidebar.checkbox("Temps réel disponible", True)
infotrafic = st.sidebar.checkbox("Incident trafic", False)
dernierDepart = st.sidebar.checkbox("Dernier départ", False)
numLigne = st.sidebar.selectbox("Numéro de ligne", sorted(encoders['numLigne'].classes_))
typeLigne = st.sidebar.selectbox("Type de ligne", sorted(encoders['typeLigne'].classes_))
modeTransport = st.sidebar.selectbox("Mode de transport", sorted(encoders['ModeTransport'].classes_))
jour_semaine = st.sidebar.slider("Jour de la semaine (0 = Lundi)", 0, 6, 0)

# Construction de la ligne d'entrée
input_data = [[
    encode('codeArret', codeArret),
    sens,
    encode('terminus', terminus),
    int(dernierDepart),
    int(tempsReel),
    int(infotrafic),
    encode('numLigne', numLigne),
    encode('typeLigne', typeLigne),
    encode('ModeTransport', modeTransport),
    jour_semaine
]]

# === Affichage de la prédiction ===
st.divider()

if st.button("📊 Lancer la prédiction"):

    if mode == "Temps d’attente (en minutes)":
        prediction = models['temps'].predict(input_data)[0]
        st.success(f"⏱ Temps d’attente estimé : **{prediction:.1f} minutes**")

    elif mode == "Incident trafic (oui/non)":
        prediction = models['infotrafic'].predict(input_data)[0]
        st.success("⚠️ Incident probable" if prediction else "✅ Aucun incident prévu")

    elif mode == "Disponibilité du temps réel":
        prediction = models['tempsReel'].predict(input_data)[0]
        st.success("✅ Temps réel disponible" if prediction else "❌ Pas de données temps réel")

    elif mode == "Dernier départ":
        prediction = models['dernierDepart'].predict(input_data)[0]
        st.success("🕑 C’est le **dernier départ** de la journée" if prediction else "▶️ Il reste encore des départs")

import streamlit as st
import pandas as pd
import datetime
from sqlalchemy import create_engine
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split

st.set_page_config(page_title="Prédictions transport TAN", layout="wide")

@st.cache_resource
def charger_et_preparer():
    engine = create_engine("postgresql+psycopg2://postgres:postgres123@localhost:5432/ml_prediction")
    df = pd.read_sql("SELECT * FROM trafic_arrets", engine)

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
    df['heure_en_minutes'] = df['Date'].dt.hour * 60 + df['Date'].dt.minute

    features = ['codeArret', 'sens', 'terminus', 'dernierDepart', 'tempsReel', 'infotrafic',
                'numLigne', 'typeLigne', 'ModeTransport', 'jour_semaine', 'heure_en_minutes']
    X = df[features]

    X_train, X_test, y_temps_train, y_temps_test = train_test_split(X, df['temps'], test_size=0.2, random_state=42)
    _, _, y_infotrafic_train, y_infotrafic_test = train_test_split(X, df['infotrafic'], test_size=0.2, random_state=42)
    _, _, y_tempsReel_train, y_tempsReel_test = train_test_split(X, df['tempsReel'], test_size=0.2, random_state=42)
    _, _, y_dernier_train, y_dernier_test = train_test_split(X, df['dernierDepart'], test_size=0.2, random_state=42)

    models = {
        'temps': RandomForestRegressor(n_estimators=100, random_state=42).fit(X_train, y_temps_train),
        'infotrafic': RandomForestClassifier(n_estimators=100, random_state=42).fit(X_train, y_infotrafic_train),
        'tempsReel': RandomForestClassifier(n_estimators=100, random_state=42).fit(X_train, y_tempsReel_train),
        'dernierDepart': RandomForestClassifier(n_estimators=100, random_state=42).fit(X_train, y_dernier_train)
    }

    return df, encoders, models

df, encoders, models = charger_et_preparer()

st.title("🚌 Prédictions pour le Réseau de Transport TAN")

st.sidebar.header("🔹 Paramètres")

codeArret = st.sidebar.selectbox("Départ - Code de l'arrêt", sorted(encoders['codeArret'].classes_))
terminus = st.sidebar.selectbox("Terminus", sorted(encoders['terminus'].classes_))
sens_label = st.sidebar.selectbox("Sens du trajet", ["Aller", "Retour"])
sens = 1 if sens_label == "Aller" else 2

tempsReel = st.sidebar.checkbox("Temps réel disponible", True)
infotrafic = st.sidebar.checkbox("Incident trafic", False)
dernierDepart = st.sidebar.checkbox("Dernière course", False)
numLigne = st.sidebar.selectbox("Numéro de ligne", sorted(encoders['numLigne'].classes_))
typeLigne = st.sidebar.selectbox("Type de ligne", sorted(encoders['typeLigne'].classes_))
modeTransport = st.sidebar.selectbox("Mode de transport", sorted(encoders['ModeTransport'].classes_))
date_depart = st.sidebar.date_input("📅 Date de départ", value=datetime.date.today())
heure_depart = st.sidebar.time_input("🕒 Heure de départ", value=datetime.time(8, 0))

jour_semaine = date_depart.weekday()
heure_en_minutes = heure_depart.hour * 60 + heure_depart.minute

def encode(col, val):
    return encoders[col].transform([val])[0]

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
    jour_semaine,
    heure_en_minutes
]]

st.subheader("🔍 Choisissez une prédiction :")
choix = st.radio("", [
    "Temps d'attente",
    "Incident trafic",
    "Temps réel disponible",
    "Dernière course"
])

if st.button("📊 Prédire"):
    st.markdown(f"### 🎯 Résultat pour la ligne **{numLigne}**, sens **{sens_label}**, terminus **{terminus}**")

    if choix == "Temps d'attente":
        pred = models['temps'].predict(input_data)[0]
        st.success(f"🕛 Temps d'attente estimé : {pred:.1f} minutes")

    elif choix == "Incident trafic":
        pred = models['infotrafic'].predict(input_data)[0]
        st.success("⚠️ Incident prévu" if pred else "✅ Aucun incident prévu")

    elif choix == "Temps réel disponible":
        pred = models['tempsReel'].predict(input_data)[0]
        st.success("✅ Temps réel disponible" if pred else "❌ Non disponible")

    elif choix == "Dernière course":
        pred = models['dernierDepart'].predict(input_data)[0]
        st.success("🕒 C'est la dernière course" if pred else "➡️ Encore des départs")

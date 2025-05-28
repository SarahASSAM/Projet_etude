import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, accuracy_score

# Connexion PostgreSQL
engine = create_engine("postgresql+psycopg2://postgres:postgres123@localhost:5432/ml_prediction")
df = pd.read_sql("SELECT * FROM trafic_arrets", engine)

# Nettoyage colonne 'temps'
df['temps'] = df['temps'].astype(str).str.replace("mn", "").str.strip()
df['temps'] = pd.to_numeric(df['temps'], errors='coerce')
df = df.dropna(subset=['temps'])

# Encodage des colonnes catégorielles
cat_cols = ['codeArret', 'LibelleArret', 'terminus', 'numLigne', 'typeLigne', 'codeArret.1', 'ModeTransport']
label_encoders = {}
for col in cat_cols:
    le = LabelEncoder()
    df[col] = le.fit_transform(df[col].astype(str))
    label_encoders[col] = le

# Conversion des booléens
for col in ['dernierDepart', 'tempsReel', 'infotrafic']:
    df[col] = df[col].astype(int)

# Date en jour de semaine
df['Date'] = pd.to_datetime(df['Date'])
df['jour_semaine'] = df['Date'].dt.dayofweek

# Définition des variables
features = ['codeArret', 'sens', 'terminus', 'dernierDepart', 'tempsReel', 'infotrafic',
            'numLigne', 'typeLigne', 'ModeTransport', 'jour_semaine']

# Création des modèles
X = df[features]

# 1. Modèle pour le temps d'attente
y_temps = df['temps']
model_temps = RandomForestRegressor(n_estimators=100, random_state=42)
model_temps.fit(X, y_temps)

# 2. Modèle pour incident trafic
y_info = df['infotrafic']
model_info = RandomForestClassifier(n_estimators=100, random_state=42)
model_info.fit(X, y_info)

# 3. Modèle pour disponibilité du temps réel
y_real = df['tempsReel']
model_real = RandomForestClassifier(n_estimators=100, random_state=42)
model_real.fit(X, y_real)

# 4. Modèle pour dernier départ
y_dernier = df['dernierDepart']
model_dernier = RandomForestClassifier(n_estimators=100, random_state=42)
model_dernier.fit(X, y_dernier)

# Interface Streamlit
st.title("🚌 Multi-Prédiction des données de transport TAN")

# Choix utilisateur
st.subheader("Saisir les paramètres de la situation :")

def get_user_input():
    codeArret = st.selectbox("Code arrêt", sorted(label_encoders['codeArret'].classes_))
    sens = st.selectbox("Sens", sorted(df['sens'].dropna().unique()))
    terminus = st.selectbox("Terminus", sorted(label_encoders['terminus'].classes_))
    tempsReel = st.checkbox("Temps réel disponible", value=True)
    infotrafic = st.checkbox("Incident trafic", value=False)
    dernierDepart = st.checkbox("Dernier départ", value=False)
    numLigne = st.selectbox("Numéro de ligne", sorted(label_encoders['numLigne'].classes_))
    typeLigne = st.selectbox("Type de ligne", sorted(label_encoders['typeLigne'].classes_))
    modeTransport = st.selectbox("Mode de transport", sorted(label_encoders['ModeTransport'].classes_))
    jour_semaine = st.slider("Jour de la semaine (0=Lundi, 6=Dimanche)", 0, 6, 0)

    # Encodage
    def encode(col, val):
        return label_encoders[col].transform([val])[0]

    row = [[
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
    return row

# Sélection du type de prédiction
mode = st.radio("Quel type de prédiction souhaitez-vous ?", [
    "Temps d’attente (en minutes)",
    "Incident trafic (oui/non)",
    "Disponibilité du temps réel",
    "Dernier départ"
])

# Bouton pour prédire
if st.button("📊 Lancer la prédiction"):
    row = get_user_input()

    if mode == "Temps d’attente (en minutes)":
        prediction = model_temps.predict(row)[0]
        st.success(f"⏱ Temps d’attente estimé : {prediction:.1f} minutes")

    elif mode == "Incident trafic (oui/non)":
        prediction = model_info.predict(row)[0]
        st.success("⚠️ Incident probable" if prediction else "✅ Aucun incident prévu")

    elif mode == "Disponibilité du temps réel":
        prediction = model_real.predict(row)[0]
        st.success("✅ Temps réel disponible" if prediction else "❌ Pas de temps réel")

    elif mode == "Dernier départ":
        prediction = model_dernier.predict(row)[0]
        st.success("🕑 C'est le dernier départ" if prediction else "▶️ Pas le dernier départ")

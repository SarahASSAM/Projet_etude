import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder

# Connexion à la base PostgreSQL
engine = create_engine("postgresql+psycopg2://postgres:postgres123@localhost:5432/ml_prediction")
df = pd.read_sql("SELECT * FROM trafic_arrets", engine)

# Nettoyage de la colonne 'temps'
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

# Autres transformations
df['dernierDepart'] = df['dernierDepart'].astype(int)
df['tempsReel'] = df['tempsReel'].astype(int)
df['infotrafic'] = df['infotrafic'].astype(int)
df['Date'] = pd.to_datetime(df['Date'])
df['jour_semaine'] = df['Date'].dt.dayofweek

# Données d'entraînement
features = ['codeArret', 'sens', 'terminus', 'dernierDepart', 'tempsReel', 'infotrafic',
            'numLigne', 'typeLigne', 'ModeTransport', 'jour_semaine']
X = df[features]
y = df['temps']

# Entraînement du modèle
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X, y)

# Interface Streamlit
st.title("🚌 Prédiction du Temps d’Attente à un Arrêt TAN")

# Champs utilisateur avec les vraies valeurs texte
codeArret = st.selectbox("Code arrêt", sorted(label_encoders['codeArret'].classes_))
sens = st.selectbox("Sens", sorted(df['sens'].dropna().unique()))
terminus = st.selectbox("Terminus", sorted(label_encoders['terminus'].classes_))
dernierDepart = st.checkbox("Dernier départ", value=False)
tempsReel = st.checkbox("Temps réel disponible", value=True)
infotrafic = st.checkbox("Incident trafic", value=False)
numLigne = st.selectbox("Numéro de ligne", sorted(label_encoders['numLigne'].classes_))
typeLigne = st.selectbox("Type de ligne", sorted(label_encoders['typeLigne'].classes_))
modeTransport = st.selectbox("Mode de transport", sorted(label_encoders['ModeTransport'].classes_))
jour_semaine = st.slider("Jour de la semaine (0=Lundi, 6=Dimanche)", 0, 6, 0)

# Fonction pour encoder
def encode(col, value):
    return label_encoders[col].transform([value])[0]

# Création du vecteur d'entrée
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

# Bouton de prédiction
if st.button("📊 Prédire le temps d’attente"):
    prediction = model.predict(input_data)[0]
    st.success(f"⏱ Temps d’attente estimé : {prediction:.1f} minutes")

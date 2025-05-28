import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error
from sqlalchemy import create_engine

# Connexion à PostgreSQL
engine = create_engine("postgresql+psycopg2://postgres:postgres123@localhost:5432/ml_prediction")
df = pd.read_sql("SELECT * FROM trafic_arrets", engine)

# Nettoyage de la colonne 'temps' (ex: "2mn" → 2.0)
df['temps'] = df['temps'].astype(str).str.replace("mn", "").str.strip()
df['temps'] = pd.to_numeric(df['temps'], errors='coerce')
df = df.dropna(subset=['temps'])

# Encodage des colonnes texte
cat_cols = ['codeArret', 'LibelleArret', 'terminus', 'numLigne', 'typeLigne', 'codeArret.1', 'ModeTransport']
label_encoders = {}
for col in cat_cols:
    le = LabelEncoder()
    df[col] = le.fit_transform(df[col].astype(str))
    label_encoders[col] = le

# Conversion des booléens + ajout jour de la semaine
df['dernierDepart'] = df['dernierDepart'].astype(int)
df['tempsReel'] = df['tempsReel'].astype(int)
df['infotrafic'] = df['infotrafic'].astype(int)
df['Date'] = pd.to_datetime(df['Date'])
df['jour_semaine'] = df['Date'].dt.dayofweek

# Définition des variables
features = ['codeArret', 'sens', 'terminus', 'dernierDepart', 'tempsReel', 'infotrafic',
            'numLigne', 'typeLigne', 'ModeTransport', 'jour_semaine']
X = df[features]
y = df['temps']

# Split + Entraînement
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Évaluation
y_pred = model.predict(X_test)
mae = mean_absolute_error(y_test, y_pred)
print(f"✅ Modèle entraîné avec succès | Erreur MAE : {mae:.2f} minutes")

# Exemple de prédiction manuelle
exemple = X_test.iloc[0:1]
predicted = model.predict(exemple)[0]
print("\n🎯 Prédiction sur un exemple :")
print(f"Données d'entrée :\n{exemple}")
print(f"Temps d’attente estimé : {predicted:.1f} minutes")

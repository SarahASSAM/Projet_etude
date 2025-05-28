import pandas as pd
from sqlalchemy import create_engine
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, accuracy_score

# Connexion à la base PostgreSQL
engine = create_engine("postgresql+psycopg2://postgres:postgres123@localhost:5432/ml_prediction")
df = pd.read_sql("SELECT * FROM trafic_arrets", engine)

# Nettoyage
df['temps'] = df['temps'].astype(str).str.replace("mn", "").str.strip()
df['temps'] = pd.to_numeric(df['temps'], errors='coerce')
df = df.dropna(subset=['temps'])

# Encodage des colonnes catégorielles
cat_cols = ['codeArret', 'LibelleArret', 'terminus', 'numLigne', 'typeLigne', 'codeArret.1', 'ModeTransport']
encoders = {}
for col in cat_cols:
    le = LabelEncoder()
    df[col] = le.fit_transform(df[col].astype(str))
    encoders[col] = le

for col in ['dernierDepart', 'tempsReel', 'infotrafic']:
    df[col] = df[col].astype(int)

# Features temporelles
df['Date'] = pd.to_datetime(df['Date'])
df['jour_semaine'] = df['Date'].dt.dayofweek
df['heure_en_minutes'] = df['Date'].dt.hour * 60 + df['Date'].dt.minute

# Variables explicatives
features = ['codeArret', 'sens', 'terminus', 'dernierDepart', 'tempsReel', 'infotrafic',
            'numLigne', 'typeLigne', 'ModeTransport', 'jour_semaine', 'heure_en_minutes']
X = df[features]

# Données cibles
y_temps = df['temps']
y_infotrafic = df['infotrafic']
y_tempsReel = df['tempsReel']
y_dernier = df['dernierDepart']

# Séparation train/test
X_train, X_test, y_train_temps, y_test_temps = train_test_split(X, y_temps, test_size=0.2, random_state=42)
_, _, y_train_infotrafic, y_test_infotrafic = train_test_split(X, y_infotrafic, test_size=0.2, random_state=42)
_, _, y_train_tempsReel, y_test_tempsReel = train_test_split(X, y_tempsReel, test_size=0.2, random_state=42)
_, _, y_train_dernier, y_test_dernier = train_test_split(X, y_dernier, test_size=0.2, random_state=42)

# Entraînement
model_temps = RandomForestRegressor(n_estimators=100, random_state=42)
model_temps.fit(X_train, y_train_temps)

model_infotrafic = RandomForestClassifier(n_estimators=100, random_state=42)
model_infotrafic.fit(X_train, y_train_infotrafic)

model_tempsReel = RandomForestClassifier(n_estimators=100, random_state=42)
model_tempsReel.fit(X_train, y_train_tempsReel)

model_dernier = RandomForestClassifier(n_estimators=100, random_state=42)
model_dernier.fit(X_train, y_train_dernier)

# Évaluation
mae_temps = mean_absolute_error(y_test_temps, model_temps.predict(X_test))
acc_infotrafic = accuracy_score(y_test_infotrafic, model_infotrafic.predict(X_test))
acc_tempsReel = accuracy_score(y_test_tempsReel, model_tempsReel.predict(X_test))
acc_dernier = accuracy_score(y_test_dernier, model_dernier.predict(X_test))

# Résultats
print("📊 Évaluation des modèles :")
print(f"⏱ Temps d'attente - MAE : {mae_temps:.2f} minutes")
print(f"⚠️ Incident trafic - Accuracy : {acc_infotrafic * 100:.2f} %")
print(f"📶 Temps réel dispo - Accuracy : {acc_tempsReel * 100:.2f} %")
print(f"🕒 Dernier départ - Accuracy : {acc_dernier * 100:.2f} %")

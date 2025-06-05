import pandas as pd
import requests
from datetime import datetime
import certifi
from sqlalchemy import create_engine

# ✅ Connexion à PostgreSQL : base ML_prediction
engine = create_engine("postgresql+psycopg2://postgres:postgres123@localhost:5432/ML_prediction?sslmode=disable")

# ✅ Lecture du fichier des arrêts
arrets_df = pd.read_csv("stops copy.txt", encoding='utf-8')[['stop_id', 'stop_name', 'stop_lat', 'stop_lon']]
arrets_df = arrets_df.rename(columns={
    "stop_id": "codeArret",
    "stop_name": "libelleArret"
})

now = datetime.now()
print(f"📡 Récupération à {now.strftime('%H:%M:%S')}...")

resultats = []

for _, row in arrets_df.iterrows():
    code_arret = row["codeArret"]
    libelle_arret = row["libelleArret"]
    stop_lat = row["stop_lat"]
    stop_lon = row["stop_lon"]

    url = f"https://open.tan.fr/ewp/tempsattente.json/{code_arret}"

    try:
        response = requests.get(url, timeout=5, verify=certifi.where())
        response.raise_for_status()
        data = response.json()

        for element in data:
            ligne = element.get("ligne", {})
            arret = element.get("arret", {})

            resultats.append({
                "sens": element.get("sens", None),
                "terminus": element.get("terminus", ""),
                "infotrafic": element.get("infotrafic", ""),
                "temps": element.get("temps", ""),
                "dernierDepart": element.get("dernierDepart", ""),
                "tempsReel": element.get("tempsReel", ""),
                "ligne": ligne.get("numLigne", "") if isinstance(ligne, dict) else ligne,
                "arret": arret.get("codeArret", "") if isinstance(arret, dict) else arret,
                "date_requete": now,
                "codeArret": code_arret,
                "libelleArret": libelle_arret,
                "stop_lat": stop_lat,
                "stop_lon": stop_lon
            })

        print(f"✅ Données reçues pour l'arrêt {code_arret}")

    except Exception as e:
        print(f"❌ Erreur pour l'arrêt {code_arret} : {e}")

# ✅ Insertion automatique dans PostgreSQL
if resultats:
    df = pd.DataFrame(resultats)

    # Nettoyage UTF-8 léger pour éviter les erreurs d'encodage
    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].astype(str).apply(lambda x: x.encode('utf-8', errors='ignore').decode('utf-8'))

    df.to_sql("localisation", con=engine, if_exists="append", index=False)
    print(f"📥 {len(df)} lignes insérées dans la table 'localisation'.")
else:
    print("⚠️ Aucune donnée à insérer.")

print("✅ Fin de traitement.")

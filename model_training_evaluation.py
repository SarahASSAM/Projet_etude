import pandas as pd
import requests
import time
from datetime import datetime, timedelta
import certifi
from sqlalchemy import create_engine, inspect, text

# ✅ Connexion à PostgreSQL
engine = create_engine("postgresql+psycopg2://postgres:postgres123@localhost:5432/ml_prediction?sslmode=disable")

# ✅ Lecture des arrêts depuis le fichier
arrets_df = pd.read_csv("stops.txt", encoding='utf-8')[['stop_id', 'stop_name', 'stop_lat', 'stop_lon']]
arrets_df = arrets_df.rename(columns={"stop_id": "codearret", "stop_name": "libellearret"})

# ✅ Fenêtre horaire : 17h30 à 17h45
heure_debut = datetime.now().replace(hour=17, minute=30, second=0, microsecond=0)
heure_fin = datetime.now().replace(hour=17, minute=45, second=0, microsecond=0)

# ✅ Nom de la table
table_name = "temps_reel_fenetre"
interval_minutes = 5
next_collect_time = datetime.now()

print(f"🚀 Démarrage de la collecte entre {heure_debut.strftime('%H:%M')} et {heure_fin.strftime('%H:%M')} dans la table '{table_name}'.")

# ✅ Vérification et création/recréation de la table si nécessaire
def verifier_et_recreer_table_si_necessaire(df, table_name, engine):
    inspector = inspect(engine)
    if table_name in inspector.get_table_names():
        colonnes_existantes = [col["name"] for col in inspector.get_columns(table_name)]
        colonnes_df = df.columns.tolist()
        if set(colonnes_df) != set(colonnes_existantes):
            print("⚠️ Colonnes incompatibles, recréation de la table.")
            with engine.begin() as conn:
                conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
                df.head(0).to_sql(table_name, con=engine, if_exists="replace", index=False)
        else:
            print("✅ Table existante compatible.")
    else:
        print("🛠️ Création de la table car elle n'existe pas.")
        df.head(0).to_sql(table_name, con=engine, if_exists="replace", index=False)

# 🔁 Boucle de collecte dans la plage horaire
while True:
    now = datetime.now()

    if now > heure_fin:
        print("⏹️ Fin de la fenêtre horaire. Arrêt du script.")
        break

    if now >= next_collect_time and heure_debut <= now <= heure_fin:
        print(f"📡 Récupération à {now.strftime('%H:%M:%S')}...")
        resultats = []

        for _, row in arrets_df.iterrows():
            code_arret = row["codearret"]
            libelle_arret = row["libellearret"]
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

        if resultats:
            df_resultats = pd.DataFrame(resultats)
            verifier_et_recreer_table_si_necessaire(df_resultats, table_name, engine)
            df_resultats.to_sql(table_name, con=engine, if_exists="append", index=False)
            print(f"📥 {len(df_resultats)} lignes insérées dans '{table_name}'.")
        else:
            print("⚠️ Aucune donnée à insérer.")

        next_collect_time = now + timedelta(minutes=interval_minutes)
        print("⏳ Attente de la prochaine collecte...\n")
    else:
        print(f"🕒 En attente... ({now.strftime('%H:%M:%S')})")
        time.sleep(10)

print(f"✅ Fin de collecte. Données enregistrées dans la table '{table_name}'.")

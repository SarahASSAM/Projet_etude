import pandas as pd

# Charger le fichier (premier onglet par défaut)
df = pd.read_excel(r"MachineLearning - Prediction des trafics dans les arrêts ou le temps d'attente.xlsx")

print(df.head())


import pandas as pd
from sqlalchemy import create_engine

# 1. Chemin du fichier Excel
excel_path = r"C:\Users\sarah\Desktop\ml prediction\MachineLearning - Prediction des trafics dans les arrêts ou le temps d'attente.xlsx"


# 2. Charger l'onglet Feuil1
df = pd.read_excel(excel_path, sheet_name="Feuil1", engine="openpyxl")

# 3. Connexion à ta base PostgreSQL 'ml_prediction'
engine = create_engine("postgresql+psycopg2://postgres:postgres123@localhost:5432/ml_prediction")

# 4. Exporter vers PostgreSQL dans une table nommée 'trafic_arrets'
df.to_sql("trafic_arrets", engine, if_exists="replace", index=False)

print("✅ Données importées avec succès dans la table 'trafic_arrets'.")

import psycopg2

# Connexion à PostgreSQL (base par défaut)
conn = psycopg2.connect(
    dbname="postgres",
    user="postgres",
    password="postgres123",
    host="localhost",
    port="5432"
)
conn.autocommit = True
cur = conn.cursor()

# Création de la base
cur.execute("CREATE DATABASE ml_prediction;")

cur.close()
conn.close()
print("Base 'ml_prediction' créée avec succès.")
import pandas as pd

# Charger le fichier (premier onglet par défaut)
df = pd.read_excel("MachineLearning - Prediction des trafics dans les arrêts ou le temps d'attente.xlsx")

print(df.head())

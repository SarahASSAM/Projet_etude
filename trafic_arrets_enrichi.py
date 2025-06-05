from sqlalchemy import create_engine, text

# Connexion à ta base ML_prediction via SQLAlchemy
engine = create_engine("postgresql+psycopg2://postgres:postgres123@localhost:5432/ml_prediction")

# Requête de jointure
query = """
CREATE TABLE IF NOT EXISTS trafic_arrets_enrichi AS
SELECT 
    t1.*,
    t2.stop_lat,
    t2.stop_lon,
    t2.date_requete
FROM 
    trafic_arrets t1
JOIN 
    temps_reel_tan.temps_reel_collecte t2
ON 
    t1."codeArret" = t2."codeArret"
    AND t1."numLigne" = t2."ligne"
    AND t1."Date" = DATE(t2."date_requete");
"""

# Exécution de la requête
with engine.connect() as connection:
    try:
        connection.execute(text(query))
        print("✅ Table `trafic_arrets_enrichi` créée avec succès.")
    except Exception as e:
        print("❌ Erreur lors de la création :", e)

import pymongo
import pandas as pd
import os
import logging

# Configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_to_mongodb():
    # 1. Connexion à MongoDB Locale
    logger.info("🍃 Connexion à MongoDB...")
    client = pymongo.MongoClient("mongodb://localhost:27017/")
    
    # Créer la base de données "arxiv_db"
    db = client["arxiv_db"]
    
    # Créer la collection "papers" (l'équivalent d'une table en SQL)
    collection = db["papers"]
    
    # Vider la collection si elle existe pour éviter les doublons
    collection.delete_many({})
    
    cleaned_dir = "data_lake/cleaned"
    files = [f for f in os.listdir(cleaned_dir) if f.endswith('.parquet')]
    
    total_inserted = 0
    
    logger.info("=" * 70)
    logger.info("📤 CHARGEMENT DES DONNÉES DANS MONGODB")
    logger.info("=" * 70)
    
    # 2. Lire chaque fichier Parquet et l'insérer en masse
    for file in sorted(files):
        filepath = os.path.join(cleaned_dir, file)
        
        # Lire le Parquet (rapide et léger en mémoire)
        df = pd.read_parquet(filepath)
        
        # Convertir le DataFrame en liste de dictionnaires (format natif MongoDB)
        records = df.to_dict("records")
        
        # Insertion en masse (Bulk Insert) - Ultra rapide !
        if records:
            collection.insert_many(records)
            total_inserted += len(records)
            logger.info(f"✅ {len(records)} documents insérés depuis {file} (Total: {total_inserted})")
    
    # 3. Créer des Index (CRUCIAL pour la performance)
    logger.info("\n🚀 Création des Index pour des requêtes foudroyantes...")
    
    # Index sur la catégorie (pour filtrer par domaine)
    collection.create_index([("primary_category", pymongo.ASCENDING)])
    # Index sur l'année (pour filtrer par date)
    collection.create_index([("year", pymongo.ASCENDING)])
    
    logger.info("✅ Index créés !")
    
    logger.info("\n" + "=" * 70)
    logger.info(f"🎉 CHARGEMENT MONGODB TERMINÉ ! {total_inserted} documents dans la base.")
    logger.info("=" * 70)

if __name__ == "__main__":
    load_to_mongodb()
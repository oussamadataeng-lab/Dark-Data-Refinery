import pymongo
import logging
from datetime import datetime

# Configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_arxiv_data():
    # Connexion à MongoDB
    client = pymongo.MongoClient("mongodb://localhost:27017/")
    db = client["arxiv_db"]
    collection = db["papers"]
    
    logger.info("=" * 70)
    logger.info("📊 ANALYSE EXPLORATOIRE DES DONNÉES ARXIV (MONGODB)")
    logger.info("=" * 70)
    
    # ---------------------------------------------------------
    # REQUÊTE 1 : Les tendances de 2023 (Top Catégories)
    # ---------------------------------------------------------
    logger.info("\n📈 Top 10 des catégories scientifiques les plus publiées en 2023 :")
    
    pipeline_trends = [
        {"$match": {"year": "2023"}}, # Filtrer sur l'année 2023
        {"$group": {"_id": "$primary_category", "total": {"$sum": 1}}}, # Grouper et compter
        {"$sort": {"total": -1}}, # Trier par le plus grand
        {"$limit": 10} # Garder le Top 10
    ]
    
    results_trends = collection.aggregate(pipeline_trends)
    
    for idx, result in enumerate(results_trends, 1):
        print(f"  {idx}. {result['_id']:20} -> {result['total']} publications")
    
    # ---------------------------------------------------------
    # REQUÊTE 2 : Recherche ciblée (Intelligence Artificielle)
    # ---------------------------------------------------------
    logger.info("\n🤖 Dernières publications en Intelligence Artificielle (cs.AI) en 2024 :")
    
    query_ai = {
        "primary_category": "cs.AI", 
        "year": "2024"
    }
    
    # On ne récupère que le titre et la date, trié par date décroissante
    projection = {"_id": 0, "title": 1, "update_date": 1}
    
    results_ai = collection.find(query_ai, projection).sort("update_date", -1).limit(5)
    
    for idx, paper in enumerate(results_ai, 1):
        print(f"  {idx}. [{paper.get('update_date', 'N/A')}] {paper.get('title', 'No Title')}")
    
    # ---------------------------------------------------------
    # REQUÊTE 3 : Le Saviez-vous ? (Stats globales)
    # ---------------------------------------------------------
    logger.info("\n🌍 Statistiques Globales de l'archive :")
    
    total_papers = collection.count_documents({})
    oldest_paper = collection.find().sort("year", 1).limit(1)[0]
    newest_paper = collection.find().sort("year", -1).limit(1)[0]
    
    print(f"  📚 Nombre total de publications nettoyées : {total_papers:,}")
    print(f"  📅 La plus ancienne date de : {oldest_paper.get('year', '?')} ({oldest_paper.get('title', '?')[:50]}...)")
    print(f"  🆕 La plus récente date de : {newest_paper.get('year', '?')} ({newest_paper.get('title', '?')[:50]}...)")
    
    logger.info("\n" + "=" * 70)
    logger.info("✅ ANALYSE TERMINÉE")
    logger.info("=" * 70)

if __name__ == "__main__":
    analyze_arxiv_data()
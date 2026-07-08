from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from typing import List, Optional

# 1. Initialiser FastAPI
app = FastAPI(
    title="ArXiv Dark Data API",
    description="API pour interroger les publications scientifiques nettoyées",
    version="1.0"
)

# 2. Connexion à MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["arxiv_db"]
collection = db["papers"]

# ---------------------------------------------------------
# ROUTE 1 : Page d'accueil
# ---------------------------------------------------------
@app.get("/")
def root():
    return {
        "message": "Bienvenue sur l'API ArXiv Dark Data !",
        "endpoints": {
            "/search": "Rechercher par mot-clé (ex: /search?keyword=quantum)",
            "/top-categories/{year}": "Top catégories pour une année (ex: /top-categories/2023)",
            "/docs": "Documentation interactive de l'API"
        }
    }

# ---------------------------------------------------------
# ROUTE 2 : Recherche par mot-clé dans le titre
# ---------------------------------------------------------
@app.get("/search")
def search_papers(keyword: str, limit: int = 5):
    """
    Recherche des publications contenant un mot-clé dans le titre.
    Utilise une Regex MongoDB (insensible à la casse).
    """
    query = {"title": {"$regex": keyword, "$options": "i"}}
    
    # Ne récupérer que le titre, l'année et la catégorie
    projection = {"_id": 0, "title": 1, "year": 1, "primary_category": 1}
    
    results = list(collection.find(query, projection).limit(limit))
    
    if not results:
        raise HTTPException(status_code=404, detail=f"Aucune publication trouvée avec le mot '{keyword}'")
        
    return {"keyword": keyword, "results": results}

# ---------------------------------------------------------
# ROUTE 3 : Top des catégories pour une année donnée
# ---------------------------------------------------------
@app.get("/top-categories/{year}")
def top_categories(year: str, limit: int = 10):
    """
    Retourne le classement des catégories les plus publiées pour une année spécifique.
    Utilise le fameux Aggregation Pipeline !
    """
    pipeline = [
        {"$match": {"year": year}},
        {"$group": {"_id": "$primary_category", "total": {"$sum": 1}}},
        {"$sort": {"total": -1}},
        {"$limit": limit}
    ]
    
    results = list(collection.aggregate(pipeline))
    
    if not results:
        raise HTTPException(status_code=404, detail=f"Aucune donnée trouvée pour l'année {year}")
        
    return {"year": year, "top_categories": results}
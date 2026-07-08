import json
import re
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import os
import logging

# Configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- LES ARMES SECRETES : REGEX POUR NETTOYER LE LATEX ---
def clean_latex(text):
    """Nettoie les formules mathématiques LaTeX illisibles"""
    if not isinstance(text, str):
        return ""
    
    # Supprimer les équations mathématiques (ex: $\mathcal{L}$)
    text = re.sub(r'\$[^$]+\$', ' ', text)
    # Supprimer les commandes LaTeX (ex: \textit{mot} -> mot)
    text = re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', text)
    # Supprimer les accolades restantes
    text = re.sub(r'[{}]', '', text)
    # Remplacer les sauts de ligne \n par des espaces
    text = text.replace('\n', ' ').replace('\\n', ' ')
    # Nettoyer les multiples espaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def process_arxiv_data():
    input_file = 'data_lake/raw/arxiv-metadata-oai-snapshot.json'
    output_dir = 'data_lake/cleaned'
    
    os.makedirs(output_dir, exist_ok=True)
    
    logger.info("=" * 70)
    logger.info("🧹 DÉMARRAGE DU NETTOYAGE BIG DATA (STREAMING)")
    logger.info("=" * 70)
    
    # Variables pour le chunking (traitement par lots)
    chunk_size = 50000  # On traite 50 000 lignes à la fois
    chunk_number = 1
    current_chunk = []
    total_processed = 0
    
    # Ouvrir le fichier géant en mode lecture streaming
    with open(input_file, 'r', encoding='utf-8') as f:
        for line_number, line in enumerate(f):
            try:
                # 1. Lire la ligne JSON
                record = json.loads(line)
                
                # 2. Gestion des Schémas Manquants (Schema Evolution)
                # Certaines anciennes publications n'ont pas les mêmes clés
                authors = record.get('authors', '')
                categories = record.get('categories', '')
                
                # Extraire la catégorie principale (la première)
                primary_category = categories.split(' ')[0] if categories else 'unknown'
                
                # Extraire l'année (parfois 'update_date' manque)
                update_date = record.get('update_date', '1900-01-01')
                year = update_date[:4]
                
                # 3. Nettoyage LaTeX des textes
                title_clean = clean_latex(record.get('title', ''))
                abstract_clean = clean_latex(record.get('abstract', ''))
                
                # 4. Structurer la donnée propre
                clean_record = {
                    'id': record.get('id', ''),
                    'title': title_clean,
                    'abstract': abstract_clean,
                    'authors': authors,
                    'primary_category': primary_category,
                    'all_categories': categories,
                    'year': year,
                    'update_date': update_date
                }
                
                current_chunk.append(clean_record)
                
                # 5. Si le lot est plein, on sauvegarde en Parquet et on vide
                if len(current_chunk) >= chunk_size:
                    df = pd.DataFrame(current_chunk)
                    
                    # Sauvegarder en format Parquet (ultra compressé)
                    parquet_path = os.path.join(output_dir, f'arxiv_clean_chunk_{chunk_number}.parquet')
                    df.to_parquet(parquet_path, engine='pyarrow', index=False)
                    
                    total_processed += len(current_chunk)
                    logger.info(f"✅ Chunk {chunk_number} traité: {len(current_chunk)} lignes -> {parquet_path} (Total: {total_processed})")
                    
                    # Réinitialiser pour le prochain lot
                    current_chunk = []
                    chunk_number += 1
                    
            except json.JSONDecodeError:
                # Ignorer les lignes JSON corrompues (Data Quality en action !)
                logger.warning(f"⚠️ Ligne JSON corrompue ignorée à la ligne {line_number}")
                continue
            except Exception as e:
                logger.error(f"❌ Erreur inattendue ligne {line_number}: {str(e)}")
                continue

        # 6. Sauvegarder le dernier lot (s'il reste des données)
        if current_chunk:
            df = pd.DataFrame(current_chunk)
            parquet_path = os.path.join(output_dir, f'arxiv_clean_chunk_{chunk_number}.parquet')
            df.to_parquet(parquet_path, engine='pyarrow', index=False)
            total_processed += len(current_chunk)
            logger.info(f"✅ Dernier chunk {chunk_number} traité: {len(current_chunk)} lignes -> {parquet_path}")

    logger.info("=" * 70)
    logger.info(f"🎉 NETTOYAGE TERMINÉ ! {total_processed} publications scientifiques nettoyées !")
    logger.info("=" * 70)

if __name__ == "__main__":
    process_arxiv_data()
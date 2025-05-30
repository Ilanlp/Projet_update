import numpy as np
from sklearn.metrics import make_scorer
from sklearn.metrics.pairwise import cosine_similarity
import time
import logging

from jobmarket_ml.config.config import SCORING_CONFIG, LOG_CONFIG

# Configuration du logging
logging.basicConfig(
    level=LOG_CONFIG['level'],
    format=LOG_CONFIG['format'],
    datefmt=LOG_CONFIG['date_format']
)
logger = logging.getLogger(__name__)

def compute_similarity_score(estimator, X, df_candidats):
    """
    Calcule un score de similarité entre les offres et les profils candidats.
    
    Args:
        estimator: Pipeline d'estimation complet
        X: DataFrame des offres d'emploi (colonne TEXT)
        df_candidats: DataFrame des profils candidats (colonne TEXT)
    
    Returns:
        float: Score composite de similarité
    """
    start_time = time.time()
    
    try:
        logger.debug("Début de la transformation des textes en embeddings")
        # Obtenir les embeddings bruts avant le matching
        offres_embeddings = estimator.named_steps['encoder'].transform(
            estimator.named_steps['preprocessor'].transform(X)
        )
        candidats_embeddings = estimator.named_steps['encoder'].transform(
            estimator.named_steps['preprocessor'].transform(df_candidats)
        )
        
        # Normalisation des embeddings pour la similarité cosinus
        offres_norm = offres_embeddings / np.linalg.norm(offres_embeddings, axis=1)[:, np.newaxis]
        candidats_norm = candidats_embeddings / np.linalg.norm(candidats_embeddings, axis=1)[:, np.newaxis]
        
        # Calcul de la matrice de similarité
        similarity_matrix = np.dot(candidats_norm, offres_norm.T)
        
        # Calcul des différentes métriques
        scores = {
            'mean_similarity': np.mean(np.max(similarity_matrix, axis=1)),
            'diversity': np.mean(np.std(similarity_matrix, axis=1)),
            'coverage': np.mean(similarity_matrix > SCORING_CONFIG['similarity_threshold']),
            'computation_time': min(1.0, 2.0 / (time.time() - start_time))
        }
        
        # Utilisation des poids depuis la configuration
        weights = SCORING_CONFIG['weights']
        
        # Calcul du score final pondéré
        final_score = sum(weights[k] * v for k, v in scores.items())
        
        # Logging des scores détaillés
        logger.debug("Scores détaillés:")
        for metric, score in scores.items():
            logger.debug(f"{metric}: {score:.3f} (poids: {weights[metric]})")
        logger.debug(f"Score final: {final_score:.3f}")
        
        return final_score
        
    except Exception as e:
        logger.error(f"Erreur lors du calcul du score: {str(e)}")
        return 0.0

# Création du scorer pour GridSearchCV
matching_scorer = make_scorer(
    compute_similarity_score,
    needs_proba=False,
    needs_threshold=False
) 
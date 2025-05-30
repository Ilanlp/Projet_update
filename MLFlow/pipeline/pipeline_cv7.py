"""
Système de Recommandation Intelligent pour Matching d'Offres

Ce module fournit un système de recommandation basé sur des embeddings 
de texte et la recherche des plus proches voisins.
"""

# Imports standards
import logging
import os
from typing import List, Tuple, Dict, Any, Optional

# Gestion des ressources
import psutil
import torch

# Manipulation de données
import numpy as np
import pandas as pd

# Machine Learning
from sentence_transformers import SentenceTransformer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.neighbors import NearestNeighbors

# Logging configuration
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

class ConfigManager:
    """
    Gestionnaire de configuration avec validation et valeurs par défaut
    """
    DEFAULT_CONFIG = {
        'max_memory_usage': 70.0,
        'max_cpu_usage': 80.0,
        'embedding_batch_size': 32,
        'dimensionality_reduction': False,
        'reduction_components': 100,
        'use_gpu': torch.cuda.is_available(),
        'model_name': 'distilbert-base-nli-stsb-mean-tokens'
    }

    @classmethod
    def get_config(cls, custom_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Génère une configuration fusionnant les valeurs par défaut et personnalisées
        
        Args:
            custom_config (dict, optional): Configuration personnalisée
        
        Returns:
            dict: Configuration finale
        """
        config = cls.DEFAULT_CONFIG.copy()
        if custom_config:
            config.update(custom_config)
        return config

class ResourceMonitor:
    """
    Surveillance et gestion des ressources système
    """
    @staticmethod
    def check_resources() -> Dict[str, float]:
        """
        Vérifie les ressources système actuelles
        
        Returns:
            dict: Statistiques des ressources
        """
        mem = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent()
        
        resources = {
            'total_memory_gb': mem.total / (1024**3),
            'available_memory_gb': mem.available / (1024**3),
            'memory_percent_used': mem.percent,
            'cpu_percent': cpu_percent
        }
        
        for key, value in resources.items():
            logger.info(f"{key}: {value}")
        
        return resources

    @staticmethod
    def is_resource_available(config: Dict[str, Any]) -> bool:
        """
        Vérifie si les ressources sont suffisantes
        
        Args:
            config (dict): Configuration du système
        
        Returns:
            bool: Ressources suffisantes
        """
        mem = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent()
        
        return (
            mem.percent <= config['max_memory_usage'] and 
            cpu_percent <= config['max_cpu_usage']
        )

class EmbeddingGenerator:
    """
    Générateur d'embeddings avec gestion de la performance
    """
    def __init__(self, config: Dict[str, Any]):
        """
        Initialise le générateur d'embeddings
        
        Args:
            config (dict): Configuration du système
        """
        self.config = config
        self.model = self._init_model()
    
    def _init_model(self) -> SentenceTransformer:
        """
        Initialise le modèle Sentence Transformer
        
        Returns:
            SentenceTransformer: Modèle initialisé
        """
        device = 'cuda' if self.config['use_gpu'] and torch.cuda.is_available() else 'cpu'
        return SentenceTransformer(self.config['model_name'], device=device)
    
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Génère des embeddings pour une liste de textes
        
        Args:
            texts (list): Liste de textes
        
        Returns:
            np.ndarray: Embeddings générés
        """
        # Génération des embeddings
        embeddings = self.model.encode(
            texts, 
            show_progress_bar=True,
            batch_size=self.config['embedding_batch_size']
        )
        
        # Réduction de dimensionnalité optionnelle
        if self.config['dimensionality_reduction']:
            embeddings = self._reduce_dimensionality(embeddings)
        
        return embeddings
    
    def _reduce_dimensionality(self, embeddings: np.ndarray) -> np.ndarray:
        """
        Réduit la dimensionnalité des embeddings
        
        Args:
            embeddings (np.ndarray): Embeddings originaux
        
        Returns:
            np.ndarray: Embeddings réduits
        """
        if embeddings.shape[0] < 2:
            logger.warning("Impossible de réduire la dimensionnalité")
            return embeddings
        
        try:
            # Normalisation
            scaler = StandardScaler()
            scaled_embeddings = scaler.fit_transform(embeddings)
            
            # Réduction PCA
            reducer = PCA(
                n_components=min(
                    self.config['reduction_components'], 
                    scaled_embeddings.shape[1]
                ),
                random_state=42
            )
            reduced_embeddings = reducer.fit_transform(scaled_embeddings)
            
            logger.info(f"Variance expliquée : {reducer.explained_variance_ratio_.sum():.2%}")
            return reduced_embeddings
        
        except Exception as e:
            logger.error(f"Erreur de réduction : {e}")
            return embeddings

class RecommendationSystem:
    """
    Système de recommandation basé sur la similarité des embeddings
    """
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialise le système de recommandation
        
        Args:
            config (dict, optional): Configuration personnalisée
        """
        # Validation et génération de la configuration
        self.config = ConfigManager.get_config(config)
        
        # Vérification des ressources
        if not ResourceMonitor.is_resource_available(self.config):
            logger.warning("Ressources système limitées. Performances potentiellement réduites.")
        
        # Composants du système
        self.embedding_generator = EmbeddingGenerator(self.config)
        self.index = None
        self.original_texts = None
        self.embeddings = None
    
    def train(self, texts: List[str]) -> 'RecommendationSystem':
        """
        Entraîne le système de recommandation
        
        Args:
            texts (list): Liste de textes à indexer
        
        Returns:
            RecommendationSystem: Instance entraînée
        """
        # Validation des données
        if len(texts) < 2:
            logger.warning("Jeu de données insuffisant pour l'entraînement")
            return self
        
        try:
            # Génération des embeddings
            self.original_texts = texts
            self.embeddings = self.embedding_generator.generate_embeddings(texts)
            
            # Construction de l'index de recherche
            self.index = NearestNeighbors(
                n_neighbors=min(5, len(texts)),
                metric='cosine',
                algorithm='auto',
                n_jobs=-1
            )
            self.index.fit(self.embeddings)
            
            logger.info(f"Système entraîné avec {len(texts)} documents")
        
        except Exception as e:
            logger.error(f"Erreur lors de l'entraînement : {e}")
        
        return self
    
    def recommend(self, query: str, top_k: int = 5) -> List[Tuple[int, float]]:
        """
        Génère des recommandations pour une requête
        
        Args:
            query (str): Texte de requête
            top_k (int, optional): Nombre de recommandations
        
        Returns:
            list: Liste de tuples (index, score de similarité)
        """
        if self.index is None or self.original_texts is None:
            raise ValueError("Le modèle doit être entraîné avant recommandation")
        
        try:
            # Génération de l'embedding de requête
            query_embedding = self.embedding_generator.generate_embeddings([query])
            
            # Recherche des plus proches voisins
            distances, indices = self.index.kneighbors(query_embedding)
            
            # Formater les recommandations
            recommendations = list(zip(indices[0], 1 - distances[0]))
            
            return recommendations[:top_k]
        
        except Exception as e:
            logger.error(f"Erreur lors de la recommandation : {e}")
            return []

def load_data(file_path: str, text_columns: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Charge et prépare les données
    
    Args:
        file_path (str): Chemin du fichier
        text_columns (list, optional): Colonnes à combiner
    
    Returns:
        pd.DataFrame: DataFrame préparé
    """
    try:
        # Charger les données
        df = pd.read_csv(
            file_path,
            compression="gzip",
            sep=",",
            encoding="utf-8",
            nrows=1000,
        )

        # Colonnes par défaut si non spécifiées
        if text_columns is None:
            text_columns = [
                "TITLE", "DESCRIPTION", "TYPE_CONTRAT", "NOM_DOMAINE", 
                "VILLE", "DEPARTEMENT", "REGION", "PAYS", 
                "TYPE_SENIORITE", "NOM_ENTREPRISE", "CATEGORIE_ENTREPRISE", 
                "COMPETENCES", "TYPES_COMPETENCES", "SOFTSKILLS_SUMMARY", 
                "SOFTSKILLS_DETAILS", "NOM_METIER", "CODE_POSTAL"
            ]
        
        # Combiner les colonnes
        df["TEXT"] = df[text_columns].fillna("").astype(str).agg(". ".join, axis=1)
        
        return df
    
    except Exception as e:
        logger.error(f"Erreur lors du chargement des données : {e}")
        raise

def main():
    """
    Fonction principale de démonstration
    """
    # Configuration personnalisée
    config = {
        'dimensionality_reduction': False,
        'embedding_batch_size': 32,
        'model_name': 'paraphrase-multilingual-MiniLM-L12-v2'
    }
    
    try:
        # Chemin du fichier (à adapter)
        file_path = "../data/OnBigTable/one_big_table.csv.gz"
        
        # Charger les données
        df = load_data(file_path)
        
        # Initialiser le système de recommandation
        recommender = RecommendationSystem(config)
        
        # Entraînement
        recommender.train(df['TEXT'].values)
        
        # Exemple de requête
        query = "Développeur Python avec expérience en data science"
        recommendations = recommender.recommend(query)
        
        # Afficher les recommandations
        print(f"\nRecommandations pour : {query}")
        for idx, score in recommendations:
            print(f"Offre {idx} (similarité : {score:.2f}) : {df.iloc[idx]['TEXT'][:200]}...")
    
    except Exception as e:
        logger.error(f"Erreur d'exécution : {e}")

if __name__ == "__main__":
    # Configuration du logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s: %(message)s'
    )
    
    # Exécution du script
    main()

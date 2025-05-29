import os
import psutil
import logging
import numpy as np
import pandas as pd
import multiprocessing

# Machine Learning
import torch
from sentence_transformers import SentenceTransformer
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import StandardScaler

# Optimisation et performance
import mlflow
import mlflow.sklearn
from tqdm import tqdm

# Configuration et logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class PerformanceOptimizer:
    """
    Classe de gestion des contraintes de performance et mémoire
    """
    def __init__(self, config=None):
        """
        Configuration des paramètres de performance
        """
        # Configuration par défaut
        self.default_config = {
            'max_memory_usage': 70.0,  # 70% de mémoire max
            'max_cpu_usage': 80.0,     # 80% de CPU max
            'embedding_batch_size': 32,
            'dimensionality_reduction': True,
            'reduction_components': 100,
            'use_sparse_matrix': True,
            'use_gpu': torch.cuda.is_available()
        }
        
        # Fusion de la configuration
        self.config = self.default_config.copy()
        if config:
            self.config.update(config)
        
        # Vérification des ressources
        self._check_system_resources()
    
    def _check_system_resources(self):
        """
        Vérifie et log les ressources système disponibles
        """
        # Mémoire
        mem = psutil.virtual_memory()
        logger.info(f"Mémoire totale: {mem.total / (1024**3):.2f} Go")
        logger.info(f"Mémoire disponible: {mem.available / (1024**3):.2f} Go")
        logger.info(f"Pourcentage mémoire utilisée: {mem.percent}%")
        
        # CPU
        cpu_percent = psutil.cpu_percent()
        logger.info(f"Utilisation CPU: {cpu_percent}%")
        
        # GPU si disponible
        if self.config['use_gpu']:
            logger.info(f"GPU disponible: {torch.cuda.get_device_name(0)}")
            logger.info(f"Mémoire GPU: {torch.cuda.get_device_properties(0).total_memory / (1024**3):.2f} Go")
    
    def _adaptive_batch_size(self, total_samples):
        """
        Calcule dynamiquement la taille de batch
        """
        mem = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent()
        
        # Ajustement en fonction de l'utilisation mémoire et CPU
        if mem.percent > self.config['max_memory_usage'] or cpu_percent > self.config['max_cpu_usage']:
            return max(self.config['embedding_batch_size'] // 2, 1)
        
        return self.config['embedding_batch_size']
    
    def dimensionality_reduction(self, embeddings):
        """
        Réduction de dimensionnalité des embeddings avec gestion des cas particuliers
        """
        if not self.config['dimensionality_reduction']:
            return embeddings
        
        # Vérification du nombre de composants
        n_components = min(
            self.config['reduction_components'], 
            embeddings.shape[0],  # Limite au nombre d'échantillons
            embeddings.shape[1]   # Limite à la dimensionnalité originale
        )
        
        # Si trop peu de composants, retourner les embeddings originaux
        if n_components <= 1:
            logger.warning("Impossible de réduire la dimensionnalité. Retour aux embeddings originaux.")
            return embeddings
        
        # Normalisation avant réduction
        scaler = StandardScaler()
        scaled_embeddings = scaler.fit_transform(embeddings)
        
        # Réduction de dimensionnalité
        try:
            reducer = TruncatedSVD(
                n_components=n_components,
                random_state=42
            )
            reduced_embeddings = reducer.fit_transform(scaled_embeddings)
            
            # Log du ratio de variance expliquée
            logger.info(f"Variance expliquée par la réduction : {reducer.explained_variance_ratio_.sum():.2%}")
            
            return reduced_embeddings
        except Exception as e:
            logger.error(f"Erreur lors de la réduction de dimensionnalité : {e}")
            return scaled_embeddings
    
    def process_large_dataset(self, texts, batch_process_func, batch_size=None):
        """
        Traitement de grands ensembles de données par lots
        """
        if batch_size is None:
            batch_size = self._adaptive_batch_size(len(texts))
        
        results = []
        for i in tqdm(range(0, len(texts), batch_size), desc="Traitement par lots"):
            batch = texts[i:i+batch_size]
            results.extend(batch_process_func(batch))
        
        return results
    
    def memory_efficient_embedding(self, texts, model_name='distilbert-base-nli-stsb-mean-tokens'):
        """
        Génération d'embeddings avec contraintes mémoire
        """
        # Choix du device
        device = 'cuda' if self.config['use_gpu'] and torch.cuda.is_available() else 'cpu'
        
        # Chargement du modèle
        model = SentenceTransformer(model_name, device=device)
        
        def embedding_batch(batch):
            return model.encode(
                batch, 
                show_progress_bar=False,
                convert_to_numpy=True
            )
        
        # Traitement par lots
        embeddings = self.process_large_dataset(
            texts, 
            embedding_batch, 
            batch_size=self.config['embedding_batch_size']
        )
        
        # Conversion et réduction de dimensionnalité
        embeddings = np.array(embeddings)
        return self.dimensionality_reduction(embeddings)

class RecommendationSystem:
    """
    Système de recommandation optimisé pour la performance
    """
    def __init__(self, performance_config=None):
        self.optimizer = PerformanceOptimizer(performance_config)
        self.index = None
        self.original_texts = None
    
    def train(self, texts, model_name='distilbert-base-nli-stsb-mean-tokens'):
        """
        Entraînement du système de recommandation
        """
        # Sauvegarde des textes originaux
        self.original_texts = texts
        
        # Gestion du cas avec peu de données
        if len(texts) < 2:
            logger.warning("Jeu de données trop petit pour l'entraînement. Utilisez plus de données.")
            return self
        
        # Génération des embeddings
        logger.info("Génération des embeddings...")
        try:
            embeddings = self.optimizer.memory_efficient_embedding(
                texts, 
                model_name=model_name
            )
            
            # Vérification de la forme des embeddings
            if embeddings.ndim != 2:
                raise ValueError(f"Forme des embeddings incorrecte: {embeddings.shape}")
            
            # Construction de l'index de recherche
            from sklearn.neighbors import NearestNeighbors
            
            logger.info("Construction de l'index de recherche...")
            self.index = NearestNeighbors(
                n_neighbors=min(5, len(texts)),  # Limiter au nombre de textes 
                metric='cosine', 
                algorithm='auto',
                n_jobs=-1  # Utilisation de tous les cœurs
            )
            self.index.fit(embeddings)
        
        except Exception as e:
            logger.error(f"Erreur lors de l'entraînement : {e}")
        
        return self
    
    def recommend(self, query, top_k=5):
        """
        Génération de recommandations
        """
        if self.index is None or self.original_texts is None:
            raise ValueError("Le modèle doit être entraîné avant de faire des recommandations")
        
        try:
            # Génération de l'embedding de requête
            query_embedding = self.optimizer.memory_efficient_embedding(
                [query], 
                model_name='distilbert-base-nli-stsb-mean-tokens'
            )
            
            # Recherche des plus proches voisins
            distances, indices = self.index.kneighbors(query_embedding)
            
            # Formater les recommandations
            recommendations = list(zip(indices[0], 1 - distances[0]))
            
            return recommendations
        
        except Exception as e:
            logger.error(f"Erreur lors de la recommandation : {e}")
            return []

def main():
    # Configuration personnalisée de performance
    performance_config = {
        'max_memory_usage': 70.0,
        'max_cpu_usage': 80.0,
        'embedding_batch_size': 32,
        'dimensionality_reduction': True,
        'reduction_components': 100,
        'use_sparse_matrix': True,
        'use_gpu': torch.cuda.is_available()
    }
    
    # Charger les données
    try:
        df = pd.read_csv(
            "../data/OnBigTable/one_big_table.csv.gz",
            compression="gzip",
            sep=",",
            encoding="utf-8",
            nrows=1000,
        )
        
        # Préparation des données
        cols_o = [
            "TITLE", "DESCRIPTION", "TYPE_CONTRAT", "NOM_DOMAINE", 
            "VILLE", "DEPARTEMENT", "REGION", "PAYS", 
            "TYPE_SENIORITE", "NOM_ENTREPRISE", "CATEGORIE_ENTREPRISE", 
            "COMPETENCES", "TYPES_COMPETENCES", "SOFTSKILLS_SUMMARY", 
            "SOFTSKILLS_DETAILS", "NOM_METIER", "CODE_POSTAL"
        ]
        df["TEXT"] = df[cols_o].fillna("").astype(str).agg(". ".join, axis=1)
        
        # Initialisation du système de recommandation
        recommender = RecommendationSystem(performance_config)
        
        # Entraînement
        recommender.train(df['TEXT'].values)
        
        # Exemple de recommandation
        query = "Développeur Python avec expérience en data science"
        recommendations = recommender.recommend(query)
        
        print("\nRecommandations pour la requête :", query)
        for idx, score in recommendations:
            print(f"Offre {idx} (similarité : {score:.2f}) : {df.iloc[idx]['TEXT'][:200]}...")
    
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution : {e}")

if __name__ == "__main__":
    main()
import os
import psutil
import logging
import numpy as np
import pandas as pd
import multiprocessing

# Machine Learning
import torch
from sentence_transformers import SentenceTransformer
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD

# Optimisation et performance
import mlflow
import mlflow.sklearn
from tqdm import tqdm

# Configuration et logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class PerformanceOptimizer:
    """
    Classe de gestion des contraintes de performance et mémoire
    """
    def __init__(self, config=None):
        """
        Configuration des paramètres de performance
        
        Args:
            config (dict): Configuration personnalisée avec les clés suivantes:
                - max_memory_usage (float): Pourcentage max de mémoire utilisable (0-100)
                - max_cpu_usage (float): Pourcentage max de CPU utilisable (0-100)
                - embedding_batch_size (int): Taille de batch pour les embeddings
                - dimensionality_reduction (bool): Activer la réduction de dimensionnalité
                - reduction_components (int): Nombre de composants pour la réduction
                - use_sparse_matrix (bool): Utiliser des matrices creuses
                - use_gpu (bool): Utiliser le GPU si disponible
        """
        # Configuration par défaut
        self.default_config = {
            'max_memory_usage': 70.0,  # 70% de mémoire max
            'max_cpu_usage': 80.0,     # 80% de CPU max
            'embedding_batch_size': 32,
            'dimensionality_reduction': True,
            'reduction_components': 100,
            'use_sparse_matrix': True,
            'use_gpu': torch.cuda.is_available()
        }
        
        # Fusion de la configuration
        self.config = self.default_config.copy()
        if config:
            self.config.update(config)
        
        # Vérification des ressources
        self._check_system_resources()
    
    def _check_system_resources(self):
        """
        Vérifie et log les ressources système disponibles
        """
        # Mémoire
        mem = psutil.virtual_memory()
        logger.info(f"Mémoire totale: {mem.total / (1024**3):.2f} Go")
        logger.info(f"Mémoire disponible: {mem.available / (1024**3):.2f} Go")
        logger.info(f"Pourcentage mémoire utilisée: {mem.percent}%")
        
        # CPU
        cpu_percent = psutil.cpu_percent()
        logger.info(f"Utilisation CPU: {cpu_percent}%")
        
        # GPU si disponible
        if self.config['use_gpu']:
            logger.info(f"GPU disponible: {torch.cuda.get_device_name(0)}")
            logger.info(f"Mémoire GPU: {torch.cuda.get_device_properties(0).total_memory / (1024**3):.2f} Go")
    
    def _adaptive_batch_size(self, total_samples):
        """
        Calcule dynamiquement la taille de batch
        """
        mem = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent()
        
        # Ajustement en fonction de l'utilisation mémoire et CPU
        if mem.percent > self.config['max_memory_usage'] or cpu_percent > self.config['max_cpu_usage']:
            return max(self.config['embedding_batch_size'] // 2, 1)
        
        return self.config['embedding_batch_size']
    
    def dimensionality_reduction(self, embeddings):
        """
        Réduction de dimensionnalité des embeddings
        """
        if not self.config['dimensionality_reduction']:
            return embeddings
        
        # Choix entre TruncatedSVD et autres méthodes
        reducer = TruncatedSVD(
            n_components=min(
                self.config['reduction_components'], 
                embeddings.shape[1]
            ),
            random_state=42
        )
        
        return reducer.fit_transform(embeddings)
    
    def process_large_dataset(self, texts, batch_process_func, batch_size=None):
        """
        Traitement de grands ensembles de données par lots
        
        Args:
            texts (list): Liste des textes
            batch_process_func (callable): Fonction de traitement par lot
            batch_size (int, optional): Taille de lot personnalisée
        """
        if batch_size is None:
            batch_size = self._adaptive_batch_size(len(texts))
        
        results = []
        for i in tqdm(range(0, len(texts), batch_size), desc="Traitement par lots"):
            batch = texts[i:i+batch_size]
            results.extend(batch_process_func(batch))
        
        return results
    
    def memory_efficient_embedding(self, texts, model_name='distilbert-base-nli-stsb-mean-tokens'):
        """
        Génération d'embeddings avec contraintes mémoire
        """
        # Choix du device
        device = 'cuda' if self.config['use_gpu'] and torch.cuda.is_available() else 'cpu'
        
        # Chargement du modèle
        model = SentenceTransformer(model_name, device=device)
        
        def embedding_batch(batch):
            return model.encode(
                batch, 
                show_progress_bar=False,
                convert_to_numpy=True
            )
        
        # Traitement par lots
        embeddings = self.process_large_dataset(
            texts, 
            embedding_batch, 
            batch_size=self.config['embedding_batch_size']
        )
        
        # Conversion et réduction de dimensionnalité
        embeddings = np.array(embeddings)
        return self.dimensionality_reduction(embeddings)

class RecommendationSystem:
    """
    Système de recommandation optimisé pour la performance
    """
    def __init__(self, performance_config=None):
        self.optimizer = PerformanceOptimizer(performance_config)
        self.embedder = None
        self.index = None
    
    def train(self, texts, model_name='distilbert-base-nli-stsb-mean-tokens'):
        """
        Entraînement du système de recommandation
        """
        # Génération des embeddings
        logger.info("Génération des embeddings...")
        embeddings = self.optimizer.memory_efficient_embedding(
            texts, 
            model_name=model_name
        )
        
        # Construction de l'index de recherche
        from sklearn.neighbors import NearestNeighbors
        
        logger.info("Construction de l'index de recherche...")
        self.index = NearestNeighbors(
            n_neighbors=5, 
            metric='cosine', 
            algorithm='auto',
            n_jobs=-1  # Utilisation de tous les cœurs
        )
        self.index.fit(embeddings)
        
        return self
    
    def recommend(self, query, top_k=5):
        """
        Génération de recommandations
        """
        if self.index is None:
            raise ValueError("Le modèle doit être entraîné avant de faire des recommandations")
        
        # Génération de l'embedding de requête
        query_embedding = self.optimizer.memory_efficient_embedding(
            [query], 
            model_name='distilbert-base-nli-stsb-mean-tokens'
        )
        
        # Recherche des plus proches voisins
        distances, indices = self.index.kneighbors(query_embedding)
        
        return list(zip(indices[0], 1 - distances[0]))

def main():
    # Configuration personnalisée de performance
    performance_config = {
        'max_memory_usage': 70.0,
        'max_cpu_usage': 80.0,
        'embedding_batch_size': 32,
        'dimensionality_reduction': True,
        'reduction_components': 100,
        'use_sparse_matrix': True,
        'use_gpu': torch.cuda.is_available()
    }
    
    # Charger les données
    try:
        df = pd.read_csv(
            "../data/OnBigTable/one_big_table.csv.gz",
            compression="gzip",
            sep=",",
            encoding="utf-8"
        )
        
        # Préparation des données
        cols_o = [
            "TITLE", "DESCRIPTION", "TYPE_CONTRAT", "NOM_DOMAINE", 
            "VILLE", "DEPARTEMENT", "REGION", "PAYS", 
            "TYPE_SENIORITE", "NOM_ENTREPRISE", "CATEGORIE_ENTREPRISE", 
            "COMPETENCES", "TYPES_COMPETENCES", "SOFTSKILLS_SUMMARY", 
            "SOFTSKILLS_DETAILS", "NOM_METIER", "CODE_POSTAL"
        ]
        df["TEXT"] = df[cols_o].fillna("").astype(str).agg(". ".join, axis=1)
        
        # Initialisation du système de recommandation
        recommender = RecommendationSystem(performance_config)
        
        # Entraînement
        recommender.train(df['TEXT'].values)
        
        # Exemple de recommandation
        query = "Développeur Python avec expérience en data science"
        recommendations = recommender.recommend(query)
        
        print("\nRecommandations pour la requête :", query)
        for idx, score in recommendations:
            print(f"Offre {idx} (similarité : {score:.2f}) : {df.iloc[idx]['TEXT'][:200]}...")
    
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution : {e}")

if __name__ == "__main__":
    main()
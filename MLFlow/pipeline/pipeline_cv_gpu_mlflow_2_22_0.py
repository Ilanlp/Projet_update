"""Job Matching Pipeline avec GridSearchCV et RandomizedSearchCV intégrés à MLflow 2.22.0"""

# Imports standards
import pandas as pd
import re
import unicodedata
from typing import Dict, List, Optional, Any, Union, Literal, Tuple
import os
import psutil
import torch
import warnings
import argparse
from dataclasses import dataclass
import hashlib
import json
import pickle
from pathlib import Path
from datetime import datetime
import time
from functools import wraps
import platform

# Imports scientifiques
import numpy as np
from scipy.stats import uniform, randint

# Imports ML
import spacy
from sentence_transformers import SentenceTransformer
from sklearn.base import BaseEstimator, TransformerMixin, ClassifierMixin, RegressorMixin
from sklearn.pipeline import Pipeline
from sklearn.neighbors import NearestNeighbors
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV, train_test_split
from joblib import parallel_backend
from sklearn.utils.validation import check_is_fitted

# Import MLflow
import mlflow
from mlflow.models import infer_signature, ModelSignature
from mlflow.types.schema import Schema, ColSpec
from mlflow.tracking import MlflowClient
from mlflow import sklearn as mlflow_sklearn  # Import correct du module sklearn de MLflow
from packaging import version

REQUIRED_MLFLOW_VERSION = "2.22.0"
CURRENT_MLFLOW_VERSION = mlflow.__version__

if version.parse(CURRENT_MLFLOW_VERSION) != version.parse(REQUIRED_MLFLOW_VERSION):
    warnings.warn(f"Version MLflow attendue: {REQUIRED_MLFLOW_VERSION}, version actuelle: {CURRENT_MLFLOW_VERSION}")

# Import des modules locaux
from mlflow_utils import MLflowManager
from search_config import SearchConfig, STOP_WORDS
from cache_manager import CacheManager

@dataclass
class ResourceConfig:
    """Configuration des ressources pour le pipeline."""
    name: str
    description: str
    use_gpu: bool
    batch_size: int
    max_seq_length: int
    n_workers: int
    use_half_precision: bool
    max_parallel_jobs: int

# Configurations prédéfinies
RESOURCE_CONFIGS = {
    "small_cpu": ResourceConfig(
        name="small_cpu",
        description="Configuration minimale CPU (8GB RAM)",
        use_gpu=False,
        batch_size=16,
        max_seq_length=256,
        n_workers=2,
        use_half_precision=False,
        max_parallel_jobs=1
    ),
    "medium_cpu": ResourceConfig(
        name="medium_cpu",
        description="Configuration moyenne CPU (16GB RAM)",
        use_gpu=False,
        batch_size=32,
        max_seq_length=384,
        n_workers=4,
        use_half_precision=False,
        max_parallel_jobs=2
    ),
    "large_cpu": ResourceConfig(
        name="large_cpu",
        description="Configuration haute CPU (32GB+ RAM)",
        use_gpu=False,
        batch_size=64,
        max_seq_length=512,
        n_workers=8,
        use_half_precision=False,
        max_parallel_jobs=4
    ),
    "gpu_basic": ResourceConfig(
        name="gpu_basic",
        description="GPU entrée de gamme (4GB VRAM)",
        use_gpu=True,
        batch_size=32,
        max_seq_length=256,
        n_workers=2,
        use_half_precision=True,
        max_parallel_jobs=2
    ),
    "gpu_medium": ResourceConfig(
        name="gpu_medium",
        description="GPU milieu de gamme (8GB VRAM)",
        use_gpu=True,
        batch_size=64,
        max_seq_length=384,
        n_workers=4,
        use_half_precision=True,
        max_parallel_jobs=2
    ),
    "gpu_high": ResourceConfig(
        name="gpu_high",
        description="GPU haut de gamme (12GB+ VRAM)",
        use_gpu=True,
        batch_size=128,
        max_seq_length=512,
        n_workers=4,
        use_half_precision=True,
        max_parallel_jobs=4
    )
}

# Configuration MLflow
def setup_mlflow_env():
    """Configure l'environnement MLflow"""
    mlflow.set_tracking_uri("sqlite:///mlflow.db")
    mlflow_sklearn.autolog(
        log_input_examples=True,
        log_model_signatures=True,
        log_models=True,
        silent=False
    )

# Définition des classes de base
class BaseMLflowManager:
    """Classe de base pour la gestion MLflow"""
    def __init__(self, experiment_name: str):
        self.experiment_name = experiment_name
        self.client = MlflowClient()
        self.current_run = None
        
    def setup_experiment(self):
        """Configure l'expérience MLflow"""
        try:
            experiment = mlflow.get_experiment_by_name(self.experiment_name)
            if experiment is None:
                self.experiment_id = mlflow.create_experiment(
                    self.experiment_name,
                    artifact_location="./mlruns"
                )
            else:
                self.experiment_id = experiment.experiment_id
        except Exception as e:
            print(f"Erreur lors de la configuration de l'expérience : {e}")
            self.experiment_id = None
            
    def cleanup(self):
        """Nettoie la session MLflow"""
        if self.current_run is not None:
            mlflow.end_run()
        self.current_run = None

class BaseModelManager:
    """Classe de base pour la gestion des modèles"""
    def __init__(self):
        self.model = None
        self.model_params = {}
        
    def get_params(self) -> Dict[str, Any]:
        """Retourne les paramètres du modèle"""
        return self.model_params
        
    def set_params(self, **params):
        """Configure les paramètres du modèle"""
        self.model_params.update(params)
        return self

class BaseDataManager:
    """Classe de base pour la gestion des données"""
    def __init__(self):
        self.data = None
        self.preprocessed_data = None
        
    def load_data(self, path: str):
        """Charge les données depuis un fichier"""
        try:
            self.data = pd.read_csv(path)
        except Exception as e:
            print(f"Erreur lors du chargement des données : {e}")
            
    def preprocess_data(self):
        """Prétraite les données"""
        if self.data is not None:
            self.preprocessed_data = self.data.copy()
        
    def get_data(self):
        """Retourne les données prétraitées"""
        return self.preprocessed_data

class MLflowManager2_22_0(BaseMLflowManager):
    """Gestionnaire MLflow adapté pour la version 2.22.0"""
    
    def __init__(self, experiment_name: str):
        super().__init__(experiment_name)
        self.setup_experiment()
        
    def start_run(self, run_name: Optional[str] = None, tags: Optional[Dict] = None):
        """Démarre un nouveau run MLflow"""
        if self.current_run is not None:
            self.cleanup()
            
        default_tags = {
            "mlflow.version": CURRENT_MLFLOW_VERSION,
            "python.version": platform.python_version(),
            "timestamp": datetime.now().isoformat()
        }
        if tags:
            default_tags.update(tags)
            
        self.current_run = mlflow.start_run(
            experiment_id=self.experiment_id,
            run_name=run_name,
            tags=default_tags
        )
        return self.current_run
        
    def log_model(self, model: Any, input_example: Union[pd.DataFrame, pd.Series, List[str]]):
        """Log le modèle avec les spécifications MLflow 2.22.0"""
        try:
            # Assurer que l'exemple d'entrée est un DataFrame
            if isinstance(input_example, pd.Series):
                input_example = pd.DataFrame({"text": input_example})
            elif isinstance(input_example, list):
                input_example = pd.DataFrame({"text": input_example})
            elif isinstance(input_example, pd.DataFrame):
                if "text" not in input_example.columns:
                    input_example = pd.DataFrame({"text": input_example.iloc[:, 0]})
                    
            # Générer des prédictions pour inférer la signature
            if hasattr(model, 'transform'):
                predictions = model.transform(input_example["text"])
            else:
                predictions = model.predict(input_example["text"])
                
            # Convertir les prédictions en DataFrame si nécessaire
            if isinstance(predictions, np.ndarray):
                if len(predictions.shape) == 1:
                    predictions = pd.DataFrame({"prediction": predictions})
                else:
                    predictions = pd.DataFrame(
                        predictions,
                        columns=[f"feature_{i}" for i in range(predictions.shape[1])]
                    )
                    
            signature = infer_signature(
                input_example,
                predictions,
                params=self._get_model_params(model)
            )
                
            # Log du modèle avec configurations spécifiques 2.22.0
            mlflow_sklearn.log_model(
                sk_model=model,
                artifact_path="model",
                signature=signature,
                input_example=input_example,
                registered_model_name="JobMatchingModel",
                pip_requirements=[
                    "scikit-learn",
                    "pandas",
                    "numpy",
                    "torch",
                    "transformers",
                    "sentence-transformers"
                ],
                metadata={
                    "task": "job_matching",
                    "framework": "sklearn",
                    "python_version": platform.python_version(),
                    "creation_timestamp": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            print(f"Erreur lors du logging du modèle : {e}")
            
    def _get_model_params(self, model: Any) -> Dict[str, Any]:
        """Extrait les paramètres du modèle"""
        params = {}
        if hasattr(model, 'get_params'):
            params = model.get_params()
        return params
        
    def log_metrics(self, metrics: Dict[str, float], step: Optional[int] = None):
        """Log les métriques avec gestion des erreurs"""
        try:
            mlflow.log_metrics(metrics, step=step)
        except Exception as e:
            print(f"Erreur lors du logging des métriques : {e}")
            
    def log_params(self, params: Dict[str, Any], prefix: str = ""):
        """Log les paramètres avec préfixe"""
        try:
            formatted_params = {}
            for k, v in params.items():
                # Conversion des valeurs numpy
                if isinstance(v, np.generic):
                    v = v.item()
                # Ajout du préfixe
                param_key = f"{prefix}_{k}" if prefix else k
                formatted_params[param_key] = v
                
            mlflow.log_params(formatted_params)
        except Exception as e:
            print(f"Erreur lors du logging des paramètres : {e}")

def train_with_grid_and_random_search(
    df: pd.DataFrame,
    experiment_name: str = "job_matching_experiment_gpu",
    resource_config: Optional[ResourceConfig] = None,
    cache_config: Optional[Dict] = None
) -> Optional[Pipeline]:
    """Version adaptée pour MLflow 2.22.0"""
    
    # Configuration MLflow
    setup_mlflow_env()
    
    # Configuration des ressources avec valeurs par défaut
    if resource_config is None:
        default_config = "gpu_high" if torch.cuda.is_available() else "medium_cpu"
        resource_config = RESOURCE_CONFIGS[default_config]
    
    # Configuration MLflow
    mlflow_manager = MLflowManager2_22_0(experiment_name)
    resource_manager = None
    
    try:
        # Préparation des données
        X = prepare_data(df)
        # Conversion en DataFrame pour MLflow
        X_df = pd.DataFrame({"text": X})
        X_train_df, X_test_df = train_test_split(X_df, test_size=0.2, random_state=42)
        
        # Utilisation du context manager pour les ressources
        with ResourceManager(resource_config) as resource_manager:
            n_jobs = resource_config.max_parallel_jobs
            
            # Configuration du backend parallèle avec gestion de None
            with parallel_backend('loky', n_jobs=n_jobs):
                # Création du pipeline avec vérification des configurations
                pipeline = Pipeline([
                    ("preprocessor", TextPreprocessor(
                        extra_stopwords=STOP_WORDS,
                        cache_config=cache_config or {}
                    )),
                    ("embedder", SBertTransformer(
                        resource_config=resource_config,
                        cache_config=cache_config or {},
                        batch_size=resource_config.batch_size if resource_config else 32
                    )),
                    ("matcher", KNNMatcher()),
                ])
                
                # Configuration des recherches
                search_config = {
                    "grid_search": {
                        "param_grid": {
                            "matcher__n_neighbors": [3, 5, 10],
                            "matcher__metric": ["cosine", "euclidean"],
                            "embedder__batch_size": [32, 64, 128],
                            "embedder__model_name": ["distilbert-base-nli-stsb-mean-tokens"],
                        },
                        "cv": 3,
                        "n_jobs": n_jobs,
                        "verbose": 1
                    },
                    "random_search": {
                        "param_distributions": {
                            "matcher__n_neighbors": randint(3, 15),
                            "matcher__metric": ["cosine", "euclidean"],
                            "embedder__batch_size": [32, 64, 128],
                            "embedder__model_name": ["distilbert-base-nli-stsb-mean-tokens"],
                        },
                        "n_iter": 10,
                        "cv": 3,
                        "n_jobs": n_jobs,
                        "verbose": 1
                    }
                }
                
                # Run MLflow pour GridSearchCV
                with mlflow_manager.start_run(run_name="grid_search") as run:
                    # Log des paramètres avec vérification
                    if resource_config is not None:
                        mlflow_manager.log_params({
                            "resource_config_name": resource_config.name,
                            "resource_config_description": resource_config.description,
                            "use_gpu": resource_config.use_gpu,
                            "batch_size": resource_config.batch_size,
                            "max_seq_length": resource_config.max_seq_length,
                            "n_workers": resource_config.n_workers,
                            "use_half_precision": resource_config.use_half_precision,
                            "max_parallel_jobs": resource_config.max_parallel_jobs,
                        }, prefix="resource")
                    
                    # Recherche par grille
                    grid_search = run_grid_search(pipeline, X_train_df, search_config["grid_search"])
                    
                    # Log des résultats
                    mlflow_manager.log_params(grid_search.best_params_, prefix="grid")
                    mlflow_manager.log_metrics({
                        "grid_best_score": grid_search.best_score_,
                        "grid_mean_fit_time": grid_search.cv_results_["mean_fit_time"].mean(),
                    })
                    
                    # Log du modèle
                    if isinstance(grid_search.best_estimator_, Pipeline):
                        mlflow_manager.log_model(
                            grid_search.best_estimator_,
                            X_train_df.head(3)
                        )
                
                # Run MLflow pour RandomizedSearchCV
                with mlflow_manager.start_run(run_name="random_search") as run:
                    # Recherche aléatoire
                    random_search = run_random_search(pipeline, X_train_df, search_config["random_search"])
                    
                    # Log des résultats
                    mlflow_manager.log_params(random_search.best_params_, prefix="random")
                    mlflow_manager.log_metrics({
                        "random_best_score": random_search.best_score_,
                        "random_mean_fit_time": random_search.cv_results_["mean_fit_time"].mean(),
                    })
                    
                    # Log du modèle
                    if isinstance(random_search.best_estimator_, Pipeline):
                        mlflow_manager.log_model(
                            random_search.best_estimator_,
                            X_train_df.head(3)
                        )
                
                # Sélection du meilleur modèle
                if grid_search.best_score_ > random_search.best_score_:
                    best_model = grid_search.best_estimator_
                    best_params = grid_search.best_params_
                    best_score = grid_search.best_score_
                    search_type = "grid_search"
                else:
                    best_model = random_search.best_estimator_
                    best_params = random_search.best_params_
                    best_score = random_search.best_score_
                    search_type = "random_search"
                
                # Run final pour le meilleur modèle
                with mlflow_manager.start_run(run_name="best_model") as run:
                    mlflow_manager.log_params(best_params, prefix="best")
                    
                    # Évaluation sur le jeu de test
                    if isinstance(best_model, Pipeline):
                        test_score = compute_metrics(best_model, X_test_df)
                        mlflow_manager.log_metrics({
                            "test_score": test_score,
                            "best_score": best_score,
                        })
                        
                        # Log du modèle final avec le DataFrame complet
                        mlflow_manager.log_model(
                            best_model,
                            X_train_df.head(3)
                        )
                        
                        return best_model
                    
    except Exception as e:
        print(f"Erreur lors de l'entraînement : {e}")
        return None
    finally:
        mlflow_manager.cleanup()
        if resource_manager is not None:
            resource_manager.cleanup()

class ResourceManager:
    """Gestionnaire de ressources pour optimiser l'utilisation CPU/GPU."""
    
    def __init__(self, config: ResourceConfig):
        self.config = config
        self.device = self._get_device()
        self.cpu_count = psutil.cpu_count(logical=False)
        self.total_memory = psutil.virtual_memory().total
        self.gpu_memory = self._get_gpu_memory() if self.device == "cuda" else 0
        
    def __enter__(self):
        """Context manager entry"""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self.device == "cuda":
            try:
                # Libérer la mémoire GPU
                torch.cuda.empty_cache()
                # Réinitialiser tous les dispositifs CUDA
                torch.cuda.reset_peak_memory_stats()
                torch.cuda.reset_accumulated_memory_stats()
            except Exception as e:
                warnings.warn(f"Erreur lors du nettoyage GPU : {e}")
        
    def _get_device(self) -> str:
        """Détermine le meilleur device disponible."""
        if self.config.use_gpu and torch.cuda.is_available():
            return "cuda"
        return "cpu"
    
    def _get_gpu_memory(self) -> int:
        """Récupère la mémoire GPU disponible en bytes."""
        try:
            if self.device == "cuda":
                return torch.cuda.get_device_properties(0).total_memory
        except Exception as e:
            warnings.warn(f"Erreur lors de l'accès aux propriétés GPU : {e}")
        return 0
    
    def cleanup(self):
        """Nettoie les ressources GPU"""
        if self.device == "cuda":
            try:
                torch.cuda.empty_cache()
                torch.cuda.reset_peak_memory_stats()
                torch.cuda.reset_accumulated_memory_stats()
            except Exception as e:
                warnings.warn(f"Erreur lors du nettoyage GPU : {e}")

class TextPreprocessor(BaseEstimator, TransformerMixin):
    """Préprocesseur de texte avec support MLflow 2.22.0"""
    
    def __init__(self, 
                 model_name: str = "fr_core_news_sm",
                 extra_stopwords: Optional[List[str]] = None,
                 cache_config: Optional[Dict] = None):
        self.model_name = model_name
        self.extra_stopwords = extra_stopwords
        self.cache_config = cache_config or {}
        self._nlp = None
        self._stopwords = None
        
    def fit(self, X, y=None):
        try:
            self._nlp = spacy.load(self.model_name, disable=["parser", "ner"])
            self._stopwords = set([] if self.extra_stopwords is None else self.extra_stopwords)
        except Exception as e:
            print(f"Erreur lors du chargement du modèle spaCy : {e}")
            self._stopwords = set()
        return self
        
    def transform(self, X):
        # Gérer les différents types d'entrée
        if isinstance(X, pd.DataFrame):
            if "text" in X.columns:
                text_series = X["text"]
            else:
                text_series = X.iloc[:, 0]
        elif isinstance(X, pd.Series):
            text_series = X
        else:
            text_series = pd.Series(X)
            
        return text_series.apply(self._preprocess_text)
        
    def _preprocess_text(self, text: str) -> str:
        if not isinstance(text, str):
            return ""
        # Nettoyage basique
        text = text.lower()
        text = unicodedata.normalize("NFD", text)
        text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        
        # Lemmatisation si spaCy est disponible
        if self._nlp is not None:
            doc = self._nlp(text)
            tokens = []
            stopwords = self._stopwords if self._stopwords is not None else set()
            for token in doc:
                if (not token.is_stop and 
                    not token.is_punct and 
                    not token.like_num and 
                    len(token.text) > 1 and
                    token.text not in stopwords):
                    tokens.append(token.lemma_)
            text = " ".join(tokens)
        
        return text.strip()
        
    def get_feature_names_out(self, input_features=None):
        """Retourne les noms des features de sortie"""
        return np.array(['text'])

class SBertTransformer(BaseEstimator, TransformerMixin):
    """Transformer SBERT avec support MLflow 2.22.0"""
    
    def __init__(self, 
                 model_name: str = "distilbert-base-nli-stsb-mean-tokens",
                 resource_config: Optional[ResourceConfig] = None,
                 cache_config: Optional[Dict] = None,
                 batch_size: Optional[int] = None):
        self.model_name = model_name
        self.resource_config = resource_config
        self.cache_config = cache_config
        self.batch_size = batch_size
        self._model = None
        
    def fit(self, X, y=None):
        if self._model is None:
            self._model = SentenceTransformer(self.model_name)
            if self.resource_config and self.resource_config.use_gpu:
                self._model = self._model.to("cuda")
        return self
        
    def transform(self, X):
        if self._model is None:
            self.fit(X)
            
        # Gérer les différents types d'entrée
        if isinstance(X, pd.DataFrame):
            if "text" in X.columns:
                texts = X["text"].tolist()
            else:
                texts = X.iloc[:, 0].tolist()
        elif isinstance(X, pd.Series):
            texts = X.tolist()
        else:
            texts = X if isinstance(X, list) else list(X)
            
        if self._model is not None:
            batch_size = (
                self.batch_size if self.batch_size is not None
                else self.resource_config.batch_size if self.resource_config
                else 32
            )
            return self._model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=True,
                device="cuda" if (self.resource_config and self.resource_config.use_gpu) else "cpu"
            )
        else:
            # Retourner un tableau vide si le modèle n'est pas initialisé
            return np.zeros((len(texts), 768))  # 768 est la dimension par défaut des embeddings BERT

    def get_params(self, deep=True):
        """Retourne les paramètres du transformateur"""
        return {
            "model_name": self.model_name,
            "resource_config": self.resource_config,
            "cache_config": self.cache_config,
            "batch_size": self.batch_size
        }

    def set_params(self, **parameters):
        """Configure les paramètres du transformateur"""
        for parameter, value in parameters.items():
            setattr(self, parameter, value)
        return self
        
    def get_feature_names_out(self, input_features=None):
        """Retourne les noms des features de sortie"""
        n_features = 768  # Dimension par défaut des embeddings BERT
        return np.array([f'embedding_{i}' for i in range(n_features)])

class KNNMatcher(BaseEstimator):
    """Matcher KNN avec support MLflow 2.22.0"""
    
    def __init__(self, n_neighbors: int = 5, metric: str = "cosine"):
        self.n_neighbors = n_neighbors
        self.metric = metric
        self._knn = None
        
    def fit(self, X, y=None):
        self._knn = NearestNeighbors(
            n_neighbors=self.n_neighbors,
            metric=self.metric,
            algorithm="auto"
        ).fit(X)
        return self
        
    def predict(self, X):
        if self._knn is None:
            return np.zeros((len(X), self.n_neighbors))
        distances, _ = self._knn.kneighbors(X)
        return 1 - distances

def prepare_data(df: pd.DataFrame) -> List[str]:
    """Prépare les données pour l'entraînement."""
    cols = [
        "TITLE", "DESCRIPTION", "TYPE_CONTRAT", "NOM_DOMAINE",
        "VILLE", "DEPARTEMENT", "REGION", "PAYS",
        "TYPE_SENIORITE", "NOM_ENTREPRISE", "COMPETENCES",
    ]
    df["TEXT"] = df[cols].fillna("").astype(str).agg(". ".join, axis=1)
    return df["TEXT"].tolist()

def run_grid_search(pipeline: Pipeline, X: Union[pd.DataFrame, pd.Series, List[str]], config: Dict[str, Any]) -> GridSearchCV:
    """Exécute la recherche par grille avec support MLflow 2.22.0"""
    # Créer une copie du pipeline pour éviter les effets de bord
    pipeline_copy = Pipeline(pipeline.steps)
    
    # Convertir les données en DataFrame si nécessaire
    if isinstance(X, pd.Series):
        X_df = pd.DataFrame({"text": X})
    elif isinstance(X, list):
        X_df = pd.DataFrame({"text": X})
    else:
        X_df = X
    
    grid_search = GridSearchCV(
        pipeline_copy,
        scoring=compute_metrics,  # Utilisation de notre fonction de scoring personnalisée
        error_score=0.0,
        **config
    )
    print(f"Démarrage de la recherche par grille...")
    grid_search.fit(X_df)
    print(f"Meilleur score Grid Search : {grid_search.best_score_:.4f}")
    return grid_search

def run_random_search(pipeline: Pipeline, X: Union[pd.DataFrame, pd.Series, List[str]], config: Dict[str, Any]) -> RandomizedSearchCV:
    """Exécute la recherche aléatoire avec support MLflow 2.22.0"""
    # Créer une copie du pipeline pour éviter les effets de bord
    pipeline_copy = Pipeline(pipeline.steps)
    
    # Convertir les données en DataFrame si nécessaire
    if isinstance(X, pd.Series):
        X_df = pd.DataFrame({"text": X})
    elif isinstance(X, list):
        X_df = pd.DataFrame({"text": X})
    else:
        X_df = X
    
    random_search = RandomizedSearchCV(
        pipeline_copy,
        scoring=compute_metrics,  # Utilisation de notre fonction de scoring personnalisée
        error_score=0.0,
        **config
    )
    print(f"Démarrage de la recherche aléatoire...")
    random_search.fit(X_df)
    print(f"Meilleur score Random Search : {random_search.best_score_:.4f}")
    return random_search

def compute_metrics(model: Pipeline, X_test: Union[pd.DataFrame, pd.Series, List[str]]) -> float:
    """Calcule les métriques d'évaluation pour MLflow 2.22.0"""
    try:
        # Convertir les données en DataFrame si nécessaire
        if isinstance(X_test, pd.Series):
            X_df = pd.DataFrame({"text": X_test})
        elif isinstance(X_test, list):
            X_df = pd.DataFrame({"text": X_test})
        else:
            X_df = X_test
            
        # Vérifier si le pipeline et ses composants sont ajustés
        needs_fitting = False
        try:
            check_is_fitted(model)
            # Vérifier chaque étape du pipeline
            for _, step in model.named_steps.items():
                check_is_fitted(step)
        except Exception:
            needs_fitting = True
            
        if needs_fitting:
            # Si le pipeline ou un de ses composants n'est pas ajusté,
            # on l'ajuste d'abord sur les données de test
            # Note: Ce n'est pas une bonne pratique en production,
            # mais nécessaire pour l'évaluation
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=FutureWarning)
                model.fit(X_df)
            
        # Prédictions
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=FutureWarning)
            if hasattr(model, 'transform'):
                predictions = model.transform(X_df)
            else:
                predictions = model.predict(X_df)
            
        # Conversion en array numpy si nécessaire
        if isinstance(predictions, tuple):
            predictions = predictions[0]  # Prendre le premier élément du tuple
        predictions = np.asarray(predictions)
            
        # Calcul des métriques
        metrics = {
            "samples_count": len(X_test),
            "embedding_dim": predictions.shape[1] if len(predictions.shape) > 1 else 1,
            "non_zero_ratio": float(np.count_nonzero(predictions)) / float(predictions.size)
        }
        
        # Retourner une métrique principale
        return metrics.get("non_zero_ratio", 0.0)
        
    except Exception as e:
        print(f"Erreur lors du calcul des métriques : {e}")
        return 0.0

def cleanup_resources():
    """Nettoie les ressources système"""
    import multiprocessing as mp
    from multiprocessing import resource_tracker
    import gc
    import warnings
    
    # Désactiver temporairement les avertissements
    warnings.filterwarnings('ignore', category=UserWarning)
    
    # Nettoyage des processus
    for p in mp.active_children():
        try:
            p.terminate()
            p.join(timeout=1.0)
        except Exception:
            pass
    
    # Nettoyage GPU si disponible
    if torch.cuda.is_available():
        try:
            torch.cuda.empty_cache()
            torch.cuda.reset_peak_memory_stats()
            torch.cuda.reset_accumulated_memory_stats()
        except Exception as e:
            warnings.warn(f"Erreur lors du nettoyage GPU : {e}")
    
    # Forcer le garbage collector
    gc.collect()
    
    # Réinitialiser le resource tracker
    if hasattr(resource_tracker, '_resource_tracker'):
        resource_tracker._resource_tracker = None

def main():
    """Fonction principale"""
    parser = argparse.ArgumentParser(description="Pipeline de matching d'emplois avec MLflow 2.22.0")
    parser.add_argument(
        "--config",
        type=str,
        choices=list(RESOURCE_CONFIGS.keys()),
        default="gpu_high" if torch.cuda.is_available() else "medium_cpu",
        help="Configuration des ressources à utiliser"
    )
    parser.add_argument(
        "--nrows",
        type=int,
        default=1000,
        help="Nombre de lignes à traiter"
    )
    parser.add_argument(
        "--experiment-name",
        type=str,
        default="job_matching_experiment",
        help="Nom de l'expérience MLflow"
    )
    parser.add_argument(
        "--cache-dir",
        type=str,
        default=".cache",
        help="Répertoire pour le cache"
    )
    
    args = parser.parse_args()
    
    # Configuration du cache
    cache_config = {
        "backend": "file",
        "cache_dir": args.cache_dir
    }
    
    try:
        # Chargement des données
        print("Chargement des données...")
        df = pd.read_csv(
            "../data/OnBigTable/one_big_table.csv.gz",
            compression="gzip",
            nrows=args.nrows
        )
        
        # Configuration des ressources
        resource_config = RESOURCE_CONFIGS[args.config]
        
        # Entraînement
        print(f"\nDémarrage de l'entraînement avec la configuration {args.config}...")
        best_model = train_with_grid_and_random_search(
            df=df,
            experiment_name=args.experiment_name,
            resource_config=resource_config,
            cache_config=cache_config
        )
        
        if best_model is not None:
            print("\nEntraînement terminé avec succès!")
        else:
            print("\nErreur lors de l'entraînement")
            
    except KeyboardInterrupt:
        print("\nInterruption par l'utilisateur. Nettoyage des ressources...")
    except Exception as e:
        print(f"\nErreur lors de l'exécution : {e}")
    finally:
        cleanup_resources()

if __name__ == "__main__":
    # Configuration pour limiter le nombre de processus parallèles
    import multiprocessing as mp
    mp.set_start_method('spawn', force=True)
    
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterruption par l'utilisateur. Nettoyage final des ressources...")
        cleanup_resources()
    except Exception as e:
        print(f"\nErreur fatale : {e}")
        cleanup_resources() 
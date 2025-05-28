# Job Matching Pipeline avec GridSearchCV et RandomizedSearchCV intégrés à MLflow

# Imports standards
import pandas as pd
import re
import unicodedata
from typing import Dict, List, Optional, Any, Union

# Imports scientifiques
import numpy as np
from scipy.stats import uniform, randint

# Imports ML
import spacy
from sentence_transformers import SentenceTransformer
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
from sklearn.neighbors import NearestNeighbors
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV, train_test_split

# Import MLflow
try:
    import mlflow
    import mlflow.sklearn
    MLFLOW_AVAILABLE = True
except ImportError:
    print("MLflow n'est pas disponible. Le logging sera désactivé.")
    MLFLOW_AVAILABLE = False
    mlflow = None

# Stop-words personnalisés
stop_perso = [
    "faire", "sens", "information", "situation", "environnement",
    "france", "preuve", "dater", "etude", "ingenieure", "capacite",
    "interlocuteur", "vue", "heure", "action", "technicienn",
]

def log_mlflow_params(params: Dict[str, Any], prefix: str = "") -> None:
    """Fonction utilitaire pour logger les paramètres dans MLflow"""
    if MLFLOW_AVAILABLE and mlflow is not None:
        try:
            mlflow.log_params({
                f"{prefix}_{k}" if prefix else k: v 
                for k, v in params.items()
            })
        except Exception as e:
            print(f"Erreur lors du logging MLflow : {e}")

def log_mlflow_model(model: Union[Pipeline, BaseEstimator], model_name: str = "best_job_matching_model") -> None:
    """Fonction utilitaire pour logger le modèle dans MLflow"""
    if MLFLOW_AVAILABLE and mlflow is not None:
        try:
            mlflow.sklearn.log_model(
                model,
                model_name,
                registered_model_name="JobMatchingModel"
            )
        except Exception as e:
            print(f"Erreur lors du logging du modèle MLflow : {e}")

class TextPreprocessor(BaseEstimator, TransformerMixin):
    def __init__(self, model_name: str = "fr_core_news_sm", extra_stopwords: Optional[List[str]] = None):
        self.model_name = model_name
        self.extra_stopwords = extra_stopwords  # Ne pas modifier le paramètre dans le constructeur
        self._nlp = None
        self._stopwords = None

    def fit(self, X: pd.Series, y=None) -> 'TextPreprocessor':
        try:
            self._nlp = spacy.load(self.model_name, disable=["parser", "ner"])
            # Initialisation des stopwords comme un set
            self._stopwords = set([] if self.extra_stopwords is None else self.extra_stopwords)
        except Exception as e:
            print(f"Erreur lors du chargement du modèle spaCy : {e}")
            self._stopwords = set()
        return self

    def _clean(self, text: str) -> str:
        if not isinstance(text, str):
            return ""
        text = text.lower()
        text = unicodedata.normalize("NFD", text)
        text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
        return re.sub(r"[^a-z0-9\s]", " ", text).strip()

    def _lemmatize(self, text: str) -> str:
        if not isinstance(text, str) or self._nlp is None:
            return text
        doc = self._nlp(text)
        lemmas = []
        stopwords = self._stopwords or set()  # Utiliser un set vide si None
        
        for tok in doc:
            lemma = tok.lemma_.lower().strip(" ,.")
            if lemma == "dater":
                lemma = "data"
            if (
                not tok.is_stop
                and not tok.is_punct
                and not tok.like_num
                and len(lemma) > 1
                and lemma not in stopwords
            ):
                lemmas.append(lemma)
        return " ".join(lemmas)

    def transform(self, X: pd.Series) -> pd.Series:
        if not isinstance(X, pd.Series):
            X = pd.Series(X)
        return X.apply(self._clean).apply(self._lemmatize)

class SBertTransformer(BaseEstimator, TransformerMixin):
    def __init__(self, model_name: str = "distilbert-base-nli-stsb-mean-tokens", batch_size: int = 16):
        self.model_name = model_name
        self.batch_size = batch_size
        self._model = None

    def fit(self, X: pd.Series, y=None) -> 'SBertTransformer':
        try:
            self._model = SentenceTransformer(self.model_name)
        except Exception as e:
            print(f"Erreur lors du chargement du modèle SBERT : {e}")
        return self

    def transform(self, X: pd.Series) -> np.ndarray:
        if self._model is None:
            return np.zeros((len(X), 768))
        try:
            return self._model.encode(X.tolist(), show_progress_bar=True, batch_size=self.batch_size)
        except Exception as e:
            print(f"Erreur lors de l'encodage : {e}")
            return np.zeros((len(X), 768))

class KNNMatcher(BaseEstimator):
    def __init__(self, n_neighbors: int = 5, metric: str = "cosine", threshold: float = 0.7):
        self.n_neighbors = n_neighbors
        self.metric = metric
        self.threshold = threshold
        self._knn = None

    def fit(self, X: np.ndarray, y=None) -> 'KNNMatcher':
        if isinstance(X, pd.Series):
            X = np.array(X.tolist())
        self._knn = NearestNeighbors(
            n_neighbors=self.n_neighbors,
            metric=self.metric,
            algorithm="auto"
        ).fit(X)
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        if self._knn is None:
            return np.zeros((len(X), self.n_neighbors))
        if isinstance(X, pd.Series):
            X = np.array(X.tolist())
        distances, _ = self._knn.kneighbors(X)
        return 1 - distances

def compute_metrics(estimator: Pipeline, X: pd.Series, y=None) -> float:
    """Fonction de scoring compatible avec scikit-learn.
    
    Cette fonction est appelée par GridSearchCV/RandomizedSearchCV pendant la validation croisée.
    À ce stade, l'estimateur a déjà été ajusté sur les données d'entraînement.
    """
    try:
        # Vérifier que tous les composants sont présents
        if not hasattr(estimator, 'steps') or len(estimator.steps) != 3:
            print("Pipeline incomplet")
            return 0.0
            
        # Récupérer les composants
        try:
            preprocessor = estimator.named_steps['preprocessor']
            embedder = estimator.named_steps['embedder']
            matcher = estimator.named_steps['matcher']
        except KeyError as e:
            print(f"Composant manquant : {e}")
            return 0.0
        
        # Vérifier que tous les composants sont ajustés
        if not all([
            hasattr(preprocessor, '_nlp') and preprocessor._nlp is not None,
            hasattr(embedder, '_model') and embedder._model is not None,
            hasattr(matcher, '_knn') and matcher._knn is not None
        ]):
            print("Un ou plusieurs composants non ajustés")
            return 0.0
            
        # Calculer les similarités
        try:
            # Prétraiter les données
            X_prep = preprocessor.transform(X)
            if X_prep is None:
                return 0.0
                
            # Calculer les embeddings
            X_emb = embedder.transform(X_prep)
            if X_emb is None:
                return 0.0
                
            # Calculer les similarités
            similarities = matcher.predict(X_emb)
            if similarities is None:
                return 0.0
            
            if isinstance(similarities, tuple):
                similarities = similarities[0]
            if similarities.ndim == 1:
                similarities = similarities.reshape(-1, 1)
            n_cols = min(5, similarities.shape[1])
            threshold = getattr(matcher, 'threshold', 0.7)  # Utiliser 0.7 par défaut si non défini
            return float(np.mean(np.any(similarities[:, :n_cols] > threshold, axis=1)))
        except Exception as e:
            print(f"Erreur lors du calcul des similarités : {e}")
            return 0.0
            
    except Exception as e:
        print(f"Erreur lors du calcul des métriques : {e}")
        return 0.0

def create_pipeline() -> Pipeline:
    """Crée et retourne un nouveau pipeline avec les composants par défaut"""
    return Pipeline([
        ("preprocessor", TextPreprocessor(extra_stopwords=stop_perso)),
        ("embedder", SBertTransformer()),
        ("matcher", KNNMatcher()),
    ])

def train_with_grid_and_random_search(df: pd.DataFrame, experiment_name: str = "job_matching_experiment") -> Optional[Union[Pipeline, BaseEstimator]]:
    # Préparation des données
    cols = [
        "TITLE", "DESCRIPTION", "TYPE_CONTRAT", "NOM_DOMAINE",
        "VILLE", "DEPARTEMENT", "REGION", "PAYS",
        "TYPE_SENIORITE", "NOM_ENTREPRISE", "COMPETENCES",
    ]
    df["TEXT"] = df[cols].fillna("").astype(str).agg(". ".join, axis=1)
    
    # Séparation train/test
    X_train, X_test = train_test_split(df["TEXT"], test_size=0.2, random_state=42)
    
    # Configuration MLflow
    mlflow_context = None
    if MLFLOW_AVAILABLE and mlflow is not None:
        try:
            mlflow.set_experiment(experiment_name)
            mlflow_context = mlflow.start_run(run_name="JobMatchingPipeline")
        except Exception as e:
            print(f"Erreur lors de la configuration MLflow : {e}")

    try:
        # Création du pipeline de base
        pipeline = create_pipeline()
        
        # Paramètres de recherche par grille
        param_grid = {
            "preprocessor__extra_stopwords": [None, stop_perso],
            "embedder__model_name": [
                "distilbert-base-nli-stsb-mean-tokens",
                "paraphrase-multilingual-MiniLM-L12-v2",
            ],
            "embedder__batch_size": [16, 32],
            "matcher__n_neighbors": [3, 5, 10],
            "matcher__threshold": [0.6, 0.7, 0.8],
        }
        
        # Configuration de la recherche par grille
        grid_search = GridSearchCV(
            pipeline,
            param_grid,
            cv=3,
            scoring=compute_metrics,
            n_jobs=1,  # Réduire pour éviter les problèmes de mémoire
            error_score=0.0,  # Utiliser 0.0 au lieu de np.nan
            verbose=2
        )
        
        print("Démarrage de la recherche par grille...")
        grid_search.fit(X_train)
        print(f"Meilleur score Grid Search : {grid_search.best_score_:.4f}")
        
        # Paramètres de recherche aléatoire
        param_distributions = {
            "preprocessor__extra_stopwords": [None, stop_perso],
            "embedder__model_name": [
                "distilbert-base-nli-stsb-mean-tokens",
                "paraphrase-multilingual-MiniLM-L12-v2",
            ],
            "embedder__batch_size": randint(16, 64),
            "matcher__n_neighbors": randint(3, 15),
            "matcher__threshold": uniform(0.5, 0.4),
        }
        
        # Configuration de la recherche aléatoire
        random_search = RandomizedSearchCV(
            pipeline,
            param_distributions,
            n_iter=10,  # Réduire le nombre d'itérations
            cv=3,
            scoring=compute_metrics,
            n_jobs=1,  # Réduire pour éviter les problèmes de mémoire
            random_state=42,
            error_score=0.0,  # Utiliser 0.0 au lieu de np.nan
            verbose=2
        )
        
        print("Démarrage de la recherche aléatoire...")
        random_search.fit(X_train)
        print(f"Meilleur score Random Search : {random_search.best_score_:.4f}")
        
        # Sélection du meilleur modèle
        if grid_search.best_score_ > random_search.best_score_:
            best_model = grid_search.best_estimator_
            best_params = grid_search.best_params_
            best_score = grid_search.best_score_
            print("Meilleur modèle trouvé par Grid Search")
        else:
            best_model = random_search.best_estimator_
            best_params = random_search.best_params_
            best_score = random_search.best_score_
            print("Meilleur modèle trouvé par Random Search")
            
        print(f"Meilleur score : {best_score:.4f}")
        print("Meilleurs paramètres :", best_params)
        
        # Log des résultats dans MLflow
        if MLFLOW_AVAILABLE and mlflow is not None:
            log_mlflow_params(best_params)
            log_mlflow_model(best_model)
            
        return best_model
            
    except Exception as e:
        print(f"Erreur lors de l'entraînement : {e}")
        return None
    finally:
        if mlflow_context is not None:
            mlflow_context.__exit__(None, None, None)

def main():
    try:
        # Chargement des données
        print("Chargement des données...")
        df = pd.read_csv(
            "../data/OnBigTable/one_big_table.csv.gz",
            compression="gzip",
            sep=",",
            encoding="utf-8",
            nrows=1000,  # Augmenter pour un test plus complet
        )
        
        # Entraînement
        print("Démarrage de l'entraînement...")
        best_model = train_with_grid_and_random_search(df)
        
        if best_model is not None:
            print("Entraînement terminé avec succès")
        else:
            print("Entraînement terminé sans modèle valide")
            
    except KeyboardInterrupt:
        print("\nInterruption par l'utilisateur. Nettoyage des ressources...")
        import multiprocessing as mp
        # Nettoyer les processus enfants
        for p in mp.active_children():
            p.terminate()
        # Nettoyer les sémaphores
        import resource_cleaner
        resource_cleaner.clean_up()
    except Exception as e:
        print(f"Erreur lors de l'exécution : {e}")
    finally:
        # S'assurer que tous les processus sont terminés
        import multiprocessing as mp
        for p in mp.active_children():
            p.terminate()

if __name__ == "__main__":
    # Configuration pour limiter le nombre de processus parallèles
    import multiprocessing as mp
    mp.set_start_method('spawn', force=True)
    main()

"""
🚀 Points Clés de l'Implémentation

1. Intégration Complète
   - GridSearchCV et RandomizedSearchCV
   - Logging avec MLflow
   - Métriques personnalisées

2. Étapes Principales
   a. Recherche par Grille
   b. Recherche Aléatoire 
   c. Sélection du Meilleur Modèle
   d. Entraînement Final

3. Avantages
   - Exploration systématique des hyperparamètres
   - Tracking détaillé des expériences
   - Reproductibilité
   - Flexibilité de configuration

4. Recommandations
   - Ajuster les distributions selon votre domaine
   - Monitorer les temps de calcul
   - Utiliser des métriques adaptées
"""

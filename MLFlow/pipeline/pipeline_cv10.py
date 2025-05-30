# Job Matching Pipeline avec GridSearchCV et RandomizedSearchCV intégrés à MLflow

import pandas as pd
import re
import unicodedata
import spacy
from tqdm.auto import tqdm
import numpy as np
import mlflow
import mlflow.sklearn
import mlflow.pyfunc

# Imports scikit-learn
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
from sklearn.neighbors import NearestNeighbors
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV, train_test_split
from scipy.stats import uniform, randint

# Librairies de transformation de texte
from sentence_transformers import SentenceTransformer
from itertools import product

# Stop-words personnalisés
stop_perso = [
    "faire",
    "sens",
    "information",
    "situation",
    "environnement",
    "france",
    "preuve",
    "dater",
    "etude",
    "ingenieure",
    "capacite",
    "interlocuteur",
    "vue",
    "heure",
    "action",
    "technicienn",
]


# 1. Preprocesseur de Texte
class TextPreprocessor(BaseEstimator, TransformerMixin):
    def __init__(self, model_name="fr_core_news_sm", extra_stopwords=None):
        self.model_name = model_name
        self.extra_stopwords = extra_stopwords if extra_stopwords is not None else []
        self.nlp = None  # On initialise nlp à None et on le charge dans fit()

    def fit(self, X, y=None):
        # Chargement du modèle spaCy dans fit() plutôt que dans __init__
        self.nlp = spacy.load(self.model_name, disable=["parser", "ner"])
        return self

    def _clean(self, text):
        text = text.lower()
        text = unicodedata.normalize("NFD", text)
        text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
        return re.sub(r"[^a-z0-9\s]", " ", text).strip()

    def _lemmatize(self, text):
        doc = self.nlp(text)
        lemmas = []
        for tok in doc:
            lemma = tok.lemma_.lower().strip(" ,.")
            if lemma == "dater":
                lemma = "data"
            if (
                not tok.is_stop
                and not tok.is_punct
                and not tok.like_num
                and len(lemma) > 1
                and lemma not in self.extra_stopwords
            ):
                lemmas.append(lemma)
        return " ".join(lemmas)

    def transform(self, X):
        return X.apply(self._clean).apply(self._lemmatize)


# 2. Transformateur SBERT
class SBertTransformer(BaseEstimator, TransformerMixin):
    def __init__(
        self, model_name="distilbert-base-nli-stsb-mean-tokens", batch_size=16
    ):
        self.model_name = model_name
        self.batch_size = batch_size
        self.model = None

    def fit(self, X, y=None):
        self.model = SentenceTransformer(self.model_name)
        return self

    def transform(self, X):
        if self.model is None:
            self.fit(X)

        # Désactiver la barre de progression par défaut et utiliser tqdm directement
        texts = X.tolist()
        total_batches = len(texts) // self.batch_size + (
            1 if len(texts) % self.batch_size > 0 else 0
        )

        with tqdm(total=total_batches, desc="Encoding batches", unit="batch") as pbar:
            embeddings = self.model.encode(
                texts,
                show_progress_bar=False,  # Désactiver la barre de progression interne
                batch_size=self.batch_size,
                convert_to_numpy=True,
            )
            pbar.update(total_batches)  # Mettre à jour la barre une seule fois à la fin

        return embeddings


# 3. Matcher avec k-Nearest Neighbors
class KNNMatcher(BaseEstimator, TransformerMixin):
    def __init__(self, n_neighbors=5, metric="cosine", threshold=0.7):
        self.n_neighbors = n_neighbors
        self.metric = metric
        self.threshold = threshold
        self.knn = None

    def fit(self, X, y=None):
        self.knn = NearestNeighbors(
            n_neighbors=self.n_neighbors, metric=self.metric, algorithm="auto"
        ).fit(X)
        return self

    def transform(self, X):
        if self.knn is None:
            raise ValueError("Modèle non entraîné. Appelez fit() d'abord.")

        distances, indices = self.knn.kneighbors(X)
        similarities = 1 - distances

        # Filtrage selon le seuil de similarité
        filtered_similarities = np.where(
            similarities >= self.threshold, similarities, 0
        )

        return filtered_similarities


# 4. Modèle MLflow Composite
class MatchingModel(mlflow.pyfunc.PythonModel):
    def load_context(self, context):
        self.preproc = mlflow.sklearn.load_model(context.artifacts["preproc"])
        self.encoder = mlflow.sklearn.load_model(context.artifacts["encoder"])
        self.matcher = mlflow.sklearn.load_model(context.artifacts["knn"])

    def predict(self, context, model_input: pd.DataFrame):
        texts = self.preproc.transform(model_input["TEXT"])
        emb = self.encoder.transform(texts)
        dists, idxs = self.matcher.kneighbors(emb)

        sims = 1 - dists
        n, k = sims.shape
        out = np.empty((n, k, 2), dtype=object)
        for i in range(n):
            for j in range(k):
                out[i, j, 0] = int(idxs[i, j])
                out[i, j, 1] = float(sims[i, j])
        return out


# 5. Métriques personnalisées
def compute_metrics(y_true, y_pred):
    """
    Calcul de métriques personnalisées pour l'évaluation des similitudes
    """
    similarities = y_pred  # y_pred contient directement les similarités

    # Calcul des métriques
    recall1 = np.mean(similarities[:, 0] >= 0.7)  # Meilleur match au-dessus du seuil
    recall5 = np.mean(
        np.any(similarities[:, :5] >= 0.7, axis=1)
    )  # Au moins un des 5 premiers au-dessus du seuil

    return {
        "recall_at_1": float(
            recall1
        ),  # Conversion en float pour assurer la sérialisation
        "recall_at_5": float(recall5),
    }


# 6. Fonction principale d'entraînement avec MLflow
def train_with_grid_and_random_search(df_o, experiment_name="job_matching_grid_search"):
    # Préparation des données
    cols_o = [
        "TITLE",
        "DESCRIPTION",
        "TYPE_CONTRAT",
        "NOM_DOMAINE",
        "VILLE",
        "DEPARTEMENT",
        "REGION",
        "PAYS",
        "TYPE_SENIORITE",
        "NOM_ENTREPRISE",
        "COMPETENCES",
    ]
    df_o["TEXT"] = df_o[cols_o].fillna("").astype(str).agg(". ".join, axis=1)

    # Séparation train/test
    X_train, X_test = train_test_split(df_o["TEXT"], test_size=0.2, random_state=42)

    # Configuration MLflow
    mlflow.set_experiment(experiment_name)

    # Définition du pipeline
    pipeline = Pipeline(
        [
            ("preprocessor", TextPreprocessor()),
            ("embedder", SBertTransformer()),
            ("matcher", KNNMatcher()),
        ]
    )

    # 7. Grid Search
    def run_grid_search():
        with mlflow.start_run(nested=True, run_name="GridSearchCV"):
            # Espace des hyperparamètres
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

            # Recherche par grille
            grid_search = GridSearchCV(
                pipeline, param_grid, cv=3, scoring=compute_metrics, n_jobs=-1
            )

            # Ajustement
            grid_search.fit(X_train)

            # Logging MLflow
            mlflow.log_params(grid_search.best_params_)
            mlflow.log_metrics(
                {
                    "best_recall_at_1": grid_search.best_score_["recall_at_1"],
                    "best_recall_at_5": grid_search.best_score_["recall_at_5"],
                }
            )

            return grid_search

    # 8. Randomized Search
    def run_randomized_search():
        with mlflow.start_run(nested=True, run_name="RandomizedSearchCV"):
            # Distribution des hyperparamètres
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

            # Recherche aléatoire
            random_search = RandomizedSearchCV(
                pipeline,
                param_distributions,
                n_iter=20,
                cv=3,
                scoring=compute_metrics,
                n_jobs=-1,
                random_state=42,
            )

            # Ajustement
            random_search.fit(X_train)

            # Logging MLflow
            mlflow.log_params(random_search.best_params_)
            mlflow.log_metrics(
                {
                    "best_recall_at_1": random_search.best_score_["recall_at_1"],
                    "best_recall_at_5": random_search.best_score_["recall_at_5"],
                }
            )

            return random_search

    # 9. Entraînement des modèles avec meilleurs hyperparamètres
    def train_best_model(best_params):
        with mlflow.start_run(nested=True, run_name="BestModel"):
            # Pipeline avec meilleurs hyperparamètres
            best_pipeline = Pipeline(
                [
                    (
                        "preprocessor",
                        TextPreprocessor(
                            extra_stopwords=best_params.get(
                                "preprocessor__extra_stopwords", None
                            )
                        ),
                    ),
                    (
                        "embedder",
                        SBertTransformer(
                            model_name=best_params.get(
                                "embedder__model_name",
                                "distilbert-base-nli-stsb-mean-tokens",
                            ),
                            batch_size=best_params.get("embedder__batch_size", 16),
                        ),
                    ),
                    (
                        "matcher",
                        KNNMatcher(
                            n_neighbors=best_params.get("matcher__n_neighbors", 5),
                            threshold=best_params.get("matcher__threshold", 0.7),
                        ),
                    ),
                ]
            )

            # Entraînement
            best_pipeline.fit(X_train)

            # Prédictions et métriques
            y_pred = best_pipeline.transform(X_test)
            metrics = compute_metrics(None, y_pred)

            # Logging MLflow
            mlflow.log_params(best_params)
            mlflow.log_metrics(metrics)

            # Logging du modèle complet
            mlflow.sklearn.log_model(best_pipeline, "best_job_matching_model")

            return best_pipeline

    # 10. Exécution complète
    with mlflow.start_run(run_name="JobMatchingExperiment"):
        # Lancer les recherches
        grid_results = run_grid_search()
        random_results = run_randomized_search()

        # Sélectionner le meilleur modèle
        best_grid_params = grid_results.best_params_
        best_random_params = random_results.best_params_

        # Choisir le meilleur modèle - ici on prend grid_results,
        # mais une vraie logique de sélection serait plus complexe
        best_model = train_best_model(best_grid_params)

        return best_model


# Script principal
def main():
    # Chargement des données
    df_o = pd.read_csv(
        "../data/OnBigTable/one_big_table.csv.gz",
        compression="gzip",
        sep=",",
        encoding="utf-8",
        nrows=1000,  # Augmenter pour un test plus complet
    )

    # Entraînement avec recherche d'hyperparamètres
    best_model = train_with_grid_and_random_search(df_o)

    print("Entraînement terminé. Meilleur modèle sélectionné.")


if __name__ == "__main__":
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

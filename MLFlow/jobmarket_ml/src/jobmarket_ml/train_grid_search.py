import argparse
import mlflow
import pandas as pd
from sklearn.model_selection import GridSearchCV
from sklearn.pipeline import Pipeline
import os

# Import des configurations
try:
    from config.config import (
        OFFERS_PATH,
        CANDIDATES_PATH,
        OFFER_COLUMNS,
        CANDIDATE_COLUMNS,
        CUSTOM_STOPWORDS,
        MLFLOW_EXPERIMENT_NAME,
    )
except ImportError:
    # En mode test, utiliser la configuration de test
    from tests.config import (
        OFFERS_PATH,
        CANDIDATES_PATH,
        OFFER_COLUMNS,
        CANDIDATE_COLUMNS,
        CUSTOM_STOPWORDS,
        MLFLOW_EXPERIMENT_NAME,
    )

# Import des composants de matching
from matching import (
    create_matching_pipeline,
    MatchingEngine,
    MatchingEvaluator,
)
from custom_transformers.text_preprocessor import TextPreprocessor
from custom_transformers.bert_encoder import BertEncoder


def parse_args():
    parser = argparse.ArgumentParser(description="Entraînement avec GridSearchCV")
    parser.add_argument(
        "--nrows_offers",
        type=int,
        default=1000,
        help="Nombre de lignes à charger pour les offres",
    )
    parser.add_argument(
        "--nrows_candidates",
        type=int,
        default=100,
        help="Nombre de lignes à charger pour les candidats",
    )
    parser.add_argument(
        "--cv_folds",
        type=int,
        default=5,
        help="Nombre de folds pour la validation croisée",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Utiliser la configuration de test (plus rapide)",
    )
    return parser.parse_args()


def load_data(nrows_offers=None, nrows_candidates=None):
    """Charge les données d'offres et de candidats."""
    # Chargement des offres
    df_o = pd.read_csv(
        OFFERS_PATH, compression="gzip", sep=",", encoding="utf-8", nrows=nrows_offers
    )

    # Chargement des candidats
    df_c = pd.read_csv(
        CANDIDATES_PATH,
        compression="gzip",
        sep=";",
        encoding="utf-8",
        nrows=nrows_candidates,
    )

    # Préparation du texte des offres
    df_o["TEXT"] = df_o[OFFER_COLUMNS].fillna("").astype(str).agg(". ".join, axis=1)
    df_c["TEXT"] = df_c[CANDIDATE_COLUMNS].fillna("").astype(str).agg(". ".join, axis=1)

    return df_o, df_c


def define_param_grid():
    """
    Définit la grille complète des paramètres pour l'optimisation par GridSearchCV.

    Cette grille explore différentes combinaisons de poids pour le texte, les compétences
    et l'expérience, ainsi que différents nombres de correspondances à retourner.

    Returns:
        dict: Grille de paramètres pour GridSearchCV
    """
    return {
        "text_weight": [0.4, 0.5, 0.6, 0.7, 0.8],  # Plus de poids sur le texte
        "skills_weight": [
            0.1,
            0.2,
            0.3,
            0.4,
        ],  # Poids intermédiaire pour les compétences
        "experience_weight": [0.1, 0.15, 0.2],  # Poids plus faible pour l'expérience
        "k_matches": [3, 5, 7, 10],  # Nombre de correspondances à retourner
    }


def define_param_grid_test():
    """Version simplifiée de la grille de paramètres pour les tests."""
    return {
        "text_weight": [0.6],
        "skills_weight": [0.2],
        "experience_weight": [0.2],
        "k_matches": [2],  # Réduit car nous avons peu de données
    }


def train_with_grid_search(
    offers_text, candidates_text, cv_folds=5, y=None, is_test=False
):
    """Entraîne le modèle avec GridSearchCV."""
    # Création des pipelines et de l'évaluateur
    offer_pipeline = Pipeline(
        [
            ("preprocessor", TextPreprocessor(extra_stopwords=CUSTOM_STOPWORDS)),
            ("encoder", BertEncoder()),
        ]
    )

    candidate_pipeline = Pipeline(
        [
            ("preprocessor", TextPreprocessor(extra_stopwords=CUSTOM_STOPWORDS)),
            ("encoder", BertEncoder()),
        ]
    )

    matching_engine = MatchingEngine()
    evaluator = MatchingEvaluator(n_splits=cv_folds)

    # Conversion des données en DataFrame
    X = pd.DataFrame(offers_text, columns=["TEXT"])
    y = pd.DataFrame(candidates_text, columns=["TEXT"])

    # Prétraitement des données
    X_encoded = offer_pipeline.fit_transform(X)
    y_encoded = candidate_pipeline.fit_transform(y)

    # Configuration de la recherche sur grille
    param_grid = define_param_grid_test() if is_test else define_param_grid()
    grid_search = GridSearchCV(
        matching_engine,
        param_grid,
        cv=2 if is_test else cv_folds,  # Réduit le nombre de folds en mode test
        scoring=evaluator.get_scorer(),
        n_jobs=1 if is_test else -1,  # Désactive la parallélisation en mode test
        verbose=2,
    )

    # Entraînement avec MLflow
    with mlflow.start_run() as parent_run:
        # Entraînement - on utilise les offres comme X et les candidats comme y
        grid_search.fit(X_encoded, y_encoded)

        # Logging des meilleurs paramètres dans un run imbriqué
        with mlflow.start_run(nested=True) as child_run:
            mlflow.log_params(grid_search.best_params_)
            mlflow.log_metric("best_score", grid_search.best_score_)

    return grid_search


def main(nrows_offers=None, nrows_candidates=None, cv_folds=5, is_test=False):
    """Fonction principale."""
    # Configuration de MLflow
    mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)

    print("1. Chargement des données...")
    df_offers, df_candidates = load_data(nrows_offers, nrows_candidates)

    print("2. Préparation des textes...")
    offers_text = df_offers["TEXT"].values
    candidates_text = df_candidates["TEXT"].values

    print("3. Configuration de la recherche sur grille...")
    try:
        grid_search = train_with_grid_search(
            offers_text, candidates_text, cv_folds, is_test=is_test
        )

        print("\nMeilleurs paramètres trouvés:")
        for param, value in grid_search.best_params_.items():
            print(f"{param}: {value}")

        print(f"\nMeilleur score: {grid_search.best_score_:.3f}")

    except Exception as e:
        print(f"\n❌ Erreur lors de l'entraînement : {str(e)}")
        raise


if __name__ == "__main__":
    args = parse_args()
    main(args.nrows_offers, args.nrows_candidates, args.cv_folds, args.test)

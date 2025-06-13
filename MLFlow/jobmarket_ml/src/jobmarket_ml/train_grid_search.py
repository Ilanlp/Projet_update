import argparse
import mlflow
import pandas as pd
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
        MLFLOW_MODEL_NAME,
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
        MLFLOW_MODEL_NAME,
    )

# Import des composants de matching
from jobmarket_ml.matching import (
    create_unified_pipeline,
    define_unified_param_grid,
    MatchingEvaluator,
    MatchingGridSearchCV,
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


def train_with_grid_search(
    offers_text, candidates_text, cv_folds=5, y=None, is_test=False
):
    """Entraîne le modèle avec GridSearchCV."""
    # Création du pipeline et de l'évaluateur
    pipeline = create_unified_pipeline(extra_stopwords=CUSTOM_STOPWORDS)
    evaluator = MatchingEvaluator(n_splits=cv_folds)

    # Conversion des données en DataFrame
    X = pd.DataFrame(offers_text, columns=["TEXT"])
    y = pd.DataFrame(candidates_text, columns=["TEXT"])

    # Configuration de la recherche sur grille
    param_grid = define_unified_param_grid(is_random_search=False, is_test=is_test)
    grid_search = MatchingGridSearchCV(
        pipeline,
        param_grid,
        cv=2 if is_test else cv_folds,  # Réduit le nombre de folds en mode test
        scoring=evaluator.get_scorer(),
        n_jobs=1 if is_test else -1,  # Désactive la parallélisation en mode test
        verbose=2,
    )

    # Entraînement avec MLflow
    with mlflow.start_run() as parent_run:
        # Log des paramètres de configuration
        mlflow.log_params(
            {
                "cv_folds": cv_folds,
                "param_grid": str(param_grid),
                "is_test": is_test,
            }
        )

        # Entraînement
        grid_search.fit(X, y)

        # Logging des meilleurs paramètres dans un run imbriqué
        with mlflow.start_run(nested=True) as child_run:
            mlflow.log_params(grid_search.best_params_)
            mlflow.log_metric("best_score", grid_search.best_score_)

            # Évaluation détaillée du meilleur modèle
            best_model = grid_search.best_estimator_
            evaluation_results = evaluator.evaluate(
                best_model.named_steps["matching_engine"],
                grid_search.X_transformed_,
                grid_search.y_transformed_,
            )
            mlflow.log_metrics(evaluation_results)

            # Sauvegarde du meilleur modèle
            print("\nSauvegarde du meilleur modèle...")
            mlflow.sklearn.log_model(best_model, MLFLOW_MODEL_NAME, input_example=X.head(1))
            print(f"Modèle sauvegardé avec le run_id: {child_run.info.run_id}")

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

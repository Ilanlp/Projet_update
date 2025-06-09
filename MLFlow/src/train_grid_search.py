import argparse
import mlflow
import pandas as pd
from sklearn.model_selection import GridSearchCV

# Import des configurations
from jobmarket_ml.config.config import (
    OFFERS_PATH,
    CANDIDATES_PATH,
    OFFER_COLUMNS,
    CANDIDATE_COLUMNS,
    CUSTOM_STOPWORDS,
    MLFLOW_EXPERIMENT_NAME,
)

# Import des composants de matching
from jobmarket_ml.matching import (
    create_matching_pipeline,
    define_param_grid,
    MatchingEvaluator,
)


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


def train_with_grid_search(offers_text, candidates_text, cv_folds=5):
    """Entraîne le modèle avec GridSearchCV."""
    # Création du pipeline et de l'évaluateur
    pipeline = create_matching_pipeline(custom_stopwords=CUSTOM_STOPWORDS)
    evaluator = MatchingEvaluator(n_splits=cv_folds)

    # Configuration de la recherche sur grille
    param_grid = define_param_grid()
    grid_search = GridSearchCV(
        pipeline,
        param_grid,
        cv=cv_folds,
        scoring=evaluator.get_scorer(),
        n_jobs=-1,
        verbose=2,
    )

    # Entraînement
    with mlflow.start_run(run_name="grid_search_training"):
        mlflow.log_params(param_grid)
        grid_search.fit(offers_text, candidates_text)

        # Logging des résultats
        mlflow.log_param("best_score", grid_search.best_score_)
        mlflow.log_params(grid_search.best_params_)

        # Évaluation détaillée du meilleur modèle
        best_model = grid_search.best_estimator_
        evaluation_results = evaluator.evaluate(
            best_model.named_steps["matching_engine"],
            best_model.named_steps["offer_preprocessor"].transform(offers_text),
            best_model.named_steps["candidate_preprocessor"].transform(candidates_text),
        )

        mlflow.log_metrics(evaluation_results)

    return grid_search


def main(nrows_offers=None, nrows_candidates=None, cv_folds=5):
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
        grid_search = train_with_grid_search(offers_text, candidates_text, cv_folds)

        print("\nMeilleurs paramètres trouvés:")
        for param, value in grid_search.best_params_.items():
            print(f"{param}: {value}")

        print(f"\nMeilleur score: {grid_search.best_score_:.3f}")

    except Exception as e:
        print(f"\n❌ Erreur lors de l'entraînement : {str(e)}")
        raise


if __name__ == "__main__":
    args = parse_args()
    main(args.nrows_offers, args.nrows_candidates, args.cv_folds)

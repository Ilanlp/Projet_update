import argparse
import mlflow
import numpy as np
import pandas as pd
from scipy.stats import uniform, randint
from sklearn.model_selection import RandomizedSearchCV
from sklearn.pipeline import Pipeline

# Import des configurations
from config.config import (
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
    MatchingRandomizedSearchCV,
)


def parse_args():
    parser = argparse.ArgumentParser(description="Entraînement avec RandomSearchCV")
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
        "--n_iter",
        type=int,
        default=100,
        help="Nombre d'itérations pour la recherche aléatoire",
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


def define_param_distributions():
    """Définit les distributions de paramètres pour RandomSearchCV."""
    return {
        "matching_engine__text_weight": uniform(0.3, 0.6),  # Entre 0.3 et 0.9
        "matching_engine__skills_weight": uniform(0.05, 0.35),  # Entre 0.05 et 0.4
        "matching_engine__experience_weight": uniform(0.05, 0.25),  # Entre 0.05 et 0.3
        "matching_engine__k_matches": randint(3, 15),  # Entre 3 et 15
        "offer_pipeline__preprocessor__min_df": randint(1, 10),
        "offer_pipeline__preprocessor__max_df": uniform(0.3, 0.6),  # Entre 0.3 et 0.9
        "candidate_pipeline__preprocessor__min_df": randint(1, 10),
        "candidate_pipeline__preprocessor__max_df": uniform(
            0.3, 0.6
        ),  # Entre 0.3 et 0.9
    }


def train_with_random_search(
    offers_text, candidates_text, cv_folds=5, n_iter=100, is_test=False
):
    """Entraîne le modèle avec RandomizedSearchCV."""
    # Création du pipeline et de l'évaluateur
    pipeline = create_unified_pipeline(extra_stopwords=CUSTOM_STOPWORDS)
    evaluator = MatchingEvaluator(n_splits=cv_folds)

    # Configuration de la recherche aléatoire
    param_distributions = define_unified_param_grid(
        is_random_search=True, is_test=is_test
    )
    random_search = MatchingRandomizedSearchCV(
        pipeline,
        param_distributions,
        n_iter=5 if is_test else n_iter,  # Réduit le nombre d'itérations en mode test
        cv=2 if is_test else cv_folds,  # Réduit le nombre de folds en mode test
        scoring=evaluator.get_scorer(),
        n_jobs=1 if is_test else -1,  # Désactive la parallélisation en mode test
        verbose=2,
        random_state=42,
    )

    # Entraînement
    with mlflow.start_run(run_name="random_search_training") as run:
        mlflow.log_params(
            {
                "n_iter": n_iter,
                "cv_folds": cv_folds,
                "param_space": str(param_distributions),
                "is_test": is_test,
            }
        )

        # Conversion des données en DataFrame
        X = pd.DataFrame(offers_text, columns=["TEXT"])
        y = pd.DataFrame(candidates_text, columns=["TEXT"])

        random_search.fit(X, y)

        # Logging des résultats
        mlflow.log_param("best_score", random_search.best_score_)
        mlflow.log_params(random_search.best_params_)

        # Évaluation détaillée du meilleur modèle
        best_model = random_search.best_estimator_
        evaluation_results = evaluator.evaluate(
            best_model.named_steps["matching_engine"],
            random_search.X_transformed_,
            random_search.y_transformed_,
        )

        mlflow.log_metrics(evaluation_results)

        # Log de la distribution des scores
        all_scores = random_search.cv_results_["mean_test_score"]
        mlflow.log_metrics(
            {
                "mean_score": np.mean(all_scores),
                "std_score": np.std(all_scores),
                "max_score": np.max(all_scores),
                "min_score": np.min(all_scores),
            }
        )

        # Sauvegarde du meilleur modèle
        print("\nSauvegarde du meilleur modèle...")
        mlflow.sklearn.log_model(best_model, MLFLOW_MODEL_NAME, input_example=X.head(1))
        print(f"Modèle sauvegardé avec le run_id: {run.info.run_id}")

    return random_search


def main(
    nrows_offers=None, nrows_candidates=None, cv_folds=5, n_iter=100, is_test=False
):
    """Fonction principale."""
    # Configuration de MLflow
    mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)

    print("1. Chargement des données...")
    df_offers, df_candidates = load_data(nrows_offers, nrows_candidates)

    print("2. Préparation des textes...")
    offers_text = df_offers["TEXT"].values
    candidates_text = df_candidates["TEXT"].values

    print(f"3. Configuration de la recherche aléatoire (n_iter={n_iter})...")
    try:
        random_search = train_with_random_search(
            offers_text,
            candidates_text,
            cv_folds=cv_folds,
            n_iter=n_iter,
            is_test=is_test,
        )

        print("\nMeilleurs paramètres trouvés:")
        for param, value in random_search.best_params_.items():
            print(f"{param}: {value}")

        print(f"\nMeilleur score: {random_search.best_score_:.3f}")

        # Affichage des statistiques des scores
        all_scores = random_search.cv_results_["mean_test_score"]
        print("\nStatistiques des scores:")
        print(f"Moyenne: {np.mean(all_scores):.3f} (±{np.std(all_scores):.3f})")
        print(f"Min: {np.min(all_scores):.3f}")
        print(f"Max: {np.max(all_scores):.3f}")

    except Exception as e:
        print(f"\n❌ Erreur lors de l'entraînement : {str(e)}")
        raise


if __name__ == "__main__":
    args = parse_args()
    main(
        args.nrows_offers, args.nrows_candidates, args.cv_folds, args.n_iter, args.test
    )

import pandas as pd
import numpy as np
from jobmarket_ml.matching.pipeline import create_matching_pipeline
from jobmarket_ml.preprocessing.text import TextPreprocessor
from sklearn.preprocessing import StandardScaler


# Charger les données
def load_data():
    # Charger les offres (on prend un petit échantillon pour l'exemple)
    offers_df = pd.read_csv("../data/all_jobs_20250609_0844_1236_offers.csv.gz")
    offers_df = offers_df.head(10)  # On prend les 10 premières offres

    # Charger les candidats
    candidates_df = pd.read_csv("../data/RAW_CANDIDAT.csv")
    candidates_df = candidates_df.head(5)  # On prend les 5 premiers candidats

    return offers_df, candidates_df


def prepare_data(offers_df, candidates_df):
    # Préparation des textes
    text_preprocessor = TextPreprocessor()

    # Préparer les offres
    offers_text = (
        offers_df["description"].fillna("") + " " + offers_df["title"].fillna("")
    )
    X_offers = text_preprocessor.fit_transform(offers_text)

    # Préparer les candidats
    candidates_text = (
        candidates_df["description"].fillna("")
        + " "
        + candidates_df["title"].fillna("")
    )
    X_candidates = text_preprocessor.transform(candidates_text)

    return X_offers, X_candidates


def main():
    print("Chargement des données...")
    offers_df, candidates_df = load_data()

    print("\nPréparation des données...")
    X_offers, X_candidates = prepare_data(offers_df, candidates_df)

    print("\nCréation et entraînement du pipeline de matching...")
    matching_pipeline = create_matching_pipeline()
    matching_pipeline.fit(X_offers, X_candidates)

    print("\nPrédiction des matches avec la nouvelle méthode predict_table...")
    # Utilisation de predict_table sans le DataFrame des offres
    results_simple = matching_pipeline.predict_table(X_candidates)
    print("\nRésultats simples (sans données des offres):")
    print(results_simple.head())

    print("\nRésultats détaillés (avec données des offres):")
    # Utilisation de predict_table avec le DataFrame des offres
    results_detailed = matching_pipeline.predict_table(
        X_candidates, df_offers=offers_df
    )

    # Sélectionner quelques colonnes intéressantes pour l'affichage
    columns_to_display = [
        "candidate_idx",
        "rank",
        "offer_idx",
        "similarity_score",
        "title",
        "company_name",
        "location",
    ]
    print(results_detailed[columns_to_display].head())

    # Analyser les résultats pour un candidat spécifique
    candidate_idx = 0
    print(f"\nDétail des matches pour le candidat {candidate_idx}:")
    candidate_matches = results_detailed[
        results_detailed["candidate_idx"] == candidate_idx
    ]
    print(candidate_matches[columns_to_display])


if __name__ == "__main__":
    main()

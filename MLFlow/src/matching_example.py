import pandas as pd
import numpy as np
import sys
import os
from pathlib import Path

# Ajouter le chemin du package jobmarket_ml au PYTHONPATH
project_root = Path(__file__).parent.parent
workspace_root = project_root.parent
sys.path.append(str(project_root / "jobmarket_ml" / "src"))

from jobmarket_ml.matching.pipeline import create_matching_pipeline
from sklearn.preprocessing import StandardScaler


# Charger les données
def load_data():
    # Charger les offres (on prend un petit échantillon pour l'exemple)
    data_path = workspace_root / "data"
    offers_df = pd.read_csv(data_path / "all_jobs_20250609_0844_1236_offers.csv.gz")
    offers_df = offers_df.head(10)  # On prend les 10 premières offres

    # Charger les candidats et les données associées
    candidates_df = pd.read_csv(data_path / "RAW_CANDIDAT.csv")
    metiers_df = pd.read_csv(data_path / "RAW_METIERS.csv")

    # Joindre les métiers aux candidats pour avoir la description du métier
    candidates_df = candidates_df.merge(
        metiers_df[["code_rome", "libelle", "libelle_search"]],
        left_on="id_metier",
        right_on="code_rome",
        how="left",
    )
    candidates_df = candidates_df.head(5)  # On prend les 5 premiers candidats

    return offers_df, candidates_df


def prepare_data(offers_df, candidates_df):
    # Préparer les offres
    offers_text = pd.Series(
        offers_df["description"].fillna("") + " " + offers_df["title"].fillna("")
    )

    # Préparer les candidats (utiliser le libellé et la description de recherche)
    candidates_text = pd.Series(
        candidates_df["libelle"].fillna("")
        + " "
        + candidates_df["libelle_search"].fillna("")
    )

    return offers_text, candidates_text


def main():
    print("Chargement des données...")
    offers_df, candidates_df = load_data()

    print("\nPréparation des données...")
    X_offers, X_candidates = prepare_data(offers_df, candidates_df)

    print("\nCréation et entraînement du pipeline de matching...")
    matching_pipeline = create_matching_pipeline()

    # Entraîner le pipeline des offres
    print("Traitement des offres...")
    offer_pipeline = matching_pipeline.named_steps["offer_pipeline"]
    X_offers_encoded = offer_pipeline.fit_transform(X_offers)

    # Entraîner le pipeline des candidats
    print("Traitement des candidats...")
    candidate_pipeline = matching_pipeline.named_steps["candidate_pipeline"]
    X_candidates_encoded = candidate_pipeline.fit_transform(X_candidates)

    # Entraîner le matching engine
    print("Calcul des correspondances...")
    matching_engine = matching_pipeline.named_steps["matching_engine"]
    matching_engine.fit(X_offers_encoded, X_candidates_encoded)

    print("\nPrédiction des matches avec la nouvelle méthode predict_table...")
    # Utilisation de predict_table sans le DataFrame des offres
    results_simple = matching_engine.predict_table(X_candidates_encoded)
    print("\nRésultats simples (sans données des offres):")
    print(results_simple.head())

    print("\nRésultats détaillés (avec données des offres):")
    # Utilisation de predict_table avec le DataFrame des offres
    results_detailed = matching_engine.predict_table(
        X_candidates_encoded, df_offers=offers_df
    )

    # Sélectionner quelques colonnes intéressantes pour l'affichage
    columns_to_display = [
        "candidate_idx",
        "rank",
        "offer_idx",
        "similarity_score",
        "title",
        "company_name",
        "location_name",
    ]
    print(results_detailed[columns_to_display].head())

    # Analyser les résultats pour un candidat spécifique
    candidate_idx = 0
    print(f"\nDétail des matches pour le candidat {candidate_idx}:")
    candidate_matches = results_detailed[
        results_detailed["candidate_idx"] == candidate_idx
    ]
    print(candidate_matches[columns_to_display])

    # Afficher les informations du candidat
    print(f"\nInformations du candidat {candidate_idx}:")
    candidate_info = candidates_df.iloc[candidate_idx]
    print(
        {
            "id_candidat": candidate_info["id_candidat"],
            "nom": candidate_info["nom"],
            "prenom": candidate_info["prenom"],
            "metier": candidate_info["libelle"],
            "description_metier": candidate_info["libelle_search"],
        }
    )


if __name__ == "__main__":
    main()

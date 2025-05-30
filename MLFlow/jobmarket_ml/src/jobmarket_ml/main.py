import pandas as pd
import mlflow
from sklearn.pipeline import Pipeline

# Import des configurations
from config.config import (
    OFFERS_PATH, CANDIDATES_PATH, OFFER_COLUMNS,
    CANDIDATE_COLUMNS, CUSTOM_STOPWORDS, PARAM_GRID,
    MLFLOW_EXPERIMENT_NAME
)

# Import des transformers
from custom_transformers.text_preprocessor import TextPreprocessor
from custom_transformers.bert_encoder import BertEncoder
from custom_transformers.knn_matcher import KNNMatcher

# Import des utilitaires
from utils.mlflow_utils import MLflowGridSearchCV
from utils.scoring import matching_scorer, compute_similarity_score

def load_data(nrows_offers=None, nrows_candidates=None):
    """Charge les données d'offres et de candidats."""
    # Chargement des offres
    df_o = pd.read_csv(
        OFFERS_PATH,
        compression="gzip",
        sep=",",
        encoding="utf-8",
        nrows=nrows_offers
    )
    
    # Chargement des candidats
    df_c = pd.read_csv(
        CANDIDATES_PATH,
        compression="gzip",
        sep=";",
        encoding="utf-8",
        nrows=nrows_candidates
    )
    
    # Préparation du texte des offres
    df_o["TEXT"] = df_o[OFFER_COLUMNS].fillna("").astype(str).agg(". ".join, axis=1)
    
    return df_o, df_c[CANDIDATE_COLUMNS]

def create_pipeline():
    """Crée le pipeline de matching."""
    return Pipeline([
        ('preprocessor', TextPreprocessor(extra_stopwords=CUSTOM_STOPWORDS)),
        ('encoder', BertEncoder()),
        ('matcher', KNNMatcher())
    ])

def evaluate_model(estimator, df_offers, df_candidates):
    """
    Évalue le modèle sur les données de test et affiche les résultats.
    """
    print("\nÉvaluation du modèle:")
    score = compute_similarity_score(estimator, df_offers["TEXT"], df_candidates["TEXT"])
    print(f"Score global de similarité: {score:.3f}")
    
    print("\nTest des prédictions:")
    predictions = estimator.transform(df_candidates["TEXT"])
    
    print("\nExemple de matchs pour le premier candidat:")
    for i in range(min(5, predictions.shape[1])):
        idx = int(predictions[0, i, 0])
        sim = float(predictions[0, i, 1])
        print(f"Match {i+1}: Offre {idx} (similarité: {sim:.3f})")
        # Afficher un extrait de l'offre correspondante
        print(f"Titre: {df_offers.iloc[idx]['TITLE']}\n")

def main():
    """Fonction principale."""
    # Configuration de MLflow
    mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)
    
    # Chargement des données (échantillon pour test)
    print("Chargement des données...")
    df_offers, df_candidates = load_data(nrows_offers=100, nrows_candidates=10)
    
    # Création du pipeline
    pipeline = create_pipeline()
    
    # Configuration de la recherche sur grille
    print("Configuration de la recherche sur grille...")
    grid_search = MLflowGridSearchCV(
        pipeline,
        PARAM_GRID,
        cv=5,
        scoring=matching_scorer,
        n_jobs=-1,
        verbose=2
    )
    
    # Entraînement et évaluation
    print("Début de la recherche sur grille...")
    grid_search.fit(df_offers["TEXT"], df_candidates["TEXT"])
    
    # Affichage des résultats
    print("\nMeilleurs paramètres trouvés:")
    for param, value in grid_search.best_params_.items():
        print(f"{param}: {value}")
    
    print(f"\nMeilleur score: {grid_search.best_score_:.3f}")
    
    # Évaluation du meilleur modèle
    evaluate_model(grid_search.best_estimator_, df_offers, df_candidates)

if __name__ == "__main__":
    main() 
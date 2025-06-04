"""Script de test pour le pipeline de matching."""

import pandas as pd
import mlflow
from mlflow.models.signature import ModelSignature
from mlflow.types.schema import Schema, ColSpec
from jobmarket_ml.config.config import (
    OFFERS_PATH, CANDIDATES_PATH, OFFER_COLUMNS,
    CANDIDATE_COLUMNS, CUSTOM_STOPWORDS, MLFLOW_TRACKING_URI,
    MLFLOW_EXPERIMENT_NAME, PIPELINE_CONFIG
)
from jobmarket_ml.custom_transformers.text_preprocessor import TextPreprocessor
from jobmarket_ml.custom_transformers.bert_encoder import BertEncoder
from jobmarket_ml.custom_transformers.knn_matcher import KNNMatcher
from jobmarket_ml.utils.scoring import compute_similarity_score
from sklearn.pipeline import Pipeline
import time
import numpy as np

def train_model():
    """Test du pipeline complet avec tracking MLflow."""
    # Configuration de MLflow
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)

    print("1. Chargement des données...")
    # Chargement d'un petit échantillon de données
    df_offers = pd.read_csv(
        OFFERS_PATH,
        compression="gzip",
        sep=",",
        encoding="utf-8",
        nrows=5  # petit échantillon pour le test
    )
    
    df_candidates = pd.read_csv(
        CANDIDATES_PATH,
        compression="gzip",
        sep=";",
        encoding="utf-8",
        nrows=2  # petit échantillon pour le test
    )
    
    print("2. Préparation des textes...")
    # Préparation du texte des offres
    df_offers["TEXT"] = df_offers[OFFER_COLUMNS].fillna("").astype(str).agg(". ".join, axis=1)
    df_candidates["TEXT"] = df_candidates[CANDIDATE_COLUMNS].fillna("").astype(str).agg(". ".join, axis=1)
    
    print("3. Création du pipeline...")
    # Création du pipeline
    pipeline = Pipeline([
        ('preprocessor', TextPreprocessor(extra_stopwords=CUSTOM_STOPWORDS)),
        ('encoder', BertEncoder(model_name='paraphrase-multilingual-MiniLM-L12-v2', batch_size=16)),
        ('matcher', KNNMatcher(n_neighbors=3, threshold=0.75))
    ])

    # Début du run MLflow
    with mlflow.start_run(run_name="test_pipeline") as run:
        print("4. Test du pipeline...")
        start_time = time.time()
        
        try:
            # Test du préprocesseur
            print("   - Test du préprocesseur...")
            preprocessed_text = pipeline.named_steps['preprocessor'].fit_transform(df_offers["TEXT"])
            print(f"     ✓ Texte préprocessé : {preprocessed_text[:1]}")
            
            # Test de l'encodeur
            print("   - Test de l'encodeur...")
            encoded_text = pipeline.named_steps['encoder'].fit_transform(preprocessed_text)
            print(f"     ✓ Shape des embeddings : {encoded_text.shape}")
            
            # Test du matcher
            print("   - Test du matcher...")
            matches = pipeline.named_steps['matcher'].fit_transform(encoded_text)
            print(f"     ✓ Shape des matchs : {matches.shape}")
            
            # Test du pipeline complet
            print("\n5. Test du pipeline complet...")
            results = pipeline.fit_transform(df_offers["TEXT"])
            print("   ✓ Pipeline exécuté avec succès!")
            print(f"   ✓ Shape des résultats finaux : {results.shape}")
            
            # Test avec les candidats
            print("\n6. Test avec les candidats...")
            candidate_matches = pipeline.transform(df_candidates["TEXT"])
            print("   ✓ Matching des candidats réussi!")
            print(f"   ✓ Shape des matchs candidats : {candidate_matches.shape}")

            # Calcul du temps d'exécution
            execution_time = time.time() - start_time
            
            # Calcul des métriques avec la fonction de scoring
            similarity_score = compute_similarity_score(pipeline, df_offers["TEXT"], df_candidates["TEXT"])
            
            # Calcul des métriques supplémentaires
            mean_similarity = np.mean([match[0][1] for match in candidate_matches])
            diversity_score = np.std([match[0][1] for match in candidate_matches])
            coverage_score = np.mean([1 if match[0][1] >= pipeline.named_steps['matcher'].threshold else 0 
                                    for match in candidate_matches])
            
            # Logging des paramètres
            mlflow.log_params({
                "model_name": pipeline.named_steps['encoder'].model_name,
                "batch_size": pipeline.named_steps['encoder'].batch_size,
                "n_neighbors": pipeline.named_steps['matcher'].n_neighbors,
                "threshold": pipeline.named_steps['matcher'].threshold,
                **PIPELINE_CONFIG
            })
            
            # Logging des métriques
            mlflow.log_metrics({
                "similarity_score": float(similarity_score),
                "mean_similarity": float(mean_similarity),
                "diversity_score": float(diversity_score),
                "coverage_score": float(coverage_score),
                "execution_time": float(execution_time),
                "num_offers": len(df_offers),
                "num_candidates": len(df_candidates)
            })
            
            # Création d'un exemple d'entrée pour la signature du modèle
            input_example = pd.DataFrame({
                "TEXT": ["Développeur Python avec expérience en ML et NLP. Maîtrise de scikit-learn, " +
                        "pandas, et PyTorch. Capable de travailler en équipe et de gérer des projets " +
                        "complexes. Formation en informatique ou équivalent."]
            })
            
            # Définition de la signature du modèle
            input_schema = Schema([
                ColSpec("string", "TEXT")
            ])
            output_schema = Schema([
                ColSpec("double", "match_index"),
                ColSpec("double", "similarity_score")
            ])
            signature = ModelSignature(inputs=input_schema, outputs=output_schema)
            
            # Enregistrement du modèle avec signature
            mlflow.sklearn.log_model(
                pipeline,
                "matching_pipeline",
                registered_model_name="MatchingPipeline",
                signature=signature,
                input_example=input_example
            )
            
            # Affichage d'un exemple de match
            print("\nExemple de match pour le premier candidat:")
            for i in range(min(3, candidate_matches.shape[1])):
                idx = int(candidate_matches[0, i, 0])
                sim = float(candidate_matches[0, i, 1])
                print(f"Match {i+1}: Offre {idx} (similarité: {sim:.3f})")
                print(f"Titre de l'offre: {df_offers.iloc[idx]['TITLE']}\n")
            
        except Exception as e:
            mlflow.log_param("error", str(e))
            print(f"\n❌ Erreur lors du test : {str(e)}")
            raise
        
        print("\n✅ Tous les tests ont réussi!")
        print(f"🔗 Run MLflow ID: {run.info.run_id}")

if __name__ == "__main__":
    train_model() 
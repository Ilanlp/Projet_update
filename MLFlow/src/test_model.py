"""Script pour tester le chargement et l'utilisation du modèle MLflow."""

import mlflow.pyfunc
import pandas as pd
import numpy as np
from jobmarket_ml.config.config import OFFERS_PATH, OFFER_COLUMNS


def test_model():
    """Test du chargement et de l'utilisation du modèle MLflow."""
    
    print(f"OFFERS_PATH {OFFERS_PATH}")
    print(f"OFFER_COLUMNS {OFFER_COLUMNS}")
    
    print("1. Configuration de MLflow...")
    mlflow.set_tracking_uri("http://localhost:8000")
    
    print("2. Chargement du modèle et des données de référence...")
    # Chargement de la dernière version du modèle
    model_uri = f"models:/jobmarket/2"
    model = mlflow.pyfunc.load_model(model_uri)
    
    # Chargement des offres de référence
    df_offers = pd.read_csv(
        OFFERS_PATH,
        compression="gzip",
        sep=",",
        encoding="utf-8",
        usecols=["TITLE", "NOM_ENTREPRISE", "VILLE"] + OFFER_COLUMNS
    )
    
    print("3. Préparation des données de test...")
    # Création d'un exemple de données
    test_data = pd.DataFrame({
        "TEXT": [
            "Développeur Python Senior avec 5 ans d'expérience en ML et Deep Learning. "
            "Expert en TensorFlow et PyTorch. Capable de diriger une équipe technique.",
            
            "Data Scientist junior avec Master en ML. Expérience en NLP et computer vision. "
            "Maîtrise de scikit-learn et pandas.",
            
            "DevOps Engineer avec expertise en Docker et Kubernetes. "
            "Expérience en CI/CD et automatisation."
        ]
    })
    
    print("\n4. Test de matching...")
    try:
        # Prédiction avec le modèle
        matches = model.predict(test_data["TEXT"])
        
        print("\nStructure des résultats:")
        print(f"Type: {type(matches)}")
        print(f"Shape: {matches.shape if hasattr(matches, 'shape') else 'N/A'}")
        
        print("\nRésultats des matches :")
        print("-" * 80)
        
        for i, (text, match_idx) in enumerate(zip(test_data["TEXT"], matches)):
            print(f"\nProfil {i+1}:")
            print(f"Description: {text[:100]}...")
            print("\nMeilleur match:")
            
            # Récupération des informations de l'offre
            offer = df_offers.iloc[match_idx]
            print(f"Titre: {offer['TITLE']}")
            print(f"Entreprise: {offer['NOM_ENTREPRISE']}")
            print(f"Localisation: {offer['VILLE']}")
            print("-" * 80)
            
        print("\n✅ Test réussi!")
        
    except Exception as e:
        print(f"\n❌ Erreur lors du test : {str(e)}")
        raise

if __name__ == "__main__":
    test_model() 
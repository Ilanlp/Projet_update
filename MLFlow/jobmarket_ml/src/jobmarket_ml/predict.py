import argparse
import pandas as pd
import numpy as np
import mlflow
from config.config import (
    MLFLOW_EXPERIMENT_NAME,
    CANDIDATE_COLUMNS,
    OFFERS_PATH,
    OFFER_COLUMNS,
)

# Configuration de l'URI MLflow
MLFLOW_TRACKING_URI = "http://localhost:5010"
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Prédiction avec le modèle de matching"
    )
    parser.add_argument(
        "--run_id",
        type=str,
        required=True,
        help="ID du run MLflow contenant le modèle à utiliser",
    )
    parser.add_argument(
        "--candidate_text",
        type=str,
        required=True,
        help="Texte du candidat à matcher",
    )
    parser.add_argument(
        "--top_k",
        type=int,
        default=5,
        help="Nombre de meilleures offres à retourner",
    )
    parser.add_argument(
        "--nrows_offers",
        type=int,
        default=None,
        help="Nombre de lignes à charger pour les offres (doit être identique à l'entraînement)",
    )
    return parser.parse_args()


def load_model(run_id):
    """Charge le modèle MLflow."""
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    try:
        # Essaie de charger directement depuis l'URI du modèle
        model_uri = f"{MLFLOW_TRACKING_URI}/mlflow-artifacts/{run_id}/artifacts/model"
        print(f"Tentative de chargement du modèle depuis : {model_uri}")
        model = mlflow.sklearn.load_model(model_uri)
        return model
    except Exception as e:
        print(f"Erreur lors du chargement du modèle : {str(e)}")
        # Si ça ne fonctionne pas, essaie avec le format runs:/
        try:
            model_uri = f"runs:/{run_id}/model"
            print(f"Nouvelle tentative avec : {model_uri}")
            model = mlflow.sklearn.load_model(model_uri)
            return model
        except Exception as e:
            print(f"Erreur lors de la seconde tentative : {str(e)}")
            raise


def load_offers(nrows=None):
    """Charge les offres d'emploi."""
    print("Chargement des offres d'emploi...")
    df_offers = pd.read_csv(
        OFFERS_PATH, compression="gzip", sep=",", encoding="utf-8", nrows=nrows
    )

    # Préparation du texte des offres comme à l'entraînement
    df_offers["TEXT"] = (
        df_offers[OFFER_COLUMNS].fillna("").astype(str).agg(". ".join, axis=1)
    )

    return df_offers


def prepare_candidate_data(candidate_text):
    """Prépare les données du candidat pour la prédiction."""
    # Création d'un DataFrame avec une seule ligne
    df = pd.DataFrame({"TEXT": [candidate_text]})
    return df


def predict(model, candidate_data, offers_data, top_k=5):
    """
    Fait des prédictions avec le modèle.

    Parameters:
    -----------
    model : Pipeline
        Le modèle chargé depuis MLflow
    candidate_data : pd.DataFrame
        Les données du candidat
    offers_data : pd.DataFrame
        Les données des offres
    top_k : int
        Nombre de meilleures offres à retourner

    Returns:
    --------
    list : Liste des offres correspondantes avec leurs scores
    """
    # Prétraitement des données
    print("Prétraitement des données...")
    X = pd.DataFrame(offers_data["TEXT"])

    # Prétraitement du candidat
    print("Transformation du candidat...")
    candidate_processed = model.named_steps["preprocessing"].transform(candidate_data)

    # Prédiction avec le MatchingEngine
    print("Calcul des similarités...")
    matching_engine = model.named_steps["matching_engine"]
    similarities = matching_engine.predict(candidate_processed)

    # Conversion en numpy array
    similarities_array = np.array(similarities)

    # Récupération des top_k meilleures offres
    print(f"Sélection des {top_k} meilleures offres...")
    top_indices = similarities_array.argsort()[-top_k:][::-1]
    top_scores = similarities_array[top_indices]

    # Récupération des offres correspondantes
    top_offers = []
    for idx, score in zip(top_indices, top_scores):
        offer = offers_data.iloc[idx]
        offer_info = {
            "score": float(score),  # Conversion en float pour la sérialisation
            "titre": offer["TITLE"],
            "entreprise": offer["NOM_ENTREPRISE"],
            "ville": offer["VILLE"],
            "departement": offer["DEPARTEMENT"],
            "type_contrat": offer["TYPE_CONTRAT"],
            "competences": offer["COMPETENCES"],
            "description": (
                offer["DESCRIPTION"][:500] + "..."
                if len(offer["DESCRIPTION"]) > 500
                else offer["DESCRIPTION"]
            ),
        }
        top_offers.append(offer_info)

    return top_offers


def format_offer(offer):
    """Formate une offre pour l'affichage."""
    return f"""
Score de similarité : {offer['score']:.3f}
Titre : {offer['titre']}
Entreprise : {offer['entreprise']}
Localisation : {offer['ville']}, {offer['departement']}
Type de contrat : {offer['type_contrat']}
Compétences requises : {offer['competences']}

Description :
{offer['description']}
---"""


def main():
    """Fonction principale."""
    args = parse_args()

    try:
        # Chargement du modèle
        print(f"Chargement du modèle depuis le run {args.run_id}...")
        model = load_model(args.run_id)

        # Chargement des offres
        offers_data = load_offers(args.nrows_offers)

        # Préparation des données du candidat
        print("Préparation des données du candidat...")
        candidate_data = prepare_candidate_data(args.candidate_text)

        # Prédiction
        print(f"\nRecherche des {args.top_k} meilleures offres...")
        predictions = predict(model, candidate_data, offers_data, args.top_k)

        # Affichage des résultats
        print("\nMeilleures offres trouvées :")
        for offer in predictions:
            print(format_offer(offer))

    except Exception as e:
        print(f"\n❌ Erreur lors de la prédiction : {str(e)}")
        raise


if __name__ == "__main__":
    main()

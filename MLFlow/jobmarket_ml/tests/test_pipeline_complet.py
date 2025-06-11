import pytest
import pandas as pd
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from jobmarket_ml.custom_transformers.text_preprocessor import TextPreprocessor


@pytest.fixture
def sample_job_data():
    """Données d'exemple pour les offres d'emploi"""
    jobs = [
        # Offres Data
        "Data Engineer avec expertise Python et SQL. Développement de pipelines ETL.",
        "Data Scientist maîtrisant scikit-learn et TensorFlow. Analyse prédictive.",
        "Data Analyst pour analyse de données et création de tableaux de bord.",
        "ML Engineer pour développement de modèles d'apprentissage automatique.",
        "Data Engineer Cloud avec expertise AWS et Azure. Big Data.",
        # Offres Dev
        "Développeur Full Stack JavaScript, React et Node.js.",
        "Développeur Python Django pour application web.",
        "Ingénieur DevOps avec Docker et Kubernetes.",
        "Développeur Java Spring pour applications d'entreprise.",
        "Développeur Frontend React avec TypeScript.",
    ]

    # Labels : 1 pour Data, 0 pour Dev
    labels = [1, 1, 1, 1, 1, 0, 0, 0, 0, 0]

    return pd.DataFrame({"description": jobs, "categorie": labels})


def test_pipeline_complet(sample_job_data):
    """Test du pipeline complet de classification"""

    # Séparation des données
    X = sample_job_data["description"]
    y = sample_job_data["categorie"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42
    )

    # Création du pipeline
    pipeline = Pipeline(
        [
            (
                "preprocessor",
                TextPreprocessor(
                    language="fr", min_df=1, max_df=0.9, ngram_range=(1, 2)
                ),
            ),
            ("classifier", LogisticRegression(random_state=42)),
        ]
    )

    # Entraînement
    pipeline.fit(X_train, y_train)

    # Prédictions
    y_pred = pipeline.predict(X_test)

    # Vérifications
    assert len(y_pred) == len(y_test), "Nombre de prédictions incorrect"
    assert all(
        isinstance(pred, (np.int64, int)) for pred in y_pred
    ), "Type de prédictions incorrect"

    # Score et rapport
    score = pipeline.score(X_test, y_test)
    print("\nScore de classification:", score)
    print("\nRapport de classification:")
    print(classification_report(y_test, y_pred, target_names=["Dev", "Data"]))

    # Test avec de nouvelles données
    nouvelles_offres = pd.Series(
        [
            "Ingénieur MLOps avec expertise en Deep Learning",
            "Développeur Ruby on Rails pour startup",
        ]
    )

    predictions = pipeline.predict(nouvelles_offres)
    assert (
        len(predictions) == 2
    ), "Nombre de prédictions incorrect pour les nouvelles données"

    # Test des probabilités
    proba = pipeline.predict_proba(nouvelles_offres)
    assert proba.shape == (2, 2), "Format des probabilités incorrect"
    assert np.allclose(np.sum(proba, axis=1), 1), "Les probabilités ne somment pas à 1"

    # Vérification des features importantes
    preprocessor = pipeline.named_steps["preprocessor"]
    classifier = pipeline.named_steps["classifier"]
    feature_names = preprocessor.get_feature_names()

    # Obtention des coefficients les plus importants
    coef = classifier.coef_[0]
    top_features_idx = np.argsort(np.abs(coef))[-5:]  # Top 5 features

    print("\nFeatures les plus importantes:")
    for idx in top_features_idx:
        print(f"{feature_names[idx]}: {coef[idx]:.3f}")


def test_pipeline_edge_cases(sample_job_data):
    """Test des cas limites du pipeline"""

    pipeline = Pipeline(
        [
            ("preprocessor", TextPreprocessor(language="fr")),
            ("classifier", LogisticRegression(random_state=42)),
        ]
    )

    # Test avec une seule classe
    X_single = sample_job_data["description"][:5]  # Seulement les offres Data
    y_single = sample_job_data["categorie"][:5]

    with pytest.raises(ValueError):
        pipeline.fit(X_single, y_single)

    # Test avec texte vide
    pipeline.fit(sample_job_data["description"], sample_job_data["categorie"])
    empty_text = pd.Series(["", "   "])
    predictions = pipeline.predict(empty_text)
    assert len(predictions) == 2, "Devrait gérer les textes vides"

    # Test avec caractères spéciaux
    special_chars = pd.Series(
        ["Data ### Engineer $$$ Python @@@", "Développeur !!! Java &&& Spring"]
    )
    predictions = pipeline.predict(special_chars)
    assert len(predictions) == 2, "Devrait gérer les caractères spéciaux"

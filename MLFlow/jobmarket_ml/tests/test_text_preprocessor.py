import pytest
import pandas as pd
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.model_selection import GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from jobmarket_ml.custom_transformers.text_preprocessor import TextPreprocessor


@pytest.fixture
def sample_texts():
    return pd.Series(
        [
            "Je suis un développeur Python avec 5 ans d'expérience.",
            "Recherche développeur Python expérimenté.",
            "Nous recrutons un développeur Java senior.",
            "Python, Java et SQL sont requis pour ce poste.",
        ]
    )


@pytest.fixture
def preprocessor():
    return TextPreprocessor(
        extra_stopwords=["recruter", "rechercher"], language="fr", min_df=1, max_df=0.9
    )


def test_initialization(preprocessor):
    """Test l'initialisation du TextPreprocessor"""
    assert preprocessor.language == "fr"
    assert preprocessor.min_df == 1
    assert preprocessor.max_df == 0.9
    assert "recruter" in preprocessor.extra_stopwords


def test_clean_text(preprocessor):
    """Test la fonction de nettoyage du texte"""
    text = "Python-3.8 & SQL   2023!"
    cleaned = preprocessor._clean(text)
    assert cleaned == "python sql"


def test_preprocessing_pipeline(preprocessor, sample_texts):
    """Test le pipeline complet de prétraitement"""
    # Fit et transform
    preprocessor.fit(sample_texts)
    result = preprocessor.transform(sample_texts)

    # Vérifications
    assert isinstance(result, csr_matrix)
    assert result.shape[0] == len(sample_texts)

    # Vérification des features
    feature_names = preprocessor.get_feature_names()
    assert "python" in feature_names
    assert "développeur" in feature_names

    # Vérification que les stopwords sont bien filtrés
    assert "rechercher" not in feature_names
    assert "recruter" not in feature_names


def test_tfidf_parameters(sample_texts):
    """Test les différents paramètres TF-IDF"""
    # Test avec max_features
    preprocessor_limited = TextPreprocessor(language="fr", max_features=5)
    preprocessor_limited.fit(sample_texts)
    result_limited = preprocessor_limited.transform(sample_texts)
    assert len(preprocessor_limited.get_feature_names()) <= 5

    # Test avec ngram_range
    preprocessor_bigrams = TextPreprocessor(language="fr", ngram_range=(1, 2))
    preprocessor_bigrams.fit(sample_texts)
    feature_names = preprocessor_bigrams.get_feature_names()
    # Vérifier la présence de bigrammes
    bigrams = [f for f in feature_names if " " in f]
    assert len(bigrams) > 0


def test_error_handling(preprocessor, sample_texts):
    """Test la gestion des erreurs"""
    # Test transform sans fit
    new_preprocessor = TextPreprocessor()
    with pytest.raises(ValueError):
        new_preprocessor.transform(sample_texts)

    # Test get_feature_names sans fit
    with pytest.raises(ValueError):
        new_preprocessor.get_feature_names()


def test_input_handling(preprocessor):
    """Test la gestion des différents formats d'entrée"""
    # Test avec DataFrame
    df = pd.DataFrame({"text": ["Test avec DataFrame", "Autre test"], "other": [1, 2]})
    preprocessor.fit(df)
    result = preprocessor.transform(df)
    assert isinstance(result, csr_matrix)

    # Test avec Series
    series = pd.Series(["Test avec Series", "Autre test"])
    preprocessor.fit(series)
    result = preprocessor.transform(series)
    assert isinstance(result, csr_matrix)


def test_grid_search_compatibility(sample_texts):
    """Test la compatibilité avec GridSearchCV"""
    # Création de données factices pour la classification
    y = np.array([1, 1, 0, 0])  # Labels binaires pour les 4 textes d'exemple

    # Création du pipeline
    pipeline = Pipeline(
        [
            ("preprocessor", TextPreprocessor(language="fr")),
            ("classifier", LogisticRegression(random_state=42)),
        ]
    )

    # Paramètres à tester (ajustés pour éviter les combinaisons invalides)
    param_grid = {
        "preprocessor__min_df": [1],  # Fixé à 1 pour les petits jeux de données
        "preprocessor__max_df": [0.9],  # Augmenté pour éviter les conflits
        "preprocessor__ngram_range": [(1, 1), (1, 2)],
        "classifier__C": [0.1, 1.0],
    }

    # Configuration de GridSearchCV
    grid_search = GridSearchCV(
        pipeline, param_grid, cv=2, n_jobs=-1, scoring="accuracy"
    )

    # Entraînement
    grid_search.fit(sample_texts, y)

    # Vérifications
    assert hasattr(
        grid_search, "best_params_"
    ), "GridSearchCV n'a pas trouvé de meilleurs paramètres"
    assert hasattr(grid_search, "best_score_"), "GridSearchCV n'a pas calculé de score"
    assert grid_search.best_score_ > 0, "Le score devrait être positif"
    assert not np.isnan(
        grid_search.best_score_
    ), "Le meilleur score ne devrait pas être NaN"

    # Test de prédiction avec les meilleurs paramètres
    predictions = grid_search.predict(sample_texts)
    assert len(predictions) == len(
        sample_texts
    ), "Le nombre de prédictions ne correspond pas"
    assert all(
        isinstance(pred, (np.int64, int)) for pred in predictions
    ), "Les prédictions devraient être des entiers"

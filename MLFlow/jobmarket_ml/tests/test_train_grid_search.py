import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from sklearn.model_selection import GridSearchCV
from sklearn.base import BaseEstimator, TransformerMixin

# Import de la configuration de test
from tests.config import (
    OFFERS_PATH,
    CANDIDATES_PATH,
    OFFER_COLUMNS,
    CANDIDATE_COLUMNS,
    CUSTOM_STOPWORDS,
    MLFLOW_EXPERIMENT_NAME,
)


# Classes Mock pour les composants de matching
class MockPreprocessor:
    def __init__(self, min_df=2, max_df=0.7):
        self.min_df = min_df
        self.max_df = max_df

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        # Retourne un tableau de nombres pour éviter les problèmes de type
        return np.random.rand(len(X), 10)

    def get_params(self, deep=True):
        return {"min_df": self.min_df, "max_df": self.max_df}

    def set_params(self, **params):
        for key, value in params.items():
            setattr(self, key, value)
        return self


class MockOfferPipeline(BaseEstimator, TransformerMixin):
    def __init__(self, custom_stopwords=None):
        self.custom_stopwords = custom_stopwords
        self.preprocessor = MockPreprocessor()

    def fit(self, X, y=None):
        self.preprocessor.fit(X)
        return self

    def transform(self, X):
        return self.preprocessor.transform(X)

    def get_params(self, deep=True):
        params = super().get_params(deep=deep)
        if deep:
            params.update(
                {
                    f"preprocessor__{key}": val
                    for key, val in self.preprocessor.get_params().items()
                }
            )
        return params

    def set_params(self, **params):
        preprocessor_params = {}
        other_params = {}

        for key, value in params.items():
            if key.startswith("preprocessor__"):
                preprocessor_params[key.split("__", 1)[1]] = value
            else:
                other_params[key] = value

        if preprocessor_params:
            self.preprocessor.set_params(**preprocessor_params)
        if other_params:
            super().set_params(**other_params)

        return self


class MockCandidatePipeline(MockOfferPipeline):
    pass


class MockMatchingEngine(BaseEstimator, TransformerMixin):
    def __init__(
        self, text_weight=0.6, skills_weight=0.2, experience_weight=0.2, k_matches=5
    ):
        self.text_weight = text_weight
        self.skills_weight = skills_weight
        self.experience_weight = experience_weight
        self.k_matches = k_matches

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        # Retourne un tableau de nombres pour éviter les problèmes de type
        return np.random.rand(len(X), 3)

    def predict(self, X):
        # Retourne des prédictions binaires
        return np.random.randint(0, 2, size=len(X))


class MockMatchingEvaluator:
    def __init__(self, n_splits=5):
        self.n_splits = n_splits

    def get_scorer(self):
        return "accuracy"

    def evaluate(self, engine, offers_vectors, candidates_vectors):
        return {"precision": 0.85, "recall": 0.80, "f1_score": 0.82}


# Import après la configuration du mock
from jobmarket_ml.train_grid_search import (
    load_data,
    create_matching_pipeline,
    define_param_grid,
    train_with_grid_search,
)


@pytest.fixture
def mock_data():
    """Création de données factices pour les tests"""
    # Offres d'emploi
    offers = pd.DataFrame(
        {
            "job_title": ["Data Engineer", "Full Stack Developer", "Data Scientist"],
            "job_description": [
                "Python, SQL, ETL",
                "JavaScript, React, Node.js",
                "Machine Learning, Python, R",
            ],
            "required_skills": [
                "Python,SQL,Airflow",
                "JavaScript,React,Node.js",
                "Python,R,scikit-learn",
            ],
        }
    )

    # Candidats
    candidates = pd.DataFrame(
        {
            "title": ["Senior Data Engineer", "Full Stack Developer", "ML Researcher"],
            "description": [
                "Expert en Python et SQL",
                "Développeur JavaScript et React",
                "Spécialiste en Deep Learning",
            ],
            "skills": [
                "Python,SQL,Spark",
                "JavaScript,React,Vue.js",
                "Python,TensorFlow,PyTorch",
            ],
        }
    )

    return offers, candidates


@pytest.fixture
def mock_mlflow():
    """Mock pour MLflow"""
    with patch("mlflow.start_run") as mock_run:
        mock_context = MagicMock()
        mock_run.return_value.__enter__.return_value = mock_context
        yield mock_run


def test_create_matching_pipeline():
    """Test la création du pipeline de matching"""
    pipeline = create_matching_pipeline()

    # Vérification de la structure du pipeline
    assert len(pipeline.steps) == 3
    assert pipeline.named_steps.keys() == {
        "offer_pipeline",
        "candidate_pipeline",
        "matching_engine",
    }

    # Vérification des paramètres par défaut
    assert hasattr(pipeline.named_steps["matching_engine"], "text_weight")
    assert hasattr(pipeline.named_steps["matching_engine"], "skills_weight")


def test_define_param_grid():
    """Test la définition de la grille de paramètres"""
    param_grid = define_param_grid()

    # Vérification des paramètres requis
    assert "matching_engine__text_weight" in param_grid
    assert "matching_engine__skills_weight" in param_grid
    assert "matching_engine__experience_weight" in param_grid
    assert "matching_engine__k_matches" in param_grid

    # Vérification des plages de valeurs
    assert all(0 <= w <= 1 for w in param_grid["matching_engine__text_weight"])
    assert all(0 <= w <= 1 for w in param_grid["matching_engine__skills_weight"])
    assert all(k > 0 for k in param_grid["matching_engine__k_matches"])


@patch("pandas.read_csv")
def test_load_data(mock_read_csv, mock_data):
    """Test le chargement des données"""
    offers, candidates = mock_data
    mock_read_csv.side_effect = [offers, candidates]

    # Test avec limitation du nombre de lignes
    df_o, df_c = load_data(nrows_offers=3, nrows_candidates=2)

    # Vérification de la création du champ TEXT
    assert "TEXT" in df_o.columns
    assert "TEXT" in df_c.columns

    # Vérification que le texte est bien concaténé
    assert isinstance(df_o["TEXT"].iloc[0], str)
    assert isinstance(df_c["TEXT"].iloc[0], str)


@pytest.mark.integration
def test_train_with_grid_search(mock_data):
    """Test l'entraînement avec GridSearchCV"""
    offers, candidates = mock_data

    # Préparation des données
    offers_text = offers.apply(
        lambda x: f"{x['job_title']}. {x['job_description']}", axis=1
    ).values
    candidates_text = candidates.apply(
        lambda x: f"{x['title']}. {x['description']}", axis=1
    ).values

    # Création d'étiquettes binaires pour le test
    y = np.array([1, 0, 1])  # Simule des correspondances

    # Configuration d'une grille réduite pour le test
    with patch("jobmarket_ml.train_grid_search.define_param_grid") as mock_grid:
        mock_grid.return_value = {
            "matching_engine__text_weight": [0.6],
            "matching_engine__skills_weight": [0.2],
            "matching_engine__experience_weight": [0.2],
            "matching_engine__k_matches": [3],
            "offer_pipeline__preprocessor__min_df": [2],
            "offer_pipeline__preprocessor__max_df": [0.7],
            "candidate_pipeline__preprocessor__min_df": [2],
            "candidate_pipeline__preprocessor__max_df": [0.7],
        }

        # Mock de MLflow
        with patch("mlflow.start_run") as mock_run:
            mock_context = MagicMock()
            mock_run.return_value.__enter__.return_value = mock_context

            # Mock de log_params pour éviter les erreurs de paramètres
            with patch("mlflow.log_params") as mock_log_params:
                # Lancement de l'entraînement avec les étiquettes
                grid_search = train_with_grid_search(
                    offers_text, candidates_text, cv_folds=2, y=y
                )

                # Vérifications
                assert isinstance(grid_search, GridSearchCV)
                assert hasattr(grid_search, "best_params_")
                assert hasattr(grid_search, "best_score_")
                assert grid_search.best_score_ > 0


@pytest.mark.integration
def test_grid_search_parameter_effects(mock_data):
    """Test l'effet des différents paramètres sur les résultats"""
    offers, candidates = mock_data

    # Préparation des données
    offers_text = offers.apply(
        lambda x: f"{x['job_title']}. {x['job_description']}", axis=1
    ).values
    candidates_text = candidates.apply(
        lambda x: f"{x['title']}. {x['description']}", axis=1
    ).values

    # Création d'étiquettes binaires pour le test
    y = np.array([1, 0, 1])  # Simule des correspondances

    # Test avec différentes configurations
    param_configs = [
        # Plus de poids sur le texte
        {
            "matching_engine__text_weight": [0.8],
            "matching_engine__skills_weight": [0.1],
            "matching_engine__experience_weight": [0.1],
        },
        # Plus de poids sur les compétences
        {
            "matching_engine__text_weight": [0.2],
            "matching_engine__skills_weight": [0.6],
            "matching_engine__experience_weight": [0.2],
        },
    ]

    scores = []
    for config in param_configs:
        with patch("jobmarket_ml.train_grid_search.define_param_grid") as mock_grid:
            mock_grid.return_value = {
                **config,
                "matching_engine__k_matches": [3],
                "offer_pipeline__preprocessor__min_df": [2],
                "offer_pipeline__preprocessor__max_df": [0.7],
                "candidate_pipeline__preprocessor__min_df": [2],
                "candidate_pipeline__preprocessor__max_df": [0.7],
            }

            # Nouveau run MLflow pour chaque configuration
            with patch("mlflow.start_run") as mock_run:
                mock_context = MagicMock()
                mock_run.return_value.__enter__.return_value = mock_context

                # Mock de log_params pour éviter les erreurs de paramètres
                with patch("mlflow.log_params") as mock_log_params:
                    grid_search = train_with_grid_search(
                        offers_text, candidates_text, cv_folds=2, y=y
                    )
                    scores.append(grid_search.best_score_)

    # Vérification que les scores sont différents
    assert (
        len(set(scores)) > 1
    ), "Les différentes configurations devraient donner des scores différents"

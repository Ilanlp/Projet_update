from sklearn.pipeline import Pipeline
from sklearn.base import BaseEstimator, TransformerMixin
from jobmarket_ml.custom_transformers.text_preprocessor import TextPreprocessor
from jobmarket_ml.custom_transformers.bert_encoder import BertEncoder
from .pipeline import MatchingEngine


class UnifiedPipeline(Pipeline):
    """Pipeline personnalisé qui gère les dimensions différentes entre X et y."""

    def fit(self, X, y=None, **fit_params):
        """
        Adapte le pipeline aux données d'entraînement.
        Gère le cas où X et y ont des dimensions différentes.
        """
        # Prétraitement de X et y séparément
        if len(X.shape) == 2 and X.shape[1] > 1:
            # Les données sont déjà encodées
            Xt = X
        else:
            # Les données doivent être prétraitées
            Xt = self.named_steps["preprocessing"].fit_transform(X)

        if y is not None:
            if len(y.shape) == 2 and y.shape[1] > 1:
                # Les données sont déjà encodées
                yt = y
            else:
                # Les données doivent être prétraitées
                yt = self.named_steps["preprocessing"].fit_transform(y)
        else:
            yt = None

        # Entraînement du MatchingEngine
        self.named_steps["matching_engine"].fit(Xt, yt)

        return self

    def transform(self, X):
        """Applique la transformation aux données."""
        if len(X.shape) == 2 and X.shape[1] > 1:
            # Les données sont déjà encodées
            return X
        else:
            # Les données doivent être prétraitées
            return self.named_steps["preprocessing"].transform(X)


def create_unified_pipeline(extra_stopwords=None):
    """
    Crée un pipeline unifié pour l'optimisation des hyperparamètres.
    Cette version est compatible avec GridSearchCV et RandomizedSearchCV.

    Parameters:
    -----------
    extra_stopwords : list, optional
        Liste de mots à exclure du traitement

    Returns:
    --------
    UnifiedPipeline : Un pipeline scikit-learn configuré pour le matching
    """
    # Pipeline de prétraitement commun
    preprocessing = Pipeline(
        [
            ("text_prep", TextPreprocessor(extra_stopwords=extra_stopwords)),
            ("encoder", BertEncoder()),
        ]
    )

    # Pipeline complet
    return UnifiedPipeline(
        [("preprocessing", preprocessing), ("matching_engine", MatchingEngine())]
    )


def define_unified_param_grid(is_random_search=False, is_test=False):
    """
    Définit une grille de paramètres unifiée pour l'optimisation.

    Parameters:
    -----------
    is_random_search : bool
        Si True, retourne les distributions pour RandomizedSearchCV
        Si False, retourne la grille pour GridSearchCV
    is_test : bool
        Si True, retourne une grille réduite pour les tests

    Returns:
    --------
    dict : Grille de paramètres ou distributions pour l'optimisation
    """
    if is_test:
        if is_random_search:
            from scipy.stats import uniform, randint

            return {
                "matching_engine__text_weight": uniform(0.4, 0.2),
                "matching_engine__skills_weight": uniform(0.1, 0.1),
                "matching_engine__experience_weight": uniform(0.1, 0.1),
                "matching_engine__k_matches": randint(3, 5),
                "preprocessing__text_prep__min_df": randint(1, 2),
                "preprocessing__text_prep__max_df": uniform(0.3, 0.2),
            }
        else:
            return {
                "matching_engine__text_weight": [0.4, 0.6],
                "matching_engine__skills_weight": [0.1, 0.2],
                "matching_engine__experience_weight": [0.1],
                "matching_engine__k_matches": [3],
                "preprocessing__text_prep__min_df": [1],
                "preprocessing__text_prep__max_df": [0.3, 0.5],
            }
    else:
        if is_random_search:
            from scipy.stats import uniform, randint

            return {
                "matching_engine__text_weight": uniform(0.3, 0.6),
                "matching_engine__skills_weight": uniform(0.05, 0.35),
                "matching_engine__experience_weight": uniform(0.05, 0.25),
                "matching_engine__k_matches": randint(3, 15),
                "preprocessing__text_prep__min_df": randint(1, 5),
                "preprocessing__text_prep__max_df": uniform(0.3, 0.6),
            }
        else:
            return {
                "matching_engine__text_weight": [0.4, 0.6, 0.8],
                "matching_engine__skills_weight": [0.1, 0.2, 0.3],
                "matching_engine__experience_weight": [0.1, 0.2],
                "matching_engine__k_matches": [3, 5, 10],
                "preprocessing__text_prep__min_df": [1, 2, 3],
                "preprocessing__text_prep__max_df": [0.3, 0.5, 0.7],
            }

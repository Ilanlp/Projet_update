from sklearn.pipeline import Pipeline
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from jobmarket_ml.custom_transformers.text_preprocessor import TextPreprocessor
from jobmarket_ml.custom_transformers.bert_encoder import BertEncoder


class MatchingEngine(BaseEstimator, TransformerMixin):
    def __init__(
        self, text_weight=0.6, skills_weight=0.3, experience_weight=0.1, k_matches=5
    ):
        self.text_weight = text_weight
        self.skills_weight = skills_weight
        self.experience_weight = experience_weight
        self.k_matches = k_matches

    def fit(self, X, y=None):
        """
        X : Les vecteurs des offres
        y : Les vecteurs des candidats
        """
        self.offer_vectors_ = X
        self.candidate_vectors_ = y
        return self

    def compute_similarity_matrix(self):
        """
        Calcule la matrice de similarité entre les candidats et les offres.
        """
        if not hasattr(self, "offer_vectors_") or not hasattr(
            self, "candidate_vectors_"
        ):
            raise ValueError("Le modèle n'a pas été entraîné. Appelez fit() d'abord.")

        return cosine_similarity(self.candidate_vectors_, self.offer_vectors_)

    def transform(self, X):
        """
        Calcule et retourne la matrice de similarité
        """
        similarity_matrix = self.compute_similarity_matrix()
        return similarity_matrix

    def predict(self, X):
        """
        Prédit les meilleurs matches pour chaque candidat.
        Retourne uniquement les indices des offres.
        """
        matches = self.get_top_matches(self.transform(X))
        return [match[0] for match in matches]

    def get_params(self, deep=True):
        """Obtient les paramètres pour cet estimateur.

        Args:
            deep: Si True, retourne aussi les paramètres des sous-estimateurs

        Returns:
            dict: Dictionnaire des paramètres
        """
        return {
            "text_weight": self.text_weight,
            "skills_weight": self.skills_weight,
            "experience_weight": self.experience_weight,
            "k_matches": self.k_matches,
        }

    def set_params(self, **parameters):
        """Configure les paramètres de cet estimateur.

        Args:
            **parameters: Paramètres à configurer

        Returns:
            self: L'estimateur lui-même
        """
        for parameter, value in parameters.items():
            setattr(self, parameter, value)
        return self

    def predict_table(self, X, df_offers=None):
        """
        Prédit les meilleurs matches pour chaque candidat et retourne un DataFrame
        avec les offres et leurs indices.

        Parameters:
        -----------
        X : array-like
            Les vecteurs des candidats
        df_offers : pandas.DataFrame, optional
            Le DataFrame contenant les offres originales.
            Si fourni, les colonnes des offres seront incluses dans le résultat.

        Returns:
        --------
        pandas.DataFrame
            Un DataFrame avec les colonnes suivantes :
            - candidate_idx : L'index du candidat
            - rank : Le rang de l'offre pour ce candidat (1 = meilleur match)
            - offer_idx : L'index de l'offre
            - similarity_score : Le score de similarité
            - ... : Les colonnes du DataFrame des offres si df_offers est fourni
        """
        import pandas as pd

        # Obtenir les matches
        matches = self.transform(X)

        # Créer une liste pour stocker les résultats
        results = []

        # Pour chaque candidat
        for match in matches:
            candidate_idx = match["candidate_idx"]

            # Pour chaque offre correspondante
            for rank, (offer_idx, score) in enumerate(
                zip(match["offer_indices"], match["similarity_scores"]), 1
            ):
                result = {
                    "candidate_idx": candidate_idx,
                    "rank": rank,
                    "offer_idx": offer_idx,
                    "similarity_score": score,
                }

                # Si le DataFrame des offres est fourni, ajouter ses colonnes
                if df_offers is not None:
                    offer_data = df_offers.iloc[offer_idx].to_dict()
                    result.update(offer_data)

                results.append(result)

        # Créer le DataFrame final
        df_results = pd.DataFrame(results)

        # Trier par candidat et rang
        df_results = df_results.sort_values(["candidate_idx", "rank"])

        return df_results

    def get_top_matches(self, similarity_matrix):
        """
        Retourne les k meilleurs matchs pour chaque offre.

        Args:
            similarity_matrix: Matrice de similarité entre offres et candidats

        Returns:
            matches: Liste de tuples (indices_offres, scores_similarité)
        """
        matches = []
        for i in range(similarity_matrix.shape[0]):
            # Obtenir les indices des k meilleurs candidats pour l'offre i
            top_k_indices = np.argsort(similarity_matrix[i])[-self.k_matches :][::-1]
            # Obtenir les scores correspondants
            top_k_scores = similarity_matrix[i][top_k_indices]
            matches.append((top_k_indices.tolist(), top_k_scores.tolist()))
        return matches


def create_matching_pipeline(extra_stopwords=None):
    """
    Crée un pipeline de matching complet avec tous les composants nécessaires.

    Parameters:
    -----------
    extra_stopwords : list, optional
        Liste de mots à exclure du traitement

    Returns:
    --------
    Pipeline : Un pipeline scikit-learn configuré pour le matching
    """
    # Pipeline pour les offres
    offer_pipeline = Pipeline(
        [
            ("preprocessor", TextPreprocessor(extra_stopwords=extra_stopwords)),
            ("encoder", BertEncoder()),
        ]
    )

    # Pipeline pour les candidats
    candidate_pipeline = Pipeline(
        [
            ("preprocessor", TextPreprocessor(extra_stopwords=extra_stopwords)),
            ("encoder", BertEncoder()),
        ]
    )

    # Pipeline complet
    return Pipeline(
        [
            ("offer_pipeline", offer_pipeline),
            ("candidate_pipeline", candidate_pipeline),
            ("matching_engine", MatchingEngine()),
        ]
    )


def define_param_grid():
    """
    Définit la grille de paramètres pour GridSearchCV.

    Returns:
    --------
    dict : Grille de paramètres pour l'optimisation
    """
    return {
        "matching_engine__text_weight": [0.4, 0.6, 0.8],
        "matching_engine__skills_weight": [0.1, 0.2, 0.3],
        "matching_engine__experience_weight": [0.1, 0.2],
        "matching_engine__k_matches": [3, 5, 10],
    }


def define_param_distributions():
    """
    Définit les distributions de paramètres pour RandomizedSearchCV.

    Returns:
    --------
    dict : Distributions de paramètres pour l'optimisation aléatoire
    """
    from scipy.stats import uniform, randint

    return {
        "matching_engine__text_weight": uniform(0.3, 0.6),
        "matching_engine__skills_weight": uniform(0.05, 0.35),
        "matching_engine__experience_weight": uniform(0.05, 0.25),
        "matching_engine__k_matches": randint(3, 15),
    }

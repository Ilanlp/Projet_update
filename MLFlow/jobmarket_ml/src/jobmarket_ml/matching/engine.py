import numpy as np
from sklearn.base import BaseEstimator
from sklearn.metrics.pairwise import cosine_similarity


class MatchingEngine(BaseEstimator):
    def __init__(
        self, text_weight=0.6, skills_weight=0.3, experience_weight=0.1, k_matches=5
    ):
        self.text_weight = text_weight
        self.skills_weight = skills_weight
        self.experience_weight = experience_weight
        self.k_matches = k_matches
        self.offer_vectors = None
        self.candidate_vectors = None

    def fit(self, offer_vectors, candidate_vectors):
        """Stocke les vecteurs d'offres et de candidats"""
        self.offer_vectors = offer_vectors
        self.candidate_vectors = candidate_vectors
        return self

    def compute_similarity_matrix(self):
        """Calcule la matrice de similarité entre offres et candidats"""
        if self.offer_vectors is None or self.candidate_vectors is None:
            raise ValueError(
                "Les vecteurs d'offres et de candidats doivent être définis"
            )

        return cosine_similarity(self.candidate_vectors, self.offer_vectors)

    def get_top_matches(self, similarity_matrix=None):
        """Retourne les k meilleurs matches pour chaque candidat"""
        if similarity_matrix is None:
            similarity_matrix = self.compute_similarity_matrix()

        n_candidates = similarity_matrix.shape[0]
        matches = []

        for i in range(n_candidates):
            # Obtenir les indices des k meilleures offres pour le candidat i
            top_k_indices = np.argsort(similarity_matrix[i])[-self.k_matches :][::-1]
            # Obtenir les scores correspondants
            top_k_scores = similarity_matrix[i][top_k_indices]

            matches.append(
                {
                    "candidate_idx": i,
                    "offer_indices": top_k_indices.tolist(),
                    "similarity_scores": top_k_scores.tolist(),
                }
            )

        return matches

    def compute_skills_score(self, offer_skills, candidate_skills):
        """À implémenter : calcul du score de correspondance des compétences"""
        return 0.0

    def compute_experience_score(self, required_exp, candidate_exp):
        """À implémenter : calcul du score de correspondance de l'expérience"""
        return 0.0

    def combine_scores(self, text_score, skills_score, experience_score):
        """Combine les différents scores avec leurs poids"""
        return (
            self.text_weight * text_score
            + self.skills_weight * skills_score
            + self.experience_weight * experience_score
        )

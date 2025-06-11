import numpy as np
from sklearn.model_selection import KFold
from sklearn.metrics import make_scorer


class MatchingEvaluator:
    def __init__(self, n_splits=5, random_state=42):
        self.n_splits = n_splits
        self.kf = KFold(n_splits=n_splits, shuffle=True, random_state=random_state)

    def precision_at_k(self, y_true, y_pred, k=5):
        """Calcule la précision@k pour les recommandations"""
        if len(y_pred) > k:
            y_pred = y_pred[:k]

        # Conversion en listes pour pouvoir utiliser set()
        y_true = y_true.tolist() if hasattr(y_true, "tolist") else y_true
        y_pred = y_pred.tolist() if hasattr(y_pred, "tolist") else y_pred

        # Si y_true est une liste de listes, on prend la première liste
        if isinstance(y_true[0], list):
            y_true = y_true[0]

        # Si y_pred est une liste de listes, on prend la première liste
        if isinstance(y_pred[0], list):
            y_pred = y_pred[0]

        # Conversion en tuples pour pouvoir utiliser set()
        y_true = [tuple(x) if isinstance(x, list) else x for x in y_true]
        y_pred = [tuple(x) if isinstance(x, list) else x for x in y_pred]

        return len(set(y_true) & set(y_pred)) / min(k, len(y_true))

    def ndcg_at_k(self, y_true, y_pred_scores, k=5):
        """Calcule le NDCG@k (Normalized Discounted Cumulative Gain)"""
        if len(y_pred_scores) > k:
            y_pred_scores = y_pred_scores[:k]

        dcg = sum(
            (2**score - 1) / np.log2(i + 2) for i, score in enumerate(y_pred_scores)
        )

        # Calcul de l'IDCG (DCG idéal)
        ideal_scores = sorted(y_pred_scores, reverse=True)
        idcg = sum(
            (2**score - 1) / np.log2(i + 2) for i, score in enumerate(ideal_scores)
        )

        return dcg / idcg if idcg > 0 else 0

    def evaluate(self, matching_engine, offer_vectors, candidate_vectors):
        """Évalue le système de matching avec validation croisée"""
        results = {"precision_at_k": [], "ndcg_at_k": [], "mean_similarity": []}

        for train_idx, test_idx in self.kf.split(candidate_vectors):
            # Entraînement sur un sous-ensemble
            train_candidates = candidate_vectors[train_idx]
            test_candidates = candidate_vectors[test_idx]

            # Fit et prédiction
            matching_engine.fit(offer_vectors, train_candidates)
            similarity_matrix = matching_engine.transform(offer_vectors)
            matches = matching_engine.get_top_matches(similarity_matrix)

            # Calcul des métriques
            for match in matches:
                results["precision_at_k"].append(
                    self.precision_at_k(match[0], match[1][:5])
                )
                results["ndcg_at_k"].append(self.ndcg_at_k(match[0], match[1]))
                results["mean_similarity"].append(np.mean(match[1]))

        # Calcul des moyennes
        return {
            "precision_at_5": np.mean(results["precision_at_k"]),
            "ndcg_at_5": np.mean(results["ndcg_at_k"]),
            "mean_similarity": np.mean(results["mean_similarity"]),
        }

    def get_scorer(self):
        """Retourne un scorer compatible avec scikit-learn"""
        return make_scorer(self.precision_at_k)

from sklearn.base import BaseEstimator, TransformerMixin
from sentence_transformers import SentenceTransformer
import numpy as np
import pandas as pd


class BertEncoder(BaseEstimator, TransformerMixin):
    """Transformer pour l'encodage BERT des textes."""

    def __init__(
        self, model_name="paraphrase-multilingual-MiniLM-L12-v2", batch_size=32
    ):
        """Initialise l'encodeur BERT.

        Args:
            model_name: Nom du modèle BERT à utiliser
            batch_size: Taille des lots pour l'encodage
        """
        self.model_name = model_name
        self.batch_size = batch_size

    def fit(self, X, y=None):
        """Charge le modèle BERT."""
        if not hasattr(self, "model_"):
            self.model_ = SentenceTransformer(self.model_name)
        return self

    def transform(self, X):
        """
        Transforme les textes en vecteurs BERT.

        Parameters:
        -----------
        X : array-like ou sparse matrix
            Les textes à transformer

        Returns:
        --------
        array : Les vecteurs BERT
        """
        # Si X est une matrice sparse, la convertir en array dense
        if hasattr(X, "toarray"):
            X = X.toarray()
        elif hasattr(X, "values"):
            X = X.values

        # Si les données sont déjà encodées (2D avec plus d'une colonne)
        if isinstance(X, np.ndarray) and len(X.shape) == 2 and X.shape[1] > 1:
            return X

        # Convertir en liste de textes
        if isinstance(X, pd.DataFrame):
            if len(X.shape) == 2 and X.shape[1] > 1:
                return X.values
            X = X.iloc[:, 0]
        elif isinstance(X, pd.Series):
            X = X.values
        elif isinstance(X, np.ndarray):
            if len(X.shape) == 2:
                if X.shape[1] > 1:
                    return X
                X = X.flatten()

        # Convertir les valeurs numériques en chaînes
        X = [str(x) if not isinstance(x, str) else x for x in X]

        # Encoder les textes
        return self.model_.encode(
            X,
            batch_size=self.batch_size,
            show_progress_bar=False,
        )

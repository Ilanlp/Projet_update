from sklearn.model_selection import RandomizedSearchCV, GridSearchCV
from sklearn.base import BaseEstimator, clone
import numpy as np


class MatchingRandomizedSearchCV(RandomizedSearchCV):
    """Version adaptée de RandomizedSearchCV pour le matching."""

    def fit(self, X, y=None, **fit_params):
        """
        Adapte la recherche aléatoire aux données d'entraînement.
        Gère le cas où X et y ont des dimensions différentes.
        """
        self._validate_params()

        # Clone de l'estimateur pour chaque fold
        estimator = clone(self.estimator)

        # Prétraitement initial des données
        if len(X.shape) == 2 and X.shape[1] > 1:
            # Les données sont déjà encodées
            Xt = X
        else:
            # Les données doivent être prétraitées
            Xt = estimator.named_steps["preprocessing"].fit_transform(X)

        if y is not None:
            if len(y.shape) == 2 and y.shape[1] > 1:
                # Les données sont déjà encodées
                yt = y
            else:
                # Les données doivent être prétraitées
                yt = estimator.named_steps["preprocessing"].fit_transform(y)
        else:
            yt = None

        # Création d'un index artificiel pour la validation croisée
        n_samples = len(Xt)
        indices = np.arange(n_samples)

        # Stockage des données transformées pour l'évaluation
        self.X_transformed_ = Xt
        self.y_transformed_ = yt

        # Appel de la méthode fit parent avec les indices
        super().fit(Xt, indices, **fit_params)

        return self


class MatchingGridSearchCV(GridSearchCV):
    """Version adaptée de GridSearchCV pour le matching."""

    def fit(self, X, y=None, **fit_params):
        """
        Adapte la recherche sur grille aux données d'entraînement.
        Gère le cas où X et y ont des dimensions différentes.
        """
        self._validate_params()

        # Clone de l'estimateur pour chaque fold
        estimator = clone(self.estimator)

        # Prétraitement initial des données
        if len(X.shape) == 2 and X.shape[1] > 1:
            # Les données sont déjà encodées
            Xt = X
        else:
            # Les données doivent être prétraitées
            Xt = estimator.named_steps["preprocessing"].fit_transform(X)

        if y is not None:
            if len(y.shape) == 2 and y.shape[1] > 1:
                # Les données sont déjà encodées
                yt = y
            else:
                # Les données doivent être prétraitées
                yt = estimator.named_steps["preprocessing"].fit_transform(y)
        else:
            yt = None

        # Création d'un index artificiel pour la validation croisée
        n_samples = len(Xt)
        indices = np.arange(n_samples)

        # Stockage des données transformées pour l'évaluation
        self.X_transformed_ = Xt
        self.y_transformed_ = yt

        # Appel de la méthode fit parent avec les indices
        super().fit(Xt, indices, **fit_params)

        return self

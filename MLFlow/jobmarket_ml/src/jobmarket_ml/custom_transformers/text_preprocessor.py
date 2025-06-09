import re
import spacy
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_extraction.text import TfidfVectorizer


class TextPreprocessor(BaseEstimator, TransformerMixin):
    """Transformer pour le prétraitement du texte."""

    def __init__(
        self,
        extra_stopwords=None,
        language="fr",
    ):
        """
        Initialise le préprocesseur de texte.

        Args:
            extra_stopwords: Liste de stopwords supplémentaires
            language: Code de langue pour spaCy ('fr' ou 'en')
        """
        self.extra_stopwords = extra_stopwords if extra_stopwords is not None else []
        self.language = language
        self.nlp_ = None

    def _clean(self, text):
        """
        Nettoie le texte en appliquant plusieurs transformations.

        Args:
            text: Texte à nettoyer

        Returns:
            str: Texte nettoyé
        """
        if isinstance(text, pd.Series):
            text = text.iloc[0] if len(text) > 0 else ""
        elif not isinstance(text, str):
            text = str(text)

        # Conversion en minuscules
        text = text.lower()

        # Suppression des caractères spéciaux et des nombres
        text = re.sub(r"[^a-zA-ZÀ-ÿ\s]", " ", text)

        # Suppression des espaces multiples
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    def _lemmatize(self, text):
        """
        Lemmatise le texte en utilisant spaCy.

        Args:
            text: Texte à lemmatiser

        Returns:
            str: Texte lemmatisé
        """
        if isinstance(text, pd.Series):
            text = text.iloc[0] if len(text) > 0 else ""
        elif not isinstance(text, str):
            text = str(text)

        doc = self.nlp_(text)

        # Filtrage des stopwords et lemmatisation
        tokens = [
            token.lemma_ for token in doc if not token.is_stop and len(token.text) > 2
        ]

        return " ".join(tokens)

    def fit(self, X, y=None):
        """
        Prépare le préprocesseur.

        Args:
            X: Textes d'entraînement
            y: Non utilisé, présent pour la compatibilité avec scikit-learn

        Returns:
            self: Le préprocesseur entraîné
        """
        if self.nlp_ is None:
            # Chargement du modèle spaCy
            if self.language == "fr":
                try:
                    self.nlp_ = spacy.load("fr_core_news_sm")
                except OSError:
                    spacy.cli.download("fr_core_news_sm")
                    self.nlp_ = spacy.load("fr_core_news_sm")
            else:
                try:
                    self.nlp_ = spacy.load("en_core_web_sm")
                except OSError:
                    spacy.cli.download("en_core_web_sm")
                    self.nlp_ = spacy.load("en_core_web_sm")

            # Ajout des stopwords personnalisés
            if not hasattr(self.nlp_.Defaults, "stop_words"):
                self.nlp_.Defaults.stop_words = set()
            self.nlp_.Defaults.stop_words.update(self.extra_stopwords)

        return self

    def transform(self, X):
        """
        Applique le prétraitement sur les textes.

        Args:
            X: Series, DataFrame ou array contenant les textes à prétraiter

        Returns:
            array: Liste des textes prétraités
        """
        if self.nlp_ is None:
            raise ValueError("Le modèle n'a pas été initialisé. Appelez fit() d'abord.")

        # Si X est un tableau numpy, on vérifie s'il contient des données numériques
        if isinstance(X, np.ndarray):
            if len(X.shape) == 2 and X.shape[1] > 1:
                # Les données sont déjà encodées
                return X
            X = pd.Series(X)
        elif isinstance(X, pd.DataFrame):
            if len(X.shape) == 2 and X.shape[1] > 1:
                # Les données sont déjà encodées
                return X.values
            X = X.iloc[:, 0]

        # Prétraitement des textes
        preprocessed_texts = X.apply(lambda x: self._lemmatize(self._clean(x)))

        return preprocessed_texts.values

    def get_params(self, deep=True):
        """Obtient les paramètres pour cet estimateur.

        Args:
            deep: Si True, retourne aussi les paramètres des sous-estimateurs

        Returns:
            dict: Dictionnaire des paramètres
        """
        return {
            "extra_stopwords": self.extra_stopwords,
            "language": self.language,
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

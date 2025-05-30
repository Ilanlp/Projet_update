import re
import spacy
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

class TextPreprocessor(BaseEstimator, TransformerMixin):
    """Transformer pour le prétraitement du texte."""
    
    def __init__(self, extra_stopwords=None, language='fr'):
        """
        Initialise le préprocesseur de texte.
        
        Args:
            extra_stopwords: Liste de stopwords supplémentaires
            language: Code de langue pour spaCy ('fr' ou 'en')
        """
        self.extra_stopwords = extra_stopwords or []
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
            
        # Conversion en minuscules
        text = text.lower()
        
        # Suppression des caractères spéciaux et des nombres
        text = re.sub(r'[^a-zA-ZÀ-ÿ\s]', ' ', text)
        
        # Suppression des espaces multiples
        text = re.sub(r'\s+', ' ', text)
        
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
            
        doc = self.nlp_(text)
        
        # Filtrage des stopwords et lemmatisation
        tokens = [token.lemma_ for token in doc if not token.is_stop and len(token.text) > 2]
        
        return ' '.join(tokens)
        
    def fit(self, X, y=None):
        """Charge le modèle spaCy si nécessaire."""
        if self.nlp_ is None:
            # Chargement du modèle spaCy
            if self.language == 'fr':
                try:
                    self.nlp_ = spacy.load('fr_core_news_sm')
                except OSError:
                    spacy.cli.download('fr_core_news_sm')
                    self.nlp_ = spacy.load('fr_core_news_sm')
            else:
                try:
                    self.nlp_ = spacy.load('en_core_web_sm')
                except OSError:
                    spacy.cli.download('en_core_web_sm')
                    self.nlp_ = spacy.load('en_core_web_sm')
                    
            # Ajout des stopwords personnalisés
            self.nlp_.Defaults.stop_words.update(self.extra_stopwords)
        
        return self
        
    def transform(self, X):
        """
        Applique le prétraitement sur les textes.
        
        Args:
            X: Series ou DataFrame contenant les textes à prétraiter
            
        Returns:
            Series: Textes prétraités
        """
        if self.nlp_ is None:
            raise ValueError("Le modèle n'a pas été initialisé. Appelez fit() d'abord.")
            
        if isinstance(X, pd.DataFrame):
            X = X.iloc[:, 0]
            
        return X.apply(lambda x: self._lemmatize(self._clean(x))) 
from sklearn.base import BaseEstimator, TransformerMixin
from sentence_transformers import SentenceTransformer

class BertEncoder(BaseEstimator, TransformerMixin):
    """Transformer pour l'encodage BERT des textes."""
    
    def __init__(self, model_name='paraphrase-multilingual-MiniLM-L12-v2', batch_size=32):
        """Initialise l'encodeur BERT.
        
        Args:
            model_name: Nom du modèle BERT à utiliser
            batch_size: Taille des lots pour l'encodage
        """
        self.model_name = model_name
        self.batch_size = batch_size
        
    def fit(self, X, y=None):
        """Charge le modèle BERT."""
        if not hasattr(self, 'model_'):
            self.model_ = SentenceTransformer(self.model_name)
        return self
        
    def transform(self, X):
        """Encode les textes en vecteurs."""
        return self.model_.encode(
            X.tolist(),
            batch_size=self.batch_size,
            show_progress_bar=True
        ) 
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.neighbors import NearestNeighbors
import numpy as np

class KNNMatcher(BaseEstimator, TransformerMixin):
    """Transformer pour le matching par k plus proches voisins."""
    
    def __init__(self, n_neighbors=5, threshold=0.75):
        """Initialise le matcher KNN.
        
        Args:
            n_neighbors: Nombre de voisins à considérer
            threshold: Seuil de similarité minimum
        """
        self.n_neighbors = n_neighbors
        self.threshold = threshold
        self.knn = None
        self.reference_embeddings = None
        
    def fit(self, X, y=None):
        """
        Entraîne le modèle KNN sur les embeddings de référence.
        
        Args:
            X: Embeddings des documents de référence (offres)
            y: Non utilisé, présent pour la compatibilité avec sklearn
        """
        self.reference_embeddings = X
        self.knn = NearestNeighbors(n_neighbors=self.n_neighbors, metric='cosine')
        self.knn.fit(X)
        return self
        
    def transform(self, X):
        """
        Trouve les n plus proches voisins pour chaque embedding d'entrée.
        
        Args:
            X: Embeddings des documents à matcher
            
        Returns:
            array: Pour chaque document, liste des n plus proches voisins avec leurs distances
        """
        if self.knn is None:
            raise ValueError("Le modèle n'a pas été entraîné. Appelez fit() d'abord.")
            
        distances, indices = self.knn.kneighbors(X)
        
        # Convertir les distances cosinus en similarités
        similarities = 1 - distances
        
        # Créer un tableau de résultats avec indices et similarités
        results = np.zeros((X.shape[0], self.n_neighbors, 2))
        results[:, :, 0] = indices  # indices des matches
        results[:, :, 1] = similarities  # scores de similarité
        
        return results

    def predict(self, X):
        """
        Prédit les meilleurs matches pour chaque embedding d'entrée.
        
        Args:
            X: Embeddings des documents à matcher
            
        Returns:
            array: Pour chaque document, l'indice du meilleur match
        """
        results = self.transform(X)
        # Retourne l'indice du meilleur match pour chaque document
        return results[:, 0, 0].astype(int)

    def predict_proba(self, X):
        """
        Retourne les probabilités (similarités) pour les meilleurs matches.
        
        Args:
            X: Embeddings des documents à matcher
            
        Returns:
            array: Pour chaque document, le score de similarité du meilleur match
        """
        results = self.transform(X)
        return results[:, 0, 1] 
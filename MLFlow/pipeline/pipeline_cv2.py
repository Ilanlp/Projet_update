import pandas as pd
import numpy as np
import re
import unicodedata
import spacy
import logging

# Scikit-learn imports
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
from sklearn.neighbors import NearestNeighbors
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import make_scorer

# MLflow imports
import mlflow
import mlflow.sklearn

# Sentence Transformers
from sentence_transformers import SentenceTransformer

# Logging configuration
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Custom stop words
STOP_PERSO = [
    "faire", "sens", "information", "situation", "environnement", 
    "france", "preuve", "dater", "etude", "ingenieure", 
    "capacite", "interlocuteur", "vue", "heure", "action", 
    "technicienn"
]

class TextPreprocessor:
    """
    Classe de prétraitement du texte avec nettoyage et lemmatisation
    """
    def __init__(self, model_name="fr_core_news_sm", extra_stopwords=None):
        # Charger le modèle spaCy pour le français
        self.nlp = spacy.load(model_name, disable=["parser", "ner"])
        self.extra_stopwords = set(extra_stopwords or [])

    def clean_text(self, text):
        """
        Nettoie le texte : passage en minuscules, suppression des accents
        """
        # Convertir en minuscules
        text = text.lower()
        
        # Normalisation Unicode et suppression des accents
        text = unicodedata.normalize("NFD", text)
        text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
        
        # Suppression des caractères spéciaux
        text = re.sub(r"[^a-z0-9\s]", " ", text).strip()
        
        return text

    def lemmatize_text(self, text):
        """
        Lemmatisation et suppression des stop words
        """
        doc = self.nlp(text)
        lemmas = []
        
        for tok in doc:
            lemma = tok.lemma_.lower().strip(" ,.")
            
            # Correction spécifique pour "dater"
            if lemma == "dater":
                lemma = "data"
            
            # Critères de filtrage des tokens
            if (
                not tok.is_stop
                and not tok.is_punct
                and not tok.like_num
                and len(lemma) > 1
                and lemma not in self.extra_stopwords
            ):
                lemmas.append(lemma)
        
        return " ".join(lemmas)

    def preprocess(self, texts):
        """
        Pipeline complet de prétraitement
        """
        cleaned_texts = [self.clean_text(text) for text in texts]
        lemmatized_texts = [self.lemmatize_text(text) for text in cleaned_texts]
        return lemmatized_texts

class SBertEmbedder:
    """
    Classe pour générer des embeddings avec Sentence-BERT
    """
    def __init__(self, model_name='distilbert-base-nli-stsb-mean-tokens', batch_size=16):
        self.model_name = model_name
        self.batch_size = batch_size
        self.model = SentenceTransformer(model_name)

    def embed_texts(self, texts):
        """
        Génère des embeddings pour une liste de textes
        """
        return self.model.encode(
            texts, 
            show_progress_bar=True, 
            batch_size=self.batch_size
        )

class RecommendationSystem:
    """
    Système de recommandation basé sur k-NN et embeddings SBERT
    """
    def __init__(self, preprocessor, embedder, n_neighbors=5):
        self.preprocessor = preprocessor
        self.embedder = embedder
        self.n_neighbors = n_neighbors
        self.knn = NearestNeighbors(n_neighbors=n_neighbors, metric='cosine')
        self.embeddings = None
        
    def fit(self, texts):
        """
        Prétraitement, génération d'embeddings et ajustement du k-NN
        """
        # Prétraitement
        preprocessed_texts = self.preprocessor.preprocess(texts)
        
        # Génération des embeddings
        self.embeddings = self.embedder.embed_texts(preprocessed_texts)
        
        # Ajustement du k-NN
        self.knn.fit(self.embeddings)
        
        return self
    
    def recommend(self, query_text, top_k=5):
        """
        Trouve les top_k recommandations les plus proches
        """
        # Prétraitement du texte de requête
        preprocessed_query = self.preprocessor.preprocess([query_text])[0]
        
        # Génération de l'embedding
        query_embedding = self.embedder.embed_texts([preprocessed_query])
        
        # Recherche des plus proches voisins
        distances, indices = self.knn.kneighbors(query_embedding)
        
        return list(zip(indices[0], 1 - distances[0]))

def create_matching_pipeline(df):
    """
    Crée le pipeline de matching avec recherche de grille
    """
    # Initialisation des composants
    preprocessor = TextPreprocessor(extra_stopwords=STOP_PERSO)
    
    # Paramètres à tester
    param_grid = {
        'model_name': [
            'distilbert-base-nli-stsb-mean-tokens', 
            'paraphrase-multilingual-MiniLM-L12-v2'
        ],
        'batch_size': [16, 32, 64],
        'n_neighbors': [3, 5, 10]
    }
    
    # Fonction de scoring personnalisée
    def custom_scorer(y_true, y_pred):
        # Exemple simple : moyenne des similarités
        return np.mean(y_pred)
    
    # Préparation des données
    X = df['TEXT'].values
    
    # Séparation train/test
    X_train, X_test = train_test_split(X, test_size=0.2, random_state=42)
    
    # Tracker MLflow
    mlflow.set_experiment("recommendation_system_grid_search")
    
    best_score = -np.inf
    best_config = None
    
    with mlflow.start_run():
        # Grille de recherche manuelle
        for model_name in param_grid['model_name']:
            for batch_size in param_grid['batch_size']:
                for n_neighbors in param_grid['n_neighbors']:
                    logger.info(f"Testing: {model_name}, batch_size={batch_size}, n_neighbors={n_neighbors}")
                    
                    # Initialisation des composants
                    embedder = SBertEmbedder(model_name=model_name, batch_size=batch_size)
                    recommender = RecommendationSystem(
                        preprocessor=preprocessor, 
                        embedder=embedder, 
                        n_neighbors=n_neighbors
                    )
                    
                    # Entraînement
                    recommender.fit(X_train)
                    
                    # Évaluation
                    scores = []
                    for query in X_test:
                        recommendations = recommender.recommend(query)
                        scores.append(np.mean([sim for _, sim in recommendations]))
                    
                    avg_score = np.mean(scores)
                    
                    # Logging MLflow
                    mlflow.log_params({
                        'model_name': model_name,
                        'batch_size': batch_size,
                        'n_neighbors': n_neighbors
                    })
                    mlflow.log_metric('avg_recommendation_score', avg_score)
                    
                    # Mise à jour du meilleur modèle
                    if avg_score > best_score:
                        best_score = avg_score
                        best_config = {
                            'model_name': model_name,
                            'batch_size': batch_size,
                            'n_neighbors': n_neighbors
                        }
        
        # Log du meilleur modèle
        mlflow.log_params(best_config)
        mlflow.log_metric('best_score', best_score)
    
    logger.info(f"Best Configuration: {best_config}")
    logger.info(f"Best Score: {best_score}")
    
    return best_config

def main():
    # Chargement des données
    try:
        df = pd.read_csv(
            "../data/OnBigTable/one_big_table.csv.gz",
            compression="gzip",
            sep=",",
            encoding="utf-8",
            nrows=1000  # Ajustez selon vos besoins
        )
        
        # Colonnes à concaténer
        cols_o = [
            "TITLE", "DESCRIPTION", "TYPE_CONTRAT", "NOM_DOMAINE", 
            "VILLE", "DEPARTEMENT", "REGION", "PAYS", 
            "TYPE_SENIORITE", "NOM_ENTREPRISE", "CATEGORIE_ENTREPRISE", 
            "COMPETENCES", "TYPES_COMPETENCES", "SOFTSKILLS_SUMMARY", 
            "SOFTSKILLS_DETAILS", "NOM_METIER", "CODE_POSTAL"
        ]
        
        # Création de la colonne TEXT
        df["TEXT"] = df[cols_o].fillna("").astype(str).agg(". ".join, axis=1)
        
        # Lancement du pipeline de matching
        best_config = create_matching_pipeline(df)
        
        # Exemple d'utilisation avec la meilleure configuration
        preprocessor = TextPreprocessor(extra_stopwords=STOP_PERSO)
        embedder = SBertEmbedder(
            model_name=best_config['model_name'], 
            batch_size=best_config['batch_size']
        )
        recommender = RecommendationSystem(
            preprocessor=preprocessor, 
            embedder=embedder, 
            n_neighbors=best_config['n_neighbors']
        )
        
        # Entraînement du modèle final
        recommender.fit(df['TEXT'].values)
        
        # Exemple de recommandation
        query = "Développeur Python avec expérience en data science"
        recommendations = recommender.recommend(query)
        
        print("\nRecommandations pour la requête :", query)
        for idx, score in recommendations:
            print(f"Offre {idx} (similarité : {score:.2f}) : {df.iloc[idx]['TEXT'][:200]}...")
    
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution : {e}")

if __name__ == "__main__":
    main()
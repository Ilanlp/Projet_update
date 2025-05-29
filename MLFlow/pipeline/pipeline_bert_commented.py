# Job Matching Pipeline using BERT and Machine Learning
# This script demonstrates a comprehensive NLP pipeline for job matching

# Import necessary libraries
import pandas as pd  # Data manipulation
import re  # Regular expressions for text cleaning
import unicodedata  # Unicode text normalization
import spacy  # Advanced NLP processing
from tqdm.auto import tqdm  # Progress bars for long operations
from sklearn.base import BaseEstimator, TransformerMixin  # Custom transformer creation
from sklearn.pipeline import Pipeline  # Machine learning pipeline
from sklearn.neighbors import NearestNeighbors  # k-Nearest Neighbors algorithm
import numpy as np  # Numerical computing
import mlflow  # Machine learning experiment tracking
import mlflow.sklearn  # MLflow integration with scikit-learn
import mlflow.pyfunc  # MLflow Python function model support
from sentence_transformers import SentenceTransformer  # BERT-based sentence embeddings
from itertools import product  # Cartesian product for grid search

# Custom stopwords to remove from text preprocessing
# These are domain-specific words that might not add significant meaning
stop_perso = [
    "faire", "sens", "information", "situation", "environnement", 
    "france", "preuve", "dater", "etude", "ingenieure", 
    "capacite", "interlocuteur", "vue", "heure", "action", 
    "technicienn",
]

# 1. Data Loading
# Load a sample of job offers and candidate data 
# Using limited rows for demonstration and computational efficiency
df_o = pd.read_csv(
    "../data/OnBigTable/one_big_table.csv.gz",
    compression="gzip",  # Handling compressed file
    sep=",",  # CSV separator
    encoding="utf-8",  # Encoding specification
    nrows=100,  # Limit to 100 rows for quick processing
)
df_c = pd.read_csv(
    "../data/OnBigTable/candidat_data.csv.gz",
    compression="gzip",
    sep=";",
    encoding="utf-8",
    nrows=10,
)

# 2. Text Consolidation
# Combine multiple columns into a single 'TEXT' column for comprehensive matching
cols_o = [
    "TITLE", "DESCRIPTION", "TYPE_CONTRAT", "NOM_DOMAINE", "VILLE", 
    "DEPARTEMENT", "REGION", "PAYS", "TYPE_SENIORITE", "NOM_ENTREPRISE", 
    "CATEGORIE_ENTREPRISE", "COMPETENCES", "TYPES_COMPETENCES", 
    "SOFTSKILLS_SUMMARY", "SOFTSKILLS_DETAILS", "NOM_METIER", "CODE_POSTAL"
]
# Join selected columns into a single text field, separated by periods
df_o["TEXT"] = df_o[cols_o].fillna("").astype(str).agg(". ".join, axis=1)

# Enable progress bars for pandas operations
tqdm.pandas()

# 3. Custom Text Preprocessor
# A scikit-learn compatible transformer for text cleaning and preprocessing
class TextPreprocessor(BaseEstimator, TransformerMixin):
    def __init__(self, model_name="fr_core_news_sm", extra_stopwords=None):
        # Load spaCy French language model
        self.nlp = spacy.load(model_name, disable=["parser", "ner"])
        # Combine default and custom stopwords
        self.extra_stopwords = set(extra_stopwords or [])

    def fit(self, X, y=None):
        # Required method for sklearn transformer, does nothing here
        return self

    def _clean(self, text):
        """
        Clean text by:
        1. Converting to lowercase
        2. Normalizing Unicode characters
        3. Removing non-alphanumeric characters
        """
        text = text.lower()
        text = unicodedata.normalize("NFD", text)
        text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
        return re.sub(r"[^a-z0-9\s]", " ", text).strip()

    def _lemmatize(self, text):
        """
        Lemmatize text by:
        1. Breaking text into tokens
        2. Lemmatizing each token
        3. Filtering out stopwords, punctuation, and short tokens
        """
        doc = self.nlp(text)
        lemmas = []
        for tok in doc:
            lemma = tok.lemma_.lower().strip(" ,.")
            # Special handling for 'dater'
            if lemma == "dater":
                lemma = "data"
            
            # Keep only meaningful tokens
            if (
                not tok.is_stop
                and not tok.is_punct
                and not tok.like_num
                and len(lemma) > 1
                and lemma not in self.extra_stopwords
            ):
                lemmas.append(lemma)
        return " ".join(lemmas)

    def transform(self, X):
        """
        Apply cleaning and lemmatization to input texts
        """
        return X.apply(self._clean).apply(self._lemmatize)

# 4. BERT Sentence Transformer Wrapper
# Converts text into dense vector representations
class SBertTransformer(BaseEstimator, TransformerMixin):
    def __init__(self, model_name, batch_size):
        self.model_name = model_name
        self.batch_size = batch_size

    def fit(self, X, y=None):
        # Load SBERT model
        self.model = SentenceTransformer(self.model_name)
        return self

    def transform(self, X):
        # Convert texts to embeddings
        return self.model.encode(
            X.tolist(), show_progress_bar=True, batch_size=self.batch_size
        )

# 5. k-Nearest Neighbors Matcher
# Finds similar job offers based on embedding similarity
class KNNMatcher(BaseEstimator, TransformerMixin):
    def __init__(self, n_neighbors, metric="cosine"):
        self.n_neighbors = n_neighbors
        self.metric = metric

    def fit(self, X, y=None):
        # Fit k-NN model to embeddings
        self.knn_ = NearestNeighbors(
            n_neighbors=self.n_neighbors, metric=self.metric, algorithm="auto"
        ).fit(X)
        return self

    def transform(self, X):
        # Find nearest neighbors and their distances
        dists, idxs = self.knn_.kneighbors(X)
        return 1 - dists, idxs

# 6. MLflow Python Model Wrapper
# Combines preprocessing, encoding, and matching in a single model
class MatchingModel(mlflow.pyfunc.PythonModel):
    def load_context(self, context):
        # Load saved models from artifacts
        self.preproc = mlflow.sklearn.load_model(context.artifacts["preproc"])
        self.encoder = mlflow.sklearn.load_model(context.artifacts["encoder"])
        self.matcher = mlflow.sklearn.load_model(context.artifacts["knn"])

    def predict(self, context, model_input: pd.DataFrame):
        # Full prediction pipeline:
        # 1. Preprocess text
        # 2. Encode to embeddings
        # 3. Find nearest neighbors
        texts = self.preproc.transform(model_input["TEXT"])
        emb = self.encoder.transform(texts)
        dists, idxs = self.matcher.kneighbors(emb)

        # Format results with similarities and indices
        sims = 1 - dists
        n, k = sims.shape
        out = np.empty((n, k, 2), dtype=object)
        for i in range(n):
            for j in range(k):
                out[i, j, 0] = int(idxs[i, j])
                out[i, j, 1] = float(sims[i, j])
        return out

# 7. Hyperparameter Grid Search
# Systematically explore different model configurations
param_grid = {
    "sbert_model": [
        "distilbert-base-nli-stsb-mean-tokens",
        "paraphrase-multilingual-MiniLM-L12-v2",
    ],
    "batch_size": [16, 32],
    "knn_n": [3, 5, 10],
    "threshold": [0.65, 0.75, 0.85],
}

# Set MLflow experiment name
mlflow.set_experiment("matching_offres_candidats_sbert_grid")

# Iterate through all parameter combinations
for model_name, batch_size, knn_n, thresh in product(
    param_grid["sbert_model"],
    param_grid["batch_size"],
    param_grid["knn_n"],
    param_grid["threshold"],
):
    # Start a new MLflow run for each configuration
    with mlflow.start_run():
        # Log hyperparameters for tracking
        mlflow.log_params({
            "sbert_model": model_name,
            "batch_size": batch_size,
            "knn_n_neighbors": knn_n,
            "threshold": thresh,
            "stopwords_count": len(stop_perso),
        })

        # Text Preprocessing
        tp = TextPreprocessor(extra_stopwords=stop_perso)
        texts = tp.transform(df_o["TEXT"])
        
        # Sentence Embedding
        sbert = SentenceTransformer(model_name)
        emb = sbert.encode(
            texts.tolist(), show_progress_bar=True, batch_size=batch_size
        )

        # k-Nearest Neighbors
        knn = NearestNeighbors(n_neighbors=knn_n, metric="cosine").fit(emb)

        # Log preprocessing model
        mlflow.sklearn.log_model(tp, "preproc")

        # Create and log SBERT transformer
        sbert_transformer = SBertTransformer(model_name, batch_size).fit(
            pd.Series(texts)
        )
        mlflow.sklearn.log_model(sbert_transformer, "encoder")
        mlflow.sklearn.log_model(knn, "knn")

        # Log composite model for deployment
        mlflow.pyfunc.log_model(
            artifact_path="matching_service",
            python_model=MatchingModel(),
            artifacts={
                "preproc": f"runs:/{mlflow.active_run().info.run_id}/preproc",
                "encoder": f"runs:/{mlflow.active_run().info.run_id}/encoder",
                "knn": f"runs:/{mlflow.active_run().info.run_id}/knn",
            },
        )

        # Compute evaluation metrics
        dists, idxs = knn.kneighbors(emb)
        sims = 1 - dists
        
        # Recall: Proportion of relevant items found
        recall1 = (sims[:, 0] >= thresh).mean()
        recall5 = (sims[:, :5] >= thresh).any(axis=1).mean()
        
        # Precision: Proportion of retrieved items that are relevant
        prec5 = (sims[:, :5] >= thresh).sum(axis=1).mean() / 5
        
        # Mean Reciprocal Rank: Average of the reciprocal ranks of the first relevant result
        ranks = np.where(
            sims.max(axis=1) >= thresh, 
            np.argmax(sims >= thresh, axis=1) + 1, 
            np.inf
        ).astype(float)
        mrr = (1 / ranks[ranks < np.inf]).mean()

        # Discounted Cumulative Gain: Measures ranking quality
        def dcg(rel):
            return np.sum((2**rel - 1) / np.log2(np.arange(2, rel.size + 2)))

        rels = (sims[:, :5] >= thresh).astype(int)
        ndcg5 = np.mean(
            [
                dcg(r) / dcg(np.sort(r)[::-1]) if dcg(np.sort(r)[::-1]) > 0 else 0
                for r in rels
            ]
        )

        # Log evaluation metrics
        mlflow.log_metrics({
            "recall_at_1": recall1,
            "recall_at_5": recall5,
            "precision_at_5": prec5,
            "MRR": mrr,
            "nDCG5": ndcg5,
        })

        print(f"Run done: {model_name}, batch={batch_size}, k={knn_n}, thr={thresh}")

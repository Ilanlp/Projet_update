import pandas as pd
import numpy as np
import re
import unicodedata
import spacy
from tqdm.auto import tqdm

# Scikit-learn imports
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
from sklearn.neighbors import NearestNeighbors
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import make_scorer

# MLflow imports
import mlflow
import mlflow.sklearn
import mlflow.pyfunc

# Sentence Transformers
from sentence_transformers import SentenceTransformer

# Scipy for parameter distributions
from scipy.stats import uniform, randint

# Custom stop words
stop_perso = [
    "faire",
    "sens",
    "information",
    "situation",
    "environnement",
    "france",
    "preuve",
    "dater",
    "etude",
    "ingenieure",
    "capacite",
    "interlocuteur",
    "vue",
    "heure",
    "action",
    "technicienn",
]


# Text Preprocessor (previously defined class)
class TextPreprocessor(BaseEstimator, TransformerMixin):
    def __init__(self, model_name="fr_core_news_sm", extra_stopwords=None):
        self.nlp = spacy.load(model_name, disable=["parser", "ner"])
        self.extra_stopwords = set(extra_stopwords or [])

    def fit(self, X, y=None):
        return self

    def _clean(self, text):
        text = text.lower()
        text = unicodedata.normalize("NFD", text)
        text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
        return re.sub(r"[^a-z0-9\s]", " ", text).strip()

    def _lemmatize(self, text):
        doc = self.nlp(text)
        lemmas = []
        for tok in doc:
            lemma = tok.lemma_.lower().strip(" ,.")
            if lemma == "dater":
                lemma = "data"
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
        return X.apply(self._clean).apply(self._lemmatize)


# SBERT Transformer
class SBertTransformer(BaseEstimator, TransformerMixin):
    def __init__(
        self, model_name="distilbert-base-nli-stsb-mean-tokens", batch_size=16
    ):
        self.model_name = model_name
        self.batch_size = batch_size
        self.model = None

    def fit(self, X, y=None):
        self.model = SentenceTransformer(self.model_name)
        return self

    def transform(self, X):
        return self.model.encode(
            X.tolist(), show_progress_bar=True, batch_size=self.batch_size
        )


# KNN Matcher
class KNNMatcher(BaseEstimator, TransformerMixin):
    def __init__(self, n_neighbors=5, metric="cosine"):
        self.n_neighbors = n_neighbors
        self.metric = metric
        self.knn_ = None

    def fit(self, X, y=None):
        self.knn_ = NearestNeighbors(
            n_neighbors=self.n_neighbors, metric=self.metric, algorithm="auto"
        ).fit(X)
        return self

    def transform(self, X):
        dists, idxs = self.knn_.kneighbors(X)
        return 1 - dists, idxs


# Evaluation Metrics Function
def compute_metrics(sims, thresh):
    # Compute various ranking metrics
    recall1 = (sims[:, 0] >= thresh).mean()
    recall5 = (sims[:, :5] >= thresh).any(axis=1).mean()
    prec5 = (sims[:, :5] >= thresh).sum(axis=1).mean() / 5

    ranks = np.where(
        sims.max(axis=1) >= thresh, np.argmax(sims >= thresh, axis=1) + 1, np.inf
    ).astype(float)
    mrr = (1 / ranks[ranks < np.inf]).mean()

    def dcg(rel):
        return np.sum((2**rel - 1) / np.log2(np.arange(2, rel.size + 2)))

    rels = (sims[:, :5] >= thresh).astype(int)
    ndcg5 = np.mean(
        [
            dcg(r) / dcg(np.sort(r)[::-1]) if dcg(np.sort(r)[::-1]) > 0 else 0
            for r in rels
        ]
    )

    return {
        "recall_at_1": recall1,
        "recall_at_5": recall5,
        "precision_at_5": prec5,
        "MRR": mrr,
        "nDCG5": ndcg5,
    }


# Custom Scorer
def custom_scorer(y_true, y_pred):
    # This would need to be adapted to your specific use case
    return np.mean(y_pred)


# Create the full pipeline
def create_matching_pipeline(df_o):
    # Preprocess texts
    tp = TextPreprocessor(extra_stopwords=stop_perso)
    texts = tp.transform(df_o["TEXT"])

    # Create full pipeline
    pipeline = Pipeline(
        [
            ("preprocessor", tp),
            ("sbert", SBertTransformer()),
            ("scaler", StandardScaler()),  # Optional: normalize embeddings
            ("knn", KNNMatcher()),
        ]
    )

    # Parameter grid for GridSearchCV
    param_grid = {
        "sbert__model_name": [
            "distilbert-base-nli-stsb-mean-tokens",
            "paraphrase-multilingual-MiniLM-L12-v2",
        ],
        "sbert__batch_size": [16, 32, 64],
        "knn__n_neighbors": [3, 5, 10],
        "knn__metric": ["cosine", "euclidean"],
    }

    # Parameter distributions for RandomizedSearchCV
    param_distributions = {
        "sbert__model_name": [
            "distilbert-base-nli-stsb-mean-tokens",
            "paraphrase-multilingual-MiniLM-L12-v2",
        ],
        "sbert__batch_size": randint(16, 64),
        "knn__n_neighbors": randint(3, 15),
        "knn__metric": ["cosine", "euclidean"],
    }

    # Custom scorer (you'd need to define this based on your specific metrics)
    scorer = make_scorer(custom_scorer)

    # GridSearchCV
    grid_search = GridSearchCV(
        pipeline,
        param_grid,
        cv=3,  # 3-fold cross-validation
        scoring=scorer,
        n_jobs=-1,  # Use all available cores
    )

    # RandomizedSearchCV
    random_search = RandomizedSearchCV(
        pipeline,
        param_distributions,
        n_iter=20,  # Number of parameter settings sampled
        cv=3,
        scoring=scorer,
        n_jobs=-1,
    )

    return grid_search, random_search


# Main execution function
def main():
    # Load data (sample data loading)
    df_o = pd.read_csv(
        "../data/OnBigTable/one_big_table.csv.gz",
        compression="gzip",
        sep=",",
        encoding="utf-8",
        nrows=100,
    )

    # Concatenate columns into TEXT
    cols_o = [
        "TITLE",
        "DESCRIPTION",
        "TYPE_CONTRAT",
        "NOM_DOMAINE",
        "VILLE",
        "DEPARTEMENT",
        "REGION",
        "PAYS",
        "TYPE_SENIORITE",
        "NOM_ENTREPRISE",
        "CATEGORIE_ENTREPRISE",
        "COMPETENCES",
        "TYPES_COMPETENCES",
        "SOFTSKILLS_SUMMARY",
        "SOFTSKILLS_DETAILS",
        "NOM_METIER",
        "CODE_POSTAL",
    ]
    df_o["TEXT"] = df_o[cols_o].fillna("").astype(str).agg(". ".join, axis=1)

    # Create search objects
    grid_search, random_search = create_matching_pipeline(df_o)

    # MLflow tracking
    mlflow.set_experiment("matching_offres_candidats_grid_random_search")

    with mlflow.start_run():
        # Fit GridSearchCV
        grid_search.fit(df_o[["TEXT"]], None)

        # Log best parameters and score for Grid Search
        mlflow.log_param("grid_best_params", grid_search.best_params_)
        mlflow.log_metric("grid_best_score", grid_search.best_score_)

        # Fit RandomizedSearchCV
        random_search.fit(df_o[["TEXT"]], None)

        # Log best parameters and score for Random Search
        mlflow.log_param("random_best_params", random_search.best_params_)
        mlflow.log_metric("random_best_score", random_search.best_score_)

        # Optional: Save best model
        mlflow.sklearn.log_model(grid_search.best_estimator_, "best_grid_model")

    # Print results
    print("Grid Search Best Parameters:", grid_search.best_params_)
    print("Grid Search Best Score:", grid_search.best_score_)

    print("\nRandom Search Best Parameters:", random_search.best_params_)
    print("Random Search Best Score:", random_search.best_score_)


if __name__ == "__main__":
    main()

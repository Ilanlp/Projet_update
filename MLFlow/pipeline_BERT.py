import pandas as pd
import re
import unicodedata
import spacy
from tqdm.auto import tqdm
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
from sklearn.neighbors import NearestNeighbors
import numpy as np
import mlflow
import mlflow.sklearn
import mlflow.pyfunc
from sentence_transformers import SentenceTransformer
from itertools import product

# === Vos stop-words personnalisés ===
stop_perso = [
    'faire','sens','information','situation','environnement','france',
    'preuve','dater','etude','ingenieure','capacite','interlocuteur',
    'vue','heure','action','technicienn'
]

# === 1. Charger un échantillon limité ===
df_o = pd.read_csv(
    'data/OnBigTable/one_big_table.csv.gz',
    compression='gzip', sep=',', encoding='utf-8', nrows=100
)
df_c = pd.read_csv(
    'data/OnBigTable/candidat_data.csv.gz',
    compression='gzip', sep=';', encoding='utf-8', nrows=10
)

# === 2. Concaténation des colonnes d’offres en TEXT ===
cols_o = [
    'TITLE','DESCRIPTION','TYPE_CONTRAT','NOM_DOMAINE','VILLE','DEPARTEMENT',
    'REGION','PAYS','TYPE_SENIORITE','NOM_ENTREPRISE','CATEGORIE_ENTREPRISE',
    'COMPETENCES','TYPES_COMPETENCES','SOFTSKILLS_SUMMARY','SOFTSKILLS_DETAILS',
    'NOM_METIER','CODE_POSTAL'
]
df_o['TEXT'] = df_o[cols_o].fillna('').astype(str).agg('. '.join, axis=1)

# === 3. Activer tqdm pour pandas ===
tqdm.pandas()

# === 4. Preprocessor FR (clean + lemmatisation + stop-words) ===
class TextPreprocessor(BaseEstimator, TransformerMixin):
    def __init__(self, model_name='fr_core_news_sm', extra_stopwords=None):
        self.nlp = spacy.load(model_name, disable=['parser','ner'])
        self.extra_stopwords = set(extra_stopwords or [])
    def fit(self, X, y=None): return self
    def _clean(self, text):
        text = text.lower()
        text = unicodedata.normalize('NFD', text)
        text = ''.join(ch for ch in text if unicodedata.category(ch) != 'Mn')
        return re.sub(r'[^a-z0-9\s]', ' ', text).strip()
    def _lemmatize(self, text):
        doc = self.nlp(text)
        lemmas = []
        for tok in doc:
            lemma = tok.lemma_.lower().strip(' ,.')
            if lemma == "dater":
                lemma = "data"
            if (not tok.is_stop 
                and not tok.is_punct 
                and not tok.like_num 
                and len(lemma) > 1 
                and lemma not in self.extra_stopwords):
                lemmas.append(lemma)
        return ' '.join(lemmas)
    def transform(self, X):
        return X.apply(self._clean).apply(self._lemmatize)

# === 5. Wrapper SBERT pour sklearn ===
class SBertTransformer(BaseEstimator, TransformerMixin):
    def __init__(self, model_name, batch_size):
        self.model_name = model_name
        self.batch_size = batch_size
    def fit(self, X, y=None):
        self.model = SentenceTransformer(self.model_name)
        return self
    def transform(self, X):
        return self.model.encode(
            X.tolist(),
            show_progress_bar=True,
            batch_size=self.batch_size
        )

# === 6. Wrapper k-NN pour sklearn ===
class KNNMatcher(BaseEstimator, TransformerMixin):
    def __init__(self, n_neighbors, metric='cosine'):
        self.n_neighbors = n_neighbors
        self.metric = metric
    def fit(self, X, y=None):
        self.knn_ = NearestNeighbors(
            n_neighbors=self.n_neighbors,
            metric=self.metric,
            algorithm='auto'
        ).fit(X)
        return self
    def transform(self, X):
        dists, idxs = self.knn_.kneighbors(X)
        return 1 - dists, idxs

# === 7. Wrapper pyfunc composite inline ===
class MatchingModel(mlflow.pyfunc.PythonModel):
    def load_context(self, context):
        self.preproc = mlflow.sklearn.load_model(context.artifacts["preproc"])
        self.encoder = mlflow.sklearn.load_model(context.artifacts["encoder"])
        self.matcher = mlflow.sklearn.load_model(context.artifacts["knn"])
    def predict(self, context, model_input: pd.DataFrame):
        # text preprocessing
        texts = self.preproc.transform(model_input["TEXT"])
        # SBERT encoding
        emb = self.encoder.transform(texts)
        # k-NN query
        dists, idxs = self.matcher.kneighbors(emb)

        sims = 1 - dists
        # format (n_queries, k, 2)
        n, k = sims.shape
        out = np.empty((n, k, 2), dtype=object)
        for i in range(n):
            for j in range(k):
                out[i,j,0] = int(idxs[i,j])
                out[i,j,1] = float(sims[i,j])
        return out

# === 8. Grid search & runs MLflow ===
param_grid = {
    "sbert_model": [
        "distilbert-base-nli-stsb-mean-tokens",
        "paraphrase-multilingual-MiniLM-L12-v2"
    ],
    "batch_size": [16, 32],
    "knn_n": [3, 5, 10],
    "threshold": [0.65, 0.75, 0.85]
}
mlflow.set_experiment("matching_offres_candidats_sbert_grid")

for model_name, batch_size, knn_n, thresh in product(
        param_grid["sbert_model"],
        param_grid["batch_size"],
        param_grid["knn_n"],
        param_grid["threshold"]
    ):
    with mlflow.start_run():
        # log params
        mlflow.log_params({
            "sbert_model":     model_name,
            "batch_size":      batch_size,
            "knn_n_neighbors": knn_n,
            "threshold":       thresh,
            "stopwords_count": len(stop_perso)
        })

        # 1) préproc + SBERT encode offres
        tp = TextPreprocessor(extra_stopwords=stop_perso)
        texts = tp.transform(df_o['TEXT'])
        sbert = SentenceTransformer(model_name)
        emb = sbert.encode(texts.tolist(), show_progress_bar=True, batch_size=batch_size)

        # 2) fit k-NN
        knn = NearestNeighbors(n_neighbors=knn_n, metric="cosine").fit(emb)

        # 3) log sklearn artifacts
        mlflow.sklearn.log_model(tp,   "preproc")
        # 1) Crée ton transformer sklearn, puis fit pour instancier .model
        sbert_transformer = SBertTransformer(model_name, batch_size).fit(
        pd.Series(texts)  # c.à.d. une Series de tes textes lemmas
        )

        # 2) Log cet objet, pas le SentenceTransformer brut
        mlflow.sklearn.log_model(sbert_transformer, "encoder")
        mlflow.sklearn.log_model(knn,  "knn")

        # 4) log composite pyfunc
        mlflow.pyfunc.log_model(
            artifact_path="matching_service",
            python_model=MatchingModel(),
            artifacts={
                "preproc": f"runs:/{mlflow.active_run().info.run_id}/preproc",
                "encoder": f"runs:/{mlflow.active_run().info.run_id}/encoder",
                "knn":     f"runs:/{mlflow.active_run().info.run_id}/knn"
            }
        )

        # 5) calcul metrics
        dists, idxs = knn.kneighbors(emb)
        sims = 1 - dists
        recall1 = (sims[:,0] >= thresh).mean()
        recall5 = (sims[:,:5] >= thresh).any(axis=1).mean()
        prec5   = (sims[:,:5] >= thresh).sum(axis=1).mean() / 5
        ranks   = np.where(sims.max(axis=1)>=thresh,
                           np.argmax(sims>=thresh,axis=1)+1,
                           np.inf).astype(float)
        mrr     = (1 / ranks[ranks < np.inf]).mean()
        def dcg(rel): return np.sum((2**rel - 1)/np.log2(np.arange(2,rel.size+2)))
        rels    = (sims[:,:5]>=thresh).astype(int)
        ndcg5   = np.mean([dcg(r)/dcg(np.sort(r)[::-1]) if dcg(np.sort(r)[::-1])>0 else 0 for r in rels])

        mlflow.log_metrics({
            "recall_at_1":   recall1,
            "recall_at_5":   recall5,
            "precision_at_5":prec5,
            "MRR":           mrr,
            "nDCG5":         ndcg5
        })

        print(f"Run done: {model_name}, batch={batch_size}, k={knn_n}, thr={thresh}")

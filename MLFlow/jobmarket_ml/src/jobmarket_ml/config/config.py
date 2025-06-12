import os
from pathlib import Path

# Chemin de base du projet
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent

# Chemins des données avec chemins absolus
DATA_DIR = os.path.join(BASE_DIR, "data", "OnBigTable")
OFFERS_PATH = os.path.join(DATA_DIR, "one_big_table.csv.gz")
CANDIDATES_PATH = os.path.join(DATA_DIR, "text_candidat_data.csv.gz")

# Vérification de l'existence des fichiers
if not os.path.exists(OFFERS_PATH):
    raise FileNotFoundError(f"Le fichier des offres n'existe pas: {OFFERS_PATH}")
if not os.path.exists(CANDIDATES_PATH):
    raise FileNotFoundError(f"Le fichier des candidats n'existe pas: {CANDIDATES_PATH}")

# Configuration des colonnes
OFFER_COLUMNS = [
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

CANDIDATE_COLUMNS = ["TEXT"]

# Stopwords personnalisés
CUSTOM_STOPWORDS = [
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

# Configuration du scoring
SCORING_CONFIG = {
    "similarity_threshold": 0.7,  # Seuil pour considérer un match comme pertinent
    "weights": {
        "mean_similarity": 0.4,  # Poids pour la similarité moyenne
        "diversity": 0.3,  # Poids pour la diversité des matchs
        "coverage": 0.2,  # Poids pour la couverture
        "computation_time": 0.1,  # Poids pour la performance
    },
}

# Paramètres pour GridSearchCV
PARAM_GRID = {
    "encoder__model_name": [
        "distilbert-base-nli-stsb-mean-tokens",
        "paraphrase-multilingual-MiniLM-L12-v2",
    ],
    "encoder__batch_size": [16, 32],
    "matcher__n_neighbors": [3, 5, 10],
    "matcher__threshold": [0.65, 0.75, 0.85],
}

# Configuration MLflow
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow-tracking:5000")
MLFLOW_EXPERIMENT_NAME = os.getenv("MLFLOW_EXPERIMENT_NAME", "jobmarket_grid_search")
MLFLOW_MODEL_URI = os.getenv("MLFLOW_MODEL_URI")
MLFLOW_RUN_ID = os.getenv("MLFLOW_RUN_ID")
MLFLOW_MODEL_NAME = os.getenv("MLFLOW_MODEL_NAME", "jobmarket")
MLFLOW_MODEL_VERSION = os.getenv("MLFLOW_MODEL_VERSION", 1)
MLFLOW_MODEL_STAGE = os.getenv("MLFLOW_MODEL_STAGE", "Development")
MLFLOW_MODEL_PORT = os.getenv("MLFLOW_MODEL_PORT", 5001)

# Configuration du pipeline
PIPELINE_CONFIG = {
    "max_length": 512,  # Longueur maximale des séquences pour BERT
    "device": (
        "cuda" if os.getenv("USE_GPU", "0") == "1" else "cpu"
    ),  # Utilisation GPU/CPU
    "batch_size": 32,  # Taille de batch par défaut
    "num_workers": 4,  # Nombre de workers pour le chargement des données
    "random_state": 42,  # Seed pour la reproductibilité
}

# Configuration des logs
LOG_CONFIG = {
    "level": os.getenv("LOG_LEVEL", "INFO"),
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "date_format": "%Y-%m-%d %H:%M:%S",
}
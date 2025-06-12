#!/bin/bash

# Couleurs pour une meilleure lisibilité
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color
BLUE='\033[0;34m'

# Fonction d'aide
show_help() {
  echo -e "${BLUE}JobMarket Infrastructure Management Script${NC}"
  echo
  echo "Usage: $0 [command] [profile] [options]"
  echo
  echo "Commands:"
  echo "  init            - Initialise le projet complet (ETL, MLflow, Airflow)"
  echo "  init-db         - Initialise uniquement l'ETL Snowflake et DBT"
  echo "  init-extract    - Exécute uniquement l'extraction des données"
  echo "  init-load       - Exécute uniquement le chargement des données"
  echo "  init-transform  - Exécute uniquement la transformation des données"
  echo "  init-ml         - Initialise l'environnement MLflow"
  echo "  init-tracking   - Initialise uniquement le tracking MLflow"
  echo "  init-train      - Initialise et entraîne le modèle"
  echo "  train           - Lance un container pour l'entraînement interactif"
  echo "  init-air        - Initialise l'environnement Airflow"
  echo "  start [profile] - Démarre les services avec le profil spécifié"
  echo "  stop            - Arrête tous les services"
  echo "  status          - Affiche le statut de tous les services"
  echo "  logs [service]  - Affiche les logs d'un service spécifique ou de tous les services"
  echo "  clean           - Nettoie les containers et volumes"
  echo
  echo "Available profiles:"
  echo "  frontend         - Frontend dashboard uniquement"
  echo "  training         - Environnement d'entraînement MLflow"
  echo "  development      - Entraînement + Déploiement du modèle"
  echo "  production       - Environnement de production"
  echo "  monitoring       - Inclut les services de monitoring"
  echo "  airflow          - Services Airflow"
  echo
  echo "Examples:"
  echo "  $0 init                     - Initialise le projet complet"
  echo "  $0 init-ml                  - Initialise uniquement MLflow"
  echo "  $0 start development        - Démarre l'environnement de développement"
  echo "  $0 logs backend             - Affiche les logs du backend"
  echo "  $0 status                   - Affiche le statut de tous les services"
  echo
  echo "Commande train - Exemples d'utilisation:"
  echo "  $0 train                    - Lance un shell interactif pour l'entraînement"
  echo "  Fonctionnalités disponibles dans le container d'entraînement:"
  echo "    - Prétraitement de texte avec TextPreprocessor"
  echo "    - Encodage BERT multilingue (paraphrase-multilingual-MiniLM-L12-v2)"
  echo "    - Matching KNN avec seuil de similarité configurable"
  echo "    - Tracking MLflow avec métriques:"
  echo "      * Score de similarité"
  echo "      * Similarité moyenne"
  echo "      * Score de diversité"
  echo "      * Score de couverture"
  echo "      * Temps d'exécution"
  echo "    - Enregistrement automatique du modèle dans MLflow"
  echo
  # echo "  Exemples d'utilisation dans le container:"
  # echo "    python train_model.py                     - Entraînement avec paramètres par défaut"
  # echo "    python -m pytest tests/                   - Exécution des tests unitaires"
  # echo "    python train_model.py --quick-test        - Test rapide avec petit échantillon"
  # echo "    python train_model.py --batch-size 32     - Modifie la taille du batch"
  # echo "    python train_model.py --threshold 0.85    - Ajuste le seuil de similarité"
  # echo "    python train_model.py --n-neighbors 5     - Change le nombre de voisins KNN"
}

# Fonction pour vérifier si Docker est en cours d'exécution
check_docker() {
  if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running${NC}"
    exit 1
  fi
}

init_extract_data() {
  echo -e "${BLUE}Extraction des données...${NC}"
  echo -e "${YELLOW}Étape 0: Vérification des fichiers de configuration...${NC}"

  if [ ! -f "pipeline/src/.env" ]; then
    echo -e "${RED}Erreur: Fichier de configuration pipeline ETL manquant${NC}"
    exit 1
  fi

  echo -e "${YELLOW}Étape 1: Démarrage du service ETL Normalizer...${NC}"
  echo -e "${BLUE}Extraction des données...${NC}"
  docker compose --profile init-db up jm-etl-normalizer
}

init_load_data() {
  echo -e "${BLUE}Chargement des données...${NC}"
  echo -e "${YELLOW}Étape 0: Vérification des fichiers de configuration...${NC}"

  if [ ! -f "pipeline/src/.env" ]; then
    echo -e "${RED}Erreur: Fichier de configuration pipeline ETL manquant${NC}"
    exit 1
  fi

  echo -e "${YELLOW}Étape 1: Démarrage du service ETL Snowflake...${NC}"
  echo -e "${BLUE}Chargement des données...${NC}"
  docker compose --profile init-db up jm-elt-snowflake
}

init_transform_data() {
  echo -e "${BLUE}Transformation des données...${NC}"
  echo -e "${YELLOW}Étape 0: Vérification des fichiers de configuration...${NC}"

  if [ ! -f "snowflake/DBT/.env" ]; then
    echo -e "${RED}Erreur: Fichier de configuration pipeline ELT manquant${NC}"
    exit 1
  fi

  echo -e "${YELLOW}Étape 1: Démarrage du service DBT...${NC}"
  echo -e "${BLUE}Transformation des données...${NC}"
  docker compose --profile init-db up jm-elt-dbt
}

# Initialisation base de données et ETL / ELT (Snowflake, DBT, Normalizer : Datalake, Datawarehouse, Dataflow)
init_db() {
  echo -e "${BLUE}Initialisation ETL / ELT...${NC}"

  init_extract_data
  init_load_data
  init_transform_data

  echo -e "${GREEN}Initialisation terminée avec succès!${NC}"
}

init_tracking_mlflow() {
  echo -e "${BLUE}Démarrage du tracking MLflow...${NC}"

  echo -e "${YELLOW}Étape 1: Vérification du fichier de configuration MLFlow...${NC}"
  if [ ! -f "MLFlow/.env" ]; then
    echo -e "${RED}Erreur: Fichier de configuration MLFlow manquant${NC}"
    exit 1
  fi

  echo -e "${YELLOW}Étape 2: Vérification et création de mlflow.db si nécessaire${NC}"
  if [ ! -f "MLFlow/mlflow.db" ]; then
    touch MLFlow/mlflow.db
    echo -e "${GREEN}Fichier mlflow.db créé avec succès${NC}"
  fi

  echo -e "${YELLOW}Étape 3: Démarrage du service MLflow Tracking${NC}"
  docker compose --profile init-ml up -d mlflow-tracking

  if [ $? -ne 0 ]; then
    echo -e "${RED}Erreur lors de l'initialisation de MLflow Tracking${NC}"
    exit 1
  fi

  echo -e "${GREEN}Tracking MLflow démarré avec succès!${NC}"
}

init_train_model() {
  echo -e "${BLUE}Entrainement et enregistrement du modèle...${NC}"

  echo -e "${YELLOW}Étape 1: Vérification du fichier de configuration MLFlow...${NC}"
  if [ ! -f "MLFlow/.env" ]; then
    echo -e "${RED}Erreur: Fichier de configuration MLFlow manquant${NC}"
    exit 1
  fi

  echo -e "${YELLOW}Étape 2: Vérification et création de mlflow.db si nécessaire${NC}"
  if [ ! -f "MLFlow/mlflow.db" ]; then
    touch MLFlow/mlflow.db
    echo -e "${GREEN}Fichier mlflow.db créé avec succès${NC}"
  fi

  echo -e "${YELLOW}Étape 4: Entrainement et enregistrement du modèle...${NC}"
  docker compose --profile init-ml up -d mlflow-training
  sleep 10
  train_output=$(docker compose --profile init-ml run --rm \
    mlflow-training quick_train)

  # train_output=$(docker compose --profile init-ml run --rm \
  #     -v "$(pwd)"/MLFlow/scripts/ml_entrypoint.sh:/app/scripts/ml_entrypoint.sh \
  #     mlflow-training quick_train)

  if [ $? -ne 0 ]; then
    echo -e "${RED}Erreur lors de l'entrainement du modèle${NC}"
    exit 1
  fi

  run_id=$(echo "$train_output" | grep "Run MLflow ID:" | sed 's/.*Run MLflow ID: \(.*\)/\1/')

  docker compose --profile init-ml run --rm \
    mlflow-training register "$run_id" jobmarket

  # docker compose --profile init-ml run --rm \
  #   -v "$(pwd)"/MLFlow/scripts/ml_entrypoint.sh:/app/scripts/ml_entrypoint.sh \
  #   mlflow-training register "$run_id" jobmarket

  if [ $? -ne 0 ]; then
    echo -e "${RED}Erreur lors de l'enregistrement du modèle${NC}"
    exit 1
  fi

  echo -e "${YELLOW}Étape 5: Update du fichier de configuration MLFlow Model${NC}"

  # Détection du système d'exploitation pour la commande sed
  if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s#MLFLOW_RUN_ID=.*#MLFLOW_RUN_ID=$run_id#" MLFlow/.env
    sed -i '' "s#MLFLOW_MODEL_URI=.*#MLFLOW_MODEL_URI=runs:$run_id/jobmarket#" MLFlow/.env
    sed -i '' "s#MLFLOW_MODEL_NAME=.*#MLFLOW_MODEL_NAME=jobmarket#" MLFlow/.env
    sed -i '' "s#MLFLOW_MODEL_VERSION=.*#MLFLOW_MODEL_VERSION=1#" MLFlow/.env
    sed -i '' "s#MLFLOW_MODEL_STAGE=.*#MLFLOW_MODEL_STAGE=Development#" MLFlow/.env
  else
    # Linux
    sed -i "s#MLFLOW_RUN_ID=.*#MLFLOW_RUN_ID=$run_id#" MLFlow/.env
    sed -i "s#MLFLOW_MODEL_URI=.*#MLFLOW_MODEL_URI=runs:$run_id/jobmarket#" MLFlow/.env
    sed -i "s#MLFLOW_MODEL_NAME=.*#MLFLOW_MODEL_NAME=jobmarket#" MLFlow/.env
    sed -i "s#MLFLOW_MODEL_VERSION=.*#MLFLOW_MODEL_VERSION=1#" MLFlow/.env
    sed -i "s#MLFLOW_MODEL_STAGE=.*#MLFLOW_MODEL_STAGE=Development#" MLFlow/.env
  fi

  echo -e "${GREEN}Entrainement et enregistrement du modèle terminé avec succès!${NC}"
}

train_model() {
  echo -e "${BLUE}Entrainement de modèle...${NC}"

  echo -e "${YELLOW}Étape 1: Vérification du fichier de configuration MLFlow...${NC}"
  if [ ! -f "MLFlow/.env" ]; then
    echo -e "${RED}Erreur: Fichier de configuration MLFlow manquant${NC}"
    exit 1
  fi

  echo -e "${YELLOW}Étape 2: Vérification et création de mlflow.db si nécessaire${NC}"
  if [ ! -f "MLFlow/mlflow.db" ]; then
    touch MLFlow/mlflow.db
    echo -e "${GREEN}Fichier mlflow.db créé avec succès${NC}"
  fi

  echo -e "${YELLOW}Étape 3: Lancement du container pour l'entrainement du modèle...${NC}"
  docker compose --profile init-ml run --rm \
    mlflow-training bash

  # train_output=$(docker compose --profile init-ml run --rm \
  #     -v "$(pwd)"/MLFlow/scripts/ml_entrypoint.sh:/app/scripts/ml_entrypoint.sh \
  #     mlflow-training quick_train)

  if [ $? -ne 0 ]; then
    echo -e "${RED}Erreur lors du lancement du container pour l'entrainement du modèle${NC}"
    exit 1
  fi
}

init_mlflow() {
  echo -e "${BLUE}Initialisation de MLflow...${NC}"

  init_tracking_mlflow
  init_train_model

  echo -e "${GREEN}MLflow initialisé avec succès!${NC}"
}

init_airflow() {
  echo -e "${BLUE}Initialisation d'Airflow...${NC}"
  LOCAL_UID=$(id -u)
  LOCAL_GID=$(id -g)

  echo -e "${YELLOW}UID: $LOCAL_UID${NC}"
  echo -e "${YELLOW}GID: $LOCAL_GID${NC}"

  # export LOCAL_UID=$LOCAL_UID
  # export LOCAL_GID=$LOCAL_GID

  echo -e "${YELLOW}Étape 1: Création des répertoires Airflow...${NC}"
  mkdir -p airflow/{dags,logs,plugins,config}
  if [ ! -f "airflow/.env" ]; then
    echo "AIRFLOW_UID=$(id -u)" >airflow/.env
    echo "AIRFLOW_GID=0" >>airflow/.env
    echo "_AIRFLOW_WWW_USER_USERNAME=airflow" >>airflow/.env
    echo "_AIRFLOW_WWW_USER_PASSWORD=airflow" >>airflow/.env
  fi

  echo -e "${YELLOW}Étape 2: Initialisation d'Airflow...${NC}"
  docker compose --profile airflow up airflow-init
  if [ $? -ne 0 ]; then
    echo -e "${RED}Erreur lors de l'initialisation d'Airflow${NC}"
    exit 1
  fi
}

# Fonction pour démarrer les services
start_services() {
  local profile=$1
  echo "Starting services with profile: $profile"

  # if [ "$profile" = "airflow" ]; then
  #   echo "Starting Airflow services..."
  #   echo "Initializing Airflow database..."
  #   docker compose --profile airflow run airflow-webserver airflow db migrate
  #   echo "Creating Airflow admin user airflow/airflow..."
  #   docker compose --profile airflow run airflow-webserver airflow users create \
  #     --username airflow \
  #     --firstname Admin \
  #     --lastname User \
  #     --role Admin \
  #     --email admin@example.com \
  #     --password airflow || true
  #   echo "Starting PostgreSQL and Redis..."
  #   docker compose --profile airflow up -d postgres-airflow redis-airflow
  #   sleep 10 # Attendre que PostgreSQL et Redis soient prêts
  #   echo "Starting Airflow webserver and scheduler..."
  #   docker compose --profile airflow up -d airflow-webserver airflow-scheduler
  #   sleep 5 # Attendre que le webserver et le scheduler soient prêts
  #   echo "Starting Airflow worker..."
  #   docker compose --profile airflow up -d airflow-worker
  #   echo "Services started successfully"
  # else
  # Pour les autres profils, démarrer normalement
  docker compose --profile $profile up -d
  # fi
}

# Fonction pour arrêter les services
stop_services() {
  echo -e "${YELLOW}Stopping all services...${NC}"
  docker compose down
  echo -e "${GREEN}All services stopped${NC}"
}

# Fonction pour afficher les logs
show_logs() {
  local service=$1
  if [ -z "$service" ]; then
    docker compose logs --tail=100 -f
  else
    docker compose logs --tail=100 -f $service
  fi
}

# Fonction pour afficher le statut
show_status() {
  echo -e "${BLUE}Current services status:${NC}"
  docker compose ps
}

# Fonction pour nettoyer
clean_environment() {
  echo -e "${YELLOW}Cleaning up environment...${NC}"
  docker compose --profile init-db down -v --remove-orphans
  docker compose --profile init-ml down -v --remove-orphans
  docker compose --profile development down
  docker compose --profile airflow down -v --remove-orphans
  # docker compose --profile airflow down -v --rmi all
  docker compose --profile production down
  # docker compose --profile monitoring down -v --remove-orphans
  echo -e "${GREEN}Environment cleaned${NC}"
}

# Vérification de Docker
check_docker

# Traitement des commandes
case "$1" in
init)
  init_db
  init_mlflow
  init_airflow
  ;;
init-db)
  init_db
  ;;
init-extract)
  init_extract_data
  ;;
init-load)
  init_load_data
  ;;
init-transform)
  init_transform_data
  ;;
init-ml)
  init_mlflow
  ;;
init-tracking)
  init_tracking_mlflow
  ;;
init-train)
  init_train_model
  ;;
train)
  train_model
  ;;
init-air)
  init_airflow
  ;;
start)
  start_services "$2"
  ;;
stop)
  stop_services
  ;;
logs)
  show_logs "$2"
  ;;
status)
  show_status
  ;;
clean)
  clean_environment
  ;;
help | --help | -h)
  show_help
  ;;
*)
  echo -e "${RED}Invalid command${NC}"
  show_help
  exit 1
  ;;
esac

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
  echo "  init             - Initialise le projet (ETL Snowflake et DBT)"
  echo "  start [profile]  - Start services with specified profile"
  echo "  stop            - Stop all services"
  echo "  status          - Show status of all services"
  echo "  logs [service]  - Show logs of specific service or all services"
  echo "  clean          - Clean up containers and volumes"
  echo
  echo "Available profiles:"
  echo "  frontend         - Frontend dashboard only"
  echo "  training         - MLflow training environment"
  echo "  development      - Training + Model serving"
  echo "  production       - Production environment"
  echo "  monitoring       - Include monitoring services"
  echo "  airflow          - Airflow services"
  echo
  echo "Options:"
  echo "  --init           - Initialize ETL process (with init command only)"
  echo
  echo "Examples:"
  echo "  $0 init                     - Initialize project with ETL"
  echo "  $0 start development        - Start development environment"
  echo "  $0 logs backend             - Show backend logs"
  echo "  $0 status                   - Show status of all services"
}

# Fonction pour vérifier si Docker est en cours d'exécution
check_docker() {
  if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running${NC}"
    exit 1
  fi
}

# Fonction pour initialiser le projet
init_project() {
  echo -e "${BLUE}Initialisation du projet JobMarket...${NC}"

  export LOCAL_UID=$(id -u)
  export LOCAL_GID=$(id -g)

  echo -e "${YELLOW}UID: $LOCAL_UID${NC}"
  echo -e "${YELLOW}GID: $LOCAL_GID${NC}"

  # Vérification des fichiers de configuration
  echo -e "${YELLOW}Étape 0: Vérification des fichiers de configuration...${NC}"

  if [ ! -f "pipeline/src/.env" ]; then
    echo -e "${RED}Erreur: Fichier de configuration pipeline ETL manquant${NC}"
    exit 1
  fi

  if [ ! -f "snowflake/DBT/.env" ]; then
    echo -e "${RED}Erreur: Fichier de configuration pipeline ELT manquant${NC}"
    exit 1
  fi

  if [ ! -f "MLFlow/.env" ]; then
    echo -e "${RED}Erreur: Fichier de configuration MLFlow manquant${NC}"
    exit 1
  fi

  # Création des répertoires Airflow si nécessaire
  echo -e "${YELLOW}Étape 0.1: Création des répertoires Airflow...${NC}"
  mkdir -p airflow/{dags,logs,plugins,config}
  if [ ! -f "airflow/.env" ]; then
    echo "AIRFLOW_UID=$(id -u)" > airflow/.env
    echo "AIRFLOW_GID=$(id -g)" >> airflow/.env
    echo "_AIRFLOW_WWW_USER_USERNAME=airflow" >> airflow/.env
    echo "_AIRFLOW_WWW_USER_PASSWORD=airflow" >> airflow/.env
  fi

  echo -e "${YELLOW}Étape 0: Démarrage du service ETL Normalizer...${NC}"
  docker compose --profile init-db up jm-etl-normalizer

  if [ $? -ne 0 ]; then
    echo -e "${RED}Erreur lors de l'initialisation de ETL Normalizer${NC}"
    exit 1
  fi

  echo -e "${YELLOW}Étape 1: Démarrage du service ETL Snowflake...${NC}"
  docker compose --profile init-db up --build jm-elt-snowflake

  if [ $? -ne 0 ]; then
    echo -e "${RED}Erreur lors de l'initialisation de Snowflake ETL${NC}"
    exit 1
  fi

  echo -e "${YELLOW}Étape 2: Démarrage du service DBT...${NC}"
  docker compose --profile init-db up jm-elt-dbt

  if [ $? -ne 0 ]; then
    echo -e "${RED}Erreur lors de l'initialisation de DBT${NC}"
    exit 1
  fi
  
  echo -e "${YELLOW}Étape 3: Vérification et création de mlflow.db si nécessaire${NC}"
  if [ ! -f "MLFlow/mlflow.db" ]; then
    touch MLFlow/mlflow.db
    echo -e "${GREEN}Fichier mlflow.db créé avec succès${NC}"
  fi

  echo -e "${YELLOW}Étape 4: Démarrage du service MLflow Tracking${NC}"
  docker compose --profile init-ml up -d mlflow-tracking

  if [ $? -ne 0 ]; then
    echo -e "${RED}Erreur lors de l'initialisation de MLflow Tracking${NC}"
    exit 1
  fi

  echo -e "${YELLOW}Étape 5: Entrainement et enregistrement du modèle...${NC}"
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

  echo -e "${YELLOW}Étape 6: Update du fichier de configuration MLFlow Model${NC}"

  # Détection du système d'exploitation pour la commande sed
  if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s/RUN_ID=.*/RUN_ID=$run_id/" MLFlow/.env
    sed -i '' "s/RUN_ID=.*/RUN_ID=$run_id/" MLFlow/.env.example
    sed -i '' "s/MODEL_NAME=.*/MODEL_NAME=jobmarket/" MLFlow/.env
    sed -i '' "s/MODEL_NAME=.*/MODEL_NAME=jobmarket/" MLFlow/.env.example
    sed -i '' "s/MODEL_STAGE=.*/MODEL_STAGE=Development/" MLFlow/.env
    sed -i '' "s/MODEL_STAGE=.*/MODEL_STAGE=Development/" MLFlow/.env.example
  else
    # Linux
    sed -i "s/RUN_ID=.*/RUN_ID=$run_id/" MLFlow/.env
    sed -i "s/RUN_ID=.*/RUN_ID=$run_id/" MLFlow/.env.example
    sed -i "s/MODEL_NAME=.*/MODEL_NAME=jobmarket/" MLFlow/.env
    sed -i "s/MODEL_NAME=.*/MODEL_NAME=jobmarket/" MLFlow/.env.example
    sed -i "s/MODEL_STAGE=.*/MODEL_STAGE=Development/" MLFlow/.env
    sed -i "s/MODEL_STAGE=.*/MODEL_STAGE=Development/" MLFlow/.env.example
  fi

  if [ $? -ne 0 ]; then
    echo -e "${RED}Erreur lors de la configuration de MLflow Model${NC}"
    exit 1
  fi

  echo -e "${YELLOW}Étape 5: Initialisation d'Airflow...${NC}"
  docker compose --profile airflow up airflow-init
  if [ $? -ne 0 ]; then
    echo -e "${RED}Erreur lors de l'initialisation d'Airflow${NC}"
    exit 1
  fi

  echo -e "${GREEN}Initialisation terminée avec succès!${NC}"
}

# Fonction pour démarrer les services
start_services() {
  local profile=$1
  echo "Starting services with profile: $profile"

  if [ "$profile" = "airflow" ]; then
    echo "Starting Airflow services..."
    echo "Initializing Airflow database..."
    docker compose --profile airflow run airflow-webserver airflow db migrate
    echo "Creating Airflow admin user airflow/airflow..."
    docker compose --profile airflow run airflow-webserver airflow users create \
      --username airflow \
      --firstname Admin \
      --lastname User \
      --role Admin \
      --email admin@example.com \
      --password airflow || true
    echo "Starting PostgreSQL and Redis..."
    docker compose --profile airflow up -d postgres-airflow redis-airflow
    sleep 10 # Attendre que PostgreSQL et Redis soient prêts
    echo "Starting Airflow webserver and scheduler..."
    docker compose --profile airflow up -d airflow-webserver airflow-scheduler
    sleep 5 # Attendre que le webserver et le scheduler soient prêts
    echo "Starting Airflow worker..."
    docker compose --profile airflow up -d airflow-worker
    echo "Services started successfully"
  else
    # Pour les autres profils, démarrer normalement
    docker compose --profile $profile up -d
  fi
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
  docker compose --profile airflow down -v --remove-orphans
  docker compose --profile development down -v --remove-orphans
  docker compose --profile production down -v --remove-orphans
  # docker compose --profile monitoring down -v --remove-orphans
  echo -e "${GREEN}Environment cleaned${NC}"
}

# Vérification de Docker
check_docker

# Traitement des commandes
case "$1" in
init)
  init_project
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

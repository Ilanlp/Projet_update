# JOBMARKET

## Execution ELT

### Lancer d'abord le service jm-elt-snowflake

```bash
docker-compose -f docker-compose.etl.init.yaml up --build jm-elt-snowflake
```

### Lancer ensuite le service jm-elt-dbt

```bash
docker-compose -f docker-compose.elt.init.yaml up --build jm-elt-dbt
```

## MLFlow infrastructure

<!--
# ===========================================
# CONFIGURATION DES PROFILS
# ===========================================

# Profils disponibles :
# - training     : Service d'entraînement ML
# - development  : Training
# - monitoring   : Prometheus pour monitoring
# - postgres     : Base PostgreSQL au lieu de SQLite
# - cache        : Redis pour cache

# Exemples d'utilisation :
# docker-compose --profile development up                    # Training + Model
# docker-compose --profile training up                       # Entraînement seulement
# docker-compose --profile training --profile monitoring up  # Training + Monitoring
# docker-compose --profile postgres up mlflow-server         # MLflow avec PostgreSQL
-->

### Development

```bash
docker compose -f docker-compose.mlflow.yaml --profile development up -d --build
docker compose -f docker-compose.mlflow.yaml --profile development down -v
```

### Training model

```bash
# Démarage du conteneur en mode interactif
docker compose run --rm mlflow-training bash

# Workflow d'entrainement rapide
docker compose -f docker-compose.mlflow.yaml run --rm mlflow-training --build train --register
```

### Liste experience

```bash
python3 src/list_runs.py
```

### Register model

```bash
# python3 src/register_model.py $RUN_ID $MODEL_NAME
docker compose run --rm mlflow-training python3 src/register_model.py 2a36b41a11734595b155d8d42927d75d jobmarket
```

### Serve model

```bash
# python3 src/register_model.py $RUN_ID $MODEL_NAME
export RUN_ID=2a36b41a11734595b155d8d42927d75d
docker compose run --rm mlflow-model python3 src/register_model.py $RUN_ID $MODEL_NAME
```

### Request Model

```bash
python3 src/request_model.py tracking_uri model_uri models:/jobmarket/latest
```

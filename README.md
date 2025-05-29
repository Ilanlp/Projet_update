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
docker compose -f docker-compose_workspace.yaml --profile development up -d --build
docker compose -f docker-compose_workspace.yaml --profile development down -v
```

### Training model

```bash
# Démarage du conteneur en mode interactif
docker compose -f docker-compose_workspace.yaml run --rm mlflow-training --build bash
```

### Register model

```bash
python3 src/register_model.py \
            --tracking_uri "http://127.0.0.1:5010" \
            --experiment_name "Apple_Models" \
            --model_name "apple_demand_predictor"
            # --tags
            # --run_id
```

```bash
python3 src/register_model.py \
            --tracking_uri "http://127.0.0.1:5010" \
            --experiment_name "Apple_Models" \
            --model_name "apple_demand_predictor" \
            --tags "version=1.0,environment=production,author=data_team"
            # --run_id
```

### Serve model

```bash
python3 src/serve_registry_model.py \
    --tracking_uri "http://127.0.0.1:5010" \
    --model_name "apple_demand_predictor" \
    --version 3 \
    --port 5020
```

```bash
docker run -p 5020:5001 \
  -e TRACKING_URI="http://mlflow-tracking:5000" \
  -e MODEL_NAME="apple_demand_predictor" \
  -e MODEL_VERSION="3" \
  -e MODEL_PORT="5001" \
  jm-serve-model
```

```bash
docker compose -f docker-compose_workspace.yaml run --rm mlflow-training python src/register_model.py 7b46206452614e5a93e98d556fe2bd37 apple_demand_predictor
```

## Request Model

```bash
python3 src/predict.py
```

```bash
curl -X POST "http://localhost:8000/invocations" \
  -H "Content-Type: application/json" \
  -d '{
    "dataframe_records": [
      {
        "year": 2022,
        "month": 1,
        "day_of_year": 1,
        "day_of_week": 5,
        "week_of_year": 52,
        "quarter": 1,
        "temperature": 17.65,
        "humidity": 35.38,
        "rainfall": 1.10,
        "sunshine_hours": 7.35,
        "apple_price": 2.23,
        "economic_index": 100.17,
        "is_weekend": 1,
        "trend": 0.0,
        "season_fall": false,
        "season_spring": false,
        "season_summer": false,
        "season_winter": true,
        "holiday_back_to_school": false,
        "holiday_normal": false,
        "holiday_summer_holidays": false,
        "holiday_winter_holidays": true
      }
    ]
  }'
```

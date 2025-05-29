#!/bin/bash

# URL de l'endpoint
ENDPOINT="http://localhost:8000/invocations"

# Données de test (un seul exemple pour simplifier)
DATA='{
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

# Afficher la commande
echo "🚀 Sending request to: $ENDPOINT"
echo "📝 Data:"
echo "$DATA" | jq '.'

# Exécuter la requête curl
echo -e "\n📤 Sending request..."
curl -X POST "$ENDPOINT" \
  -H "Content-Type: application/json" \
  -d "$DATA" |
  jq '.'

# Note: le pipe vers jq permet de formater joliment la réponse JSON

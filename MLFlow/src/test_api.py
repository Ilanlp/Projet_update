import requests
import pandas as pd
import json

# Préparer les données
data = pd.read_csv("data/fake_data.csv")
X = data.drop(columns=["date", "demand"])
X = X.astype('float')

# Convertir les données en format JSON
json_data = {
    "dataframe_split": {
        "columns": X.columns.tolist(),
        "data": X.head(2).values.tolist()  # On teste avec 2 lignes
    }
}

# Envoyer la requête à l'API
response = requests.post(
    url="http://localhost:5002/invocations",
    json=json_data,
    headers={"Content-Type": "application/json"}
)

# Afficher les prédictions
if response.status_code == 200:
    predictions = response.json()
    print("\nPrédictions reçues :")
    print(predictions)
else:
    print(f"Erreur : {response.status_code}")
    print(response.text)
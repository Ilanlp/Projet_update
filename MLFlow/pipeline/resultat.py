import pandas as pd
import requests
import json

# 1) Charger les offres
df_o = pd.read_csv(
    'data/OnBigTable/one_big_table.csv.gz',
    compression='gzip', sep=',', encoding='utf-8'
)

# 2) Préparer et envoyer la requête
payload = {
    "dataframe_records": [
        {"TEXT": "Dev ops paris"}
    ]
}
resp = requests.post(
    "http://127.0.0.1:1234/invocations",
    headers={"Content-Type": "application/json"},
    data=json.dumps(payload)
)

print("STATUT HTTP:", resp.status_code)
if resp.status_code != 200:
    print("Erreur :", resp.json())
    exit(1)

# 3) Récupérer la structure renvoyée
# MLflow renvoie : {"predictions": [ [ [idx, score], ... ] ]}
resp_json = resp.json()
pred_lists = resp_json.get("predictions", [])

if not pred_lists:
    print("Aucune prédiction retournée.")
    exit(1)

# Comme on a une seule requête, on prend le premier élément
preds = pred_lists[0]  # liste de [idx, score]

# 4) Construire les résultats (description complète)
results = []
for idx, score in preds:
    row = df_o.iloc[int(idx)]
    results.append({
        "title":       row["TITLE"],
        "company":     row["NOM_ENTREPRISE"],
        "location":    f"{row['VILLE']} ({int(row['CODE_POSTAL'])})",
        "description": row["DESCRIPTION"],   # description complète
        "score":       round(float(score), 3)
    })

# 5) Afficher
for r in results:
    print(f"{r['title']} @ {r['company']} — {r['location']} — score {r['score']}")
    print(f"{r['description']}\n")

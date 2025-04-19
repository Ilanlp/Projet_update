import requests
import json

# Étape 1 : Charger le token depuis un fichier texte
def load_token(token_file):
    with open(token_file, "r") as file:
        return file.read().strip()

# Étape 2 : Récupérer toutes les données d'un dataset avec pagination
def fetch_all_data(api_url, token, application_id):
    headers = {
        "Authorization": f"Bearer {token}",
        "Application-ID": application_id
    }
    all_data = []
    size = 1000  # Taille maximale par requête définie par l'API
    from_index = 0  # Index initial pour la pagination

    while True:
        # Ajouter les paramètres de pagination à l'URL
        paginated_url = f"{api_url}?size={size}&from={from_index}"
        response = requests.get(paginated_url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            all_data.extend(results)  # Ajouter les résultats à la liste totale

            print(f"Page récupérée : {from_index // size + 1}, Nombre de résultats : {len(results)}")
            
            # Vérifier si tous les résultats ont été récupérés
            if len(results) < size:  # Si le nombre de résultats est inférieur à "size", on a tout récupéré
                break

            # Passer à la page suivante
            from_index += size
        else:
            print(f"Erreur lors de la récupération des données depuis {paginated_url} : {response.status_code}")
            print(response.text)
            break

    return all_data

# Étape 3 : Enregistrer les données dans un fichier JSON avec le nom du dataset
def save_data(data, dataset_name):
    file_name = f"{dataset_name.replace(' ', '_')}.json"  # Remplacement des espaces par des underscores
    with open(file_name, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
    print(f"Données sauvegardées dans '{file_name}'")

# Configurations
token_file = "token_onisep_24h.txt"
application_id = "67f8998435746621218b4567"
datasets = {
    "5fa5949243f97": ("https://api.opendata.onisep.fr/api/1.0/dataset/5fa5949243f97/search", "Onisep_Idéo_Métiers_Onisep"),
    "605344579a7d7": ("https://api.opendata.onisep.fr/api/1.0/dataset/605344579a7d7/search", "Onisep_Idéo_Actions_de_Formation_Initiale"),
    "6152ccdf850ef": ("https://api.opendata.onisep.fr/api/1.0/dataset/6152ccdf850ef/search", "Onisep_Table_de_Passage_Codes_Certifications"),
    "57a292918b": ("https://api.opendata.onisep.fr/api/1.0/dataset/5fa57a292918b/search", "Onisep_Idéo_Organismes_Info_Orientation"),
    "5fa58d750a60c": ("https://api.opendata.onisep.fr/api/1.0/dataset/5fa58d750a60c/search", "Onisep_Idéo_Nomenclature_Domaines_Sous_Domaines")
}

# Charger le token
token = load_token(token_file)

# Récupérer et enregistrer les données pour chaque dataset
for dataset_id, (dataset_url, dataset_name) in datasets.items():
    all_data = fetch_all_data(dataset_url, token, application_id)
    save_data(all_data, dataset_name)
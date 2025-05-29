# Matching Model Deployment & Testing

Ce projet déploie un modèle de matching offres‑candidats basé sur **SBERT + k‑NN**, entièrement géré via **MLflow**.

---

## Table des matières

- [Matching Model Deployment \& Testing](#matching-model-deployment--testing)
  - [Table des matières](#table-des-matières)
  - [1. Prérequis \& Installation](#1-prérequis--installation)
  - [2. Entraînement \& Log (pipeline\_BERT)](#2-entraînement--log-pipeline_bert)
  - [3. Publication en production](#3-publication-en-production)
  - [4. Servir le modèle REST](#4-servir-le-modèle-rest)
  - [5. Tester l'API](#5-tester-lapi)
  - [6. Personnalisation \& Hyperparamètres](#6-personnalisation--hyperparamètres)
  - [7. Explorer l’UI MLflow](#7-explorer-lui-mlflow)

---

## 1. Prérequis & Installation

1. Activer l'environnement Python :

   ```bash
   cd MLFlow
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Vérifier la présence des données :

   * `data/OnBigTable/one_big_table.csv.gz`
   * `data/OnBigTable/candidat_data.csv.gz`

---

## 2. Entraînement & Log (pipeline\_BERT)

Le script `pipeline_BERT.py` :

* Charge un échantillon de la table **offres** (`df_o`) et **candidats** (`df_c`).
* Concatène plusieurs colonnes en champ unique `TEXT`.
* Prétraite le texte (*cleaning*, lemmatisation, stopwords) via la liste `stop_perso`.
* Génère des embeddings SBERT et entraîne un k‑NN.
* Logge sur MLflow :

  * `preproc` (préprocesseur)
  * `encoder` (SBERT transformer)
  * `knn` (modèle k‑NN)
  * `matching_service` (service composite PyFunc)

Lancer :

```bash
python3 pipeline_BERT.py
```

Les runs s’affichent dans l’UI MLflow (`http://localhost:5000`).

---

## 3. Publication en production

Le script `MLFlow_Experiment_TO_production.py` permet de :

1. Récupérer le `run_id` du run MLflow à publier.
2. Créer (ou récupérer) l’enregistrement nommé `model_name`.
3. Enregistrer la version `runs:/{run_id}/matching_service`.
4. Promouvoir cette version en **Production** (archive les autres).

Adapter les variables `run_id` et `model_name` en début de fichier, puis :

```bash
python3 MLFlow_Experiment_TO_production.py
```

---

## 4. Servir le modèle REST

Démarrer le serveur REST MLflow :

```bash
mlflow models serve \
  -m "models:/<model_name>/Production" \
  --no-conda \
  -p 1234
```

* Remplacer `<model_name>` par celui utilisé en production (ex. `BERT_SW_8`).
* L’API écoute sur le port **1234**.

---

## 5. Tester l'API

Le script `resultat.py` :

1. Charge la table offres complète.
2. Envoie une requête POST à l’API :

   ```json
   { "dataframe_records": [{"TEXT":"Votre requête ici"}] }
   ```
3. Récupère la réponse JSON `predictions` : liste de `[indice_offre, score]`.
4. Affiche pour chaque offre : titre, entreprise, localisation, description, score.

Lancer :

```bash
python3 resultat.py
```

---

## 6. Personnalisation & Hyperparamètres

* **Stop‑words** : modifier la liste `stop_perso` dans `pipeline_BERT.py` ou le script de recherche.
* **Hyperparamètres** : ajuster `param_grid` (Grid Search) ou `param_dist` (RandomizedSearchCV).
* **Recherche d’hyperparamètres** :

  * **Grid Search** via boucles `product(...)`.
  * **RandomizedSearchCV** pour un échantillonnage rapide.

---

## 7. Explorer l’UI MLflow

1. Lancer :

   ```bash
   mlflow ui
   ```

2. Se rendre sur `http://localhost:5000` pour voir :

   * Les **Expériences** et leurs runs.
   * Les **Modèles** enregistrés et leurs **versions**.
   * Les métriques et artefacts associés.

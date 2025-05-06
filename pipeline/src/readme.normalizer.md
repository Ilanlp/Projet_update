# Normalisateur de Données d'Emploi

Ce projet permet de collecter, normaliser et analyser des données d'offres d'emploi provenant de deux sources principales : Adzuna et France Travail (ex Pôle Emploi). Il fournit des outils pour effectuer des recherches ponctuelles ou des collectes de données historiques sur de longues périodes.

## Fonctionnalités

- **Collecte de données récentes** depuis Adzuna et France Travail
- **Normalisation** des données vers un format commun
- **Collecte historique exhaustive** sur plusieurs mois
- **Analyse automatique** des données collectées
- **Points de contrôle** permettant de reprendre une collecte interrompue
- **Gestion d'erreurs robuste** avec backoff exponentiel
- **Exportation CSV et JSON** des données et analyses

## Installation

### Prérequis

- Python 3.8 ou supérieur
- Accès aux API Adzuna et France Travail (clés d'API)

### Installation des dépendances

```bash
pip install -r requirements.txt
```

### Configuration

Créez un fichier `.env` à la racine du projet avec les informations d'authentification suivantes :

```env
ADZUNA_APP_ID=votre_app_id_adzuna
ADZUNA_APP_KEY=votre_app_key_adzuna
FRANCE_TRAVAIL_ID=votre_id_france_travail
FRANCE_TRAVAIL_KEY=votre_key_france_travail
OUTPUT_DIR=./data/
```

## Utilisation via ligne de commande

Le script principal `job_market_normalizer.py` offre une interface en ligne de commande complète avec de nombreuses options.

### Mode standard (collecte récente)

Ce mode récupère les offres d'emploi récentes des deux sources, les normalise et les analyse.

```bash
python job_market_normalizer.py --search-terms "python développeur" --max-results 100
```

#### Options du mode standard

- `--output-dir` : Répertoire de sortie pour les fichiers générés (défaut: "./data/")
- `--search-terms` : Termes de recherche pour les offres d'emploi (défaut: "python data ingénieur")
- `--max-results` : Nombre maximum de résultats par source (défaut: 50)
- `--location-adzuna` : Localisation pour Adzuna (ville, région) (défaut: "Paris")
- `--location-france-travail` : Localisation pour France Travail (code département) (défaut: "75")

### Mode historique (collecte exhaustive)

Ce mode permet de collecter des données sur une longue période (plusieurs mois) en utilisant des stratégies optimisées pour maximiser la couverture.

```bash
python job_market_normalizer.py --historical --historical-months 6
```

#### Options du mode historique

- `--historical` : Active le mode de collecte historique
- `--historical-source` : Source(s) pour la collecte historique (choix: "adzuna", "france_travail", "all"; défaut: "all")
- `--historical-months` : Nombre de mois à remonter dans le temps (défaut: 12)

## Exemples d'utilisation

### Collecte récente avec critères spécifiques

```bash
python job_market_normalizer.py \
  --search-terms "data scientist" \
  --max-results 200 \
  --location-adzuna "Lyon" \
  --location-france-travail "69"
```

### Collecte historique d'Adzuna uniquement

```bash
python job_market_normalizer.py \
  --historical \
  --historical-source adzuna \
  --historical-months 3
```

### Collecte historique de France Travail avec termes spécifiques

```bash
python job_market_normalizer.py \
  --historical \
  --historical-source france_travail \
  --search-terms "développeur full stack" \
  --historical-months 6
```

### Collecte historique complète

```bash
python job_market_normalizer.py \
  --historical \
  --historical-source all \
  --historical-months 12 \
  --output-dir "./donnees_historiques/"
```

## Structure des fichiers générés

### Fichiers CSV

Le script génère différents fichiers CSV selon le mode d'exécution :

- **Mode standard** :
  - `all_jobs_YYYYMMDD.csv` : Toutes les offres normalisées
  - `adzuna_jobs_YYYYMMDD.csv` : Offres Adzuna normalisées
  - `france_travail_jobs_YYYYMMDD.csv` : Offres France Travail normalisées

- **Mode historique** :
  - `adzuna_historical_YYYYMMDD.csv` : Données historiques Adzuna
  - `france_travail_historical_YYYYMMDD.csv` : Données historiques France Travail

### Fichiers d'analyse

- `analysis_YYYYMMDD.json` : Statistiques et analyses des offres collectées

### Fichiers de point de contrôle

- `*.csv.checkpoint` : Fichiers de point de contrôle pour reprendre une collecte interrompue

## Points de contrôle

Pour les collectes historiques qui peuvent prendre beaucoup de temps, le système génère automatiquement des points de contrôle. Si la collecte est interrompue (par une panne, une erreur réseau, etc.), vous pouvez simplement relancer la même commande et la collecte reprendra là où elle s'était arrêtée.

## Stratégies de collecte historique

### Adzuna

- Collecte organisée par catégories d'emploi
- Découpage en périodes temporelles d'un mois
- Pagination avec limite de 100 pages maximum par période

### France Travail

- Collecte organisée par départements et domaines d'activité
- Découpage en périodes temporelles d'un mois
- Pagination avec limite de 1000 résultats maximum par requête

## Limitations connues

1. **Limites des API** : Les API peuvent imposer des limites de taux ou de volume qui ralentissent la collecte
2. **Couverture temporelle** : Les données historiques peuvent être incomplètes pour les offres très anciennes
3. **Doublons possibles** : Certaines offres peuvent apparaître avec des identifiants différents selon les sources
4. **Volumétrie** : Les collectes historiques complètes peuvent générer des fichiers très volumineux (plusieurs Go)

## Résolution des problèmes courants

### Erreurs d'API

- **Problème** : "Error 429 Too Many Requests"
  - **Solution** : Augmentez la valeur de `rate_limit_delay` dans le code ou attendez quelques heures avant de relancer

- **Problème** : "Error 403 Forbidden"
  - **Solution** : Vérifiez vos clés d'API dans le fichier `.env`

### Interruptions de collecte

- **Problème** : Collecte interrompue par un plantage ou Ctrl+C
  - **Solution** : Relancez simplement la même commande, la collecte reprendra au point de contrôle

### Fichiers volumineux

- **Problème** : Fichiers CSV trop volumineux pour être ouverts
  - **Solution** : Utilisez des outils comme `pandas` pour charger et filtrer les données par portions

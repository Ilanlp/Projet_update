# AdzunaHistoricalCollector

Collecteur de données historiques pour les offres d'emploi Adzuna.

## Description

AdzunaHistoricalCollector est un outil Python conçu pour collecter des offres d'emploi depuis l'API Adzuna sur une longue période temporelle (plusieurs mois). Il utilise une approche par catégories et périodes temporelles pour maximiser la couverture des données et gérer efficacement les limitations de l'API.

## Fonctionnalités

- Collection d'offres d'emploi par catégorie (ex: IT, finance, etc.)
- Découpage temporel automatique pour maximiser la couverture
- Gestion des limitations de l'API Adzuna
- Mécanisme de reprise après interruption via points de contrôle
- Normalisation des données collectées
- Gestion des erreurs et retries automatiques
- Export des données au format CSV compatible avec le modèle `NormalizedJobOffer`

## Prérequis

- Python 3.10+
- Librairies: httpx, asyncio, dotenv, pydantic

## Installation

1. Clonez le dépôt:
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Installez les dépendances:
   ```bash
   pip install -r requirements.txt
   ```

3. Créez un fichier `.env` à la racine du projet avec les variables d'environnement suivantes:
   ```
   ADZUNA_APP_ID=votre_app_id
   ADZUNA_APP_KEY=votre_app_key
   FRANCE_TRAVAIL_ID=votre_id
   FRANCE_TRAVAIL_KEY=votre_key
   DEFAULT_CODE_ROME_ADZUNA=it-jobs
   ```

## Utilisation

### En ligne de commande

```bash
python jm_a_collector.py --output data/adzuna_jobs.csv --months 6 --category it-jobs --country fr
```

### Options disponibles

| Option | Description | Valeur par défaut |
|--------|-------------|-------------------|
| `--output` | Chemin du fichier CSV de sortie | `data/adzuna_jobs_<date>.csv` |
| `--months` | Nombre de mois à remonter dans le passé | 12 |
| `--country` | Code pays pour la recherche (fr, uk, etc.) | fr |
| `--category` | Catégorie d'emploi à rechercher | it-jobs |
| `--results-per-page` | Nombre de résultats par page (max 50) | 50 |
| `--checkpoint-interval` | Intervalle de sauvegarde de l'état (nombre d'offres) | 100 |
| `--rate-limit-delay` | Délai entre les requêtes API en secondes | 0.5 |

### Exemple d'utilisation programmatique

```python
import asyncio
from adzuna import AdzunaClient, CountryCode
from jm_a_collector import AdzunaHistoricalCollector

async def collect_data():
    # Créer un client Adzuna
    adzuna_client = AdzunaClient(
        app_id="VOTRE_APP_ID",
        app_key="VOTRE_APP_KEY"
    )
    
    # Initialiser le collecteur
    collector = AdzunaHistoricalCollector(
        adzuna_client=adzuna_client,
        country=CountryCode.FR,
        category="it-jobs",
        results_per_page=50,
        retry_count=3,
        retry_delay=5,
        rate_limit_delay=0.5,
        checkpoint_interval=100
    )
    
    # Lancer la collecte
    output_file = await collector.collect_data(
        output_file="data/adzuna_jobs.csv",
        max_months=6
    )
    
    print(f"Collecte terminée! Données enregistrées dans {output_file}")

if __name__ == "__main__":
    asyncio.run(collect_data())
```

## Structure des données collectées

Les données collectées sont normalisées via la classe `JobDataNormalizer` et suivent le modèle `NormalizedJobOffer`. Le fichier CSV de sortie contient exactement les champs définis dans ce modèle.

## Mécanisme de points de contrôle

Le collecteur sauvegarde régulièrement son état dans un fichier de checkpoint (par défaut toutes les 100 offres). En cas d'interruption du processus, il pourra reprendre là où il s'était arrêté lors du prochain lancement.

## Gestion des erreurs

Le collecteur intègre un mécanisme de retry avec backoff exponentiel en cas d'erreur API:
- Nombre de tentatives configurable
- Délai croissant entre les tentatives
- Gestion des limites de taux d'utilisation de l'API

## Limites connues

- Le collecteur est limité à 100 pages de résultats par requête (limitation de l'API Adzuna)
- Les résultats sont limités à une profondeur historique maximale d'un an
- Seule la France est pleinement supportée actuellement, bien que le code soit préparé pour d'autres pays

## Licence

[Inclure la licence du projet]
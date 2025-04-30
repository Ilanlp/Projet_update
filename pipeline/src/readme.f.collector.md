# Collecteur de Données Historiques France Travail

Ce projet permet de collecter des offres d'emploi depuis l'API France Travail (anciennement Pôle Emploi) sur une longue période temporelle, en utilisant une approche systématique par départements et périodes pour maximiser la couverture des données.

## Fonctionnalités

- Collecte d'offres d'emploi sur plusieurs mois en arrière (jusqu'à 12 mois par défaut)
- Recherche systématique par départements et codes ROME
- Normalisation des données vers un format standardisé
- Gestion des limites de l'API (pagination, taux de requêtes)
- Points de contrôle réguliers pour reprendre une collecte interrompue
- Optimisation pour maximiser la couverture des données

## Prérequis

- Python 3.8 ou supérieur
- Clés d'API pour France Travail et Adzuna (utilisées par le normalisateur)

## Installation

1. Cloner le dépôt :
```bash
git clone <url-du-depot>
cd <nom-du-depot>
```

2. Installer les dépendances :
```bash
pip install -r requirements.txt
```

3. Créer un fichier `.env` à la racine du projet avec les clés API :
```
FRANCE_TRAVAIL_ID=votre_id_api
FRANCE_TRAVAIL_KEY=votre_cle_api
ADZUNA_APP_ID=votre_id_adzuna
ADZUNA_APP_KEY=votre_cle_adzuna
```

## Utilisation

### Ligne de commande

Le collecteur peut être exécuté directement depuis la ligne de commande :

```bash
python jm_f_collector.py --output data/jobs.csv --months 6 --search "data engineer"
```

### Options disponibles

| Option | Description | Valeur par défaut |
|--------|-------------|-------------------|
| `--output` | Chemin du fichier CSV de sortie | `data/france_travail_jobs_YYYYMMDD.csv` |
| `--months` | Nombre de mois à remonter dans le passé | 12 |
| `--search` | Termes de recherche optionnels | None |
| `--results-per-page` | Nombre de résultats par page (max 150) | 150 |
| `--checkpoint-interval` | Intervalle de sauvegarde de l'état | 100 |
| `--rate-limit-delay` | Délai entre les requêtes API (secondes) | 1.0 |

### Exemple d'utilisation programmatique

```python
import asyncio
from dotenv import load_dotenv
from os import environ
from france_travail import FranceTravailAPI
from jm_f_collector import FranceTravailHistoricalCollector

async def run_collector():
    # Charger les variables d'environnement
    load_dotenv()
    
    # Créer le client API
    france_travail_api = FranceTravailAPI(
        client_id=environ.get("FRANCE_TRAVAIL_ID"),
        client_secret=environ.get("FRANCE_TRAVAIL_KEY")
    )
    
    # Initialiser le collecteur
    collector = FranceTravailHistoricalCollector(
        france_travail_api=france_travail_api,
        results_per_page=150,
        rate_limit_delay=1.0
    )
    
    # Lancer la collecte
    output_file = await collector.collect_data(
        output_file="data/output.csv",
        max_months=6,
        search_terms="data scientist"
    )
    
    print(f"Collecte terminée! Fichier généré: {output_file}")

if __name__ == "__main__":
    asyncio.run(run_collector())
```

## Structure des données

Le collecteur génère un fichier CSV contenant les offres d'emploi normalisées. Les champs sont définis par la classe `NormalizedJobOffer` du module `jm_normalizer`. 

## Paramètres de recherche

### Départements

Le collecteur effectue une recherche exhaustive sur tous les départements français, y compris les DOM-TOM.

### Codes ROME ciblés

Le collecteur cible par défaut les codes ROME suivants :
- M1811 : Gestion de systèmes informatisés de production
- M1827 : Administration de systèmes d'information 
- M1851 : Big data
- K1906 : Intelligence artificielle
- M1405 : Développement informatique

Ces codes correspondent aux classifications métiers du numérique et de l'informatique.

## Points de contrôle

Pour les collectes volumineuses, le système maintient automatiquement des points de contrôle qui permettent de reprendre une collecte interrompue. Ces points de contrôle sont enregistrés dans un fichier `.checkpoint` à côté du fichier CSV de sortie.

## Limites et bonnes pratiques

- L'API France Travail impose des limites de taux de requêtes. Le paramètre `rate_limit_delay` permet d'ajuster le délai entre les requêtes.
- La pagination est limitée à environ 1000 résultats par recherche. Le collecteur contourne cette limitation en divisant la recherche par départements et périodes.
- Pour les collectes volumineuses, augmenter l'intervalle des points de contrôle peut améliorer les performances.

## Dépendances

- `france_travail` : Module client pour l'API France Travail
- `jm_normalizer` : Module de normalisation des offres d'emploi
- `dotenv` : Gestion des variables d'environnement
- `asyncio` : Gestion asynchrone des requêtes

# Script d'Ingestion pour JobMarket

Ce script automatise le processus d'ingestion des données d'offres d'emploi pour le projet JobMarket. Il enchaîne les étapes de normalisation (collecte depuis les API) et de chargement dans Snowflake.

## Fonctionnalités

- Exécution du normalisateur (`jm_normalizer.py`) pour collecter les nouvelles offres d'emploi
- Chargement des données dans Snowflake (`snowflakeCSVLoader.py`) 
- Journalisation détaillée de toutes les étapes
- Mode test pour vérifier la configuration sans exécuter l'ingestion complète

## Prérequis

- Python 3.6 ou supérieur
- Accès au projet JobMarket
- Variables d'environnement Snowflake configurées

## Structure de dossiers

Le script attend la structure de dossiers suivante :

```
/home/ubuntu/JobMarket_Projet/mar25_bootcamp_de_job_market/
├── .env                  # Fichier contenant les variables d'environnement
├── pipeline/             # Dossier contenant les scripts de normalisation
│   └── jm_normalizer.py  # Script de normalisation des données
├── snowflake/            # Dossier contenant les scripts Snowflake
│   └── snowflakeCSVLoader.py  # Script de chargement dans Snowflake
├── output/               # Dossier pour les fichiers CSV générés
└── logs/                 # Dossier pour les fichiers journaux (créé automatiquement)
```

## Configuration

### Variables d'environnement

Créez un fichier `.env` à la racine du projet (`/home/ubuntu/JobMarket_Projet/mar25_bootcamp_de_job_market/.env`) avec les variables suivantes :

```
# Identifiants Snowflake
SNOWFLAKE_USER=votre_utilisateur
SNOWFLAKE_PASSWORD=votre_mot_de_passe
SNOWFLAKE_ACCOUNT=votre_compte
SNOWFLAKE_WAREHOUSE=votre_entrepot
SNOWFLAKE_DATABASE=votre_base
SNOWFLAKE_SCHEMA=votre_schema

# Paramètres de recherche (optionnels)
SEARCH_TERMS=data
CATEGORY_ADZUNA=it-jobs
CODE_ROME=M1805
```

## Utilisation

### Exécution manuelle

Pour exécuter le script manuellement :

```bash
python3 /home/ubuntu/JobMarket_Projet/mar25_bootcamp_de_job_market/ingestion_autov4.py
```

### Mode Test

Pour vérifier la configuration sans exécuter l'ingestion :

```bash
python3 /home/ubuntu/JobMarket_Projet/mar25_bootcamp_de_job_market/ingestion_autov4.py --test
```

Ce mode teste :
- L'existence des scripts requis
- La configuration des variables d'environnement

### Configuration Cron

Pour automatiser l'exécution quotidienne à 2h du matin :

1. Ouvrez l'éditeur crontab :
   ```bash
   crontab -e
   ```

2. Ajoutez la ligne suivante :
   ```
   0 2 * * * /usr/bin/python3 /home/ubuntu/JobMarket_Projet/mar25_bootcamp_de_job_market/scripts/job_market_ingestion.py >> /home/ubuntu/JobMarket_Projet/mar25_bootcamp_de_job_market/logs/cron_execution.log 2>&1
   ```

## Journalisation

Les journaux sont écrits dans :
- `/home/ubuntu/JobMarket_Projet/mar25_bootcamp_de_job_market/logs/job_market_ingestion.log` (journal principal)
- `/home/ubuntu/JobMarket_Projet/mar25_bootcamp_de_job_market/logs/cron_execution.log` (journal cron)

Le fichier de journal principal contient des informations détaillées sur :
- L'initialisation du script
- Les chemins utilisés
- L'exécution des commandes 
- Les erreurs éventuelles

## Dépannage

### Le script ne trouve pas le fichier .env

Vérifiez que le fichier `.env` existe à l'emplacement `/home/ubuntu/JobMarket_Projet/mar25_bootcamp_de_job_market/.env` et qu'il est lisible.

### Le script ne trouve pas les scripts de normalisation ou de chargement

Vérifiez les chemins des dossiers et que les fichiers suivants existent :
- `/home/ubuntu/JobMarket_Projet/mar25_bootcamp_de_job_market/pipeline/jm_normalizer.py`
- `/home/ubuntu/JobMarket_Projet/mar25_bootcamp_de_job_market/snowflake/snowflakeCSVLoader.py`

### Erreurs d'authentification Snowflake

Vérifiez les variables d'environnement dans votre fichier `.env`.

### Aucun fichier CSV n'est généré

Vérifiez les journaux pour comprendre pourquoi le normalisateur n'a pas généré de fichier CSV. Les raisons possibles incluent :
- Problèmes d'accès aux API
- Erreurs dans les paramètres de recherche
- Aucune nouvelle offre d'emploi disponible

## Maintenance

- Vérifiez régulièrement les fichiers journaux pour vous assurer que le script fonctionne correctement
- Conservez une copie de sauvegarde de ce script et de sa configuration
- Considérez la rotation des journaux pour éviter qu'ils ne deviennent trop volumineux

## Support

En cas de problème, consultez d'abord les fichiers journaux pour obtenir des informations détaillées sur l'erreur. Si vous ne parvenez pas à résoudre le problème, contactez l'équipe de développement du projet JobMarket.

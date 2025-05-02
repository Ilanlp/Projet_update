#!/usr/bin/env python3
"""
Script d'ingestion des données dans Snowflake pour le projet JobMarket
Ce script simplifié se concentre uniquement sur l'ingestion de données:
1. Exécute le normalisateur depuis le dossier 'pipeline' pour collecter les nouvelles offres d'emploi
2. Exécute le script snowflakeCSVLoader.py depuis le dossier 'snowflake' pour charger les données
3. Journalise l'exécution

À exécuter comme une tâche planifiée quotidienne (cron)
"""

import os
import sys
import logging
import subprocess
from datetime import datetime
from dotenv import load_dotenv

# Définir explicitement la racine du projet
project_root = "."

# Définir les chemins des dossiers spécifiques
PIPELINE_DIR = os.path.join(project_root, "")
SNOWFLAKE_DIR = os.path.join(project_root, "snowflake")
OUTPUT_DIR = os.path.join(project_root, "data")

# Ajouter les dossiers au PYTHONPATH
sys.path.insert(0, project_root)

# Changer le répertoire de travail à la racine du projet
os.chdir(project_root)

# Charger les variables d'environnement depuis le fichier .env
env_file = os.path.join(project_root, ".env")
if os.path.exists(env_file):
    load_dotenv(env_file)
else:
    print(f"Attention: Fichier .env non trouvé à {env_file}")

# Créer un répertoire pour les logs
logs_dir = os.path.join(project_root, "logs")
os.makedirs(logs_dir, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Configuration du logging
log_file = os.path.join(logs_dir, "job_market_ingestion.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
)
logger = logging.getLogger("job_market_ingestion")

# Journaliser l'initialisation avec les chemins
logger.info("Script initialisé avec les chemins suivants:")
logger.info(f"- Racine du projet: {project_root}")
logger.info(f"- Dossier pipeline: {PIPELINE_DIR}")
logger.info(f"- Dossier snowflake: {SNOWFLAKE_DIR}")
logger.info(f"- Dossier output: {OUTPUT_DIR}")
logger.info(f"- Fichier de log: {log_file}")

# Vérifier l'existence des scripts nécessaires
normalizer_script = os.path.join(PIPELINE_DIR, "normalizer.py")
snowflake_loader_script = os.path.join(SNOWFLAKE_DIR, "snowflakeCSVLoader.py")

if not os.path.exists(normalizer_script):
    logger.error(f"Script normalisateur non trouvé: {normalizer_script}")
    sys.exit(1)

if not os.path.exists(snowflake_loader_script):
    logger.error(f"Script Snowflake Loader non trouvé: {snowflake_loader_script}")
    sys.exit(1)

logger.info("Tous les scripts nécessaires ont été trouvés")


class JobMarketIngestion:
    """
    Classe pour l'ingestion des données du projet JobMarket dans Snowflake
    """

    def __init__(self):
        """
        Initialise le processus d'ingestion
        """
        self.pipeline_dir = PIPELINE_DIR
        self.snowflake_dir = SNOWFLAKE_DIR
        self.output_dir = OUTPUT_DIR
        self.normalizer_script = normalizer_script
        self.snowflake_loader_script = snowflake_loader_script

        # État du processus
        self.run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        logger.info(f"Processus d'ingestion initialisé avec l'ID {self.run_id}")

    def run_normalizer(self):
        """
        Exécute le script de normalisation pour récupérer les nouvelles offres d'emploi

        Returns:
            bool: True si l'exécution réussit, False sinon
        """
        logger.info("Démarrage du processus de normalisation des données")

        try:
            # Créer la commande avec les paramètres
            cmd = [sys.executable, self.normalizer_script]

            # Définir l'environnement pour subprocess en incluant le PYTHONPATH actuel
            env = os.environ.copy()
            env["OUTPUT_DIR"] = self.output_dir

            # Exécuter la commande
            logger.info(f"Exécution de la commande: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=env,
                cwd=project_root,  # Exécuter depuis la racine du projet
            )

            # Vérifier si l'exécution a réussi
            if result.returncode != 0:
                logger.error(f"Échec de la normalisation: {result.stderr}")
                return False

            logger.info("Normalisation terminée avec succès")
            logger.info(
                f"Sortie du normalisateur: {result.stdout[:500]}..."
            )  # Afficher les 500 premiers caractères

            # Vérifier si des fichiers CSV ont été générés
            files = [
                f
                for f in os.listdir(self.output_dir)
                if f.startswith("all_jobs_") and f.endswith(".csv")
            ]
            if files:
                latest_file = max(
                    files,
                    key=lambda x: os.path.getmtime(os.path.join(self.output_dir, x)),
                )
                latest_csv = os.path.join(self.output_dir, latest_file)
                logger.info(f"Fichier CSV généré: {latest_csv}")
            else:
                logger.warning(
                    "Aucun fichier CSV généré par le normalisateur n'a été trouvé"
                )

            return True

        except Exception as e:
            logger.error(f"Erreur lors de l'exécution du normalisateur: {str(e)}")
            import traceback

            logger.error(traceback.format_exc())
            return False

    def load_to_snowflake(self):
        """
        Exécute le script snowflakeCSVLoader.py pour charger les données dans Snowflake

        Returns:
            bool: True si le chargement réussit, False sinon
        """
        logger.info("Démarrage du chargement des données dans Snowflake")

        try:
            # Vérifier que les variables d'environnement Snowflake nécessaires sont définies
            required_vars = [
                "SNOWFLAKE_USER",
                "SNOWFLAKE_PASSWORD",
                "SNOWFLAKE_ACCOUNT",
                "SNOWFLAKE_WAREHOUSE",
                "SNOWFLAKE_DATABASE",
                "SNOWFLAKE_SCHEMA",
            ]

            missing_vars = [var for var in required_vars if not os.getenv(var)]
            if missing_vars:
                logger.error(
                    f"Variables d'environnement manquantes: {', '.join(missing_vars)}"
                )
                logger.error("Vérifiez votre fichier .env")
                return False

            # Vérifier si des fichiers CSV existent dans le répertoire de sortie
            csv_files = [f for f in os.listdir(self.output_dir) if f.endswith(".csv")]
            if not csv_files:
                logger.warning(f"Aucun fichier CSV trouvé dans {self.output_dir}")
                return False

            logger.info(f"Fichiers CSV trouvés: {', '.join(csv_files)}")

            # Préparer la commande pour exécuter le script snowflakeCSVLoader.py
            cmd = [sys.executable, self.snowflake_loader_script]

            # Définir l'environnement pour subprocess
            env = os.environ.copy()

            # Exécuter la commande
            logger.info(f"Exécution de la commande: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=env,
                cwd=project_root,  # Exécuter depuis le dossier snowflake
            )

            # Vérifier si l'exécution a réussi
            if result.returncode != 0:
                logger.error(f"Échec du chargement dans Snowflake: {result.stderr}")
                return False

            logger.info("Chargement dans Snowflake terminé avec succès")
            logger.info(
                f"Sortie du chargeur: {result.stdout[:500]}..."
            )  # Afficher les 500 premiers caractères

            return True

        except Exception as e:
            logger.error(f"Erreur lors du chargement dans Snowflake: {str(e)}")
            import traceback

            logger.error(traceback.format_exc())
            return False

    def run_ingestion(self):
        """
        Exécute le processus complet d'ingestion

        Returns:
            bool: True si l'ingestion réussit, False sinon
        """
        logger.info(f"Démarrage du processus d'ingestion JobMarket (ID: {self.run_id})")
        start_time = datetime.now()

        try:
            # Étape 1: Normalisation des données
            normalizer_success = self.run_normalizer()
            if not normalizer_success:
                logger.error("Échec de l'étape de normalisation, arrêt du processus")
                return False

            # Étape 2: Chargement dans Snowflake
            load_success = self.load_to_snowflake()
            if not load_success:
                logger.error("Échec de l'étape de chargement, arrêt du processus")
                return False

            # Calculer la durée totale
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(
                f"Processus d'ingestion terminé avec succès en {duration:.2f} secondes (ID: {self.run_id})"
            )
            return True

        except Exception as e:
            logger.error(
                f"Erreur critique lors de l'exécution du processus d'ingestion: {str(e)}"
            )
            import traceback

            logger.error(traceback.format_exc())
            return False


if __name__ == "__main__":
    # Point d'entrée principal du script
    try:
        # Vérifier si le script est appelé avec des arguments
        if len(sys.argv) > 1:
            if sys.argv[1] == "--test":
                logger.info(
                    "Mode test: vérification des chemins et des dépendances sans exécution"
                )

                # Les vérifications des scripts sont déjà effectuées au début
                logger.info(f"Script normalisateur: {normalizer_script} ✓")
                logger.info(f"Script Snowflake Loader: {snowflake_loader_script} ✓")

                # Vérifier les variables d'environnement
                for var in [
                    "SNOWFLAKE_USER",
                    "SNOWFLAKE_PASSWORD",
                    "SNOWFLAKE_ACCOUNT",
                    "SNOWFLAKE_WAREHOUSE",
                    "SNOWFLAKE_DATABASE",
                    "SNOWFLAKE_SCHEMA",
                ]:
                    if os.getenv(var):
                        logger.info(f"Variable d'environnement {var} définie ✓")
                    else:
                        logger.warning(f"Variable d'environnement {var} non définie ✗")

                sys.exit(0)

        # Exécution normale du script
        logger.info("Démarrage du processus d'ingestion dans Snowflake")
        ingestion = JobMarketIngestion()
        success = ingestion.run_ingestion()

        if not success:
            logger.error("Le processus d'ingestion s'est terminé avec des erreurs")
            sys.exit(1)

        logger.info("Le processus d'ingestion s'est terminé avec succès")
        sys.exit(0)

    except Exception as e:
        logger.critical(f"Erreur non gérée: {str(e)}")
        import traceback

        logger.critical(f"Trace de la pile: {traceback.format_exc()}")
        sys.exit(1)

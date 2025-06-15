import os
import logging
import glob
from pathlib import Path
import snowflake.connector
from dotenv import load_dotenv
from colorlog import ColoredFormatter


logger = logging.getLogger("export")
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_formatter = ColoredFormatter(
    "%(log_color)s%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    log_colors={
        "DEBUG": "cyan",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "bold_red",
    },
)
console_handler.setFormatter(console_formatter)

file_handler = logging.FileHandler(
    "../logs/snowflake_export.log", mode="a", encoding="utf-8"
)
file_formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
file_handler.setFormatter(file_formatter)

logger.addHandler(console_handler)
logger.addHandler(file_handler)


class SnowflakeExporter:
    """
    Classe pour exporter des données depuis Snowflake vers des fichiers locaux.
    """

    def __init__(self, env_file=".env"):
        """
        Initialise la classe avec les paramètres de connexion à Snowflake.

        Args:
            env_file (str): Chemin vers le fichier .env contenant les identifiants
        """
        # Charge les variables d'environnement depuis le fichier .env
        load_dotenv(env_file)
        # Initialisation des attributs de classe
        self.connection = None  # Connexion à Snowflake
        self.cursor = None  # Curseur pour exécuter les requêtes
        self.stage_name = None  # Nom du stage temporaire

    def connect(self):
        """
        Établit la connexion à Snowflake en utilisant les identifiants
        stockés dans les variables d'environnement.

        Returns:
            self: Retourne l'instance pour permettre le chaînage des méthodes
        """
        self.connection = snowflake.connector.connect(
            user=os.getenv("SNOWFLAKE_USER"),
            password=os.getenv("SNOWFLAKE_PASSWORD"),
            account=os.getenv("SNOWFLAKE_ACCOUNT"),
            warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
            database=os.getenv("SNOWFLAKE_DATABASE"),
            schema=os.getenv("SNOWFLAKE_SCHEMA"),
        )
        self.cursor = self.connection.cursor()
        return self

    def is_connected(self):
        """
        Vérifie si la connexion à Snowflake est active et fonctionnelle
        en exécutant une requête simple.

        Returns:
            bool: True si la connexion est établie et fonctionnelle, False sinon
        """
        if self.connection is None or self.cursor is None:
            return False

        try:
            # Exécute une requête simple pour vérifier la connexion
            self.cursor.execute("SELECT 1")
            result = self.cursor.fetchone()
            return result is not None and result[0] == 1
        except Exception as e:
            print(f"Erreur lors de la vérification de la connexion: {str(e)}")
            return False

    def create_stage(self, stage_name):
        """
        Crée un stage Snowflake temporaire pour l'export.

        Args:
            stage_name (str): Nom du stage à créer

        Returns:
            self: Retourne l'instance pour permettre le chaînage des méthodes
        """
        if self.is_connected():
            # Crée le stage s'il n'existe pas déjà
            self.cursor.execute(f"CREATE STAGE IF NOT EXISTS {stage_name}")
            self.stage_name = stage_name
            return self
        return False

    def drop_stage(self, stage_name=None):
        """
        Supprime un stage Snowflake.

        Args:
            stage_name (str): Nom du stage à supprimer (utilise self.stage_name si None)

        Returns:
            bool: True si la suppression réussit, False sinon
        """
        if not self.is_connected():
            return False

        try:
            # Utiliser le nom du stage par défaut si non spécifié
            stage_name = stage_name or self.stage_name

            # Exécuter la commande DROP STAGE
            self.cursor.execute(f"DROP STAGE IF EXISTS {stage_name}")
            print(f"Stage {stage_name} supprimé avec succès")
            return True
        except Exception as e:
            print(f"Erreur lors de la suppression du stage {stage_name}: {str(e)}")
            return False

    def ensure_directory_exists(self, directory_path):
        """
        Vérifie si le répertoire existe et le crée si nécessaire.

        Args:
            directory_path (str): Chemin du répertoire à vérifier/créer

        Returns:
            bool: True si le répertoire existe ou a été créé, False sinon
        """
        try:
            # Créer le répertoire s'il n'existe pas
            os.makedirs(directory_path, exist_ok=True)
            # Vérifier les permissions
            if not os.access(directory_path, os.W_OK):
                logger.error(f"Pas de permission d'écriture dans le répertoire {directory_path}")
                return False
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la création/vérification du répertoire {directory_path}: {str(e)}")
            return False

    def concatenate_files(self, input_pattern, output_file):
        """
        Concatène plusieurs fichiers en un seul fichier.

        Args:
            input_pattern (str): Pattern pour trouver les fichiers à concaténer
            output_file (str): Chemin du fichier de sortie

        Returns:
            bool: True si la concaténation réussit, False sinon
        """
        try:
            # Trouver tous les fichiers correspondant au pattern
            files = sorted(glob.glob(input_pattern))
            if not files:
                logger.error(f"Aucun fichier trouvé avec le pattern {input_pattern}")
                return False

            # Concaténer les fichiers
            with open(output_file, 'wb') as outfile:
                for file in files:
                    with open(file, 'rb') as infile:
                        outfile.write(infile.read())
                    # Supprimer le fichier source après la concaténation
                    os.remove(file)

            logger.info(f"Fichiers concaténés avec succès dans {output_file}")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la concaténation des fichiers: {str(e)}")
            return False

    def export_table_to_csv(self, database, schema, table_name, output_path):
        """
        Exporte une table Snowflake vers un fichier CSV compressé.

        Args:
            database (str): Nom de la base de données
            schema (str): Nom du schéma
            table_name (str): Nom de la table à exporter
            output_path (str): Chemin complet du fichier de sortie

        Returns:
            bool: True si l'export réussit, False sinon
        """
        try:
            if not self.is_connected():
                self.connect()

            # Vérifier et créer le répertoire de sortie si nécessaire
            output_dir = os.path.dirname(output_path)
            if not self.ensure_directory_exists(output_dir):
                return False

            # Créer un stage temporaire pour l'export
            stage_name = f"TEMP_EXPORT_{table_name}"
            self.create_stage(stage_name)

            # Qualifier complètement les noms
            fully_qualified_table = f"{database}.{schema}.{table_name}"

            # Exécuter la commande COPY INTO pour l'export avec le format de fichier externe
            # Ajout des paramètres de localisation pour gérer les caractères spéciaux
            self.cursor.execute(
                f"""
                COPY INTO @{stage_name}
                FROM {fully_qualified_table}
                FILE_FORMAT = (
                    TYPE = CSV
                    COMPRESSION = GZIP
                    FIELD_DELIMITER = ","
                    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
                    EMPTY_FIELD_AS_NULL = TRUE
                    DATE_FORMAT = AUTO
                    TIMESTAMP_FORMAT = AUTO
                    ENCODING = "UTF-8"
                    ESCAPE = "\\"
                    ESCAPE_UNENCLOSED_FIELD = "\\"
                    TRIM_SPACE = TRUE
                    VALIDATE_UTF8 = TRUE
                    REPLACE_INVALID_CHARACTERS = TRUE
                    SKIP_BYTE_ORDER_MARK = TRUE
                    NULL_IF = ('NULL', 'null', '')
                    FIELD_ENCLOSED_BY = '"'
                )
                """
            )

            # Télécharger le fichier depuis le stage
            # Utiliser le répertoire parent comme destination
            output_dir = os.path.dirname(output_path)
            self.cursor.execute(
                f"""
                GET @{stage_name} file://{output_dir}
                """
            )

            # Concaténer les fichiers générés
            temp_pattern = os.path.join(output_dir, "data_*.csv.gz")
            if not self.concatenate_files(temp_pattern, output_path):
                return False

            logger.info(f"Table {fully_qualified_table} exportée avec succès vers {output_path}")
            return True

        except Exception as e:
            logger.error(f"Erreur lors de l'export de la table {table_name}: {str(e)}")
            return False
        finally:
            # Nettoyer le stage temporaire
            self.drop_stage(stage_name)


if __name__ == "__main__":
    exporter = SnowflakeExporter()

    # Obtenir le chemin absolu du script
    path_absolu = Path(__file__).resolve()
    output_dir = str(path_absolu.parents[1] / "data")

    # Exporter la table ONE_BIG_TABLE
    success = exporter.export_table_to_csv(
        database="JOB_MARKET",
        schema="GOLD",
        table_name="ONE_BIG_TABLE",
        output_path=os.path.join(output_dir, "ONE_BIG_TABLE.csv.gz")
    )

    if success:
        logger.info("Export de la table ONE_BIG_TABLE terminé avec succès")
    else:
        logger.error("Échec de l'export de la table ONE_BIG_TABLE") 
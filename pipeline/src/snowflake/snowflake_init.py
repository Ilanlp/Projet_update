import logging
from colorlog import ColoredFormatter
from snowflake_core import SnowflakeCore


logger = logging.getLogger('init')
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_formatter = ColoredFormatter(
    "%(log_color)s%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    log_colors={
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'bold_red',
    }
)
console_handler.setFormatter(console_formatter)

file_handler = logging.FileHandler("../logs/snowflake_init.log", mode='a', encoding='utf-8')
file_formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
file_handler.setFormatter(file_formatter)

logger.addHandler(console_handler)
logger.addHandler(file_handler)


class SnowflakeInit(SnowflakeCore):
    def __init__(self, env_file=".env"):
        super().__init__(env_file)
        self.connect()

    def execute_sql_file(self, file_path):
        """Exécute un fichier SQL."""
        with open(file_path, "r") as file:
            sql = file.read()

        for statement in sql.split(";"):
            if statement.strip():
                logger.info(f"Exécution: {statement[:80]}...")
                try:
                    self.cursor.execute(statement)
                    logger.info("Succès!")
                except Exception as e:
                    logger.error(f"Erreur: {e}")

        # Retourner self pour permettre le chaînage des méthodes
        return self

    def initialize(self):
        """Initialise la structure du projet Snowflake."""
        try:
            # Établir la connexion si ce n'est pas déjà fait
            if not self.is_connected():
                self.connect()

            logger.info("Début de l'initialisation du projet Snowflake...")

            # Enchaînement correct des méthodes
            self.execute_sql_file("./create_warehouses.sql")
            self.execute_sql_file("./create_database.sql")
            self.execute_sql_file("./create_schemas.sql")
            self.execute_sql_file("./create_file_format.sql")

            self.execute_sql_file("./create_tables/bronze_init.sql")  # RAW
            self.execute_sql_file("./create_tables/silver_init.sql")  # DIM
            self.execute_sql_file("./create_tables/gold_init.sql")    #

            logger.info("Initialisation du projet Snowflake terminée!")
            return True

        except Exception as e:
            # Capturer et afficher les erreurs
            logger.error(f"Erreur lors de l'initialisation du projet: {str(e)}")
            return False

        finally:
            # Ne pas fermer ici, car on pourrait vouloir réutiliser l'objet
            pass

    def close(self):
        """Ferme proprement les ressources."""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        logger.info("Connexion fermée")


if __name__ == "__main__":
    snowflake_init = SnowflakeInit()
    snowflake_init.initialize()
    snowflake_init.close()

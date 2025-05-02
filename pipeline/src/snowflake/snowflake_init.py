import logging
# Importez la classe, pas le module
from snowflakeCSVLoader import SnowflakeCSVLoader  

# Configuration du logging
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class SnowflakeInit(SnowflakeCSVLoader):
    def __init__(self, env_file=".env"):
        # Appel correct du constructeur parent
        super().__init__(env_file)
        # Établir la connexion immédiatement
        self.connect()
        
    def execute_sql_file(self, file_path):
        """Exécute un fichier SQL."""
        with open(file_path, 'r') as file:
            sql = file.read()
        
        for statement in sql.split(';'):
            if statement.strip():
                logger.info(f"Exécution: {statement[:80]}...")
                try:
                    self.cursor.execute(statement)
                    logger.info("Succès!")
                except Exception as e:
                    logger.error(f"Erreur: {e}")
        
        # Retourner self pour permettre le chaînage des méthodes
        return self
        
    def initialize_snowflake_project(self):
        """Initialise la structure du projet Snowflake."""
        try:
            # Établir la connexion si ce n'est pas déjà fait
            if not self.is_connected():
                self.connect()
                
            logger.info("Début de l'initialisation du projet Snowflake...")
            
            # Enchaînement correct des méthodes
            self.execute_sql_file('./create_database.sql')
            self.execute_sql_file('./create_schemas.sql')
            self.execute_sql_file('./create_warehouses.sql')
            self.execute_sql_file('./create_tables/silver_init.sql')
            
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
    print(snowflake_init.is_connected())
    snowflake_init.initialize_snowflake_project()
    # S'assurer que les ressources sont libérées
    snowflake_init.close()
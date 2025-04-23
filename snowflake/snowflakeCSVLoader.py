import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas
from dotenv import load_dotenv
import pandas as pd
import os, glob, re

class SnowflakeCSVLoader:
    """
    Classe pour charger des données CSV dans Snowflake et effectuer des insertions
    dans différentes tables en gérant les relations entre elles.
    """
    
    def __init__(self, env_file='.env'):
        """
        Initialise la classe avec les paramètres de connexion à Snowflake.
        
        Args:
            env_file (str): Chemin vers le fichier .env contenant les identifiants
        """
        # Charge les variables d'environnement depuis le fichier .env
        load_dotenv(env_file)
        # Initialisation des attributs de classe
        self.connection = None  # Connexion à Snowflake
        self.cursor = None      # Curseur pour exécuter les requêtes
        self.filename = None    # Nom du fichier CSV traité
        self.filepath = None    # Chemin complet du fichier CSV
        
    def connect(self):
        """
        Établit la connexion à Snowflake en utilisant les identifiants
        stockés dans les variables d'environnement.
        
        Returns:
            self: Retourne l'instance pour permettre le chaînage des méthodes
        """
        self.connection = snowflake.connector.connect(
            user=os.getenv('SNOWFLAKE_USER'),
            password=os.getenv('SNOWFLAKE_PASSWORD'),
            account=os.getenv('SNOWFLAKE_ACCOUNT'),
            warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
            database=os.getenv('SNOWFLAKE_DATABASE'),
            schema=os.getenv('SNOWFLAKE_SCHEMA')
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

    def create_stage(self):
        """
        Crée un stage Snowflake pour le téléchargement du fichier CSV.
        Le stage est un espace de stockage temporaire sur Snowflake.
        
        Returns:
            self: Retourne l'instance pour permettre le chaînage des méthodes
        """
        if self.is_connected():
            # Crée le stage s'il n'existe pas déjà
            self.cursor.execute("CREATE STAGE IF NOT EXISTS csv_stage")
            # Télécharge le fichier dans le stage
            self.cursor.execute(f"PUT file://{self.filepath_normalise} @csv_stage auto_compress=true")
            return self
        
        return False
        
    def load_file(self, directory_path):
        """
        Charge un fichier CSV commençant par 'all_jobs' dans le répertoire spécifié.
        Utilise une expression régulière pour trouver les fichiers correspondants.
        
        Args:
            directory_path (str): Chemin du répertoire contenant les fichiers
            
        Returns:
            self: Retourne l'instance pour permettre le chaînage des méthodes
            
        Raises:
            FileNotFoundError: Si aucun fichier correspondant n'est trouvé
        """
        # Récupérer tous les fichiers CSV du répertoire
        all_files = glob.glob(os.path.join(directory_path, "*.csv"))
        # Utiliser regex pour trouver le fichier qui commence par all_jobs
        pattern = re.compile(r'all_jobs.*\.csv$')
        matched_files = [f for f in all_files if pattern.search(os.path.basename(f))]
        
        # Lever une exception si aucun fichier ne correspond
        if not matched_files:
            raise FileNotFoundError("Aucun fichier commençant par 'all_jobs' n'a été trouvé.")
        
        # Utiliser le premier fichier correspondant
        self.filepath = os.path.abspath(matched_files[0])
        # Normaliser le chemin pour Snowflake (utiliser des / au lieu de \)
        self.filepath_normalise = self.filepath.replace('\\', '/')
        # Extraire le nom du fichier sans extension et le mettre en majuscules
        self.filename = os.path.basename(self.filepath).split('.')[0].upper()
        print(f"Préparation du fichier: {self.filename}")
        return self    
    
    def load_to_table(self, chunk_size=10000):
        """
        Charge les données du fichier CSV dans une table temporaire Snowflake.
        Utilise pandas pour lire le CSV et snowflake.connector pour le chargement.
        
        Args:
            chunk_size (int): Nombre de lignes à charger par lot pour optimiser la mémoire
            
        Returns:
            self: Retourne l'instance pour permettre le chaînage des méthodes
        """
        if self.is_connected():
            # Lire le fichier CSV avec pandas
            df = pd.read_csv(self.filepath)
            # Utiliser write_pandas pour charger les données dans une table temporaire
            success, nchunks, nrows, output = write_pandas(
                self.connection,
                df,
                self.filename,  # Nom de la table temporaire
                auto_create_table=True,  # Créer la table automatiquement
                table_type='temporary',  # Table temporaire
                chunk_size=chunk_size    # Taille des lots
            )
            print(f"Succès: {success}")
            print(f"Chunks utilisés: {nchunks}")
            print(f"Lignes insérées: {nrows}")

            # Supprimer le fichier local après le chargement
            os.remove(self.filepath)
            return self
        
        return False

    def insert_all_job(self):
        """
        Insère les données depuis la table temporaire vers les tables permanentes.
        Gère les relations entre les tables ENTREPRISE et OFFREEMPLOI.
        
        Returns:
            bool: True si l'insertion réussit, False sinon
        """
        if self.is_connected():
            # Insertion des entreprises qui n'existent pas encore
            self.cursor.execute(f"""
            INSERT INTO ENTREPRISE (nom)
            SELECT DISTINCT t."company_name" FROM {self.filename} t
            WHERE NOT EXISTS (
                SELECT 1 FROM ENTREPRISE e 
                WHERE e.nom = t."company_name"
            )
            """)

            # Insertion des offres d'emploi en reliant à l'entreprise correspondante
            self.cursor.execute(f"""
            INSERT INTO OFFREEMPLOI (id, description, date_publication, date_mise_a_jour, source, source_url, salaire, id_entreprise)
            SELECT 
                o."id",
                o."description", 
                o."date_created", 
                o."date_updated", 
                o."source", 
                o."source_url", 
                o."salary_min",
                e.id_entreprise
            FROM {self.filename} o
            LEFT JOIN ENTREPRISE e ON o."company_name" = e.nom
            """)

            return True
        
        return False

    def drop_db(self):
        """
        Supprime la table temporaire créée lors du chargement.
        
        Returns:
            bool: True si la suppression réussit, False sinon
        """
        if self.is_connected():
            self.cursor.execute(f"""
            DROP TABLE IF EXISTS {self.filename}
            """)
            return True
        return False       

    def process_file(self, directory_path, chunk_size=10000):
        """
        Méthode principale pour traiter un fichier de bout en bout.
        Enchaîne toutes les étapes du processus de chargement.
        
        Args:
            directory_path (str): Chemin du répertoire contenant les fichiers CSV
            chunk_size (int): Taille des chunks pour le chargement
            
        Returns:
            bool: True si le traitement réussit, False sinon
        """
        try:
            # Établir la connexion et enchaîner les opérations
            self.connect()
            (self.load_file(directory_path)
            .create_stage()
            .load_to_table(chunk_size)
            .insert_all_job())
            return True
        except Exception as e:
            # Capturer et afficher les erreurs
            print(f"Erreur lors du traitement du fichier: {str(e)}")
            return False
        finally:
            # Fermer la connexion et le curseur dans tous les cas
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()

    
if __name__ == "__main__":
    # Point d'entrée principal du script
    loader = SnowflakeCSVLoader()
    # Traitement d'un répertoire contenant des fichiers all_jobs*.csv
    success = loader.process_file('data/')
    
    # Affichage du résultat
    if success:
        print(f"Traitement du fichier {loader.filename} terminé avec succès")
    else:
        print(f"Échec du traitement du fichier {loader.filename}")
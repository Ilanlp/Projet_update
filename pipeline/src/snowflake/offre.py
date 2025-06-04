import os
import glob
from snowflake_core import SnowflakeCore

def load_latest_file_to_snowflake():
    try:
        # 1. Trouver le fichier le plus récent
        data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        files = glob.glob(os.path.join(data_dir, 'all_jobs_*.csv.gz'))
        if not files:
            print("Aucun fichier all_jobs trouvé")
            return False
        
        latest_file = max(files, key=os.path.getctime)
        print(f"Fichier trouvé : {latest_file}")

        # 2. Se connecter à Snowflake
        sf = SnowflakeCore()
        sf.connect()
        sf.cursor.execute("USE DATABASE JOB_MARKET")
        sf.cursor.execute("USE SCHEMA RAW")
        # 3. Créer le format de fichier
        sf.cursor.execute("""
        CREATE OR REPLACE FILE FORMAT raw.csv_gz_format
        TYPE = CSV
        FIELD_DELIMITER = ','
        FIELD_OPTIONALLY_ENCLOSED_BY = '"'
        SKIP_HEADER = 1
        NULL_IF = ('NULL', 'null', '')
        EMPTY_FIELD_AS_NULL = TRUE
        COMPRESSION = GZIP
        ERROR_ON_COLUMN_COUNT_MISMATCH = FALSE
        """)
        print("Format de fichier créé")

        # 4. Créer un stage temporaire
        stage_name = "TEMP_STAGE"
        sf.cursor.execute(f"CREATE OR REPLACE TEMPORARY STAGE {stage_name}")
        
        # 5. Uploader le fichier vers le stage
        sf.cursor.execute(f"PUT file://{latest_file} @{stage_name} AUTO_COMPRESS=FALSE OVERWRITE=TRUE")
        print("Fichier uploadé vers le stage")

        # 6. Copier les données dans la table en spécifiant les colonnes
        sf.cursor.execute("""
        COPY INTO raw.RAW_OFFRE (
            id_local, source, title, description, company_name,
            location_name, latitude, longitude, date_created, date_updated,
            contract_type, contract_duration, working_hours, salary_min,
            salary_max, salary_currency, salary_period, experience_required,
            category, sector, application_url, source_url, skills,
            remote_work, is_handicap_accessible, code_rome, langues,
            date_extraction
        )
        FROM @TEMP_STAGE
        FILE_FORMAT = raw.csv_gz_format
        """)
        
        # 7. Vérifier le résultat
        result = sf.cursor.fetchall()
        rows_loaded = sum(row[2] for row in result) if result else 0
        print(f"Données chargées avec succès : {rows_loaded} lignes")
        
        # 8. Nettoyer
        sf.cursor.execute(f"DROP STAGE IF EXISTS {stage_name}")
        
        return True

    except Exception as e:
        print(f"Erreur : {str(e)}")
        return False

if __name__ == "__main__":
    load_latest_file_to_snowflake()

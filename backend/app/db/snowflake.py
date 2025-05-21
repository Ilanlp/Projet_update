import snowflake.connector
from snowflake.connector.connection import SnowflakeConnection
from contextlib import contextmanager
from app.config import settings
import logging
from typing import Union

logger = logging.getLogger(__name__)


@contextmanager
def get_snowflake_connection() -> SnowflakeConnection:
    """Crée et gère une connexion à Snowflake"""
    conn = None
    try:
        conn = snowflake.connector.connect(
            account=settings.SNOWFLAKE_ACCOUNT,
            user=settings.SNOWFLAKE_USER,
            password=settings.SNOWFLAKE_PASSWORD,
            database=settings.SNOWFLAKE_DATABASE,
            schema=settings.SNOWFLAKE_SCHEMA,
            warehouse=settings.SNOWFLAKE_WAREHOUSE,
            role=settings.SNOWFLAKE_ROLE,
        )
        logger.info("Connexion à Snowflake établie")
        yield conn
    except Exception as e:
        logger.error(f"Erreur lors de la connexion à Snowflake: {str(e)}")
        raise
    finally:
        if conn:
            conn.close()
            logger.info("Connexion à Snowflake fermée")


def execute_query(query: str, params: Union[dict, list, None] = None) -> list:
    """Exécute une requête SQL et retourne les résultats"""
    with get_snowflake_connection() as conn:
        cursor = conn.cursor(snowflake.connector.DictCursor)
        try:
            # Log pour le débogage
            logger.info("=== Détails de l'exécution de la requête ===")
            logger.info(f"Requête brute: {query}")
            logger.info(f"Paramètres reçus: {params}")

            # Traitement des paramètres selon leur type
            if isinstance(params, dict):
                processed_params = {}
                for key, value in params.items():
                    if isinstance(value, (int, float)):
                        processed_params[key] = value
                    else:
                        try:
                            processed_params[key] = int(value)
                        except (ValueError, TypeError):
                            try:
                                processed_params[key] = float(value)
                            except (ValueError, TypeError):
                                processed_params[key] = value
            elif isinstance(params, list):
                processed_params = []
                for value in params:
                    if isinstance(value, (int, float)):
                        processed_params.append(value)
                    else:
                        try:
                            processed_params.append(int(value))
                        except (ValueError, TypeError):
                            try:
                                processed_params.append(float(value))
                            except (ValueError, TypeError):
                                processed_params.append(value)
            else:
                processed_params = params

            logger.info(f"Paramètres traités: {processed_params}")

            # Exécution de la requête avec paramètres bindés
            cursor.execute(query, processed_params)

            # Récupération des résultats
            results = cursor.fetchall()
            logger.info(f"Nombre de résultats obtenus: {len(results)}")
            return results
        except Exception as e:
            logger.error("=== Erreur lors de l'exécution de la requête ===")
            logger.error(f"Message d'erreur: {str(e)}")
            logger.error(f"Requête: {query}")
            logger.error(f"Paramètres originaux: {params}")
            logger.error(
                f"Paramètres traités: {processed_params if 'processed_params' in locals() else None}"
            )
            raise
        finally:
            cursor.close()

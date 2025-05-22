import snowflake.connector
from snowflake.connector.connection import SnowflakeConnection
from contextlib import asynccontextmanager
from app.config import settings
import logging
from typing import Union, Dict, List, Any
import asyncio

logger = logging.getLogger(__name__)


@asynccontextmanager
async def get_snowflake_connection() -> SnowflakeConnection:
    """Crée et gère une connexion à Snowflake de manière asynchrone"""
    conn = None
    try:
        loop = asyncio.get_event_loop()
        conn = await loop.run_in_executor(
            None,
            lambda: snowflake.connector.connect(
                account=settings.SNOWFLAKE_ACCOUNT,
                user=settings.SNOWFLAKE_USER,
                password=settings.SNOWFLAKE_PASSWORD,
                database=settings.SNOWFLAKE_DATABASE,
                schema=settings.SNOWFLAKE_SCHEMA,
                warehouse=settings.SNOWFLAKE_WAREHOUSE,
                role=settings.SNOWFLAKE_ROLE,
            ),
        )
        logger.info("Connexion à Snowflake établie")
        yield conn
    except Exception as e:
        logger.error(f"Erreur lors de la connexion à Snowflake: {str(e)}")
        raise
    finally:
        if conn:
            await loop.run_in_executor(None, conn.close)
            logger.info("Connexion à Snowflake fermée")


def convert_to_numeric(value: Any) -> Any:
    """
    Convertit une valeur en numérique si possible.

    Args:
        value: La valeur à convertir

    Returns:
        La valeur convertie en int ou float si possible, sinon la valeur originale
    """
    if isinstance(value, (int, float)):
        return value

    try:
        return int(value)
    except (ValueError, TypeError):
        try:
            return float(value)
        except (ValueError, TypeError):
            return value


def process_value(value: Any) -> Any:
    """
    Traite une valeur pour la rendre compatible avec Snowflake.

    Args:
        value: La valeur à traiter

    Returns:
        - None pour les valeurs Python None (sera converti en NULL par Snowflake)
        - Valeur numérique si possible
        - Valeur originale sinon
    """
    if value is None:
        return None
    return convert_to_numeric(value)


def process_dict_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Traite les paramètres de type dictionnaire pour les rendre compatibles avec Snowflake.

    Cette fonction:
    1. Gère les valeurs None (convertis en NULL dans Snowflake)
    2. Convertit les valeurs numériques si possible
    3. Préserve les autres types de données

    Args:
        params: Dictionnaire de paramètres à traiter

    Returns:
        Dictionnaire avec les valeurs traitées
    """
    if not params:
        return {}
    return {key: process_value(value) for key, value in params.items()}


def process_list_params(params: List[Any]) -> List[Any]:
    """
    Traite les paramètres de type liste pour les rendre compatibles avec Snowflake.

    Cette fonction:
    1. Gère les valeurs None (convertis en NULL dans Snowflake)
    2. Convertit les valeurs numériques si possible
    3. Préserve les autres types de données

    Args:
        params: Liste de paramètres à traiter

    Returns:
        Liste avec les valeurs traitées
    """
    if not params:
        return []
    return [process_value(value) for value in params]


def format_query_with_params(query: str, params: Dict[str, Any]) -> str:
    """
    Formate la requête avec les paramètres.

    Cette fonction:
    1. Gère les valeurs None en les convertissant en NULL SQL
    2. Entoure les chaînes de caractères avec des guillemets
    3. Convertit les autres valeurs en leur représentation SQL

    Args:
        query: La requête SQL avec des placeholders (:param)
        params: Dictionnaire des paramètres à remplacer

    Returns:
        La requête SQL formatée avec les valeurs
    """
    for key, value in params.items():
        placeholder = f":{key}"
        if value is None:
            formatted_value = "NULL"
        elif isinstance(value, str):
            formatted_value = f"'{value}'"
        elif isinstance(value, bool):
            formatted_value = str(value).upper()
        else:
            formatted_value = str(value)
        query = query.replace(placeholder, formatted_value)
    return query


async def execute_query(query: str, params: Union[dict, list, None] = None) -> list:
    """Exécute une requête SQL de manière asynchrone et retourne les résultats"""
    async with get_snowflake_connection() as conn:
        cursor = conn.cursor(snowflake.connector.DictCursor)
        loop = asyncio.get_event_loop()

        try:
            logger.info("=== Détails de l'exécution de la requête ===")
            logger.info(f"Requête brute: {query}")
            logger.info(f"Paramètres reçus: {params}")

            processed_params = None
            if isinstance(params, dict):
                processed_params = process_dict_params(params)
                query = format_query_with_params(query, processed_params)
                processed_params = None
            elif isinstance(params, list):
                processed_params = process_list_params(params)

            logger.info(f"Requête modifiée: {query}")
            logger.info(f"Paramètres traités: {processed_params}")

            await loop.run_in_executor(None, cursor.execute, query, processed_params)
            results = await loop.run_in_executor(None, cursor.fetchall)

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
            await loop.run_in_executor(None, cursor.close)

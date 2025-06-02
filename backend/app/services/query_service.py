import os
import jinja2
from typing import Dict, Any, List, Optional, Type, TypeVar, Tuple
from pathlib import Path
from pydantic import BaseModel
from app.db.snowflake import execute_query
import logging
from app.models.schemas import PaginatedResponse, PaginationParams, Offre
from app.models.search_schemas import OffreSearchParams, FilterOperator
from math import ceil
from app.utils.exceptions import DatabaseException, ValidationException

logger = logging.getLogger(__name__)

# Répertoire racine des fichiers SQL
SQL_DIR = Path(__file__).parents[2] / "sql"

# Configuration de l'environnement Jinja2
template_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(str(SQL_DIR)),
    autoescape=jinja2.select_autoescape(["sql"]),
    trim_blocks=True,
    lstrip_blocks=True,
)

T = TypeVar("T", bound=BaseModel)


def load_query(query_path: str) -> jinja2.Template:
    """Charge une requête SQL à partir d'un fichier"""
    try:
        return template_env.get_template(query_path)
    except jinja2.exceptions.TemplateNotFound:
        logger.error(f"Le fichier de requête '{query_path}' n'a pas été trouvé")
        raise DatabaseException(
            message=f"Le fichier de requête '{query_path}' n'a pas été trouvé",
            details={"query_path": query_path},
        )


def render_query(query_path: str, template_params: Dict[str, Any] = None) -> str:
    """
    Charge et rend une requête SQL avec les paramètres de template Jinja

    Note: Cette fonction remplace uniquement les paramètres Jinja (comme {% if ... %} et {{ ... }}),
    pas les paramètres bindés Snowflake (comme :param_name).
    """
    template = load_query(query_path)
    logger.info(f"=== Rendu du template {query_path} ===")
    logger.info(f"Paramètres du template: {template_params}")

    rendered_query = template.render(**(template_params or {}))
    logger.info(f"Requête après rendu du template:")
    logger.info(rendered_query)
    return rendered_query


async def execute_sql_file(
    query_path: str,
    query_params: Dict[str, Any] = None,
    template_params: Dict[str, Any] = None,
) -> List[Dict[str, Any]]:
    """
    Exécute une requête SQL à partir d'un fichier

    Args:
        query_path: Chemin vers le fichier SQL relatif au dossier sql/
        query_params: Paramètres bindés pour la requête SQL (comme :customer_id)
        template_params: Paramètres pour le rendu du template Jinja (conditionnels, etc.)
    """
    logger.info(f"=== Début de l'exécution de {query_path} ===")
    logger.info(f"Template params: {template_params}")
    logger.info(f"Query params: {query_params}")

    params = query_params if query_params is not None else {}

    try:
        query = render_query(query_path, template_params)
        logger.info("=== Requête finale à exécuter ===")
        logger.info(query)
        logger.info(f"Avec les paramètres bindés: {params}")

        results = await execute_query(query, params)
        logger.info(f"Requête exécutée avec succès, {len(results)} résultats obtenus")
        return results
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution de la requête: {str(e)}")
        logger.error("État des paramètres au moment de l'erreur:")
        logger.error(f"Template params: {template_params}")
        logger.error(f"Query params: {params}")
        raise DatabaseException(
            message=f"Erreur lors de l'exécution de la requête: {str(e)}",
            details={
                "query_path": query_path,
                "template_params": template_params,
                "query_params": params,
            },
        )


async def execute_and_map_to_model(
    query_path: str,
    model_class: Type[T],
    query_params: Dict[str, Any] = None,
    template_params: Dict[str, Any] = None,
) -> List[T]:
    """
    Exécute une requête SQL et mappe les résultats à une classe de modèle Pydantic
    """
    try:
        params = query_params if query_params is not None else {}
        results = await execute_sql_file(query_path, params, template_params)

        try:
            return [model_class.model_validate(row) for row in results]
        except Exception as e:
            raise ValidationException(
                message=f"Erreur lors de la validation des données: {str(e)}",
                details={"model_class": model_class.__name__, "results": results},
            )
    except DatabaseException:
        raise
    except Exception as e:
        raise DatabaseException(
            message=f"Erreur lors de l'exécution et du mapping de la requête: {str(e)}",
            details={
                "query_path": query_path,
                "model_class": model_class.__name__,
                "query_params": query_params,
                "template_params": template_params,
            },
        )


async def paginate_query(
    query_path: str,
    model_class: Type[T],
    pagination: PaginationParams,
    template_params: Dict[str, Any] = None,
    query_params: Dict[str, Any] = None,
) -> Tuple[List[T], int]:
    """
    Exécute une requête SQL paginée et mappe les résultats à une classe de modèle Pydantic

    Retourne:
        - La liste des éléments pour la page demandée
        - Le nombre total d'éléments
    """
    try:
        logger.info("=== Début de paginate_query ===")
        logger.info(f"Query path: {query_path}")
        logger.info(f"Model class: {model_class}")
        logger.info(f"Pagination: {pagination}")

        params = query_params if query_params is not None else {}
        offset = (pagination.page - 1) * pagination.page_size

        template_params_with_pagination = {
            **(template_params or {}),
            "with_pagination": True,
        }

        query_params_with_pagination = {
            **params,
            "page_size": pagination.page_size,
            "offset": offset,
        }

        items = await execute_and_map_to_model(
            query_path,
            model_class,
            query_params=query_params_with_pagination,
            template_params=template_params_with_pagination,
        )

        count_query_path = query_path.rsplit(".", 1)[0] + "_count.sql"
        try:
            count_result = await execute_sql_file(
                count_query_path, params, template_params
            )
            total = count_result[0].get("total", 0) if count_result else 0
        except Exception as e:
            raise DatabaseException(
                message=f"Erreur lors du comptage des résultats: {str(e)}",
                details={"count_query_path": count_query_path, "params": params},
            )

        return items, total
    except (DatabaseException, ValidationException):
        raise
    except Exception as e:
        raise DatabaseException(
            message=f"Erreur lors de la pagination: {str(e)}",
            details={
                "query_path": query_path,
                "model_class": model_class.__name__,
                "pagination": pagination.model_dump(),
            },
        )


def create_paginated_response(
    items: List[T], total: int, pagination: PaginationParams
) -> PaginatedResponse[T]:
    """
    Crée une réponse paginée à partir des éléments et du total
    """
    # Calculer le nombre total de pages
    pages = ceil(total / pagination.page_size) if total > 0 else 0

    return PaginatedResponse[T](
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pages,
        has_next=pagination.page < pages,
        has_prev=pagination.page > 1,
    )


def prepare_search_params(
    search_params: OffreSearchParams,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Prépare les paramètres de template et de requête pour la recherche.

    Args:
        search_params: Paramètres de recherche

    Returns:
        Tuple contenant les paramètres de template et les paramètres de requête
    """
    logger.debug("Préparation des paramètres de recherche")
    logger.debug(f"Paramètres reçus: {search_params.model_dump()}")

    # Paramètres de template
    template_params = {
        "with_pagination": True,
        "filters": search_params.filters if search_params.filters else [],
        "sort": search_params.sort if search_params.sort else [],
        "search_text": bool(search_params.search_text),
    }

    # Paramètres de requête de base
    query_params = {
        "page_size": search_params.page_size,
        "offset": (search_params.page - 1) * search_params.page_size,
    }

    # Traitement des filtres
    if search_params.filters:
        for filter in search_params.filters:
            # Validation du champ
            if not filter.field or not isinstance(filter.field, str):
                raise ValidationException(
                    message=f"Champ de filtre invalide: {filter.field}", field="field"
                )

            # Construction de la clé du paramètre
            param_key = f"{filter.field}_value"

            # Traitement selon l'opérateur
            try:
                if filter.operator == FilterOperator.LIKE:
                    query_params[param_key] = f"%{filter.value}%"
                elif filter.operator == FilterOperator.BETWEEN:
                    if not isinstance(filter.value, list) or len(filter.value) != 2:
                        raise ValidationException(
                            message="La valeur pour l'opérateur BETWEEN doit être une liste de 2 éléments",
                            field=filter.field,
                        )
                    query_params[f"{filter.field}_start"] = filter.value[0]
                    query_params[f"{filter.field}_end"] = filter.value[1]
                elif filter.operator == FilterOperator.IN:
                    if not isinstance(filter.value, (list, tuple)):
                        raise ValidationException(
                            message="La valeur pour l'opérateur IN doit être une liste",
                            field=filter.field,
                        )
                    query_params[param_key] = ",".join(map(str, filter.value))
                else:
                    # Pour les opérateurs simples (eq, neq, gt, gte, lt, lte)
                    query_params[param_key] = filter.value
            except Exception as e:
                raise ValidationException(
                    message=f"Erreur lors du traitement du filtre {filter.field}: {str(e)}",
                    field=filter.field,
                )

    # Traitement de la recherche textuelle
    if search_params.search_text:
        query_params["search_text"] = f"%{search_params.search_text}%"

    # Log des paramètres finaux
    logger.debug("Paramètres préparés:")
    logger.debug(f"Template params: {template_params}")
    logger.debug(f"Query params: {query_params}")

    return template_params, query_params


async def search_offres(search_params: OffreSearchParams) -> Tuple[List[Offre], int]:
    """
    Recherche des offres selon les critères spécifiés.

    Args:
        search_params: Paramètres de recherche

    Returns:
        Tuple contenant la liste des offres et le nombre total de résultats
    """
    try:
        logger.info("Début de la recherche d'offres")
        logger.info(f"Paramètres de recherche: {search_params.model_dump()}")

        # Préparation des paramètres
        template_params, query_params = prepare_search_params(search_params)

        # Log de la requête qui va être exécutée
        logger.info("Exécution de la requête principale")
        logger.info(f"Template params: {template_params}")
        logger.info(f"Query params: {query_params}")

        # Exécution de la requête principale
        items = await execute_and_map_to_model(
            "offres/search.sql",
            Offre,
            query_params=query_params,
            template_params=template_params,
        )

        logger.info(f"Nombre de résultats trouvés: {len(items)}")

        # Exécution de la requête de comptage
        logger.info("Exécution de la requête de comptage")
        count_result = await execute_sql_file(
            "offres/search_count.sql",
            query_params=query_params,
            template_params=template_params,
        )
        total = count_result[0].get("total", 0) if count_result else 0

        logger.info(f"Nombre total de résultats: {total}")

        return items, total

    except ValidationException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la recherche d'offres: {str(e)}", exc_info=True)
        raise DatabaseException(
            message="Erreur lors de la recherche d'offres",
            details={"search_params": search_params.model_dump(), "error": str(e)},
        )

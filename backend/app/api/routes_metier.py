from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
from app.models.schemas import (
    ResponseBase,
    QueryParams,
    PaginationParams,
    PaginatedResponseBase,
    METIER
)
from app.services.query_service import (
    execute_and_map_to_model,
    execute_sql_file,
    paginate_query,
    create_paginated_response,
    execute_query,
)
from app.utils.exceptions import (
    NotFoundException,
    ValidationException,
    DatabaseException,
)

router_metier = APIRouter()


@router_metier.get(
    "/metiers",
    response_model=PaginatedResponseBase[METIER],
    tags=["Références","Métiers"],
    summary="Récuperer la liste des metiers",
    description="""
    Récupère une liste paginés des métiers

    Paramètres de pagination:
    - **page**: Numéro de la page (commence à 1)
    - **page_size**: Nombre d'éléments par page (entre 1 et 100)

        Exemple de réponse:
    ```json
    {
        "success": true,
        "message": "Liste des métiers récupérée avec succès",
        "data": {
            "items": [
                {
                    "ID_METIER": 1,
                    "ID_APPELATION": "10438",
                    "NOM": "Agent/Agente de destruction d'insectes"
                }
            ],
            "total": 150,
            "page": 1,
            "page_size": 10,
            "pages": 15,
            "has_next": true,
            "has_prev": false
        }
    }
    ```
    """
)
async def get_all_metier(pagination: PaginationParams = Depends()):
    try:
        template_params = {}
        offset = (pagination.page - 1) * pagination.page_size
        query_params = {"page_size": pagination.page_size, "offset": offset}

        items, total = await paginate_query(
            "metiers/get_all.sql",
            METIER,
            pagination,
            template_params=template_params,
            query_params=query_params,
        )

        paginated_response = create_paginated_response(items, total, pagination)
        return PaginatedResponseBase(
            data=paginated_response, message="Liste des metiers récupérée avec succès"
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router_metier.get(
    "/metiers/{id}",
    tags=["Métiers"],
    summary="Récupérer un metier par son ID",
    description="""
    Récupère les détails d'un métier spécifique par son ID.
    
    Paramètres:
    - **id**: Identifiant unique d'un métier
    
    Exemple de réponse:
    ```json
    {
        "success": true,
        "message": "Métier récupérée avec succès",
        "data": {
                "ID_METIER": 1,
                "ID_APPELATION": "10438",
                "NOM": "Agent/Agente de destruction d'insectes"
        }
    }
    ```
    
    Codes de retour:
    - 200: Succès
    - 404: Métier non trouvée
    - 500: Erreur serveur
    """,

)
async def get_metier_by_id(id: int):
    try:
        result = await execute_and_map_to_model(
            "metiers/get_by_id.sql",
            METIER,
            query_params={"ID": id},
            template_params={"ID": True},
        )

        if not result:
            raise NotFoundException(
                message=f"Metier avec l'ID {id} non trouvée", field="id"
            )

        return ResponseBase(data=result[0], message="Metier récupérée avec succès")
    except NotFoundException as e:
        raise e
    except Exception as e:
        raise DatabaseException(
            message=f"Erreur lors de la récupération du lieu: {str(e)}",
            details={"id": id},
        )


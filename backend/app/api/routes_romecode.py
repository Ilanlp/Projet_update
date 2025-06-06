from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
from app.models.schemas import (
    ResponseBase,
    QueryParams,
    PaginationParams,
    PaginatedResponseBase,
    ROMECODE
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

router_romecode = APIRouter()


@router_romecode.get(
    "/romecodes",
    response_model=PaginatedResponseBase[ROMECODE],
    tags=["Références","Rome codes"],
    summary="Récuperer la liste des romes code",
    description="""
    Récupère une liste paginés des romes code

    Paramètres de pagination:
    - **page**: Numéro de la page (commence à 1)
    - **page_size**: Nombre d'éléments par page (entre 1 et 100)

        Exemple de réponse:
    ```json
    {
        "success": true,
        "message": "Liste des romes code récupérée avec succès",
        "data": {
            "items": [
                {
                    "ID_ROME": 1,
                    "CODE_ROME": "A1101",
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
async def get_all_romecode(pagination: PaginationParams = Depends()):
    try:
        template_params = {}
        offset = (pagination.page - 1) * pagination.page_size
        query_params = {"page_size": pagination.page_size, "offset": offset}

        items, total = await paginate_query(
            "romecodes/get_all.sql",
            ROMECODE,
            pagination,
            template_params=template_params,
            query_params=query_params,
        )

        paginated_response = create_paginated_response(items, total, pagination)
        return PaginatedResponseBase(
            data=paginated_response, message="Liste des codes rome récupérée avec succès"
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router_romecode.get(
    "/romecodes/{id}",
    tags=["Rome codes"],
    summary="Récupérer un rome code par son ID",
    description="""
    Récupère les détails d'un rome code spécifique par son ID.
    
    Paramètres:
    - **id**: Identifiant unique d'un rome code
    
    Exemple de réponse:
    ```json
    {
        "success": true,
        "message": "Rome code récupérée avec succès",
        "data": {
                "ID_ROME": 1,
                "CODE_ROME": "A1101",
        }
    }
    ```
    
    Codes de retour:
    - 200: Succès
    - 404: RomeCode non trouvée
    - 500: Erreur serveur
    """,

)
async def get_romecode_by_id(id: int):
    try:
        result = await execute_and_map_to_model(
            "romecodes/get_by_id.sql",
            ROMECODE,
            query_params={"ID": id},
            template_params={"ID": True},
        )

        if not result:
            raise NotFoundException(
                message=f"Code rome avec l'ID {id} non trouvée", field="id"
            )

        return ResponseBase(data=result[0], message="Code rome récupérée avec succès")
    except NotFoundException as e:
        raise e
    except Exception as e:
        raise DatabaseException(
            message=f"Erreur lors de la récupération du code rome: {str(e)}",
            details={"id": id},
        )


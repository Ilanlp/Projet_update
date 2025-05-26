from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
from app.models.schemas import (
    ResponseBase,
    QueryParams,
    PaginationParams,
    PaginatedResponseBase,
    Offre,
    SENIORITE
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

router_seniorite = APIRouter()


@router_seniorite.get(
    "/seniorite",
    response_model=ResponseBase[List[SENIORITE]],
    tags=["Références","Séniorites"],
    summary="Récuperer la liste des séniorites",
    description="""
    Récupère une liste des séniorités

    Exemple de réponse:
    ```json
    {
        "success": true,
        "message": "Liste des séniorités récupérée avec succès",
        "data": {
            "items": [
                {
                    "ID_SENIORITE": 1,
                    "TYPE_SENIORITE": "Junior",
                }
            ],
        }
    }
    ```
    """
)
async def get_all_seniorite():
    try:

        result = await execute_and_map_to_model(
            "seniorites/get_all.sql",
            SENIORITE,
        )

        if not result:
            raise NotFoundException(
                message=f"Aucune séniorite trouvé"
            )

        return ResponseBase(
            data=result, message="Liste des séniorites récupérée avec succès"
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router_seniorite.get(
    "/seniorite/{id}",
    tags=["Séniorites"],
    summary="Récupérer une séniorite par son ID",
    description="""
    Récupère les détails d'une séniorité spécifique par son ID.
    
    Paramètres:
    - **id**: Identifiant unique d'une séniorité
    
    Exemple de réponse:
    ```json
    {
        "success": true,
        "message": "Séniorité récupérée avec succès",
        "data": {
                "ID_SENIORITE": 1,
                "TYPE_SENIORITE": "Junior",
        }
    }
    ```
    
    Codes de retour:
    - 200: Succès
    - 404: Séniorité non trouvée
    - 500: Erreur serveur
    """,

)
async def get_seniorite_by_id(id: int):
    try:
        result = await execute_and_map_to_model(
            "seniorites/get_by_id.sql",
            SENIORITE,
            query_params={"ID": id},
            template_params={"ID": True},
        )

        if not result:
            raise NotFoundException(
                message=f"Séniorite avec l'ID {id} non trouvée", field="id"
            )

        return ResponseBase(data=result[0], message="Séniorite récupérée avec succès")
    except NotFoundException as e:
        raise e
    except Exception as e:
        raise DatabaseException(
            message=f"Erreur lors de la récupération de la séniorite: {str(e)}",
            details={"id": id},
        )


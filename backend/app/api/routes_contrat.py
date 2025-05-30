from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
from app.models.schemas import (
    ResponseBase,
    QueryParams,
    PaginationParams,
    PaginatedResponseBase,
    Offre,
    CONTRAT
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

router_contrat = APIRouter()


@router_contrat.get(
    "/contrats",
    response_model=ResponseBase[List[CONTRAT]],
    tags=["Références","Contrats"],
    summary="Récuperer la liste des contrats",
    description="""
    Récupère une liste des contrats

    Exemple de réponse:
    ```json
    {
        "success": true,
        "message": "Liste des contrats récupérée avec succès",
        "data": {
            "items": [
                {
                    "ID_CONTRAT": 1,
                    "TYPE_CONTRAT": "CDI",
                }
            ],
        }
    }
    ```
    """

)
async def get_all_contrat():
    try:

        result = await execute_and_map_to_model(
            "contrats/get_all.sql",
            CONTRAT,
        )

        if not result:
            raise NotFoundException(
                message=f"Aucun contrat trouvé"
            )

        return ResponseBase(
            data=result, message="Liste des contrats récupérée avec succès"
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router_contrat.get(
    "/contrats/{id}",
    tags=["Contrats"],
    summary="Récupérer un contrat par son ID",
    description="""
    Récupère les détails d'une contrat spécifique par son ID.
    
    Paramètres:
    - **id**: Identifiant unique d'un contrat
    
    Exemple de réponse:
    ```json
    {
        "success": true,
        "message": "Contrat récupérée avec succès",
        "data": {
                "ID_CONTRAT": 1,
                "TYPE_CONTRAT": "CDI",
        }
    }
    ```
    
    Codes de retour:
    - 200: Succès
    - 404: Contrat non trouvée
    - 500: Erreur serveur
    """,

)
async def get_contrat_by_id(id: int):
    try:
        result = await execute_and_map_to_model(
            "contrats/get_by_id.sql",
            CONTRAT,
            query_params={"ID": id},
            template_params={"ID": True},
        )

        if not result:
            raise NotFoundException(
                message=f"Contrat avec l'ID {id} non trouvée", field="id"
            )

        return ResponseBase(data=result[0], message="Contrat récupérée avec succès")
    except NotFoundException as e:
        raise e
    except Exception as e:
        raise DatabaseException(
            message=f"Erreur lors de la récupération de la contrat: {str(e)}",
            details={"id": id},
        )


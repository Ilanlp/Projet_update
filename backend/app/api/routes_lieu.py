from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
from app.models.schemas import (
    ResponseBase,
    QueryParams,
    PaginationParams,
    PaginatedResponseBase,
    Offre,
    LIEU
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

router_lieu = APIRouter()


@router_lieu.get(
    "/lieux",
    response_model=PaginatedResponseBase[LIEU],
    tags=["Références","Lieux"],
    summary="Récuperer la liste des lieux",
    description="""
    Récupère une liste paginés des lieux

    Paramètres de pagination:
    - **page**: Numéro de la page (commence à 1)
    - **page_size**: Nombre d'éléments par page (entre 1 et 100)

        Exemple de réponse:
    ```json
    {
        "success": true,
        "message": "Liste des lieux récupérée avec succès",
        "data": {
            "items": [
                {
                    "ID_LIEU": 1,
                    "CODE_POSTAL": "OFF123",
                    "VILLE": "Data Engineer Senior",
                    "DEPARTEMENT": "",
                    "REGION": "",
                    "PAYS": "",
                    "LATITUDE": "",
                    "LONGITUDE": "",
                    "POPULATION": ""
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
async def get_all_lieu(pagination: PaginationParams = Depends()):
    try:
        template_params = {}
        offset = (pagination.page - 1) * pagination.page_size
        query_params = {"page_size": pagination.page_size, "offset": offset}

        items, total = await paginate_query(
            "lieux/get_all.sql",
            LIEU,
            pagination,
            template_params=template_params,
            query_params=query_params,
        )

        paginated_response = create_paginated_response(items, total, pagination)
        return PaginatedResponseBase(
            data=paginated_response, message="Liste des lieux récupérée avec succès"
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router_lieu.get(
    "/lieux/{id}",
    tags=["Lieux"],
    summary="Récupérer un lieu par son ID",
    description="""
    Récupère les détails d'un lieu spécifique par son ID.
    
    Paramètres:
    - **id**: Identifiant unique d'un lieu
    
    Exemple de réponse:
    ```json
    {
        "success": true,
        "message": "Lieu récupérée avec succès",
        "data": {
            "ID_LIEU": 1,
            "CODE_POSTAL": "OFF123",
            "VILLE": "Data Engineer Senior",
            "DEPARTEMENT": "",
            "REGION": "",
            "PAYS": "",
            "LATITUDE": "",
            "LONGITUDE": "",
            "POPULATION": ""
        }
    }
    ```
    
    Codes de retour:
    - 200: Succès
    - 404: Lieu non trouvée
    - 500: Erreur serveur
    """,

)
async def get_lieu_by_id(id: int):
    try:
        result = await execute_and_map_to_model(
            "lieux/get_by_id.sql",
            LIEU,
            query_params={"ID": id},
            template_params={"ID": True},
        )

        if not result:
            raise NotFoundException(
                message=f"Lieu avec l'ID {id} non trouvée", field="id"
            )

        return ResponseBase(data=result[0], message="Lieu récupérée avec succès")
    except NotFoundException as e:
        raise e
    except Exception as e:
        raise DatabaseException(
            message=f"Erreur lors de la récupération du lieu: {str(e)}",
            details={"id": id},
        )


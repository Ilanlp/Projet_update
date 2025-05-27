from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
from app.models.schemas import (
    ResponseBase,
    QueryParams,
    PaginationParams,
    PaginatedResponseBase,
    Offre,
    COMPETENCE
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

router_competence = APIRouter()


@router_competence.get(
    "/competences",
    response_model=PaginatedResponseBase[COMPETENCE],
    tags=["Références","Compétences"],
    summary="Récuperer la liste des compétences",
    description="""
    Récupère une liste paginés des competences

    Paramètres de pagination:
    - **page**: Numéro de la page (commence à 1)
    - **page_size**: Nombre d'éléments par page (entre 1 et 100)

        Exemple de réponse:
    ```json
    {
        "success": true,
        "message": "Liste des compétences récupérée avec succès",
        "data": {
            "items": [
                {
                    "ID_COMPETENCE": 1,
                    "SKILL": "2D drafting",
                    "TYPE": "Design Software",
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
async def get_all_competence(pagination: PaginationParams = Depends()):
    try:
        template_params = {}
        offset = (pagination.page - 1) * pagination.page_size
        query_params = {"page_size": pagination.page_size, "offset": offset}

        items, total = await paginate_query(
            "competences/get_all.sql",
            COMPETENCE,
            pagination,
            template_params=template_params,
            query_params=query_params,
        )

        paginated_response = create_paginated_response(items, total, pagination)
        return PaginatedResponseBase(
            data=paginated_response, message="Liste des compétences récupérée avec succès"
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router_competence.get(
    "/competences/{id}",
    tags=["Compétences"],
    summary="Récupérer une compétence par son ID",
    description="""
    Récupère les détails d'une compétence d'emploi spécifique par son ID.
    
    Paramètres:
    - **id**: Identifiant unique d'une compétence
    
    Exemple de réponse:
    ```json
    {
        "success": true,
        "message": "Compétence récupérée avec succès",
        "data": {
            "ID_COMPETENCE": 1,
            "SKILL": "2D drafting",
            "TYPE": "Design Software",
        }
    }
    ```
    
    Codes de retour:
    - 200: Succès
    - 404: Compétence non trouvée
    - 500: Erreur serveur
    """,

)
async def get_competence_by_id(id: int):
    try:
        result = await execute_and_map_to_model(
            "competences/get_by_id.sql",
            COMPETENCE,
            query_params={"ID": id},
            template_params={"ID": True},
        )

        if not result:
            raise NotFoundException(
                message=f"Competence avec l'ID {id} non trouvée", field="id"
            )

        return ResponseBase(data=result[0], message="Offre récupérée avec succès")
    except NotFoundException as e:
        raise e
    except Exception as e:
        raise DatabaseException(
            message=f"Erreur lors de la récupération de la competence: {str(e)}",
            details={"id": id},
        )


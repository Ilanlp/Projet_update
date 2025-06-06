from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.models.schemas import (
    ResponseBase,
    PaginationParams,
    PaginatedResponseBase,
    DOMAINE,
)
from app.services.query_service import (
    execute_and_map_to_model,
    paginate_query,
    create_paginated_response,
)

router_domaine = APIRouter()


@router_domaine.get("/domaines", response_model=ResponseBase[List[DOMAINE]], tags=["Références"])
async def get_domaines():
    """
    Récupère la liste des domaines
    """
    try:
        result = await execute_and_map_to_model(
            "domaines/get_all.sql", DOMAINE, query_params={}
        )

        if not result:
            return ResponseBase(
                data=[],
                message="Aucun domaine trouvé"
            )

        return ResponseBase(
            data=result,
            message="Liste des domaines récupérée avec succès"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

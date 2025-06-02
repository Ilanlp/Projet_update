from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.models.schemas import (
    ResponseBase,
    PaginationParams,
    PaginatedResponseBase,
    TELETRAVAIL
)
from app.services.query_service import (
    execute_and_map_to_model,
    paginate_query,
    create_paginated_response,
)

router_teletravail = APIRouter()


@router_teletravail.get("/teletravail", response_model=ResponseBase[List[TELETRAVAIL]], tags=["Références"])
async def get_teletravail():
    """
    Récupère la liste des types de télétravail
    """
    try:
        result = await execute_and_map_to_model(
            "teletravail/get_all.sql", TELETRAVAIL, query_params={}
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

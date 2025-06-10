from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.models.schemas import (
    ResponseBase,
    PaginationParams,
    PaginatedResponseBase,
    TOP_VILLE,
    TOP_REGION
)
from app.services.query_service import (
    execute_and_map_to_model,
    paginate_query,
    create_paginated_response,
)

router_olap = APIRouter()


@router_olap.get("/top_ville", response_model=ResponseBase[List[TOP_VILLE]], tags=["OLAP"])
async def get_top_ville():
    """
    Récupère les 5 villes les plus demandées
    """
    try:


        # Exécution de la requête pour les soft skills
        results = await execute_and_map_to_model(
            "OLAP/top_ville.sql",
            TOP_VILLE,
            query_params={}
        )

        if not results:
            return ResponseBase(
                data=[],
                message=f"Aucune ville trouvée"
            )

        return ResponseBase(
            data=results,
            message=f"Villes récupérées avec succès"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router_olap.get("/top_region", response_model=ResponseBase[List[TOP_REGION]], tags=["OLAP"])
async def get_top_region():
    """
    Récupère les 5 régions les plus demandées
    """
    try:
        results = await execute_and_map_to_model(
            "OLAP/top_region.sql",
            TOP_REGION,
            query_params={}
            )

        if not results:
            return ResponseBase(
                data=[],
                message=f"Aucune région trouvée"
            )

        return ResponseBase(
            data=results,
            message=f"Régions récupérées avec succès"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

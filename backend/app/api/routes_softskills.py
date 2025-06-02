from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.models.schemas import (
    ResponseBase,
    PaginationParams,
    PaginatedResponseBase,
    SOFTSKILL
)
from app.services.query_service import (
    execute_and_map_to_model,
    paginate_query,
    create_paginated_response,
)

router_softskills = APIRouter()


@router_softskills.get("/softskills", response_model=PaginatedResponseBase[SOFTSKILL], tags=["Références"])
async def get_all_softskills(pagination: PaginationParams = Depends()):
    """
    Récupère la liste des soft skills avec pagination

    - **page**: Numéro de page (commençant à 1)
    - **page_size**: Nombre d'éléments par page (entre 1 et 100)
    """
    try:
        # Calcul de l'offset pour la pagination
        offset = (pagination.page - 1) * pagination.page_size

        # Paramètres pour la requête SQL incluant la pagination
        query_params = {"page_size": pagination.page_size, "offset": offset}

        # Exécuter la requête paginée
        items, total = await paginate_query(
            "softskills/get_all.sql",
            SOFTSKILL,
            pagination,
            query_params=query_params
        )

        # Créer la réponse paginée
        paginated_response = create_paginated_response(items, total, pagination)

        return PaginatedResponseBase(
            data=paginated_response,
            message="Liste des soft skills récupérée avec succès"
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router_softskills.get("/rome_softskills/{code_rome}", response_model=ResponseBase[List[SOFTSKILL]], tags=["Références"])
async def get_softskills_by_rome(code_rome: str):
    """
    Récupère les soft skills associés à un code ROME

    - **code_rome**: Le code ROME pour lequel on veut obtenir les soft skills (ex: 'A1101')
    """
    try:
        # Validation basique du format du code ROME (5 caractères)
        if not code_rome or len(code_rome) != 5:
            raise HTTPException(
                status_code=400,
                detail="Le code ROME doit être composé de 5 caractères"
            )

        # Exécution de la requête pour les soft skills
        results = await execute_and_map_to_model(
            "softskills/get_by_rome.sql",
            SOFTSKILL,
            query_params={"code_rome": code_rome}
        )

        if not results:
            return ResponseBase(
                data=[],
                message=f"Aucun soft skill trouvé pour le code ROME {code_rome}"
            )

        return ResponseBase(
            data=results,
            message=f"Soft skills récupérés avec succès pour le code ROME {code_rome}"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

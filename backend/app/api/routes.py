from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
from app.models.schemas import (
    ResponseBase,
    QueryParams,
    PaginationParams,
    PaginatedResponseBase,
    Offre,
)
from app.services.query_service import (
    execute_and_map_to_model,
    execute_sql_file,
    paginate_query,
    create_paginated_response,
)

router = APIRouter()


@router.get("/offres", response_model=PaginatedResponseBase[Offre], tags=["Relationnels"])
async def get_offres(pagination: PaginationParams = Depends()):
    """
    Récupère les offres avec pagination

    - **page**: Numéro de page (commençant à 1)
    - **page_size**: Nombre d'éléments par page (entre 1 et 100)
    """
    try:
        # Paramètres pour le template Jinja
        template_params = {}

        # Calcul de l'offset pour la pagination
        offset = (pagination.page - 1) * pagination.page_size

        # Paramètres pour la requête SQL incluant la pagination
        query_params = {"page_size": pagination.page_size, "offset": offset}

        # Exécuter la requête paginée
        items, total = paginate_query(
            "offres/get_all.sql",
            Offre,
            pagination,
            template_params=template_params,
            query_params=query_params,
        )

        # Créer la réponse paginée
        paginated_response = create_paginated_response(items, total, pagination)

        return PaginatedResponseBase(
            data=paginated_response, message="Liste des offres récupérée avec succès"
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/offres/{offre_id}", response_model=ResponseBase[Offre], tags=["Relationnels"])
async def get_offre(offre_id: int):
    """
    Récupère une offre par son ID

    - **offre_id**: ID de l'offre à récupérer
    """
    try:
        result = await execute_and_map_to_model(
            "offres/get_by_id.sql", Offre, {"id": offre_id}
        )

        if not result:
            raise HTTPException(status_code=404, detail="Offre non trouvée")

        return ResponseBase(data=result[0], message="Offre récupérée avec succès")
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/offres", response_model=ResponseBase[Offre], tags=["Relationnels"])
async def create_offre(offre: Offre):
    """
    Crée une nouvelle offre

    - **offre**: Les données de l'offre à créer
    """
    try:
        # Convertir le modèle Pydantic en dictionnaire avec les alias
        offre_dict = offre.model_dump(by_alias=True)

        # Supprimer l'ID car il sera généré par la base de données
        offre_dict.pop("ID_LOCAL", None)

        result = await execute_and_map_to_model("offres/create.sql", Offre, offre_dict)

        if not result:
            raise HTTPException(
                status_code=500, detail="Erreur lors de la création de l'offre"
            )

        return ResponseBase(data=result[0], message="Offre créée avec succès")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/offres/{offre_id}", response_model=ResponseBase[Offre], tags=["Relationnels"])
async def update_offre(offre_id: int, offre: Offre):
    """
    Met à jour une offre existante

    - **offre_id**: ID de l'offre à mettre à jour
    - **offre**: Les nouvelles données de l'offre
    """
    try:
        # Vérifier si l'offre existe
        existing_offre = await execute_and_map_to_model(
            "offres/get_by_id.sql", Offre, {"id": offre_id}
        )

        if not existing_offre:
            raise HTTPException(status_code=404, detail="Offre non trouvée")

        # Convertir le modèle Pydantic en dictionnaire avec les alias
        offre_dict = offre.model_dump(by_alias=True)
        offre_dict["id"] = offre_id

        result = await execute_and_map_to_model("offres/update.sql", Offre, offre_dict)

        return ResponseBase(data=result[0], message="Offre mise à jour avec succès")
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/offres/{offre_id}", response_model=ResponseBase[Dict[str, Any]], tags=["Relationnels"])
async def delete_offre(offre_id: int):
    """
    Supprime une offre

    - **offre_id**: ID de l'offre à supprimer
    """
    try:
        # Vérifier si l'offre existe
        existing_offre = await execute_and_map_to_model(
            "offres/get_by_id.sql", Offre, {"id": offre_id}
        )

        if not existing_offre:
            raise HTTPException(status_code=404, detail="Offre non trouvée")

        result = await execute_sql_file("offres/delete.sql", {"id": offre_id})

        if not result:
            raise HTTPException(
                status_code=500, detail="Erreur lors de la suppression de l'offre"
            )

        return ResponseBase(
            data={"id": offre_id}, message="Offre supprimée avec succès"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
from app.models.schemas import (
    ResponseBase,
    QueryParams,
    PaginationParams,
    PaginatedResponseBase,
    Offre,
    SOFTSKILL,
    ROMECODE,
)
from app.services.query_service import (
    execute_and_map_to_model,
    execute_sql_file,
    paginate_query,
    create_paginated_response,
)

router2 = APIRouter()


@router2.get(
    "/offres", response_model=PaginatedResponseBase[Offre], tags=["Relationnels"]
)
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
        items, total = await paginate_query(
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


@router2.get("/offres/{id}", response_model=ResponseBase[Offre], tags=["Relationnels"])
async def get_offre(id: int):
    """
    Récupère une offre par son ID

    - **id**: ID de l'offre à récupérer
    """
    try:
        result = await execute_and_map_to_model(
            "offres/get_by_id.sql", Offre, query_params={"id": id}
        )

        if not result:
            raise HTTPException(status_code=404, detail="Offre non trouvée")

        return ResponseBase(data=result[0], message="Offre récupérée avec succès")
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router2.post("/offres", response_model=ResponseBase[Offre], tags=["Relationnels"])
async def create_offre(offre: Offre):
    """
    Crée une nouvelle offre

    - **offre**: Les données de l'offre à créer
    """
    try:
        # Convertir le modèle Pydantic en dictionnaire avec les alias
        offre_dict = offre.model_dump(by_alias=True)    

        # Supprimer l'ID car il sera généré par la base de données
        offre_dict.pop("ID", None)

        result = await execute_and_map_to_model(
            "offres/create.sql", Offre, query_params=offre_dict
        )

        if not result:
            raise HTTPException(
                status_code=500, detail="Erreur lors de la création de l'offre"
            )

        return ResponseBase(data=result[0], message="Offre créée avec succès")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router2.put("/offres/{id}", response_model=ResponseBase[Offre], tags=["Relationnels"])
async def update_offre(id: int, offre: Offre):
    """
    Met à jour une offre existante

    - **id**: ID de l'offre à mettre à jour
    - **offre**: Les nouvelles données de l'offre
    """
    try:
        # Vérifier si l'offre existe
        existing_offre = await execute_and_map_to_model(
            "offres/get_by_id.sql", Offre, query_params={"id": id}
        )

        if not existing_offre:
            raise HTTPException(status_code=404, detail="Offre non trouvée")

        # Convertir le modèle Pydantic en dictionnaire avec les alias
        offre_dict = offre.model_dump(by_alias=True)
        offre_dict["ID"] = id

        result = await execute_and_map_to_model(
            "offres/update.sql", Offre, query_params=offre_dict
        )

        return ResponseBase(data=result[0], message="Offre mise à jour avec succès")
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router2.delete(
    "/offres/{id}", response_model=ResponseBase[Dict[str, Any]], tags=["Relationnels"]
)
async def delete_offre(id: int):
    """
    Supprime une offre

    - **id**: ID de l'offre à supprimer
    """
    try:
        # Vérifier si l'offre existe
        existing_offre = await execute_and_map_to_model(
            "offres/get_by_id.sql", Offre, query_params={"id": id}
        )

        if not existing_offre:
            raise HTTPException(status_code=404, detail="Offre non trouvée")

        # Exécuter la suppression
        await execute_sql_file("offres/delete.sql", query_params={"id": id})

        return ResponseBase(data={"id": id}, message="Offre supprimée avec succès")
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router2.get("/rome_softskills/{code_rome}", response_model=ResponseBase[List[SOFTSKILL]], tags=["Références"])
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

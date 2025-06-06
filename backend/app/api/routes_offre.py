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
    execute_query,
    search_offres,
)
from app.utils.exceptions import (
    NotFoundException,
    ValidationException,
    DatabaseException,
)
from app.models.search_schemas import OffreSearchParams

router_offre = APIRouter()


@router_offre.get(
    "/offres/filters",
    response_model=PaginatedResponseBase[Offre],
    tags=["Offres d'emploi"],
    summary="Récupérer la liste des offres d'emploi en fonction des filtres",
    description="""
    Récupère une liste paginée des offres d'emploi en fonction des filtres.
    """
)
async def get_offre_filtered(filters: Annotated[SearchOffre, Query()],pagination: PaginationParams = Depends()):

    try:
        template_params = {}
        offset = (pagination.page - 1) * pagination.page_size
        query_params = {
            "page_size": pagination.page_size,
            "offset": offset,
            "SEARCH": filters.search,
            "LOCATION": filters.location,
            "TYPE_CONTRAT": filters.type_contrat,
            "TYPE_SENIORITE": filters.type_seniorite,
            "NOM_DOMAINE": filters.nom_domaine
        }

        items, total = await paginate_query(
            "offres/get_by_filter.sql",
            Offre,
            pagination,
            query_params=query_params,
            template_params={
                "SEARCH": True,
                "TITLE": True, 
                "TYPE_CONTRAT":True,
                "TYPE_SENIORITE": True,
                "NOM_DOMAINE": True
            },
        )

        paginated_response = create_paginated_response(items, total, pagination)
        return PaginatedResponseBase(
            data=paginated_response, message="Liste des offres récupérée avec succès"
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router_offre.get(
    "/offres",
    response_model=PaginatedResponseBase[Offre],
    tags=["Offres d'emploi"],
    summary="Récupérer la liste des offres d'emploi",
    description="""
    Récupère une liste paginée des offres d'emploi.
    
    Les résultats sont triés par date de création décroissante.
    
    Paramètres de pagination:
    - **page**: Numéro de la page (commence à 1)
    - **page_size**: Nombre d'éléments par page (entre 1 et 100)
    
    Exemple de réponse:
    ```json
    {
        "success": true,
        "message": "Liste des offres récupérée avec succès",
        "data": {
            "items": [
                {
                    "ID": 1,
                    "ID_LOCAL": "OFF123",
                    "TITLE": "Data Engineer Senior",
                    "DESCRIPTION": "Nous recherchons un Data Engineer expérimenté...",
                    "TYPE_CONTRAT": "CDI",
                    "CODE_DOMAINE": "INFO",
                    "NOM_DOMAINE": "Informatique",
                    "CODE_POSTAL": 75001,
                    "VILLE": "Paris",
                    "DEPARTEMENT": "Paris",
                    "REGION": "Île-de-France",
                    "PAYS": "France",
                    "LATITUDE": 48.8566,
                    "LONGITUDE": 2.3522,
                    "POPULATION": 2148271,
                    "TYPE_TELETRAVAIL": "Hybride",
                    "TYPE_SENIORITE": "Senior",
                    "CODE_ROME": "M1805",
                    "NOM_ENTREPRISE": "Tech Company",
                    "CATEGORIE_ENTREPRISE": "Grande Entreprise",
                    "COMPETENCES": "Python, SQL, AWS",
                    "NOM_METIER": "Data Engineer"
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
    """,
)
async def get_offres(pagination: PaginationParams = Depends()):
    try:
        template_params = {}
        offset = (pagination.page - 1) * pagination.page_size
        query_params = {"page_size": pagination.page_size, "offset": offset}

        items, total = await paginate_query(
            "offres/get_all.sql",
            Offre,
            pagination,
            template_params=template_params,
            query_params=query_params,
        )

        paginated_response = create_paginated_response(items, total, pagination)
        return PaginatedResponseBase(
            data=paginated_response, message="Liste des offres récupérée avec succès"
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router_offre.get(
    "/offres/{id}",
    response_model=ResponseBase[Offre],
    tags=["Offres d'emploi"],
    summary="Récupérer une offre d'emploi par son ID",
    description="""
    Récupère les détails d'une offre d'emploi spécifique par son ID.
    
    Paramètres:
    - **id**: Identifiant unique de l'offre
    
    Exemple de réponse:
    ```json
    {
        "success": true,
        "message": "Offre récupérée avec succès",
        "data": {
            "ID": 1,
            "ID_LOCAL": "OFF123",
            "TITLE": "Data Engineer Senior",
            "DESCRIPTION": "Nous recherchons un Data Engineer expérimenté pour rejoindre notre équipe...",
            "TYPE_CONTRAT": "CDI",
            "CODE_DOMAINE": "INFO",
            "NOM_DOMAINE": "Informatique",
            "CODE_POSTAL": 75001,
            "VILLE": "Paris",
            "DEPARTEMENT": "Paris",
            "REGION": "Île-de-France",
            "PAYS": "France",
            "LATITUDE": 48.8566,
            "LONGITUDE": 2.3522,
            "POPULATION": 2148271,
            "MOIS_CREATION": 5,
            "JOUR_CREATION": 22,
            "MOIS_NOM_CREATION": "Mai",
            "JOUR_SEMAINE_CREATION": "Lundi",
            "WEEK_END_CREATION": false,
            "TYPE_TELETRAVAIL": "Hybride",
            "TYPE_SENIORITE": "Senior",
            "CODE_ROME": "M1805",
            "NOM_ENTREPRISE": "Tech Company",
            "CATEGORIE_ENTREPRISE": "Grande Entreprise",
            "DATE_CREATION_ENTREPRISE": "2010-01-01",
            "COMPETENCES": "Python, SQL, AWS, Spark, Hadoop",
            "TYPES_COMPETENCES": "Technique",
            "SOFTSKILLS_SUMMARY": "Leadership, Communication",
            "SOFTSKILLS_DETAILS": "Capacité à travailler en équipe, Excellent communicant",
            "NOM_METIER": "Data Engineer"
        }
    }
    ```
    
    Codes de retour:
    - 200: Succès
    - 404: Offre non trouvée
    - 500: Erreur serveur
    """,
)
async def get_offre(id: int):
    try:
        result = await execute_and_map_to_model(
            "offres/get_by_id.sql",
            Offre,
            query_params={"ID": id},
            template_params={"ID": True},
        )

        if not result:
            raise NotFoundException(
                message=f"Offre avec l'ID {id} non trouvée", field="id"
            )

        return ResponseBase(data=result[0], message="Offre récupérée avec succès")
    except NotFoundException as e:
        raise e
    except Exception as e:
        raise DatabaseException(
            message=f"Erreur lors de la récupération de l'offre: {str(e)}",
            details={"id": id},
        )


@router_offre.post(
    "/offres",
    response_model=ResponseBase[Offre],
    tags=["Offres d'emploi"],
    summary="Créer une nouvelle offre d'emploi",
    description="""
    Crée une nouvelle offre d'emploi dans la base de données.
    
    Corps de la requête:
    ```json
    {
        "ID_LOCAL": "OFF123",
        "TITLE": "Data Engineer Senior",
        "DESCRIPTION": "Nous recherchons un Data Engineer expérimenté...",
        "TYPE_CONTRAT": "CDI",
        "CODE_DOMAINE": "M13",
        "NOM_DOMAINE": "Informatique",
        "CODE_POSTAL": 75001,
        "VILLE": "Paris",
        "DEPARTEMENT": "Paris",
        "REGION": "Île-de-France",
        "PAYS": "France",
        "LATITUDE": 48.8566,
        "LONGITUDE": 2.3522,
        "POPULATION": 2148271,
        "TYPE_TELETRAVAIL": "Hybride",
        "TYPE_SENIORITE": "Senior",
        "CODE_ROME": "M1805",
        "NOM_ENTREPRISE": "Tech Company",
        "CATEGORIE_ENTREPRISE": "Grande Entreprise",
        "COMPETENCES": "Python, SQL, AWS",
        "TYPES_COMPETENCES": "Technique",
        "SOFTSKILLS_SUMMARY": "Leadership, Communication",
        "SOFTSKILLS_DETAILS": "Capacité à travailler en équipe, Excellent communicant",
        "NOM_METIER": "Data Engineer"
    }
    ```
    
    Notes:
    - L'ID est généré automatiquement
    - Les champs de dates sont automatiquement remplis
    
    Codes de retour:
    - 201: Offre créée avec succès
    - 400: Données invalides
    - 500: Erreur serveur
    """,
    status_code=201,
)
async def create_offre(offre: Offre):
    try:
        offre_dict = offre.model_dump(by_alias=True)
        offre_dict.pop("ID", None)

        insert_result = await execute_sql_file(
            "offres/create.sql", query_params=offre_dict
        )

        if not insert_result or insert_result[0].get("number of rows inserted", 0) != 1:
            raise DatabaseException(
                message="Erreur lors de la création de l'offre",
                details={"offre": offre_dict},
            )

        result = await execute_and_map_to_model(
            "offres/get_by_id.sql",
            Offre,
            query_params={"ID_LOCAL": offre_dict["ID_LOCAL"]},
            template_params={"ID_LOCAL": True},
        )

        if not result:
            raise DatabaseException(
                message="Erreur lors de la récupération de l'offre créée",
                details={"id_local": offre_dict["ID_LOCAL"]},
            )

        return ResponseBase(data=result[0], message="Offre créée avec succès")
    except ValidationException as e:
        raise e
    except Exception as e:
        raise DatabaseException(
            message=f"Erreur lors de la création de l'offre: {str(e)}",
            details={"offre": offre_dict},
        )


@router_offre.put(
    "/offres/{id}",
    response_model=ResponseBase[Offre],
    tags=["Offres d'emploi"],
    summary="Mettre à jour une offre d'emploi",
    description="""
    Met à jour une offre d'emploi existante.
    
    Paramètres:
    - **id**: Identifiant unique de l'offre à mettre à jour
    
    Corps de la requête:
    ```json
    {
        "TITLE": "Data Engineer Senior (Mise à jour)",
        "DESCRIPTION": "Description mise à jour...",
        "TYPE_CONTRAT": "CDI",
        "VILLE": "Paris",
        "DEPARTEMENT": "Paris",
        "REGION": "Île-de-France",
        "PAYS": "France",
        "TYPE_TELETRAVAIL": "Full Remote",
        "TYPE_SENIORITE": "Senior",
        "CODE_ROME": "M1805",
        "COMPETENCES": "Python, SQL, AWS, Kafka",
        "NOM_METIER": "Data Engineer"
    }
    ```
    
    Notes:
    - Seuls les champs fournis seront mis à jour
    - Les dates de modification sont automatiquement mises à jour
    
    Codes de retour:
    - 200: Mise à jour réussie
    - 404: Offre non trouvée
    - 400: Données invalides
    - 500: Erreur serveur
    """,
)
async def update_offre(id: int, offre: Offre):
    try:
        existing_offre = await execute_and_map_to_model(
            "offres/get_by_id.sql",
            Offre,
            query_params={"ID": id},
            template_params={"ID": True},
        )

        if not existing_offre:
            raise NotFoundException(
                message=f"Offre avec l'ID {id} non trouvée", field="id"
            )

        offre_dict = offre.model_dump(by_alias=True)
        offre_dict["ID"] = id

        result = await execute_and_map_to_model(
            "offres/update.sql", Offre, query_params=offre_dict
        )

        return ResponseBase(data=result[0], message="Offre mise à jour avec succès")
    except NotFoundException as e:
        raise e
    except ValidationException as e:
        raise e
    except Exception as e:
        raise DatabaseException(
            message=f"Erreur lors de la mise à jour de l'offre: {str(e)}",
            details={"id": id, "offre": offre_dict},
        )


@router_offre.patch(
    "/offres/{id}",
    response_model=ResponseBase[Offre],
    tags=["Offres d'emploi"],
    summary="Mettre à jour partiellement une offre d'emploi",
    description="""
    Met à jour partiellement une offre d'emploi existante.
    
    Paramètres:
    - **id**: Identifiant unique de l'offre à mettre à jour
    
    Corps de la requête:
    ```json
    {
        "TITLE": "Nouveau titre",
        "DESCRIPTION": "Nouvelle description"
    }
    ```
    
    Notes:
    - Seuls les champs fournis seront mis à jour
    - Les autres champs conserveront leurs valeurs actuelles
    - Les dates de modification sont automatiquement mises à jour
    
    Codes de retour:
    - 200: Mise à jour réussie
    - 404: Offre non trouvée
    - 400: Données invalides
    - 500: Erreur serveur
    """,
)
async def patch_offre(id: int, offre_update: Dict[str, Any]):
    try:
        # Vérifier si l'offre existe
        existing_offre = await execute_and_map_to_model(
            "offres/get_by_id.sql",
            Offre,
            query_params={"ID": id},
            template_params={"ID": True},
        )

        if not existing_offre:
            raise NotFoundException(
                message=f"Offre avec l'ID {id} non trouvée", field="id"
            )

        # Convertir l'offre existante en dictionnaire
        existing_dict = existing_offre[0].model_dump(by_alias=True)

        # Filtrer les champs None de offre_update
        filtered_update = {k: v for k, v in offre_update.items() if v is not None}

        # Mettre à jour uniquement les champs fournis
        update_dict = {**existing_dict, **filtered_update, "ID": id}

        # Valider les données avec le modèle Offre
        validated_offre = Offre.model_validate(update_dict)
        update_params = validated_offre.model_dump(by_alias=True)

        # Construire la requête de mise à jour dynamiquement
        update_fields = [f"{k.lower()} = :{k}" for k in filtered_update.keys()]
        update_query = f"""
            UPDATE ONE_BIG_TABLE
            SET {', '.join(update_fields)}
            WHERE id = :ID
        """

        # Exécuter la mise à jour avec seulement les champs modifiés
        await execute_query(
            update_query,
            {**{k: update_params[k] for k in filtered_update.keys()}, "ID": id},
        )

        # Récupérer l'offre mise à jour
        updated_offre = await execute_and_map_to_model(
            "offres/get_by_id.sql",
            Offre,
            query_params={"ID": id},
            template_params={"ID": True},
        )

        return ResponseBase(
            data=updated_offre[0], message="Offre mise à jour partiellement avec succès"
        )
    except NotFoundException as e:
        raise e
    except ValidationException as e:
        raise e
    except Exception as e:
        raise DatabaseException(
            message=f"Erreur lors de la mise à jour partielle de l'offre: {str(e)}",
            details={"id": id, "update_data": offre_update},
        )


@router_offre.delete(
    "/offres/{id}",
    response_model=ResponseBase[Dict[str, Any]],
    tags=["Offres d'emploi"],
    summary="Supprimer une offre d'emploi",
    description="""
    Supprime une offre d'emploi de la base de données.
    
    Paramètres:
    - **id**: Identifiant unique de l'offre à supprimer
    
    Exemple de réponse:
    ```json
    {
        "success": true,
        "message": "Offre supprimée avec succès",
        "data": {
            "ID": 1
        }
    }
    ```
    
    Codes de retour:
    - 200: Suppression réussie
    - 404: Offre non trouvée
    - 500: Erreur serveur
    """,
)
async def delete_offre(id: int):
    try:
        existing_offre = await execute_and_map_to_model(
            "offres/get_by_id.sql",
            Offre,
            query_params={"ID": id},
            template_params={"ID": True},
        )

        if not existing_offre:
            raise NotFoundException(
                message=f"Offre avec l'ID {id} non trouvée", field="id"
            )

        await execute_sql_file("offres/delete.sql", query_params={"ID": id})

        return ResponseBase(data={"ID": id}, message="Offre supprimée avec succès")
    except NotFoundException as e:
        raise e
    except Exception as e:
        raise DatabaseException(
            message=f"Erreur lors de la suppression de l'offre: {str(e)}",
            details={"id": id},
        )


@router_offre.post(
    "/offres/search",
    response_model=PaginatedResponseBase[Offre],
    tags=["Offres d'emploi"],
    summary="Recherche avancée d'offres d'emploi",
    description="""
    Effectue une recherche avancée d'offres d'emploi avec filtres, tri et pagination.
    
    Exemple de requête:
    ```json
    {
        "filters": [
            {
                "field": "type_contrat",
                "operator": "eq",
                "value": "CDI"
            },
            {
                "field": "ville",
                "operator": "like",
                "value": "Paris"
            },
            {
                "field": "salaire",
                "operator": "between",
                "value": [35000, 45000]
            }
        ],
        "sort": [
            {
                "field": "date_creation",
                "order": "desc"
            }
        ],
        "search_text": "data engineer python",
        "page": 1,
        "page_size": 10
    }
    ```
    
    Opérateurs disponibles:
    - eq: égal (=)
    - neq: non égal (!=)
    - gt: supérieur (>)
    - gte: supérieur ou égal (>=)
    - lt: inférieur (<)
    - lte: inférieur ou égal (<=)
    - like: recherche partielle (LIKE %value%)
    - in: dans une liste (IN)
    - between: entre deux valeurs (BETWEEN)
    
    Champs disponibles pour le tri et le filtrage:
    - id
    - title
    - description
    - type_contrat
    - ville
    - departement
    - region
    - pays
    - type_teletravail
    - type_seniorite
    - competences
    - nom_metier
    - categorie_entreprise
    """,
)
async def search_offres_route(search_params: OffreSearchParams):
    try:
        items, total = await search_offres(search_params)

        pagination = PaginationParams(
            page=search_params.page, page_size=search_params.page_size
        )

        paginated_response = create_paginated_response(items, total, pagination)

        return PaginatedResponseBase(
            data=paginated_response, message="Recherche d'offres effectuée avec succès"
        )
    except Exception as e:
        raise DatabaseException(
            message=f"Erreur lors de la recherche d'offres: {str(e)}",
            details={"search_params": search_params.model_dump()},
        )
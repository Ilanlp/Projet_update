from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
from app.models.schemas import (
    ResponseBase,
    Customer,
    Product,
    QueryParams,
    PaginationParams,
    PaginatedResponseBase,
    Order,
)
from app.services.query_service import (
    execute_and_map_to_model,
    execute_sql_file,
    paginate_query,
    create_paginated_response,
)

router = APIRouter()


@router.get("/customers", response_model=ResponseBase[List[Customer]])
async def get_customers():
    """Récupère tous les clients"""
    try:
        customers = execute_and_map_to_model("customers/get_all.sql", Customer)
        return ResponseBase(
            data=customers, message="Liste des clients récupérée avec succès"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/customers/{customer_id}", response_model=ResponseBase[Customer])
async def get_customer(customer_id: int):
    """Récupère un client par son ID"""
    try:
        # Paramètres pour le template Jinja
        template_params = {"with_email": True}

        # Paramètres pour la requête SQL (paramètres bindés)
        query_params = {"customer_id": customer_id}

        customers = execute_and_map_to_model(
            "customers/get_by_id.sql",
            Customer,
            template_params=template_params,
            query_params=query_params,
        )

        if not customers:
            raise HTTPException(
                status_code=404, detail=f"Client avec l'ID {customer_id} non trouvé"
            )

        return ResponseBase(data=customers[0], message="Client récupéré avec succès")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/products", response_model=ResponseBase[List[Product]])
async def get_products(category: Optional[str] = None):
    """Récupère tous les produits, filtré par catégorie si spécifié"""
    try:
        template_params = {"filter_by_category": category is not None}
        query_params = {"category": category} if category else {}

        products = execute_and_map_to_model(
            "products/get_all.sql",
            Product,
            template_params=template_params,
            query_params=query_params,
        )
        return ResponseBase(
            data=products, message="Liste des produits récupérée avec succès"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute_query", response_model=ResponseBase[List[Dict[str, Any]]])
async def execute_custom_query(query_path: str, params: QueryParams):
    """
    Exécute une requête SQL personnalisée à partir d'un fichier
    avec des paramètres fournis par l'utilisateur
    """
    try:
        results = execute_sql_file(query_path, params.params)
        return ResponseBase(
            data=results, message=f"Requête {query_path} exécutée avec succès"
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders", response_model=PaginatedResponseBase[Order])
async def get_orders(
    status: Optional[str] = None, pagination: PaginationParams = Depends()
):
    """
    Récupère les commandes avec pagination

    - **status**: Filtre optionnel par statut de commande
    - **page**: Numéro de page (commençant à 1)
    - **page_size**: Nombre d'éléments par page (entre 1 et 100)
    """
    try:
        # Paramètres pour le template Jinja
        template_params = {"filter_by_status": status is not None}

        # Paramètres pour la requête SQL (paramètres bindés)
        query_params = {"status": status} if status else {}

        # Exécuter la requête paginée
        items, total = paginate_query(
            "orders/get_all.sql",
            Order,
            pagination,
            template_params=template_params,
            query_params=query_params,
        )

        # Créer la réponse paginée
        paginated_response = create_paginated_response(items, total, pagination)

        return PaginatedResponseBase(
            data=paginated_response, message="Liste des commandes récupérée avec succès"
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

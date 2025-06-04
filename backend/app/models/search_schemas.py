from enum import Enum
from typing import List, Optional, Any
from pydantic import BaseModel, Field


class SortOrder(str, Enum):
    """Ordre de tri"""

    ASC = "asc"
    DESC = "desc"


class FilterOperator(str, Enum):
    """Opérateurs de filtrage disponibles"""

    EQ = "eq"  # égal (=)
    NEQ = "neq"  # non égal (!=)
    GT = "gt"  # supérieur (>)
    GTE = "gte"  # supérieur ou égal (>=)
    LT = "lt"  # inférieur (<)
    LTE = "lte"  # inférieur ou égal (<=)
    LIKE = "like"  # LIKE SQL
    IN = "in"  # IN SQL
    BETWEEN = "between"  # BETWEEN SQL


class OffreFilter(BaseModel):
    """Filtre pour les offres"""

    field: str = Field(..., description="Nom du champ à filtrer")
    operator: FilterOperator = Field(..., description="Opérateur de comparaison")
    value: Any = Field(..., description="Valeur du filtre")


class OffreSort(BaseModel):
    """Tri pour les offres"""

    field: str = Field(..., description="Nom du champ pour le tri")
    order: SortOrder = Field(
        default=SortOrder.ASC, description="Ordre de tri (asc/desc)"
    )
    def get_order_value(self) -> str:
        return self.order.value.upper()  # Convertit 'asc' en 'ASC' ou 'desc' en 'DESC'

class OffreSearchParams(BaseModel):
    """Paramètres de recherche pour les offres"""

    filters: Optional[List[OffreFilter]] = Field(
        default=None, description="Liste des filtres à appliquer"
    )
    sort: Optional[List[OffreSort]] = Field(
        default=None, description="Liste des tris à appliquer"
    )
    search_text: Optional[str] = Field(
        default=None, description="Texte de recherche global"
    )
    page: int = Field(default=1, ge=1, description="Numéro de la page (commence à 1)")
    page_size: int = Field(
        default=10, ge=1, le=100, description="Nombre d'éléments par page"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "filters": [
                        {"field": "type_contrat", "operator": "eq", "value": "CDI"},
                        {"field": "ville", "operator": "like", "value": "Paris"},
                    ],
                    "sort": [{"field": "mois_creation", "order": "desc"}],
                    "search_text": "data engineer",
                    "page": 1,
                    "page_size": 10,
                }
            ]
        }
    }

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Generic, TypeVar
from datetime import datetime

T = TypeVar("T")


class ResponseBase(BaseModel, Generic[T]):
    """Modèle de base pour les réponses API"""

    success: bool = True
    message: str = "Opération réussie"
    data: Optional[T] = None


# Nouveaux modèles pour la pagination
class PaginationParams(BaseModel):
    """Paramètres de pagination"""

    page: int = Field(default=1, ge=1, description="Numéro de page (commençant à 1)")
    page_size: int = Field(
        default=10, ge=1, le=100, description="Nombre d'éléments par page"
    )


class PaginatedResponse(BaseModel, Generic[T]):
    """Réponse paginée"""

    items: List[T]
    total: int
    page: int
    page_size: int
    pages: int
    has_next: bool
    has_prev: bool


class PaginatedResponseBase(ResponseBase[PaginatedResponse[T]]):
    """Modèle de base pour les réponses API paginées"""

    pass


class QueryParams(BaseModel):
    """Modèle pour les paramètres de requête"""

    params: Dict[str, Any] = Field(default_factory=dict)


class Order(BaseModel):
    """Exemple de modèle pour les commandes"""

    id: int
    customer_id: int
    amount: float
    status: str
    created_at: datetime

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "customer_id": 1,
                    "amount": 299.99,
                    "status": "completed",
                    "created_at": "2023-01-15T10:30:00",
                }
            ]
        }
    }


class COMPETENCE(BaseModel):
    id_competence: int
    skill: str
    type: str


class CONTRAT(BaseModel):
    id_contrat: int
    type_contrat: str


class DOMAINE(BaseModel):
    id_domaine: int
    code_domaine: str
    nom_domaine: str


class LIEU(BaseModel):
    id_lieu: int
    code_postale: str
    ville: str
    departement: str
    region: str
    pays: str
    latitude: float
    longitude: float
    population: int


class METIER(BaseModel):
    id_metier: int
    id_appelation: int
    nom: str


class ROMECODE(BaseModel):
    id_rome: int
    code_rome: str


class SENIORITE(BaseModel):
    id_seniorite: int
    type_seniorite: str


class SOFTSKILL(BaseModel):
    id_softskill: int
    summary: str
    details: str


class TELETRAVAIL(BaseModel):
    id_teletravail: int
    type_teletravail: str


class TYPE_ENTREPRISE(BaseModel):
    id_type_entreprise: int
    type_entreprise: str
    taille_min_salaries: int
    taille_max_salaries: int
    categorie_taille: str


class STOPWORDS(BaseModel):
    word: str


class CANDIDAT(BaseModel):
    id_candidat: int
    nom: str
    prenom: int
    adresse: int
    email: str
    tel: str
    id_competence: int
    id_softskill: int
    id_metier: int
    id_lieu: int
    id_contrat: int
    id_type_entreprise: int
    id_seniorite: int
    id_teletravail: int
    id_domaine: int
    salaire_min: int


class Offre(BaseModel):
    """Modèle pour les offres d'emploi"""

    id: int = Field(alias="ID")
    id_local: str = Field(alias="ID_LOCAL")
    title: str = Field(alias="TITLE")
    description: str = Field(alias="DESCRIPTION")
    type_contrat: Optional[str] = Field(alias="TYPE_CONTRAT", default=None)
    code_domaine: Optional[str] = Field(alias="CODE_DOMAINE", default=None)
    nom_domaine: Optional[str] = Field(alias="NOM_DOMAINE", default=None)
    code_postal: Optional[int] = Field(alias="CODE_POSTAL", default=None)
    ville: str = Field(alias="VILLE")
    departement: str = Field(alias="DEPARTEMENT")
    region: str = Field(alias="REGION")
    pays: str = Field(alias="PAYS")
    latitude: Optional[float] = Field(alias="LATITUDE", default=None)
    longitude: Optional[float] = Field(alias="LONGITUDE", default=None)
    population: Optional[int] = Field(alias="POPULATION", default=None)
    mois_creation: Optional[int] = Field(alias="MOIS_CREATION", default=None)
    jour_creation: Optional[int] = Field(alias="JOUR_CREATION", default=None)
    mois_nom_creation: Optional[str] = Field(alias="MOIS_NOM_CREATION", default=None)
    jour_semaine_creation: Optional[str] = Field(
        alias="JOUR_SEMAINE_CREATION", default=None
    )
    week_end_creation: Optional[bool] = Field(alias="WEEK_END_CREATION", default=None)
    mois_modification: Optional[int] = Field(alias="MOIS_MODIFICATION", default=None)
    jour_modification: Optional[int] = Field(alias="JOUR_MODIFICATION", default=None)
    mois_nom_modification: Optional[str] = Field(
        alias="MOIS_NOM_MODIFICATION", default=None
    )
    jour_semaine_modification: Optional[str] = Field(
        alias="JOUR_SEMAINE_MODIFICATION", default=None
    )
    week_end_modification: Optional[bool] = Field(
        alias="WEEK_END_MODIFICATION", default=None
    )
    type_teletravail: Optional[str] = Field(alias="TYPE_TELETRAVAIL", default=None)
    type_seniorite: Optional[str] = Field(alias="TYPE_SENIORITE", default=None)
    code_rome: str = Field(alias="CODE_ROME")
    nom_entreprise: Optional[str] = Field(alias="NOM_ENTREPRISE", default=None)
    categorie_entreprise: Optional[str] = Field(
        alias="CATEGORIE_ENTREPRISE", default=None
    )
    date_creation_entreprise: Optional[str] = Field(
        alias="DATE_CREATION_ENTREPRISE", default=None
    )
    competences: Optional[str] = Field(alias="COMPETENCES", default=None)
    types_competences: Optional[str] = Field(alias="TYPES_COMPETENCES", default=None)
    softskills_summary: Optional[str] = Field(alias="SOFTSKILLS_SUMMARY", default=None)
    softskills_details: Optional[str] = Field(alias="SOFTSKILLS_DETAILS", default=None)
    nom_metier: str = Field(alias="NOM_METIER")

    model_config = {
        "populate_by_name": True,
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "id_local": "12345",
                    "title": "Data Engineer",
                    "description": "Description du poste",
                    "ville": "Paris",
                    "departement": "Paris",
                    "region": "Île-de-France",
                    "pays": "France",
                    "code_rome": "M1805",
                    "nom_metier": "Data Engineer",
                    "mois_creation": 4,
                    "jour_creation": 28,
                    "week_end_creation": False,
                    "mois_modification": 4,
                    "jour_modification": 28,
                    "week_end_modification": False,
                }
            ]
        },
    }

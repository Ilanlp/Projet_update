from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Generic, TypeVar
from datetime import datetime
from enum import Enum


class ErrorCode(str, Enum):
    """Codes d'erreur de l'application"""

    NOT_FOUND = "NOT_FOUND"  # Ressource non trouvée
    VALIDATION_ERROR = "VALIDATION_ERROR"  # Erreur de validation des données
    DATABASE_ERROR = "DATABASE_ERROR"  # Erreur de base de données
    INTERNAL_ERROR = "INTERNAL_ERROR"  # Erreur interne du serveur
    UNAUTHORIZED = "UNAUTHORIZED"  # Non autorisé
    FORBIDDEN = "FORBIDDEN"  # Accès interdit
    BAD_REQUEST = "BAD_REQUEST"  # Requête invalide


class ErrorDetail(BaseModel):
    """Détails d'une erreur"""

    code: ErrorCode
    message: str
    field: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Réponse en cas d'erreur"""

    error: ErrorDetail


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

class LIAISON_ROME_SOFTSKILL(BaseModel):
    id_rome: int
    id_softskill: int


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

    id: Optional[int] = Field(
        alias="ID", default=None, description="Identifiant unique de l'offre"
    )
    id_local: str = Field(alias="ID_LOCAL", description="Identifiant local de l'offre")
    title: str = Field(alias="TITLE", description="Titre du poste")
    description: str = Field(
        alias="DESCRIPTION", description="Description détaillée du poste"
    )
    type_contrat: Optional[str] = Field(
        alias="TYPE_CONTRAT",
        default=None,
        description="Type de contrat (CDI, CDD, etc.)",
    )
    code_domaine: Optional[str] = Field(
        alias="CODE_DOMAINE", default=None, description="Code du domaine d'activité"
    )
    nom_domaine: Optional[str] = Field(
        alias="NOM_DOMAINE", default=None, description="Nom du domaine d'activité"
    )
    code_postal: Optional[int] = Field(
        alias="CODE_POSTAL", default=None, description="Code postal du lieu de travail"
    )
    ville: str = Field(alias="VILLE", description="Ville du poste")
    departement: str = Field(alias="DEPARTEMENT", description="Département du poste")
    region: str = Field(alias="REGION", description="Région du poste")
    pays: str = Field(alias="PAYS", description="Pays du poste")
    latitude: Optional[float] = Field(
        alias="LATITUDE",
        default=None,
        description="Latitude géographique du lieu de travail",
    )
    longitude: Optional[float] = Field(
        alias="LONGITUDE",
        default=None,
        description="Longitude géographique du lieu de travail",
    )
    population: Optional[int] = Field(
        alias="POPULATION", default=None, description="Population de la ville"
    )
    mois_creation: Optional[int] = Field(
        alias="MOIS_CREATION",
        default=None,
        description="Mois de création de l'offre (1-12)",
    )
    jour_creation: Optional[int] = Field(
        alias="JOUR_CREATION",
        default=None,
        description="Jour de création de l'offre (1-31)",
    )
    mois_nom_creation: Optional[str] = Field(
        alias="MOIS_NOM_CREATION", default=None, description="Nom du mois de création"
    )
    jour_semaine_creation: Optional[str] = Field(
        alias="JOUR_SEMAINE_CREATION",
        default=None,
        description="Jour de la semaine de création",
    )
    week_end_creation: Optional[bool] = Field(
        alias="WEEK_END_CREATION",
        default=None,
        description="Indique si l'offre a été créée pendant un weekend",
    )
    mois_modification: Optional[int] = Field(
        alias="MOIS_MODIFICATION",
        default=None,
        description="Mois de dernière modification (1-12)",
    )
    jour_modification: Optional[int] = Field(
        alias="JOUR_MODIFICATION",
        default=None,
        description="Jour de dernière modification (1-31)",
    )
    mois_nom_modification: Optional[str] = Field(
        alias="MOIS_NOM_MODIFICATION",
        default=None,
        description="Nom du mois de modification",
    )
    jour_semaine_modification: Optional[str] = Field(
        alias="JOUR_SEMAINE_MODIFICATION",
        default=None,
        description="Jour de la semaine de modification",
    )
    week_end_modification: Optional[bool] = Field(
        alias="WEEK_END_MODIFICATION",
        default=None,
        description="Indique si l'offre a été modifiée pendant un weekend",
    )
    type_teletravail: Optional[str] = Field(
        alias="TYPE_TELETRAVAIL",
        default=None,
        description="Type de télétravail proposé",
    )
    type_seniorite: Optional[str] = Field(
        alias="TYPE_SENIORITE", default=None, description="Niveau de séniorité requis"
    )
    code_rome: str = Field(alias="CODE_ROME", description="Code ROME du métier")
    nom_entreprise: Optional[str] = Field(
        alias="NOM_ENTREPRISE", default=None, description="Nom de l'entreprise"
    )
    categorie_entreprise: Optional[str] = Field(
        alias="CATEGORIE_ENTREPRISE",
        default=None,
        description="Catégorie de l'entreprise (PME, Grande entreprise, etc.)",
    )
    date_creation_entreprise: Optional[str] = Field(
        alias="DATE_CREATION_ENTREPRISE",
        default=None,
        description="Date de création de l'entreprise",
    )
    competences: Optional[str] = Field(
        alias="COMPETENCES",
        default=None,
        description="Liste des compétences techniques requises",
    )
    types_competences: Optional[str] = Field(
        alias="TYPES_COMPETENCES",
        default=None,
        description="Types de compétences requises",
    )
    softskills_summary: Optional[str] = Field(
        alias="SOFTSKILLS_SUMMARY",
        default=None,
        description="Résumé des compétences comportementales",
    )
    softskills_details: Optional[str] = Field(
        alias="SOFTSKILLS_DETAILS",
        default=None,
        description="Détails des compétences comportementales",
    )
    nom_metier: str = Field(alias="NOM_METIER", description="Nom du métier")

    model_config = {
        "populate_by_name": True,
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "ID": 1,
                    "ID_LOCAL": "12345",
                    "TITLE": "Data Engineer",
                    "DESCRIPTION": "Description du poste",
                    "VILLE": "Paris",
                    "DEPARTEMENT": "Paris",
                    "REGION": "Île-de-France",
                    "PAYS": "France",
                    "CODE_ROME": "M1805",
                    "NOM_METIER": "Data Engineer",
                    "MOIS_CREATION": 4,
                    "JOUR_CREATION": 28,
                    "WEEK_END_CREATION": False,
                    "MOIS_MODIFICATION": 4,
                    "JOUR_MODIFICATION": 28,
                    "WEEK_END_MODIFICATION": False,
                }
            ]
        },
    }


class SoftSkill(BaseModel):
    summary: str

    class Config:
        from_attributes = True

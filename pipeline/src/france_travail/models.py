from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, HttpUrl


class LieuTravail(BaseModel):
    libelle: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class Entreprise(BaseModel):
    nom: Optional[str] = None


class Contact(BaseModel):
    urlPostulation: Optional[HttpUrl] = None


class Offre(BaseModel):
    id: str
    intitule: str
    description: Optional[str] = None
    dateCreation: Optional[datetime] = None
    dateActualisation: Optional[datetime] = None
    lieuTravail: Optional[LieuTravail] = None
    entreprise: Optional[Entreprise] = None
    typeContrat: Optional[str] = None
    contact: Optional[Contact] = None


class ResultatRecherche(BaseModel):
    resultats: List[Offre]


class SearchParams(BaseModel):
    range: Optional[str] = "0-49"
    sort: Optional[int] = 1
    motsCles: Optional[str] = None

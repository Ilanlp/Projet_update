from .france_travail_api import FranceTravailAPI
from .models import SearchParams, ResultatRecherche, Offre

__all__ = [
    "FranceTravailAPI",
    "SearchParams",
    "ResultatRecherche",
    "Offre",
]

print("Le package 'france-travail' a été chargé")

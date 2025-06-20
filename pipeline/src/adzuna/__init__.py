from .models import JobSearchResults, CountryCode, SortBy
from .adzuna_api import AdzunaClient, AdzunaClientError

__all__ = [
    "AdzunaClient",
    "AdzunaClientError",
    "JobSearchResults",
    "CountryCode",
    "SortBy",
]

print("Le package 'adzuna' a été chargé")

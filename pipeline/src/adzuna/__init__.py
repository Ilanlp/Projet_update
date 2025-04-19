from .models import (
    JobSearchResults,
    CountryCode,
    SortBy,
    SortDirection,
    EnumWithValues,
    Job,
    Category,
    SalaryHistogram,
    TopCompanies,
    JobGeoData,
    HistoricalSalary,
    ApiVersion,
    SearchParams,
    Categories,
)
from .adzuna_api import AdzunaClient, AdzunaClientError

__all__ = [
    "AdzunaClient",
    "AdzunaClientError",
    "JobSearchResults",
    "CountryCode",
    "SortBy",
    "SortDirection",
    "EnumWithValues",
    "Job",
    "Category",
    "SalaryHistogram",
    "TopCompanies",
    "JobGeoData",
    "HistoricalSalary",
    "ApiVersion",
    "SearchParams",
    "Categories",
]

print("Le package 'adzuna' a été chargé")

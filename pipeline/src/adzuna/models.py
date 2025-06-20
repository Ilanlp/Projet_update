from enum import Enum
from typing import List, Dict, Optional, Any, Union, TypeVar
from pydantic import BaseModel, Field


# Type générique pour les valeurs d'énumération
T = TypeVar('T')

class EnumWithValues(Enum):
    """
    Classe de base pour les énumérations avec valeurs associées
    Cette classe permet d'accéder facilement à la valeur string associée
    """
    
    @property
    def value_str(self) -> str:
        """
        Retourne la valeur string pour une utilisation dans les requêtes API
        """
        return self.value


class CountryCode(str, Enum):
    """Codes pays supportés par l'API Adzuna"""
    FR = "fr"


class SortDirection(str, EnumWithValues):
    """Direction de tri pour les résultats"""
    UP = "up"
    DOWN = "down"


class SortBy(str, Enum):
    """Critère de tri pour les résultats"""
    DATE = "date"


# Modèles de base
class Category(BaseModel):
    tag: str = Field(description="The string which should be passed to search endpoint using the 'category' query parameter.")
    label: str = Field(description="A text string describing the category, suitable for display.")


class Location(BaseModel):
    display_name: Optional[str] = None


class Company(BaseModel):
    display_name: Optional[str] = None


class Job(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    created: Optional[str] = None
    location: Optional[Location] = None
    company: Optional[Company] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    contract_type: Optional[str] = None
    contract_time: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    redirect_url: Optional[str] = None


class JobSearchResults(BaseModel):
    results: List[Job]


class LocationJobs(BaseModel):
    location: Optional[Location] = Field(None, description="The location being described.")
    count: Optional[int] = Field(None, description="The number of jobs advertised at this location.")


class JobGeoData(BaseModel):
    locations: Optional[List[LocationJobs]] = Field(None, description="The number of live job ads in any given location, followed by a list of sub-locations and the number of live jobs in each of them, ordered from most jobs to least.")


class TopCompanies(BaseModel):
    leaderboard: Optional[List[Company]] = Field(None, description="A list of companies, ordered by the number of jobs they are advertising.")


class Categories(BaseModel):
    results: List[Category] = Field(description="An array of all the categories discovered as Adzuna::API::Response::Category objects.")


class SalaryHistogram(BaseModel):
    histogram: Optional[Dict[str, int]] = Field(None, description="The distribution of jobs by salary. Returns an array of salaries and the number of live jobs pay as much or more than each salary.")


class HistoricalSalary(BaseModel):
    month: Optional[Dict[str, float]] = Field(None, description="A series of average salary values, by month, for all jobs with a given category, title and/or location.")


class ApiVersion(BaseModel):
    api_version: float = Field(description="The major version of the API.")
    software_version: str = Field(description="The version of the software providing the API.")


# Paramètre de requête avec gestion des énumérations
class SearchParams(BaseModel):
    """
    Modèle pour les paramètres de recherche
    Gère également la conversion des énumérations
    """
    app_id: str = Field(description="Application ID, supplied by Adzuna")
    app_key: str = Field(description="Application key, supplied by Adzuna")
    what: Optional[str] = Field(None, description="The keywords to search for. Multiple terms may be space separated.")
    what_and: Optional[str] = Field(None, description="The keywords to search for, all keywords must be found.")
    what_phrase: Optional[str] = Field(None, description="An entire phrase which must be found in the description or title.")
    what_or: Optional[str] = Field(None, description="The keywords to search for, any keywords may be found. Multiple terms may be space separated.")
    what_exclude: Optional[str] = Field(None, description="Keywords to exclude from the search. Multiple terms may be space separated.")
    title_only: Optional[str] = Field(None, description="Keywords to find, but only in the title. Multiple terms may be space separated.")
    where: Optional[str] = Field(None, description="The geographic centre of the search. Place names, postal codes, etc. may be used.")
    distance: Optional[int] = Field(None, description="The distance in kilometres from the centre of the place described by the 'where' parameter. Defaults to 5km.")
    location0: Optional[str] = Field(None, description="The location fields may be used to describe a location, in a similar form to that returned in a Adzuna::API::Response::Location object.")
    location1: Optional[str] = Field(None, description="See location1")
    location2: Optional[str] = Field(None, description="See location2")
    location3: Optional[str] = Field(None, description="See location3")
    location4: Optional[str] = Field(None, description="See location4")
    location5: Optional[str] = Field(None, description="See location5")
    location6: Optional[str] = Field(None, description="See location6")
    location7: Optional[str] = Field(None, description="See location7")
    max_days_old: Optional[int] = Field(None, description="The age of the oldest advertisment in days that will be returned.")
    category: Optional[str] = Field(None, description="The category tag, as returned by the 'category' endpoint.")
    sort_dir: Optional[Union[SortDirection, str]] = Field(None, description="The direction to order the search results.")
    sort_by: Optional[Union[SortBy, str]] = Field(None, description="The ordering of the search results.")
    salary_min: Optional[int] = Field(None, description="The minimum salary we wish to get results for.")
    salary_max: Optional[int] = Field(None, description="The maximum salary we wish to get results for.")
    salary_include_unknown: Optional[str] = Field(None, description="If set it '1', jobs without a known salary are returned.")
    full_time: Optional[str] = Field(None, description="If set to '1', only full time jobs will be returned.")
    part_time: Optional[str] = Field(None, description="If set to '1', only part time jobs will be returned.")
    contract: Optional[str] = Field(None, description="If set to '1', only contract jobs will be returned.")
    permanent: Optional[str] = Field(None, description="If set to '1', only permanent jobs will be returned.")
    company: Optional[str] = Field(None, description="The canonical company name.")
    results_per_page: Optional[int] = Field(None, description="The number of results to include on a page of search results.")
    
    def prepare_for_api(self) -> Dict[str, Any]:
        """
        Prépare les paramètres pour l'API en convertissant les énumérations en chaînes
        
        Returns:
            Dictionnaire avec les paramètres prêts pour l'API
        """
        # Convertir en dictionnaire
        params = self.model_dump(exclude_none=True)
        
        # Traiter les énumérations spéciales
        if "sort_dir" in params and isinstance(params["sort_dir"], SortDirection):
            params["sort_dir"] = params["sort_dir"].value
            
        if "sort_by" in params and isinstance(params["sort_by"], SortBy):
            params["sort_by"] = params["sort_by"].value
        
        return params

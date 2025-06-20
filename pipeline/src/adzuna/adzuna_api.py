"""
Client Adzuna API simplifié
"""

import httpx
import logging
from .models import JobSearchResults, CountryCode, SortBy

logger = logging.getLogger(__name__)


class AdzunaClientError(Exception):
    """Exception levée en cas d'erreur avec l'API Adzuna"""
    pass


class AdzunaClient:
    """Client simplifié pour l'API Adzuna"""

    BASE_URL = "https://api.adzuna.com/v1/api"

    def __init__(self, app_id: str, app_key: str):
        self.app_id = app_id
        self.app_key = app_key
        self.client = httpx.AsyncClient(base_url=self.BASE_URL)

    async def close(self):
        """Ferme la session HTTP."""
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def search_jobs(self, country: CountryCode, page: int = 1, **kwargs) -> JobSearchResults:
        """Recherche des offres d'emploi."""
        params = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "page": page,
            **kwargs
        }
        
        # Convertir les énumérations en chaînes
        if "sort_by" in params and isinstance(params["sort_by"], SortBy):
            params["sort_by"] = params["sort_by"].value
        if "country" in params and isinstance(params["country"], CountryCode):
            params["country"] = params["country"].value

        country_value = country.value if isinstance(country, CountryCode) else country
        endpoint = f"/jobs/{country_value}/search/{page}"
        
        try:
            logger.info(f"Requête de l'api adzuna : {endpoint} {params}")
            response = await self.client.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()
            return JobSearchResults.model_validate(data)
        except Exception as e:
            raise AdzunaClientError(f"Erreur API Adzuna: {str(e)}") from e

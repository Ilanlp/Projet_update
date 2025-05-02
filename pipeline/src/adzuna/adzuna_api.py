"""
Client Adzuna API avec Pydantic V2
Version améliorée qui évite les conversions automatiques problématiques des énumérations
"""

from typing import List
import httpx
from pydantic import TypeAdapter
import logging

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

# Configuration du logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class AdzunaClientError(Exception):
    """Exception levée en cas d'erreur avec l'API Adzuna"""

    pass


class AdzunaClient:
    """
    Client pour l'API Adzuna qui permet de rechercher des offres d'emploi et d'accéder aux statistiques.

    Cette version améliorée gère correctement les énumérations et leur conversion en chaînes.
    """

    BASE_URL = "https://api.adzuna.com/v1/api"

    def __init__(self, app_id: str, app_key: str):
        """
        Initialise le client API Adzuna.

        Args:
            app_id: Votre identifiant d'application Adzuna
            app_key: Votre clé d'API Adzuna
        """
        self.app_id = app_id
        self.app_key = app_key
        self.client = httpx.AsyncClient(base_url=self.BASE_URL)

        # Adaptateurs de type pour validation
        self._job_list_adapter = TypeAdapter(List[Job])
        self._category_list_adapter = TypeAdapter(List[Category])

    async def close(self):
        """Ferme la session HTTP."""
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def _make_request(self, endpoint: str, params: dict) -> dict:
        """
        Effectue une requête HTTP à l'API Adzuna.

        Args:
            endpoint: Le point de terminaison de l'API
            params: Les paramètres de la requête

        Returns:
            La réponse JSON comme un dictionnaire

        Raises:
            AdzunaClientError: Si une erreur se produit lors de la requête
        """
        # Ajouter les identifiants d'application aux paramètres
        api_params = {"app_id": self.app_id, "app_key": self.app_key}

        # Fusionner avec les paramètres fournis (qui auraient déjà dû être préparés)
        api_params.update(params)

        try:
            logger.info(
                f"Requête de l'api adzuna : {endpoint} {api_params}"
            )
            response = await self.client.get(endpoint, params=api_params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            error_data = {}
            try:
                error_data = e.response.json()
            except:
                pass

            error_message = f"HTTP error {e.response.status_code}"
            if "exception" in error_data:
                error_message += f": {error_data['exception']}"
            if "display" in error_data:
                error_message += f" - {error_data['display']}"

            raise AdzunaClientError(error_message) from e
        except httpx.RequestError as e:
            raise AdzunaClientError(f"Request error: {str(e)}") from e
        except ValueError as e:
            raise AdzunaClientError(f"Invalid JSON response: {str(e)}") from e

    async def search_jobs(
        self, country: CountryCode, page: int = 1, **kwargs
    ) -> JobSearchResults:
        """
        Recherche des offres d'emploi.

        Args:
            country: Le code pays ISO 8601 du pays d'intérêt
            page: Le numéro de page pour la pagination
            **kwargs: Paramètres de recherche supplémentaires (voir SearchParams)

        Returns:
            Les résultats de la recherche
        """
        # Valider et préparer les paramètres de recherche pour l'API
        params = SearchParams(app_id=self.app_id, app_key=self.app_key, **kwargs)
        prepared_params = params.prepare_for_api()

        # Supprimer app_id et app_key car ils seront ajoutés dans _make_request
        prepared_params.pop("app_id")
        prepared_params.pop("app_key")

        # Convertir le code pays en chaîne si nécessaire
        country_value = country.value if isinstance(country, CountryCode) else country

        endpoint = f"/jobs/{country_value}/search/{page}"
        data = await self._make_request(endpoint, prepared_params)

        return JobSearchResults.model_validate(data)

    async def get_categories(self, country: CountryCode) -> Categories:
        """
        Récupère les catégories disponibles.

        Args:
            country: Le code pays ISO 8601 du pays d'intérêt

        Returns:
            Les catégories disponibles
        """
        # Convertir le code pays en chaîne si nécessaire
        country_value = country.value if isinstance(country, CountryCode) else country

        endpoint = f"/jobs/{country_value}/categories"
        data = await self._make_request(endpoint, {})

        return Categories.model_validate(data)

    async def get_salary_histogram(
        self, country: CountryCode, **kwargs
    ) -> SalaryHistogram:
        """
        Récupère l'histogramme des salaires.

        Args:
            country: Le code pays ISO 8601 du pays d'intérêt
            **kwargs: Paramètres de filtre (what, location0-7, category)

        Returns:
            L'histogramme des salaires
        """
        # Convertir le code pays en chaîne si nécessaire
        country_value = country.value if isinstance(country, CountryCode) else country

        # Préparer les paramètres
        params = {}
        for key, value in kwargs.items():
            # Traiter les énumérations
            if isinstance(value, EnumWithValues):
                params[key] = value.value
            else:
                params[key] = value

        endpoint = f"/jobs/{country_value}/histogram"
        data = await self._make_request(endpoint, params)

        return SalaryHistogram.model_validate(data)

    async def get_top_companies(self, country: CountryCode, **kwargs) -> TopCompanies:
        """
        Récupère les entreprises principales pour les termes de recherche fournis.

        Args:
            country: Le code pays ISO 8601 du pays d'intérêt
            **kwargs: Paramètres de filtre (what, location0-7, category)

        Returns:
            Les entreprises principales
        """
        # Convertir le code pays en chaîne si nécessaire
        country_value = country.value if isinstance(country, CountryCode) else country

        # Préparer les paramètres
        params = {}
        for key, value in kwargs.items():
            # Traiter les énumérations
            if isinstance(value, EnumWithValues):
                params[key] = value.value
            else:
                params[key] = value

        endpoint = f"/jobs/{country_value}/top_companies"
        data = await self._make_request(endpoint, params)

        return TopCompanies.model_validate(data)

    async def get_geodata(self, country: CountryCode, **kwargs) -> JobGeoData:
        """
        Récupère les données géographiques des emplois.

        Args:
            country: Le code pays ISO 8601 du pays d'intérêt
            **kwargs: Paramètres de filtre (location0-7, category)

        Returns:
            Les données géographiques
        """
        # Convertir le code pays en chaîne si nécessaire
        country_value = country.value if isinstance(country, CountryCode) else country

        # Préparer les paramètres
        params = {}
        for key, value in kwargs.items():
            # Traiter les énumérations
            if isinstance(value, EnumWithValues):
                params[key] = value.value
            else:
                params[key] = value

        endpoint = f"/jobs/{country_value}/geodata"
        data = await self._make_request(endpoint, params)

        return JobGeoData.model_validate(data)

    async def get_historical_salary(
        self, country: CountryCode, months: int = None, **kwargs
    ) -> HistoricalSalary:
        """
        Récupère les données historiques de salaire.

        Args:
            country: Le code pays ISO 8601 du pays d'intérêt
            months: Le nombre de mois en arrière pour lesquels récupérer les données (max 12)
            **kwargs: Paramètres de filtre (location0-7, category)

        Returns:
            Les données historiques de salaire
        """
        # Convertir le code pays en chaîne si nécessaire
        country_value = country.value if isinstance(country, CountryCode) else country

        # Préparer les paramètres
        params = {}
        for key, value in kwargs.items():
            # Traiter les énumérations
            if isinstance(value, EnumWithValues):
                params[key] = value.value
            else:
                params[key] = value

        if months is not None:
            params["months"] = months

        endpoint = f"/jobs/{country_value}/history"
        data = await self._make_request(endpoint, params)

        return HistoricalSalary.model_validate(data)

    async def get_api_version(self) -> ApiVersion:
        """
        Récupère la version actuelle de l'API.

        Returns:
            La version de l'API
        """
        endpoint = "/version"
        data = await self._make_request(endpoint, {})

        return ApiVersion.model_validate(data)


# Exemple d'utilisation
async def example_usage():
    """Exemple d'utilisation du client Adzuna amélioré"""
    # Remplacez avec vos propres identifiants
    app_id = "YOUR_APP_ID"
    app_key = "YOUR_APP_KEY"

    async with AdzunaClient(app_id, app_key) as client:
        # Rechercher des emplois - format chaîne de caractères
        print("\n--- Recherche avec paramètres sous forme de chaînes ---")
        results1 = await client.search_jobs(
            country=CountryCode.FR,
            what="python",
            where="Paris",
            results_per_page=10,
            sort_by="date",
            sort_dir="down",
        )

        print(f"Nombre d'offres trouvées: {len(results1.results)}")

        # Rechercher des emplois - format énumération
        print("\n--- Recherche avec paramètres sous forme d'énumérations ---")
        results2 = await client.search_jobs(
            country=CountryCode.FR,
            what="python",
            where="Paris",
            results_per_page=10,
            sort_by=SortBy.DATE,
            sort_dir=SortDirection.DOWN,
        )

        print(f"Nombre d'offres trouvées: {len(results2.results)}")

        # Obtenir les catégories disponibles
        categories = await client.get_categories(CountryCode.FR)
        print(f"\nNombre de catégories: {len(categories.results)}")

        # Obtenir l'histogramme des salaires
        histogram = await client.get_salary_histogram(CountryCode.FR, what="python")
        print(
            f"\nHistogramme des salaires disponible: {'Oui' if histogram.histogram else 'Non'}"
        )

        # Catégories disponibles
        print("\nQuelques catégories disponibles:")
        for category in categories.results[:5]:
            print(f"- {category.label} (tag: {category.tag})")


if __name__ == "__main__":
    import asyncio

    asyncio.run(example_usage())

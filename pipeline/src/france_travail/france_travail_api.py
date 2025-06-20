"""
API France Travail simplifiée
"""

import requests
import logging
from .models import SearchParams, ResultatRecherche

logger = logging.getLogger(__name__)


class FranceTravailAPI:
    """API simplifiée pour France Travail"""

    BASE_URL = "https://api.francetravail.io/partenaire/offresdemploi"
    TOKEN_URL = "https://entreprise.francetravail.fr/connexion/oauth2/access_token?realm=/partenaire"
    VERSION = "v2"

    def __init__(self, client_id: str, client_secret: str):
        token = self.get_token(client_id, client_secret)
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

    def get_token(self, client_id: str, client_secret: str):
        """Récupération du token"""
        response = requests.post(
            self.TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
                "scope": "api_offresdemploiv2 o2dsoffre",
            },
        )

        if response.status_code == 204:
            return {}

        if response.status_code in (200, 206):
            return response.json()["access_token"]

        error_message = f"Erreur {response.status_code}: {response.text}"
        raise Exception(error_message)

    def search_offers(self, params: SearchParams) -> ResultatRecherche:
        """Recherche des offres d'emploi"""
        endpoint = "offres/search"
        url = f"{self.BASE_URL}/{self.VERSION}/{endpoint}"
        
        params_dict = params.model_dump(exclude_none=True)
        params_dict = {k: v for k, v in params_dict.items() if v is not None}

        logger.info(f"Requête de l'api france travail : {url} avec en query {params_dict}")
        
        response = requests.get(url, headers=self.headers, params=params_dict)
        
        if response.status_code == 204:
            return ResultatRecherche(resultats=[])

        if response.status_code in (200, 206):
            data = response.json()
            return ResultatRecherche.model_validate(data)

        error_message = f"Erreur {response.status_code}: {response.text}"
        raise Exception(error_message)

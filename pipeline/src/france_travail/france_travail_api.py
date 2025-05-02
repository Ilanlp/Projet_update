"""
Requêteur automatique pour l'API Offres d'emploi de France Travail
Utilise Pydantic V2 pour la validation des données et la sérialisation
"""

import os
import requests
import logging
from dotenv import load_dotenv
from typing import List, Optional, Dict, Any
from .models import (
    SearchParams,
    ResultatRecherche,
    Offre,
    Referentiel,
    Commune,
    Departement,
    Region,
    # LieuTravail,
    # Entreprise,
    # Formation,
    # Langue,
    # Permis,
    # Competence,
    # QualitePro,
)

# Configuration du logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Classe principale pour le requêteur
class FranceTravailAPI:
    """
    Requêteur automatique pour l'API Offres d'emploi de France Travail
    """

    BASE_URL = "https://api.francetravail.io/partenaire/offresdemploi"
    TOKEN_URL = "https://entreprise.francetravail.fr/connexion/oauth2/access_token?realm=/partenaire"
    VERSION = "v2"

    def __init__(self, client_id: str, client_secret: str):
        """
        Initialise le requêteur avec un token d'authentification

        Args:
            client_id: Votre identifiant d'application France Travail
            client_secret: Votre clé d'API France Travail
        """
        token = self.get_token(client_id, client_secret)
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

    def get_token(self, client_id: str, client_secret: str):
        """
        Récupération du token

        Args:
            client_id: Votre identifiant d'application France Travail
            client_secret: Votre clé d'API France Travail
        """
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
            return {}  # Aucun résultat

        if response.status_code in (200, 206):
            return response.json()["access_token"]

        error_message = f"Erreur {response.status_code}: {response.text}"
        raise Exception(error_message)

    def _build_url(self, endpoint: str) -> str:
        """
        Construit l'URL complète pour un endpoint

        Args:
            endpoint (str): Chemin de l'endpoint

        Returns:
            str: URL complète
        """
        return f"{self.BASE_URL}/{self.VERSION}/{endpoint}"

    def _make_request(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Effectue une requête à l'API et gère les erreurs

        Args:
            endpoint (str): Chemin de l'endpoint
            params (Dict[str, Any], optional): Paramètres de la requête

        Returns:
            Dict[str, Any]: Réponse de l'API

        Raises:
            Exception: En cas d'erreur de requête
        """
        url = self._build_url(endpoint)

        # Filtre les paramètres nuls
        if params:
            params = {k: v for k, v in params.items() if v is not None}

        response = requests.get(url, headers=self.headers, params=params)
        logger.info(
            f"Requête de l'api france travail : {response.url} avec en query {params}"
        )
        # Gestion des erreurs
        if response.status_code == 204:
            return {}  # Aucun résultat

        if response.status_code in (200, 206):
            return response.json()

        error_message = f"Erreur {response.status_code}: {response.text}"
        raise Exception(error_message)

    def search_offers(self, params: SearchParams) -> ResultatRecherche:
        """
        Recherche des offres d'emploi selon les critères spécifiés

        Args:
            params (SearchParams): Paramètres de recherche

        Returns:
            ResultatRecherche: Résultat de la recherche
        """
        endpoint = "offres/search"
        logger.debug(
            f"search_offers params : {params}"
        )
        params_dict = params.model_dump(exclude_none=True)

        response_data = self._make_request(endpoint, params_dict)
        if not response_data:
            # Aucun résultat
            return ResultatRecherche(resultats=[])

        return ResultatRecherche.model_validate(response_data)

    def get_offer_details(self, offer_id: str) -> Optional[Offre]:
        """
        Récupère le détail d'une offre d'emploi

        Args:
            offer_id (str): Identifiant de l'offre

        Returns:
            Optional[Offre]: Détail de l'offre ou None si non trouvée
        """
        endpoint = f"offres/{offer_id}"

        try:
            response_data = self._make_request(endpoint)
            if not response_data:
                return None

            return Offre.model_validate(response_data)
        except Exception:
            return None

    def get_referential(self, ref_type: str) -> List[Referentiel]:
        """
        Récupère les données d'un référentiel

        Args:
            ref_type (str): Type de référentiel (appellations, nafs, communes, continents,
                           departements, domaines, langues, metiers, naturesContrats,
                           niveauxFormations, pays, permis, regions, secteursActivites,
                           themes, typesContrats)

        Returns:
            List[Referentiel]: Liste des éléments du référentiel
        """
        valid_refs = [
            "appellations",
            "nafs",
            "communes",
            "continents",
            "departements",
            "domaines",
            "langues",
            "metiers",
            "naturesContrats",
            "niveauxFormations",
            "pays",
            "permis",
            "regions",
            "secteursActivites",
            "themes",
            "typesContrats",
        ]

        if ref_type not in valid_refs:
            raise ValueError(
                f"Type de référentiel invalide. Valeurs possibles: {', '.join(valid_refs)}"
            )

        endpoint = f"referentiel/{ref_type}"
        response_data = self._make_request(endpoint)

        # Adaptation au type de référentiel
        if ref_type == "communes":
            return [Commune.model_validate(item) for item in response_data]
        elif ref_type == "departements":
            return [Departement.model_validate(item) for item in response_data]
        elif ref_type == "regions":
            return [Region.model_validate(item) for item in response_data]
        else:
            return [Referentiel.model_validate(item) for item in response_data]


# Exemple d'utilisation
if __name__ == "__main__":
    # Token d'exemple (à remplacer par un vrai token)
    # token = "votre_token_ici"

    # Chargement des variables d'environnements
    load_dotenv()

    client_id = os.getenv("FRANCE_TRAVAIL_ID")
    client_secret = os.getenv("FRANCE_TRAVAIL_KEY")

    # Initialisation de l'API
    api = FranceTravailAPI(client_id, client_secret)

    # Exemple de recherche d'offres d'emploi
    search_params = SearchParams(
        motsCles="python,data,ingénieur",
        typeContrat="CDI",
        experience=2,  # De 1 à 3 ans
        range="0-10",  # 10 premiers résultats
    )

    try:
        results = api.search_offers(search_params)
        print(f"Nombre d'offres trouvées: {len(results.resultats)}")

        # Affichage des résultats
        for offre in results.resultats:
            print(f"ID: {offre.id}")
            print(f"Titre: {offre.intitule}")
            print(
                f"Lieu: {offre.lieuTravail.libelle if offre.lieuTravail else 'Non précisé'}"
            )
            print(f"Contrat: {offre.typeContratLibelle or 'Non précisé'}")
            print(
                f"Entreprise: {offre.entreprise.nom if offre.entreprise else 'Non précisé'}"
            )
            print("---")

        # Récupération des détails d'une offre
        if results.resultats:
            first_offer_id = results.resultats[0].id
            offer_details = api.get_offer_details(first_offer_id)

            if offer_details:
                print("\nDétails de l'offre:")
                print(f"Description: {offer_details.description}")
                print(
                    f"Salaire: {offer_details.salaire.libelle if offer_details.salaire else 'Non précisé'}"
                )
                print(f"Date de création: {offer_details.dateCreation}")

                # Compétences
                if offer_details.competences:
                    print("\nCompétences requises:")
                    for comp in offer_details.competences:
                        exigence = "Exigée" if comp.exigence == "E" else "Souhaitée"
                        print(f"- {comp.libelle} ({exigence})")

        # Exemple d'utilisation des référentiels
        print("\nRécupération des types de contrats:")
        contrats = api.get_referential("typesContrats")
        for contrat in contrats[:5]:  # 5 premiers pour l'exemple
            print(f"- {contrat.code}: {contrat.libelle}")

    except Exception as e:
        print(f"Erreur: {e}")

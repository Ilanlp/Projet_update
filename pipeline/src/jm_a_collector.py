"""
Module de collecte historique des données Adzuna

Ce module contient la classe AdzunaHistoricalCollector qui permet de collecter
des offres d'emploi sur Adzuna sur une longue période temporelle (plusieurs mois)
en utilisant une approche par catégories et périodes pour maximiser la couverture.
"""

import os
from os import environ
import sys
import json
import csv
import asyncio
import logging
import httpx
import argparse
import re
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Set, Any, Tuple
from pydantic import TypeAdapter

from adzuna import AdzunaClient, CountryCode, Job, Category, AdzunaClientError
from jm_normalizer import JobDataNormalizer, NormalizedJobOffer

# Configuration du logging
logger = logging.getLogger(__name__)


class AdzunaHistoricalCollector:
    """
    Collecteur de données historiques pour l'API Adzuna

    Cette classe gère la collecte d'offres d'emploi sur une longue période
    en utilisant des stratégies pour maximiser la couverture et gérer les
    limites de l'API.
    """

    def __init__(
        self,
        adzuna_client: AdzunaClient,
        country: CountryCode = CountryCode.FR,
        category: str = "it-jobs",
        results_per_page: int = 50,
        retry_count: int = 3,
        retry_delay: int = 5,
        rate_limit_delay: float = 0.5,
        checkpoint_interval: int = 100,
    ):
        """
        Initialise le collecteur de données historiques

        Args:
            adzuna_client: Client API Adzuna existant
            country: Code pays pour la recherche (par défaut: France)
            results_per_page: Nombre de résultats par page (max 50 pour Adzuna)
            retry_count: Nombre de tentatives en cas d'erreur
            retry_delay: Délai (en secondes) entre les tentatives
            rate_limit_delay: Délai entre les requêtes pour éviter les limites de taux
            checkpoint_interval: Intervalle de sauvegarde de l'état (nombre d'offres)
        """
        self.adzuna_client = adzuna_client
        self.country = country
        self.category = category
        self.results_per_page = results_per_page
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self.rate_limit_delay = rate_limit_delay
        self.checkpoint_interval = checkpoint_interval

        # État interne
        self.collected_job_ids: Set[str] = set()
        self.total_collected = 0
        self.categories: List[Category] = []

    async def initialize(self) -> None:
        """Initialise le collecteur en récupérant les catégories d'emploi"""
        # Récupérer toutes les catégories disponibles
        try:
            categories_result = await self.adzuna_client.get_categories(self.country)
            self.categories = categories_result.results
            logger.info(f"Récupération de {len(self.categories)} catégories d'emploi")
        except AdzunaClientError as e:
            logger.error(f"Erreur lors de la récupération des catégories: {e}")
            raise

    async def collect_data(self, output_file: str, max_months: int = 12) -> str:
        """
        Collecte les données d'offres d'emploi et les sauvegarde en CSV

        Les données sont normalisées via NormalizedJobOffer avant d'être sauvegardées.
        Le header du CSV correspond exactement aux propriétés de NormalizedJobOffer.

        Args:
            output_file: Chemin du fichier CSV de sortie
            max_months: Nombre maximum de mois à remonter dans le temps

        Returns:
            Chemin du fichier CSV généré
        """
        # Initialiser l'état
        self.collected_job_ids = set()
        self.total_collected = 0
        checkpoint_file = f"{output_file}.checkpoint"

        # S'assurer que le répertoire de sortie existe
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Charger l'état de progression si disponible
        if os.path.exists(checkpoint_file):
            try:
                with open(checkpoint_file, "r", encoding="utf-8") as f:
                    checkpoint_data = json.load(f)
                    self.collected_job_ids = set(
                        checkpoint_data.get("collected_job_ids", [])
                    )
                    self.total_collected = checkpoint_data.get("total_collected", 0)
                    timestamp = checkpoint_data.get("timestamp")
                    logger.info(
                        f"Point de contrôle chargé du {timestamp}: "
                        f"{self.total_collected} offres déjà collectées"
                    )
            except Exception as e:
                logger.warning(f"Erreur lors du chargement du point de contrôle: {e}")

        # Initialiser le collecteur (récupérer les catégories)
        await self.initialize()

        # Générer les périodes temporelles (tranches d'un mois)
        time_periods = self._generate_time_periods(max_months)
        logger.info(
            f"Collecte des données sur {len(time_periods)} périodes temporelles"
        )

        # Obtenir la liste des noms de champs à partir du modèle
        fieldnames = list(NormalizedJobOffer.model_fields.keys())
        logger.info(
            f"Utilisation de {len(fieldnames)} champs du modèle NormalizedJobOffer pour le CSV"
        )

        # Préparer le fichier CSV
        file_exists = os.path.exists(output_file)
        has_content = False

        if file_exists:
            # Vérifier si le fichier contient des données et si les en-têtes correspondent
            try:
                with open(output_file, "r", newline="", encoding="utf-8") as f:
                    reader = csv.reader(f)
                    header = next(reader, None)
                    has_content = header is not None

                    # Vérifier si les en-têtes existants correspondent au modèle NormalizedJobOffer
                    if has_content and set(header) != set(fieldnames):
                        logger.warning(
                            "Le fichier existant a un schéma différent de NormalizedJobOffer. "
                            "Un nouveau fichier sera créé."
                        )
                        # Renommer le fichier existant pour le préserver
                        import shutil

                        backup_file = f"{output_file}.bak_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                        shutil.copy2(output_file, backup_file)
                        logger.info(f"Fichier existant copié vers {backup_file}")
                        has_content = False

            except Exception as e:
                logger.warning(f"Erreur lors de la lecture du fichier existant: {e}")
                has_content = False

        # Mode d'ouverture: 'a' (append) si le fichier existe et a du contenu, sinon 'w' (write)
        mode = "a" if file_exists and has_content else "w"

        # Initialiser le normalisateur une seule fois en dehors de la boucle
        normalizer = JobDataNormalizer(
            environ.get("ADZUNA_APP_ID"),
            environ.get("ADZUNA_APP_KEY"),
            environ.get("FRANCE_TRAVAIL_ID"),
            environ.get("FRANCE_TRAVAIL_KEY"),
        )

        with open(output_file, mode, newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

            # Si on est en mode écriture, écrire l'en-tête
            if mode == "w":
                writer.writeheader()
                logger.info(
                    f"En-tête CSV écrit dans {output_file} avec les champs de NormalizedJobOffer"
                )
            else:
                logger.info(f"Ajout des données au fichier existant {output_file}")

            # Parcourir les catégories et les périodes
            # for category in self.categories:
            for category in [Category(label=self.category, tag=self.category)]:
                for period_start, period_end in time_periods:
                    # Calculer max_days_old en utilisant une date aware
                    now = datetime.now().replace(tzinfo=timezone.utc)
                    max_days_old = (now - period_start).days

                    logger.info(
                        f"Collecte des offres pour la catégorie '{category.label}' "
                        f"du {period_start.strftime('%Y-%m-%d')} au {period_end.strftime('%Y-%m-%d')}"
                    )

                    page = 1
                    total_for_period = 0
                    has_more_results = True

                    while has_more_results:
                        try:
                            # Ajouter une pause pour éviter les limites de taux
                            await asyncio.sleep(self.rate_limit_delay)

                            # Utiliser la méthode personnalisée
                            try:
                                data = await self._search_jobs_direct(
                                    page=page,
                                    category=category.tag,
                                    results_per_page=self.results_per_page,
                                    max_days_old=max_days_old,
                                    sort_by="date",  # Tri par date, sans préciser la direction
                                )

                                # Convertir en objets Job
                                job_list_adapter = TypeAdapter(List[Job])

                                # Si la réponse contient des résultats, les convertir en objets Job
                                if "results" in data and data["results"]:
                                    results_list = job_list_adapter.validate_python(
                                        data["results"]
                                    )
                                else:
                                    results_list = []

                            except AdzunaClientError as e:
                                logger.warning(f"Erreur API pour la page {page}: {e}")
                                # Implémenter un backoff exponentiel
                                for retry in range(self.retry_count):
                                    delay = self.retry_delay * (2**retry)
                                    logger.info(
                                        f"Nouvelle tentative dans {delay} secondes..."
                                    )
                                    await asyncio.sleep(delay)

                                    try:
                                        # Réessayer la requête
                                        data = await self._search_jobs_direct(
                                            page=page,
                                            category=category.tag,
                                            results_per_page=self.results_per_page,
                                            max_days_old=max_days_old,
                                            sort_by="date",
                                        )

                                        # Convertir en objets Job
                                        if "results" in data and data["results"]:
                                            results_list = (
                                                job_list_adapter.validate_python(
                                                    data["results"]
                                                )
                                            )
                                        else:
                                            results_list = []

                                        # Si on arrive ici, la requête a réussi
                                        break
                                    except AdzunaClientError as retry_error:
                                        logger.warning(
                                            f"Échec de la tentative {retry+1}: {retry_error}"
                                        )
                                        # Si c'est la dernière tentative, abandonner cette page
                                        if retry == self.retry_count - 1:
                                            logger.error(
                                                f"Abandon de la page {page} après {self.retry_count} tentatives"
                                            )
                                            results_list = []
                                            has_more_results = False

                            # Vérifier s'il y a des résultats
                            if not results_list:
                                logger.info(
                                    f"Plus de résultats pour cette période. Total: {total_for_period}"
                                )
                                has_more_results = False
                                break

                            # Filtrer pour ne garder que les offres dans la période spécifiée
                            # et celles qu'on n'a pas encore traitées
                            filtered_jobs = []
                            for job in results_list:
                                # Vérifier si cette offre est déjà collectée
                                if job.id in self.collected_job_ids:
                                    continue

                                # Vérifier si l'offre est dans la période
                                job_date = datetime.fromisoformat(
                                    job.created.replace("Z", "+00:00")
                                )
                                if period_start <= job_date <= period_end:
                                    filtered_jobs.append(job)
                                    self.collected_job_ids.add(job.id)

                            # Si aucune offre après filtrage, passer à la page suivante
                            if not filtered_jobs:
                                page += 1
                                if page > 100:  # Limite de pagination Adzuna
                                    has_more_results = False
                                continue

                            # Transforme chaque offre avec le normalizer et l'écrit au format CSV
                            for job in filtered_jobs:
                                try:
                                    # Convertir l'objet Job en dictionnaire et le normaliser
                                    job_dict = job.model_dump()

                                    # Normaliser l'offre en utilisant le modèle NormalizedJobOffer
                                    normalized_job = normalizer.normalize_adzuna_job(
                                        job_dict
                                    )

                                    # Convertir l'offre normalisée en dictionnaire pour l'écriture CSV
                                    normalized_dict = normalized_job.model_dump()

                                    # Vérifier que toutes les clés correspondent au schéma attendu
                                    if set(normalized_dict.keys()) != set(fieldnames):
                                        missing_keys = set(fieldnames) - set(
                                            normalized_dict.keys()
                                        )
                                        extra_keys = set(normalized_dict.keys()) - set(
                                            fieldnames
                                        )

                                        if missing_keys:
                                            logger.warning(
                                                f"Clés manquantes dans l'offre normalisée: {missing_keys}"
                                            )
                                            # Ajouter les clés manquantes avec des valeurs None
                                            for key in missing_keys:
                                                normalized_dict[key] = None

                                        if extra_keys:
                                            logger.warning(
                                                f"Clés supplémentaires dans l'offre normalisée: {extra_keys}"
                                            )
                                            # Supprimer les clés supplémentaires
                                            for key in extra_keys:
                                                del normalized_dict[key]

                                    # Sanitizer toutes les valeurs textuelles du dictionnaire
                                    for key, value in normalized_dict.items():
                                        if isinstance(value, str):
                                            normalized_dict[key] = self._sanitize_text(
                                                value
                                            )
                                        elif isinstance(value, list) and all(
                                            isinstance(item, str) for item in value
                                        ):
                                            normalized_dict[key] = [
                                                self._sanitize_text(item)
                                                for item in value
                                            ]

                                    # Écrire l'offre normalisée dans le CSV
                                    writer.writerow(normalized_dict)
                                    csv_file.flush()  # S'assurer que les données sont écrites sur le disque

                                    total_for_period += 1
                                    self.total_collected += 1

                                except Exception as job_error:
                                    logger.error(
                                        f"Erreur lors de la normalisation/écriture de l'offre {job.id}: {job_error}",
                                        exc_info=True,
                                    )
                                    # Continuer avec l'offre suivante

                            # Log de progression
                            logger.info(
                                f"Page {page}: {len(filtered_jobs)} nouvelles offres ajoutées. "
                                f"Total pour cette période: {total_for_period}"
                            )

                            # Sauvegarde périodique de l'état
                            if self.total_collected % self.checkpoint_interval == 0:
                                self._save_checkpoint(checkpoint_file)

                            # Passer à la page suivante
                            page += 1
                            if page > 100:  # Limite de pagination Adzuna
                                has_more_results = False

                        except Exception as e:
                            logger.error(
                                f"Erreur non gérée lors de la collecte: {e}",
                                exc_info=True,
                            )
                            # Attendre et continuer avec la page suivante
                            await asyncio.sleep(self.retry_delay)
                            page += 1
                            if page > 100:  # Limite de pagination Adzuna
                                has_more_results = False

                    # Sauvegarde de l'état à la fin de chaque période
                    self._save_checkpoint(checkpoint_file)

        logger.info(
            f"Collecte terminée! {self.total_collected} offres d'emploi normalisées collectées au total."
        )
        return output_file

    async def _search_jobs_direct(self, page: int, **params):
        """
        Méthode personnalisée pour rechercher des offres d'emploi
        en contournant la conversion automatique des énumérations.

        Args:
            page: Le numéro de page
            **params: Paramètres de recherche supplémentaires

        Returns:
            Les résultats de la recherche
        """
        # Construire les paramètres de requête
        query_params = {
            "app_id": self.adzuna_client.app_id,
            "app_key": self.adzuna_client.app_key,
            **params,
        }

        # Créer un client HTTP temporaire pour cette requête
        async with httpx.AsyncClient(
            base_url="https://api.adzuna.com/v1/api"
        ) as client:
            endpoint = f"/jobs/{self.country.value}/search/{page}"

            try:
                response = await client.get(endpoint, params=query_params)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                error_message = f"Erreur HTTP: {str(e)}"
                raise AdzunaClientError(error_message) from e

    def _generate_time_periods(
        self, max_months: int
    ) -> List[Tuple[datetime, datetime]]:
        """
        Génère des périodes temporelles d'un mois, en remontant dans le temps

        Args:
            max_months: Nombre maximum de mois à générer

        Returns:
            Liste de tuples (date_début, date_fin) représentant des périodes d'un mois
        """
        periods = []
        # Utiliser datetime.now() avec timezone UTC explicite
        end_date = datetime.now().replace(tzinfo=timezone.utc)

        for i in range(max_months):
            # Calculer la date de début (un mois avant la date de fin)
            start_date = end_date - timedelta(days=30)

            # Ajouter la période
            periods.append((start_date, end_date))

            # La date de fin de la prochaine période est la date de début de celle-ci
            end_date = start_date

        return periods

    def _save_checkpoint(self, checkpoint_file: str) -> None:
        """
        Sauvegarde l'état de progression dans un fichier JSON

        Args:
            checkpoint_file: Chemin du fichier de checkpoint
        """
        checkpoint_data = {
            "collected_job_ids": list(self.collected_job_ids),
            "total_collected": self.total_collected,
            "timestamp": datetime.now().isoformat(),
        }

        with open(checkpoint_file, "w", encoding="utf-8") as f:
            json.dump(checkpoint_data, f)

        logger.info(
            f"Point de contrôle sauvegardé: {self.total_collected} offres collectées jusqu'à présent"
        )

    def _sanitize_text(self, text: Any) -> str:
        """
        Nettoie le texte pour éviter les problèmes dans les CSV

        Args:
            text: Texte à nettoyer

        Returns:
            Texte nettoyé
        """
        if text is None:
            return ""

        if not isinstance(text, str):
            text = str(text)

        # Remplacer les caractères problématiques
        text = text.replace("\r\n", " ").replace("\n", " ").replace("\r", " ")
        text = text.replace('"', '""')  # Échapper les guillemets pour le CSV

        # Supprimer les caractères de contrôle
        text = re.sub(r"[\x00-\x1F\x7F]", "", text)

        return text


async def main():
    """Fonction principale qui initialise et exécute le collecteur historique"""

    # Analyse des arguments de ligne de commande
    parser = argparse.ArgumentParser(
        description="Collecteur historique de données Adzuna"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=f'data/adzuna_jobs_{datetime.now().strftime("%Y%m%d")}.csv',
        help="Chemin du fichier de sortie CSV",
    )
    parser.add_argument(
        "--months", type=int, default=12, help="Nombre de mois à remonter dans le passé"
    )
    parser.add_argument(
        "--country",
        type=str,
        default="fr",
        help="Code pays pour la recherche (fr, uk, de, etc.)",
    )
    parser.add_argument(
        "--category",
        type=str,
        default="it-jobs",
        help="Code catégorie pour la recherche (it-jobs, etc.)",
    )
    parser.add_argument(
        "--results-per-page",
        type=int,
        default=50,
        help="Nombre de résultats par page (max 50)",
    )
    parser.add_argument(
        "--checkpoint-interval",
        type=int,
        default=100,
        help="Intervalle de sauvegarde de l'état (nombre d'offres)",
    )
    parser.add_argument(
        "--rate-limit-delay",
        type=float,
        default=0.5,
        help="Délai entre les requêtes API en secondes",
    )

    args = parser.parse_args()

    # Charger les variables d'environnement
    load_dotenv()

    # Récupérer les identifiants d'API depuis les variables d'environnement
    ADZUNA_APP_ID = environ.get("ADZUNA_APP_ID")
    ADZUNA_APP_KEY = environ.get("ADZUNA_APP_KEY")
    FRANCE_TRAVAIL_ID = environ.get("FRANCE_TRAVAIL_ID")
    FRANCE_TRAVAIL_KEY = environ.get("FRANCE_TRAVAIL_KEY")

    DEFAULT_CODE_ROME_ADZUNA = environ.get("DEFAULT_CODE_ROME_ADZUNA", "it-jobs")

    # Vérifier que les clés API sont bien définies
    required_env_vars = [
        "ADZUNA_APP_ID",
        "ADZUNA_APP_KEY",
        "FRANCE_TRAVAIL_ID",
        "FRANCE_TRAVAIL_KEY",
    ]

    missing_vars = [var for var in required_env_vars if not environ.get(var)]
    if missing_vars:
        logger.error(f"Variables d'environnement manquantes: {', '.join(missing_vars)}")
        logger.error(
            "Veuillez définir ces variables dans un fichier .env ou dans l'environnement"
        )
        return 1

    # Création du client Adzuna
    try:
        adzuna_client = AdzunaClient(
            app_id=environ.get("ADZUNA_APP_ID"), app_key=environ.get("ADZUNA_APP_KEY")
        )

        # Mapper le code pays de la ligne de commande vers l'énumération CountryCode
        country_map = {
            "fr": CountryCode.FR
            # 'gb': CountryCode.GB,
            # 'uk': CountryCode.GB,  # Alias pour GB
            # 'us': CountryCode.US,
            # 'de': CountryCode.DE,
            # 'at': CountryCode.AT,
            # 'au': CountryCode.AU,
            # 'be': CountryCode.BE,
            # 'ca': CountryCode.CA,
            # 'ch': CountryCode.CH,
            # 'it': CountryCode.IT,
            # 'nl': CountryCode.NL,
            # 'pl': CountryCode.PL,
            # 'ru': CountryCode.RU,
            # 'sg': CountryCode.SG,
            # 'za': CountryCode.ZA,
            # 'br': CountryCode.BR,
            # 'mx': CountryCode.MX,
            # 'in': CountryCode.IN
        }

        country_code = country_map.get(args.country.lower())
        if not country_code:
            logger.error(f"Code pays non reconnu: {args.country}")
            logger.error(f"Codes pays disponibles: {', '.join(country_map.keys())}")
            return 1

        # Initialisation du collecteur
        collector = AdzunaHistoricalCollector(
            adzuna_client=adzuna_client,
            country=country_code,
            category=args.category,
            results_per_page=args.results_per_page,
            rate_limit_delay=args.rate_limit_delay,
            checkpoint_interval=args.checkpoint_interval,
        )

        # Lancement de la collecte
        logger.info(
            f"Démarrage de la collecte pour {args.months} mois, pays: {args.country}"
        )
        logger.info(f"Fichier de sortie: {args.output}")

        output_file = await collector.collect_data(
            output_file=args.output, max_months=args.months
        )

        logger.info(
            f"Collecte terminée avec succès! Données enregistrées dans {output_file}"
        )
        return 0

    except Exception as e:
        logger.error(f"Erreur lors de l'exécution du collecteur: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Collecte interrompue par l'utilisateur")
        sys.exit(130)
    except Exception as e:
        logger.exception(f"Erreur non gérée: {e}")
        sys.exit(1)

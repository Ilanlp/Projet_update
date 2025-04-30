"""
Module de collecte historique des données France Travail

Ce module contient la classe FranceTravailHistoricalCollector qui permet de collecter
des offres d'emploi sur France Travail sur une longue période temporelle (plusieurs mois)
en utilisant une approche par départements et périodes pour maximiser la couverture.
"""

import os
from os import environ
import sys
import json
import csv
import asyncio
import logging
import re
import argparse
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from typing import List, Set, Any, Tuple

from france_travail import FranceTravailAPI, SearchParams
from jm_normalizer import JobDataNormalizer, NormalizedJobOffer

# Configuration du logging
logger = logging.getLogger(__name__)


class FranceTravailHistoricalCollector:
    """
    Collecteur de données historiques pour l'API France Travail

    Cette classe gère la collecte d'offres d'emploi sur une longue période
    en utilisant des stratégies pour maximiser la couverture et gérer les
    limites de l'API.
    """

    # Liste des codes départements français pour une recherche exhaustive
    DEPARTEMENTS = [
        "01",
        "02",
        "03",
        "04",
        "05",
        "06",
        "07",
        "08",
        "09",
        "10",
        "11",
        "12",
        "13",
        "14",
        "15",
        "16",
        "17",
        "18",
        "19",
        "21",
        "22",
        "23",
        "24",
        "25",
        "26",
        "27",
        "28",
        "29",
        "2A",
        "2B",
        "30",
        "31",
        "32",
        "33",
        "34",
        "35",
        "36",
        "37",
        "38",
        "39",
        "40",
        "41",
        "42",
        "43",
        "44",
        "45",
        "46",
        "47",
        "48",
        "49",
        "50",
        "51",
        "52",
        "53",
        "54",
        "55",
        "56",
        "57",
        "58",
        "59",
        "60",
        "61",
        "62",
        "63",
        "64",
        "65",
        "66",
        "67",
        "68",
        "69",
        "70",
        "71",
        "72",
        "73",
        "74",
        "75",
        "76",
        "77",
        "78",
        "79",
        "80",
        "81",
        "82",
        "83",
        "84",
        "85",
        "86",
        "87",
        "88",
        "89",
        "90",
        "91",
        "92",
        "93",
        "94",
        "95",
        "971",
        "972",
        "973",
        "974",
        "976",  # DOM-TOM
    ]

    # Liste des codes ROME pour une recherche exhaustive
    # Ces codes correspondent aux classifications ROME utilisées par France Travail
    CODE_ROME = ["M1811", "M1827", "M1851", "K1906", "M1405"]

    def __init__(
        self,
        france_travail_api: FranceTravailAPI,
        results_per_page: int = 150,  # 150 est souvent la limite max pour FranceTravail
        retry_count: int = 3,
        retry_delay: int = 5,
        rate_limit_delay: float = 1.0,  # Plus conservateur car l'API est moins tolérante
        checkpoint_interval: int = 100,
    ):
        """
        Initialise le collecteur de données historiques

        Args:
            france_travail_api: Client API France Travail existant
            results_per_page: Nombre de résultats par page (max souvent 150)
            retry_count: Nombre de tentatives en cas d'erreur
            retry_delay: Délai (en secondes) entre les tentatives
            rate_limit_delay: Délai entre les requêtes pour éviter les limites de taux
            checkpoint_interval: Intervalle de sauvegarde de l'état (nombre d'offres)
        """
        self.france_travail_api = france_travail_api
        self.results_per_page = min(
            results_per_page, 150
        )  # S'assurer de ne pas dépasser la limite
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self.rate_limit_delay = rate_limit_delay
        self.checkpoint_interval = checkpoint_interval

        # État interne
        self.collected_job_ids: Set[str] = set()
        self.total_collected = 0

    async def collect_data(
        self, output_file: str, max_months: int = 12, search_terms: str = None
    ) -> str:
        """
        Collecte les données d'offres d'emploi et les sauvegarde en CSV

        Les données sont normalisées via NormalizedJobOffer avant d'être sauvegardées.
        Le header du CSV correspond exactement aux propriétés de NormalizedJobOffer.

        Args:
            output_file: Chemin du fichier CSV de sortie
            max_months: Nombre maximum de mois à remonter dans le temps
            search_terms: Termes de recherche optionnels

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

            # Parcourir les départements
            # for departement in self.DEPARTEMENTS:
                for code_rome in self.CODE_ROME:
                    for period_start, period_end in time_periods:
                        # Convertir les dates au format attendu par France Travail (YYYY-MM-DD)
                        date_debut = period_start.strftime("%Y-%m-%dT%H:%M:%SZ")
                        date_fin = period_end.strftime("%Y-%m-%dT%H:%M:%SZ")

                        logger.info(
                            # f"Collecte des offres pour le département '{departement}', codeRome '{code_rome}' "
                            f"du {date_debut} au {date_fin}"
                        )

                        total_for_period = 0
                        start_index = 0
                        has_more_results = True

                        while has_more_results:
                            try:
                                # Ajouter une pause pour éviter les limites de taux
                                await asyncio.sleep(self.rate_limit_delay)

                                # Préparer les paramètres de recherche
                                search_params = SearchParams(
                                    motsCles=search_terms,
                                    # departement=departement,
                                    codeROME=code_rome,
                                    minCreationDate=date_debut,
                                    maxCreationDate=date_fin,
                                    range=f"{start_index}-{start_index + self.results_per_page - 1}",
                                    sort=1,  # Tri par date décroissant
                                )

                                # Effectuer la requête avec retry
                                results = None
                                for retry in range(self.retry_count + 1):
                                    try:
                                        if retry > 0:
                                            logger.info(
                                                f"Tentative {retry}/{self.retry_count}..."
                                            )
                                            await asyncio.sleep(
                                                self.retry_delay * (2 ** (retry - 1))
                                            )

                                        # Effectuer la requête
                                        results = self.france_travail_api.search_offers(
                                            search_params
                                        )
                                        break
                                    except Exception as e:
                                        logger.warning(
                                            f"Erreur lors de la recherche: {e}"
                                        )
                                        if retry == self.retry_count:
                                            logger.error(
                                                f"Abandon après {self.retry_count} tentatives"
                                            )
                                            results = None

                                # Si toutes les tentatives ont échoué, passer à la période suivante
                                if not results or not results.resultats:
                                    logger.info(
                                        f"Aucun résultat ou erreur. Passage à la période suivante."
                                    )
                                    has_more_results = False
                                    break

                                # Récupérer les offres
                                jobs = results.resultats
                                logger.info(f"Récupéré {len(jobs)} offres d'emploi")

                                # Filtrer les offres déjà collectées
                                filtered_jobs = []
                                for job in jobs:
                                    if job.id not in self.collected_job_ids:
                                        filtered_jobs.append(job)
                                        self.collected_job_ids.add(job.id)

                                # Normaliser et écrire les offres dans le CSV
                                for job in filtered_jobs:
                                    try:
                                        # Convertir l'objet Job en dictionnaire et le normaliser
                                        job_dict = job.model_dump()

                                        # Normaliser l'offre en utilisant le modèle NormalizedJobOffer
                                        normalized_job = (
                                            normalizer.normalize_france_travail_job(
                                                job_dict
                                            )
                                        )

                                        # Convertir l'offre normalisée en dictionnaire pour l'écriture CSV
                                        normalized_dict = normalized_job.model_dump()

                                        # Vérifier que toutes les clés correspondent au schéma attendu
                                        if set(normalized_dict.keys()) != set(
                                            fieldnames
                                        ):
                                            missing_keys = set(fieldnames) - set(
                                                normalized_dict.keys()
                                            )
                                            extra_keys = set(
                                                normalized_dict.keys()
                                            ) - set(fieldnames)

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
                                                normalized_dict[key] = (
                                                    self._sanitize_text(value)
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
                                    f"Ajouté {len(filtered_jobs)} nouvelles offres. "
                                    f"Total pour cette période: {total_for_period}"
                                )

                                # Sauvegarde périodique de l'état
                                if self.total_collected % self.checkpoint_interval == 0:
                                    self._save_checkpoint(checkpoint_file)

                                # Vérifier s'il y a plus de résultats
                                # L'API France Travail ne fournit pas d'attribut 'totalResultats'
                                # Utiliser une stratégie alternative pour la pagination

                                # Enregistrer le nombre d'offres récupérées dans cette requête
                                current_batch_size = len(jobs)
                                start_index += current_batch_size

                                # Déterminer s'il faut continuer la pagination en se basant sur le nombre d'offres retournées
                                # Si on a reçu moins que le nombre maximum demandé, c'est probablement la fin
                                # Ou si on a atteint la limite habituelle de l'API (1000 résultats max)
                                if (
                                    current_batch_size < self.results_per_page
                                    or start_index >= 1000
                                ):
                                    has_more_results = False
                                    logger.info(
                                        f"Fin de la pagination: {current_batch_size} < {self.results_per_page} ou limite atteinte ({start_index})"
                                    )
                                else:
                                    logger.info(
                                        f"Continuation de la pagination: {start_index} résultats traités jusqu'à présent"
                                    )

                            except Exception as e:
                                logger.error(
                                    f"Erreur non gérée lors de la collecte: {e}",
                                    exc_info=True,
                                )
                                # Attendre et continuer avec la période suivante
                                await asyncio.sleep(self.retry_delay)
                                has_more_results = False

                        # Sauvegarde de l'état à la fin de chaque période
                        self._save_checkpoint(checkpoint_file)

        logger.info(
            f"Collecte terminée! {self.total_collected} offres d'emploi normalisées collectées au total."
        )
        return output_file

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
    """Fonction principale qui initialise et exécute le collecteur historique France Travail"""

    # Analyse des arguments de ligne de commande
    parser = argparse.ArgumentParser(
        description="Collecteur historique de données France Travail"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=f'data/france_travail_jobs_{datetime.now().strftime("%Y%m%d")}.csv',
        help="Chemin du fichier de sortie CSV",
    )
    parser.add_argument(
        "--months", type=int, default=12, help="Nombre de mois à remonter dans le passé"
    )
    parser.add_argument(
        "--search", type=str, default=None, help="Termes de recherche optionnels"
    )
    parser.add_argument(
        "--results-per-page",
        type=int,
        default=150,
        help="Nombre de résultats par page (max 150)",
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
        default=1.0,
        help="Délai entre les requêtes API en secondes",
    )

    args = parser.parse_args()

    # Charger les variables d'environnement
    load_dotenv()
    # Récupérer les identifiants d'API depuis les variables d'environnement
    adzuna_app_id = environ.get("ADZUNA_APP_ID")
    adzuna_app_key = environ.get("ADZUNA_APP_KEY")
    france_travail_id = environ.get("FRANCE_TRAVAIL_ID")
    france_travail_key = environ.get("FRANCE_TRAVAIL_KEY")

    # Vérifier que les clés API sont bien définies
    required_env_vars = [
        "FRANCE_TRAVAIL_ID",
        "FRANCE_TRAVAIL_KEY",
        "ADZUNA_APP_ID",  # Nécessaire pour le normalisateur
        "ADZUNA_APP_KEY",  # Nécessaire pour le normalisateur
    ]

    missing_vars = [var for var in required_env_vars if not environ.get(var)]
    if missing_vars:
        logger.error(f"Variables d'environnement manquantes: {', '.join(missing_vars)}")
        logger.error(
            "Veuillez définir ces variables dans un fichier .env ou dans l'environnement"
        )
        return 1

    # Création du client France Travail
    try:
        france_travail_api = FranceTravailAPI(
            client_id=france_travail_id,
            client_secret=france_travail_key,
        )

        # Initialisation du collecteur
        collector = FranceTravailHistoricalCollector(
            france_travail_api=france_travail_api,
            results_per_page=args.results_per_page,
            rate_limit_delay=args.rate_limit_delay,
            checkpoint_interval=args.checkpoint_interval,
        )

        # Lancement de la collecte
        logger.info(f"Démarrage de la collecte pour {args.months} mois")
        if args.search:
            logger.info(f"Termes de recherche: {args.search}")
        logger.info(f"Fichier de sortie: {args.output}")

        output_file = await collector.collect_data(
            output_file=args.output, max_months=args.months, search_terms=args.search
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

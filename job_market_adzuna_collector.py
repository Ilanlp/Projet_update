"""
Module de collecte historique des données Adzuna

Ce module contient la classe AdzunaHistoricalCollector qui permet de collecter
des offres d'emploi sur Adzuna sur une longue période temporelle (plusieurs mois)
en utilisant une approche par catégories et périodes pour maximiser la couverture.
"""

import os
import json
import csv
import time
import asyncio
import logging
import httpx
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Set, Any, Tuple, Optional
from pydantic import TypeAdapter

from adzuna_api import AdzunaClient, CountryCode, Job, Category, AdzunaClientError

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
        results_per_page: int = 50,
        retry_count: int = 3,
        retry_delay: int = 5,
        rate_limit_delay: float = 0.5,
        checkpoint_interval: int = 100
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
    
    async def collect_data(
        self, 
        output_file: str, 
        max_months: int = 12
    ) -> str:
        """
        Collecte les données d'offres d'emploi et les sauvegarde en CSV
        
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
                with open(checkpoint_file, 'r', encoding='utf-8') as f:
                    checkpoint_data = json.load(f)
                    self.collected_job_ids = set(checkpoint_data.get("collected_job_ids", []))
                    self.total_collected = checkpoint_data.get("total_collected", 0)
                    timestamp = checkpoint_data.get("timestamp")
                    logger.info(f"Point de contrôle chargé du {timestamp}: "
                                f"{self.total_collected} offres déjà collectées")
            except Exception as e:
                logger.warning(f"Erreur lors du chargement du point de contrôle: {e}")
        
        # Initialiser le collecteur (récupérer les catégories)
        await self.initialize()
        
        # Générer les périodes temporelles (tranches d'un mois)
        time_periods = self._generate_time_periods(max_months)
        logger.info(f"Collecte des données sur {len(time_periods)} périodes temporelles")
        
        # Préparer le fichier CSV
        file_exists = os.path.exists(output_file)
        has_content = False
        
        if file_exists:
            # Vérifier si le fichier contient des données
            try:
                with open(output_file, 'r', newline='', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    header = next(reader, None)
                    has_content = header is not None
            except Exception as e:
                logger.warning(f"Erreur lors de la lecture du fichier existant: {e}")
                has_content = False
        
        # Mode d'ouverture: 'a' (append) si le fichier existe et a du contenu, sinon 'w' (write)
        mode = 'a' if file_exists and has_content else 'w'
        
        with open(output_file, mode, newline='', encoding='utf-8') as csv_file:
            # Définir les noms de champs
            fieldnames = self._get_csv_fieldnames()
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            
            # Si on est en mode écriture, écrire l'en-tête
            if mode == 'w':
                writer.writeheader()
                logger.info(f"En-tête CSV écrit dans {output_file}")
            else:
                logger.info(f"Ajout des données au fichier existant {output_file}")
            
            # Parcourir les catégories et les périodes
            for category in self.categories:
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
                                    sort_by="date"  # Tri par date, sans préciser la direction
                                )
                                
                                # Convertir en objets Job
                                job_list_adapter = TypeAdapter(List[Job])
                                
                                # Si la réponse contient des résultats, les convertir en objets Job
                                if "results" in data and data["results"]:
                                    results_list = job_list_adapter.validate_python(data["results"])
                                else:
                                    results_list = []
                                
                            except AdzunaClientError as e:
                                logger.warning(f"Erreur API pour la page {page}: {e}")
                                # Implémenter un backoff exponentiel
                                for retry in range(self.retry_count):
                                    delay = self.retry_delay * (2 ** retry)
                                    logger.info(f"Nouvelle tentative dans {delay} secondes...")
                                    await asyncio.sleep(delay)
                                    
                                    try:
                                        # Réessayer la requête
                                        data = await self._search_jobs_direct(
                                            page=page,
                                            category=category.tag,
                                            results_per_page=self.results_per_page,
                                            max_days_old=max_days_old,
                                            sort_by="date"
                                        )
                                        
                                        # Convertir en objets Job
                                        if "results" in data and data["results"]:
                                            results_list = job_list_adapter.validate_python(data["results"])
                                        else:
                                            results_list = []
                                        
                                        # Si on arrive ici, la requête a réussi
                                        break
                                    except AdzunaClientError as retry_error:
                                        logger.warning(f"Échec de la tentative {retry+1}: {retry_error}")
                                        # Si c'est la dernière tentative, abandonner cette page
                                        if retry == self.retry_count - 1:
                                            logger.error(f"Abandon de la page {page} après {self.retry_count} tentatives")
                                            results_list = []
                                            has_more_results = False
                            
                            # Vérifier s'il y a des résultats
                            if not results_list:
                                logger.info(f"Plus de résultats pour cette période. Total: {total_for_period}")
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
                                job_date = datetime.fromisoformat(job.created.replace('Z', '+00:00'))
                                if period_start <= job_date <= period_end:
                                    filtered_jobs.append(job)
                                    self.collected_job_ids.add(job.id)
                            
                            # Si aucune offre après filtrage, passer à la page suivante
                            if not filtered_jobs:
                                page += 1
                                if page > 100:  # Limite de pagination Adzuna
                                    has_more_results = False
                                continue
                            
                            # Transforme chaque offre au format CSV et l'écrit
                            for job in filtered_jobs:
                                job_dict = self._job_to_dict(job)
                                writer.writerow(job_dict)
                                csv_file.flush()  # S'assurer que les données sont écrites sur le disque
                                
                                total_for_period += 1
                                self.total_collected += 1
                            
                            # Log de progression
                            logger.info(f"Page {page}: {len(filtered_jobs)} nouvelles offres ajoutées. "
                                       f"Total pour cette période: {total_for_period}")
                            
                            # Sauvegarde périodique de l'état
                            if self.total_collected % self.checkpoint_interval == 0:
                                self._save_checkpoint(checkpoint_file)
                            
                            # Passer à la page suivante
                            page += 1
                            if page > 100:  # Limite de pagination Adzuna
                                has_more_results = False
                            
                        except Exception as e:
                            logger.error(f"Erreur non gérée lors de la collecte: {e}", exc_info=True)
                            # Attendre et continuer avec la page suivante
                            await asyncio.sleep(self.retry_delay)
                            page += 1
                            if page > 100:  # Limite de pagination Adzuna
                                has_more_results = False
                    
                    # Sauvegarde de l'état à la fin de chaque période
                    self._save_checkpoint(checkpoint_file)
        
        logger.info(f"Collecte terminée! {self.total_collected} offres d'emploi collectées au total.")
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
            **params
        }
        
        # Créer un client HTTP temporaire pour cette requête
        async with httpx.AsyncClient(base_url="https://api.adzuna.com/v1/api") as client:
            endpoint = f"/jobs/{self.country.value}/search/{page}"
            
            try:
                response = await client.get(endpoint, params=query_params)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                error_message = f"Erreur HTTP: {str(e)}"
                raise AdzunaClientError(error_message) from e
    
    def _job_to_dict(self, job: Job) -> Dict[str, Any]:
        """
        Convertit un objet Job en dictionnaire plat pour le CSV
        
        Args:
            job: Objet Job à convertir
            
        Returns:
            Dictionnaire avec les données de l'offre d'emploi
        """
        job_dict = {
            "id": job.id,
            "title": job.title,
            "description": job.description,
            "created": job.created,
            "redirect_url": job.redirect_url,
            "salary_min": job.salary_min,
            "salary_max": job.salary_max,
            "salary_is_predicted": job.salary_is_predicted,
            "contract_time": job.contract_time,
            "contract_type": job.contract_type,
            "latitude": job.latitude,
            "longitude": job.longitude,
            "category_tag": job.category.tag if job.category else None,
            "category_label": job.category.label if job.category else None,
        }
        
        # Ajouter les données de localisation si disponibles
        if job.location:
            job_dict["location_display_name"] = job.location.display_name
            if job.location.area:
                for i, area in enumerate(job.location.area):
                    job_dict[f"location_area_{i}"] = area
        
        # Ajouter les données d'entreprise si disponibles
        if job.company:
            job_dict["company_display_name"] = job.company.display_name
            job_dict["company_canonical_name"] = job.company.canonical_name
        
        return job_dict
    
    def _get_csv_fieldnames(self) -> List[str]:
        """
        Définit les noms de champs pour le CSV
        
        Returns:
            Liste des noms de colonnes pour le CSV
        """
        return [
            "id", "title", "description", "created", "redirect_url",
            "salary_min", "salary_max", "salary_is_predicted",
            "contract_time", "contract_type", "latitude", "longitude",
            "category_tag", "category_label", "location_display_name",
            "location_area_0", "location_area_1", "location_area_2", "location_area_3",
            "location_area_4", "location_area_5", "location_area_6", "location_area_7",
            "company_display_name", "company_canonical_name"
        ]
    
    def _generate_time_periods(self, max_months: int) -> List[Tuple[datetime, datetime]]:
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
            "timestamp": datetime.now().isoformat()
        }
        
        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint_data, f)
        
        logger.info(f"Point de contrôle sauvegardé: {self.total_collected} offres collectées jusqu'à présent")

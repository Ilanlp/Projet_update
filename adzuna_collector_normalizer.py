#!/usr/bin/env python
"""
Script de collecte de données d'offres d'emploi Adzuna

Ce script utilise l'API Adzuna pour récupérer des offres d'emploi sur la plus longue période
possible et les sauvegarder dans un fichier CSV. Il utilise une stratégie de collecte par périodes
temporelles et par catégories pour maximiser la couverture des données.

Utilisation:
    python adzuna_collector.py --country fr --output data/jobs.csv --months 12
"""

import os
import sys
import csv
import json
import time
import asyncio
import logging
import argparse
import httpx
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Set, Optional, Any, Tuple
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
from enum import Enum
from job_market_normalizer import NormalizedJobOffer, JobDataNormalizer

# Importer notre client Adzuna (ajustez le chemin d'importation si nécessaire)
from adzuna_api import AdzunaClient, CountryCode, Job, AdzunaClientError, Category


# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("adzuna_collector.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("AdzunaCollector")


class AdzunaDataCollector:
    """
    Collecteur de données pour l'API Adzuna
    
    Cette classe gère la collecte d'offres d'emploi sur une longue période
    en utilisant des stratégies pour maximiser la couverture et gérer les
    limites de l'API.
    """
    
    def __init__(
        self,
        app_id: str,
        app_key: str,
        country: CountryCode,
        output_file: str,
        max_months: int = 12,
        results_per_page: int = 50,
        retry_count: int = 3,
        retry_delay: int = 5,
        rate_limit_delay: float = 0.5,
        checkpoint_interval: int = 100
    ):
        """
        Initialise le collecteur de données
        
        Args:
            app_id: Identifiant d'application Adzuna
            app_key: Clé d'API Adzuna
            country: Code pays pour la recherche
            output_file: Chemin du fichier CSV de sortie
            max_months: Nombre maximum de mois à remonter dans le temps
            results_per_page: Nombre de résultats par page (max 50 pour Adzuna)
            retry_count: Nombre de tentatives en cas d'erreur
            retry_delay: Délai (en secondes) entre les tentatives
            rate_limit_delay: Délai (en secondes) entre les requêtes pour éviter les limites de taux
            checkpoint_interval: Intervalle de sauvegarde de l'état (nombre d'offres)
        """
        self.app_id = app_id
        self.app_key = app_key
        self.country = country
        self.output_file = output_file
        self.max_months = max_months
        self.results_per_page = results_per_page
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self.rate_limit_delay = rate_limit_delay
        self.checkpoint_interval = checkpoint_interval
        
        # État interne
        self.client = None
        self.collected_job_ids: Set[str] = set()
        self.total_collected = 0
        self.categories: List[Category] = []
        self.checkpoint_file = f"{output_file}.checkpoint"
        
        # S'assurer que le répertoire de sortie existe
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    async def initialize(self):
        """Initialise le client et charge les catégories"""
        self.client = AdzunaClient(self.app_id, self.app_key)
        
        # Charger l'état de progression si disponible
        await self._load_checkpoint()
        
        # Récupérer toutes les catégories disponibles
        try:
            categories_result = await self.client.get_categories(self.country)
            self.categories = categories_result.results
            logger.info(f"Récupération de {len(self.categories)} catégories d'emploi")
        except AdzunaClientError as e:
            logger.error(f"Erreur lors de la récupération des catégories: {e}")
            raise
    
    async def close(self):
        """Ferme le client et les ressources"""
        if self.client:
            await self.client.close()
    
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
            "app_id": self.app_id,
            "app_key": self.app_key,
            **params
        }
        
        # Créer un client HTTP temporaire pour cette requête
        async with httpx.AsyncClient(base_url="https://api.adzuna.com/v1/api") as client:
            endpoint = f"/jobs/{self.country.value}/search/{page}"
            
            try:
                response = await client.get(endpoint, params=query_params)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                error_message = f"HTTP error {e.response.status_code}"
                try:
                    error_data = e.response.json()
                    if "exception" in error_data:
                        error_message += f": {error_data['exception']}"
                    if "display" in error_data:
                        error_message += f" - {error_data['display']}"
                except:
                    pass
                raise AdzunaClientError(error_message) from e
            except httpx.RequestError as e:
                raise AdzunaClientError(f"Request error: {str(e)}") from e
    
    async def collect_data(self):
        """
        Collecte les données d'offres d'emploi et les sauvegarde en CSV
        
        Stratégie:
        1. Pour chaque catégorie d'emploi
        2. Pour chaque période d'un mois, en remontant dans le temps
        3. Collecter toutes les pages de résultats
        """
        try:
            await self.initialize()
            
            # Générer les périodes temporelles (tranches d'un mois)
            time_periods = self._generate_time_periods()
            logger.info(f"Collecte des données sur {len(time_periods)} périodes temporelles")
            
            # Préparer le fichier CSV s'il n'existe pas encore
            file_exists = os.path.exists(self.output_file)
            has_content = False
            
            if file_exists:
                # Vérifier si le fichier contient des données
                try:
                    with open(self.output_file, 'r', newline='', encoding='utf-8') as f:
                        reader = csv.reader(f)
                        header = next(reader, None)
                        has_content = header is not None
                except Exception as e:
                    logger.warning(f"Erreur lors de la lecture du fichier existant: {e}")
                    has_content = False
            
            # Mode d'ouverture: 'a' (append) si le fichier existe et a du contenu, sinon 'w' (write)
            mode = 'a' if file_exists and has_content else 'w'
            
            with open(self.output_file, mode, newline='', encoding='utf-8') as csv_file:
                # Définir les noms de champs
                fieldnames = self._get_csv_fieldnames()
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                
                # Si on est en mode écriture, écrire l'en-tête
                if mode == 'w':
                    writer.writeheader()
                    logger.info(f"En-tête CSV écrit dans {self.output_file}")
                else:
                    logger.info(f"Ajout des données au fichier existant {self.output_file}")
                
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
                                
                                try:
                                    # Utiliser notre méthode personnalisée sans sort_dir
                                    data = await self._search_jobs_direct(
                                        page=page,
                                        category=category.tag,
                                        results_per_page=self.results_per_page,
                                        max_days_old=max_days_old,
                                        sort_by="date"  # Tri par date, sans préciser la direction
                                    )
                                    
                                    # Convertir en objets Job
                                    from pydantic import TypeAdapter
                                    from typing import List
                                    
                                    # Adapter pour la liste de jobs
                                    job_list_adapter = TypeAdapter(List[Job])
                                    
                                    # Si la réponse contient des résultats, les convertir en objets Job
                                    if "results" in data and data["results"]:
                                        results_list = job_list_adapter.validate_python(data["results"])
                                    else:
                                        results_list = []
                                    
                                    # Créer un objet similaire à la réponse de client.search_jobs
                                    class Results:
                                        def __init__(self, results):
                                            self.results = results
                                    
                                    results = Results(results_list)
                                
                                except AdzunaClientError as e:
                                    logger.warning(f"Erreur API pour la page {page}: {e}")
                                    # Implémenter un backoff exponentiel
                                    for retry in range(self.retry_count):
                                        delay = self.retry_delay * (2 ** retry)
                                        logger.info(f"Nouvelle tentative dans {delay} secondes...")
                                        await asyncio.sleep(delay)
                                        
                                        try:
                                            # Réessayer la requête sans sort_dir
                                            await asyncio.sleep(self.rate_limit_delay)
                                            data = await self._search_jobs_direct(
                                                page=page,
                                                category=category.tag,
                                                results_per_page=self.results_per_page,
                                                max_days_old=max_days_old,
                                                sort_by="date"  # Tri par date, sans préciser la direction
                                            )
                                            
                                            # Convertir en objets Job
                                            if "results" in data and data["results"]:
                                                results_list = job_list_adapter.validate_python(data["results"])
                                            else:
                                                results_list = []
                                            
                                            results = Results(results_list)
                                            
                                            # Si on arrive ici, la requête a réussi
                                            break
                                        except AdzunaClientError as retry_error:
                                            logger.warning(f"Échec de la tentative {retry+1}: {retry_error}")
                                            # Si c'est la dernière tentative, abandonner cette page
                                            if retry == self.retry_count - 1:
                                                logger.error(f"Abandon de la page {page} après {self.retry_count} tentatives")
                                                has_more_results = False
                                
                                # Vérifier s'il y a des résultats
                                if not results.results:
                                    logger.info(f"Plus de résultats pour cette période. Total: {total_for_period}")
                                    has_more_results = False
                                    break
                                
                                # Filtrer pour ne garder que les offres dans la période spécifiée
                                # et celles qu'on n'a pas encore traitées
                                filtered_jobs = []
                                for job in results.results:
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
                                
                                
                                normalizer = JobDataNormalizer(os.getenv("ADZUNA_APP_ID"),os.getenv("ADZUNA_APP_KEY"),os.getenv("FRANCE_TRAVAIL_ID"),os.getenv("FRANCE_TRAVAIL_KEY"))

                                # Transforme chaque offre au format CSV et l'écrit
                                for job in filtered_jobs:
                                    #job_data = self._job_to_dict(job)
                                    job_data = normalizer.normalize_adzuna_job(job.model_dump())
                                    job_data = job_data.model_dump()
                                    writer.writerow(job_data)
                                    csv_file.flush()  # S'assurer que les données sont écrites sur le disque
                                    
                                    total_for_period += 1
                                    self.total_collected += 1
                                
                                # Log de progression
                                logger.info(f"Page {page}: {len(filtered_jobs)} nouvelles offres ajoutées. "
                                            f"Total pour cette période: {total_for_period}")
                                
                                # Sauvegarde périodique de l'état
                                if self.total_collected % self.checkpoint_interval == 0:
                                    await self._save_checkpoint()
                                
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
                        await self._save_checkpoint()
            
            logger.info(f"Collecte terminée! {self.total_collected} offres d'emploi collectées au total.")
        
        finally:
            await self.close()
    
    def _generate_time_periods(self) -> List[Tuple[datetime, datetime]]:
        """
        Génère des périodes temporelles d'un mois, en remontant dans le temps
        
        Returns:
            Liste de tuples (date_début, date_fin) représentant des périodes d'un mois
        """
        periods = []
        # Utiliser datetime.now() avec timezone UTC explicite
        end_date = datetime.now().replace(tzinfo=timezone.utc)
        
        for i in range(self.max_months):
            # Calculer la date de début (un mois avant la date de fin)
            start_date = end_date - timedelta(days=30)
            
            # Ajouter la période
            periods.append((start_date, end_date))
            
            # La date de fin de la prochaine période est la date de début de celle-ci
            end_date = start_date
        
        return periods
    
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
        return [
            "id", "title", "description", "created", "redirect_url",
            "salary_min", "salary_max", "salary_is_predicted",
            "contract_time", "contract_type", "latitude", "longitude",
            "category_tag", "category_label", "location_display_name",
            "location_area_0", "location_area_1", "location_area_2", "location_area_3",
            "location_area_4", "location_area_5", "location_area_6", "location_area_7",
            "company_display_name", "company_canonical_name"
        ]
        """
        return [
                "id",
                "source",
                "title",
                "description",
                "company_name",
                "location_name",
                "latitude",
                "longitude",
                "date_created",
                "date_updated",
                "contract_type",
                "contract_duration",
                "working_hours",
                "salary_min",
                "salary_max",
                "salary_currency",
                "salary_period",
                "experience_required",
                "category",
                "sector",
                "application_url",
                "source_url",
                "skills",
                "remote_work",
                "is_handicap_accessible"
        ]

    async def _save_checkpoint(self):
        """Sauvegarde l'état de progression"""
        checkpoint_data = {
            "collected_job_ids": list(self.collected_job_ids),
            "total_collected": self.total_collected,
            "timestamp": datetime.now().isoformat()
        }
        
        with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint_data, f)
        
        logger.info(f"Point de contrôle sauvegardé: {self.total_collected} offres collectées jusqu'à présent")
    
    async def _load_checkpoint(self):
        """Charge l'état de progression s'il existe"""
        if os.path.exists(self.checkpoint_file):
            try:
                with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                    checkpoint_data = json.load(f)
                
                self.collected_job_ids = set(checkpoint_data.get("collected_job_ids", []))
                self.total_collected = checkpoint_data.get("total_collected", 0)
                timestamp = checkpoint_data.get("timestamp")
                
                logger.info(f"Point de contrôle chargé du {timestamp}: "
                            f"{self.total_collected} offres déjà collectées")
            except Exception as e:
                logger.warning(f"Erreur lors du chargement du point de contrôle: {e}")
                # Continuer avec un état vide
                self.collected_job_ids = set()
                self.total_collected = 0
    
    async def get_trending_skills(self, country: CountryCode, job_title: str, top_n: int = 10) -> List[Tuple[str, int]]:
        """
        Analyse les offres d'emploi pour trouver les compétences les plus demandées
        
        Args:
            country: Le code pays pour la recherche
            job_title: Le titre de poste à rechercher (ex: "data engineer")
            top_n: Nombre de compétences à retourner
            
        Returns:
            Liste de tuples (compétence, nombre d'occurrences)
        """
        # Liste de compétences techniques à rechercher dans les descriptions
        skills = [
            "python", "java", "javascript", "js", "typescript", "ts", 
            "c#", "c++", "go", "golang", "rust", "php", "ruby", "swift",
            "sql", "mysql", "postgresql", "mongodb", "nosql", "oracle", "sqlite",
            "aws", "azure", "gcp", "cloud", "docker", "kubernetes", "k8s",
            "git", "ci/cd", "jenkins", "gitlab", "github", "bitbucket",
            "react", "angular", "vue", "node", "express", "django", "flask", "spring",
            "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy", "spark", "hadoop",
            "linux", "unix", "bash", "shell", "powershell", "windows",
            "agile", "scrum", "kanban", "jira", "confluence",
            "rest", "graphql", "api", "microservices", "soa", "soap",
            "html", "css", "sass", "less", "bootstrap", "tailwind",
            "etl", "data warehouse", "data lake", "big data",
            "machine learning", "ml", "ai", "deep learning", "nlp", 
            "devops", "sre", "security", "blockchain", "iot", "embedded"
        ]
        
        # Rechercher les offres
        try:
            # Utiliser la méthode directe sans sort_dir
            data = await self._search_jobs_direct(
                page=1,
                what=job_title,
                results_per_page=100,
                max_days_old=30,  # Limiter aux 30 derniers jours pour les tendances actuelles
                sort_by="date"
            )
            
            # Convertir en objets Job
            from pydantic import TypeAdapter
            from typing import List
            
            # Adapter pour la liste de jobs
            job_list_adapter = TypeAdapter(List[Job])
            
            # Si la réponse contient des résultats, les convertir en objets Job
            if "results" in data and data["results"]:
                jobs = job_list_adapter.validate_python(data["results"])
            else:
                jobs = []
            
            # Compter les occurrences de chaque compétence
            skill_counts = {skill: 0 for skill in skills}
            
            for job in jobs:
                description_lower = job.description.lower()
                for skill in skills:
                    # Recherche du mot entier (avec délimiteurs avant/après)
                    # Cela évite de compter "java" dans "javascript" par exemple
                    if re.search(r'\b' + re.escape(skill) + r'\b', description_lower):
                        skill_counts[skill] += 1
            
            # Trier par nombre d'occurrences
            sorted_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)
            
            # Retourner les top N compétences qui apparaissent au moins une fois
            return [(skill, count) for skill, count in sorted_skills if count > 0][:top_n]
            
        except AdzunaClientError as e:
            logger.error(f"Erreur lors de la recherche des compétences tendance: {e}")
            return []


async def main():
    """Fonction principale du script"""
    # Charger les variables d'environnement
    load_dotenv()
    
    # Parser les arguments de ligne de commande
    parser = argparse.ArgumentParser(description="Collecteur de données Adzuna")
    
    parser.add_argument(
        "--country",
        type=str,
        default="fr",
        help="Code pays (ex: fr, gb, us)"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default="adzuna_jobs.csv",
        help="Fichier CSV de sortie"
    )
    
    parser.add_argument(
        "--months",
        type=int,
        default=12,
        help="Nombre de mois à remonter dans le temps"
    )
    
    parser.add_argument(
        "--results-per-page",
        type=int,
        default=50,
        help="Nombre de résultats par page (max 50)"
    )
    
    parser.add_argument(
        "--retry-count",
        type=int,
        default=3,
        help="Nombre de tentatives en cas d'erreur"
    )
    
    parser.add_argument(
        "--retry-delay",
        type=int,
        default=5,
        help="Délai initial entre les tentatives (en secondes)"
    )
    
    parser.add_argument(
        "--rate-limit-delay",
        type=float,
        default=0.5,
        help="Délai entre les requêtes (en secondes)"
    )
    
    args = parser.parse_args()
    
    # Récupérer les identifiants d'API depuis les variables d'environnement
    app_id = os.getenv("ADZUNA_APP_ID")
    app_key = os.getenv("ADZUNA_APP_KEY")
    
    if not app_id or not app_key:
        logger.error("Les identifiants ADZUNA_APP_ID et ADZUNA_APP_KEY doivent être définis dans le fichier .env")
        return 1
    
    try:
        # Valider le code pays
        country_code = CountryCode(args.country.lower())
    except ValueError:
        logger.error(f"Code pays invalide: {args.country}")
        return 1
    
    # Créer et exécuter le collecteur
    collector = AdzunaDataCollector(
        app_id=app_id,
        app_key=app_key,
        country=country_code,
        output_file=args.output,
        max_months=args.months,
        results_per_page=args.results_per_page,
        retry_count=args.retry_count,
        retry_delay=args.retry_delay,
        rate_limit_delay=args.rate_limit_delay
    )
    
    logger.info(f"Démarrage de la collecte des données pour {args.country.upper()} "
                f"sur {args.months} mois")
    
    start_time = time.time()
    await collector.collect_data()
    end_time = time.time()
    
    duration = end_time - start_time
    hours, remainder = divmod(duration, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    logger.info(f"Collecte terminée en {int(hours)}h {int(minutes)}m {int(seconds)}s")
    logger.info(f"Total des offres collectées: {collector.total_collected}")
    logger.info(f"Données sauvegardées dans: {args.output}")
    
    return 0


if __name__ == "__main__":
    import re  # Pour la recherche de compétences avec regex
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Collecte interrompue par l'utilisateur")
        sys.exit(130)
    except Exception as e:
        logger.exception(f"Erreur non gérée: {e}")
        sys.exit(1)

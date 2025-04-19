"""
Normalisateur de données d'emploi pour les API Adzuna et France Travail
Ce script utilise les clients API existants pour récupérer les données
et les normaliser dans un format commun en utilisant pandas.
Version 1.1 - Mise à jour pour retirer le paramètre sort_dir non supporté par l'API Adzuna.
"""

import asyncio
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging
from pydantic import BaseModel
import json
import os
import dotenv
from os import environ

# Import des clients API
from adzuna import AdzunaClient, CountryCode, SortBy
from france_travail import FranceTravailAPI, SearchParams as FranceSearchParams

# Configuration du logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Modèle unifié pour les offres d'emploi
class NormalizedJobOffer(BaseModel):
    """Modèle d'offre d'emploi normalisé pour les deux sources"""

    id: str
    source: str  # 'adzuna' ou 'france_travail'
    title: str
    description: Optional[str] = None
    company_name: Optional[str] = None
    location_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    date_created: Optional[datetime] = None
    date_updated: Optional[datetime] = None
    contract_type: Optional[str] = None  # CDI, CDD, etc.
    contract_duration: Optional[str] = None
    working_hours: Optional[str] = None  # Temps plein, temps partiel
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: Optional[str] = None
    salary_period: Optional[str] = None  # mensuel, annuel, horaire
    experience_required: Optional[str] = None
    category: Optional[str] = None
    sector: Optional[str] = None
    application_url: Optional[str] = None
    source_url: Optional[str] = None
    skills: Optional[List[str]] = None
    remote_work: Optional[bool] = None
    is_handicap_accessible: Optional[bool] = None


class JobDataNormalizer:
    """
    Classe pour normaliser les données d'emploi provenant de différentes API
    """

    def __init__(
        self,
        adzuna_app_id: str,
        adzuna_app_key: str,
        france_travail_id: str,
        france_travail_key: str,
    ):
        """
        Initialise le normalisateur avec les identifiants d'API

        Args:
            adzuna_app_id: ID d'application Adzuna
            adzuna_app_key: Clé API Adzuna
            france_travail_client_id: ID d'identification France Travail
            france_travail_client_secret: Clé secret d'identification France Travail
        """
        self.adzuna_client = AdzunaClient(adzuna_app_id, adzuna_app_key)
        self.france_travail_api = FranceTravailAPI(
            france_travail_id, france_travail_key
        )

        # Mappings pour les types de contrat
        # Ces mappings vont aider à normaliser les données entre les sources
        self.contract_type_mapping = {
            # Adzuna
            "permanent": "CDI",
            "contract": "CDD",
            # Ces valeurs sont déjà conformes pour France Travail
            "CDI": "CDI",
            "CDD": "CDD",
            "MIS": "Mission intérimaire",
            "SAI": "Travail saisonnier",
            "LIB": "Profession libérale",
        }

        self.working_hours_mapping = {
            # Adzuna
            "full_time": "Temps plein",
            "part_time": "Temps partiel",
            # France Travail
            "Temps plein": "Temps plein",
            "Temps partiel": "Temps partiel",
        }

        self.experience_mapping = {
            # France Travail
            "D": "Débutant accepté",
            "S": "Expérience souhaitée",
            "E": "Expérience exigée",
            # Valeurs normalisées (pour Adzuna, à calculer manuellement)
            "Débutant accepté": "Débutant accepté",
            "Expérience souhaitée": "Expérience souhaitée",
            "Expérience exigée": "Expérience exigée",
        }

    async def close(self):
        """Ferme les connexions des clients API"""
        await self.adzuna_client.close()
        # France Travail API n'a pas de méthode close car il utilise requests et non httpx

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def fetch_adzuna_jobs(
        self, search_terms: str, location: str = None, max_results: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Récupère les offres d'emploi depuis l'API Adzuna

        Args:
            search_terms: Termes de recherche
            location: Lieu (ville, région)
            max_results: Nombre maximum de résultats à récupérer

        Returns:
            Liste des offres d'emploi brutes d'Adzuna
        """
        logger.info(
            f"Récupération des offres Adzuna pour '{search_terms}' à '{location}'"
        )

        # Limiter à 50 résultats par page selon la limitation de l'API
        results_per_page = min(50, max_results)
        page = 1
        all_jobs = []

        # Paramètres de recherche
        search_params = {
            "what": search_terms,
            "results_per_page": results_per_page,
            "sort_by": SortBy.DATE,
            # Note: Le paramètre sort_dir n'est plus supporté par l'API Adzuna
        }

        # Ajouter la localisation si elle est fournie
        if location:
            search_params["where"] = location

        try:
            # Récupérer la première page
            search_results = await self.adzuna_client.search_jobs(
                country=CountryCode.FR, page=page, **search_params
            )

            all_jobs.extend(search_results.results)

            # Récupérer les pages suivantes si nécessaire
            while (
                len(all_jobs) < max_results
                and len(search_results.results) == results_per_page
            ):
                page += 1
                search_results = await self.adzuna_client.search_jobs(
                    country=CountryCode.FR, page=page, **search_params
                )
                all_jobs.extend(search_results.results)

            # Limiter au nombre maximum demandé
            all_jobs = all_jobs[:max_results]

            logger.info(f"Récupéré {len(all_jobs)} offres d'emploi depuis Adzuna")
            return [job.model_dump() for job in all_jobs]

        except Exception as e:
            logger.error(f"Erreur lors de la récupération des offres Adzuna: {e}")
            # Tenter de gérer des erreurs spécifiques connues
            if not self._handle_adzuna_error(str(e)):
                # Si l'erreur n'a pas été gérée spécifiquement, la loguer simplement
                logger.error(f"Erreur non gérée: {e}")
            return []

    def fetch_france_travail_jobs(
        self, search_terms: str, location: str = None, max_results: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Récupère les offres d'emploi depuis l'API France Travail

        Args:
            search_terms: Termes de recherche
            location: Code INSEE de commune ou département
            max_results: Nombre maximum de résultats à récupérer

        Returns:
            Liste des offres d'emploi brutes de France Travail
        """
        logger.info(
            f"Récupération des offres France Travail pour '{search_terms}' à '{location}'"
        )

        # Configurer les paramètres de recherche
        search_params = FranceSearchParams(
            motsCles=search_terms,
            range=f"0-{min(max_results-1, 150)}",  # Limité à 150 résultats maximum par l'API
            sort=1,  # Tri par date décroissant
        )

        # Ajouter la localisation si elle est fournie
        if location:
            # Vérifier si c'est un code département (2 chiffres) ou un code INSEE (5 chiffres)
            if len(location) == 2:
                search_params.departement = location
            else:
                search_params.commune = location

        try:
            results = self.france_travail_api.search_offers(search_params)

            jobs = results.resultats
            logger.info(f"Récupéré {len(jobs)} offres d'emploi depuis France Travail")

            return [job.model_dump() for job in jobs]

        except Exception as e:
            logger.error(
                f"Erreur lors de la récupération des offres France Travail: {e}"
            )
            return []

    def normalize_adzuna_job(self, job: Dict[str, Any]) -> NormalizedJobOffer:
        """
        Normalise une offre d'emploi Adzuna vers le format commun

        Args:
            job: Offre d'emploi brute d'Adzuna

        Returns:
            Offre d'emploi normalisée
        """
        # Extraire les informations de localisation
        location_name = None
        if job.get("location") and job["location"].get("display_name"):
            location_name = job["location"]["display_name"]

        # Extraire le nom de l'entreprise
        company_name = None
        if job.get("company") and job["company"].get("display_name"):
            company_name = job["company"]["display_name"]

        # Déterminer la catégorie
        category = None
        if job.get("category") and job["category"].get("label"):
            category = job["category"]["label"]

        # Convertir la date au format datetime
        date_created = None
        if job.get("created"):
            try:
                date_created = datetime.fromisoformat(
                    job["created"].replace("Z", "+00:00")
                )
            except ValueError:
                # Essayer un autre format si nécessaire
                pass

        # Déterminer le type de contrat normalisé
        contract_type = None
        if job.get("contract_type"):
            contract_type = self.contract_type_mapping.get(
                job["contract_type"], job["contract_type"]
            )

        # Déterminer le régime horaire normalisé
        working_hours = None
        if job.get("contract_time"):
            working_hours = self.working_hours_mapping.get(
                job["contract_time"], job["contract_time"]
            )

        # Déterminer l'expérience requise (Adzuna ne fournit pas cela directement)
        experience_required = None

        # Gérer les informations de salaire
        salary_min = job.get("salary_min")
        salary_max = job.get("salary_max")
        salary_currency = "EUR"  # Par défaut pour la France
        salary_period = "annuel"  # Par défaut pour Adzuna

        # Créer l'offre normalisée
        normalized_job = NormalizedJobOffer(
            id=job["id"],
            source="adzuna",
            title=job["title"],
            description=job.get("description"),
            company_name=company_name,
            location_name=location_name,
            latitude=job.get("latitude"),
            longitude=job.get("longitude"),
            date_created=date_created,
            date_updated=date_created,  # Adzuna ne fournit pas de date de mise à jour
            contract_type=contract_type,
            contract_duration=None,  # Adzuna ne fournit pas cette information
            working_hours=working_hours,
            salary_min=salary_min,
            salary_max=salary_max,
            salary_currency=salary_currency,
            salary_period=salary_period,
            experience_required=experience_required,
            category=category,
            sector=None,  # Adzuna ne fournit pas cette information clairement
            application_url=job.get("redirect_url"),
            source_url=job.get("redirect_url"),
            skills=None,  # Adzuna ne fournit pas cette information
            remote_work=None,  # Adzuna ne fournit pas cette information
            is_handicap_accessible=None,  # Adzuna ne fournit pas cette information
        )

        return normalized_job

    def normalize_france_travail_job(self, job: Dict[str, Any]) -> NormalizedJobOffer:
        """
        Normalise une offre d'emploi France Travail vers le format commun

        Args:
            job: Offre d'emploi brute de France Travail

        Returns:
            Offre d'emploi normalisée
        """
        # Extraire les informations de localisation
        location_name = None
        latitude = None
        longitude = None

        if job.get("lieuTravail"):
            location_name = job["lieuTravail"].get("libelle")
            latitude = job["lieuTravail"].get("latitude")
            longitude = job["lieuTravail"].get("longitude")

        # Extraire le nom de l'entreprise
        company_name = None
        if job.get("entreprise"):
            company_name = job["entreprise"].get("nom")

        # Déterminer la catégorie et le secteur
        category = job.get("romeLibelle")
        sector = job.get("secteurActiviteLibelle")

        # Convertir les dates au format datetime
        date_created = job.get("dateCreation")
        date_updated = job.get("dateActualisation")

        # Déterminer le type de contrat normalisé
        contract_type = None
        if job.get("typeContrat"):
            contract_type = self.contract_type_mapping.get(
                job["typeContrat"], job["typeContrat"]
            )

        # Extraire la durée du contrat (pour les CDD)
        contract_duration = job.get("typeContratLibelle")
        if contract_duration == contract_type:
            contract_duration = None

        # Déterminer le régime horaire normalisé
        working_hours = None
        if job.get("dureeTravailLibelleConverti"):
            working_hours = self.working_hours_mapping.get(
                job["dureeTravailLibelleConverti"], job["dureeTravailLibelleConverti"]
            )

        # Déterminer l'expérience requise
        experience_required = None
        if job.get("experienceExige"):
            experience_required = self.experience_mapping.get(
                job["experienceExige"], job.get("experienceLibelle")
            )

        # Gérer les informations de salaire
        # France Travail ne donne pas directement min/max, on doit parser le libellé
        salary_min = None
        salary_max = None
        salary_currency = "EUR"  # Par défaut pour la France
        salary_period = None

        if job.get("salaire") and job["salaire"].get("libelle"):
            salary_info = job["salaire"]["libelle"]

            # Déterminer la période de salaire
            if "Mensuel" in salary_info:
                salary_period = "mensuel"
            elif "Annuel" in salary_info:
                salary_period = "annuel"
            elif "Horaire" in salary_info:
                salary_period = "horaire"

            # Tenter d'extraire les valeurs de salaire (méthode simplifiée)
            # Dans une implémentation réelle, utilisez regex pour une extraction plus précise
            try:
                # Exemple simple: "Mensuel de 1500.00 Euros à 2000.00 Euros"
                if " de " in salary_info and " à " in salary_info:
                    parts = salary_info.split(" de ")[1].split(" à ")
                    salary_min = float(parts[0].split(" ")[0].replace(",", "."))
                    salary_max = float(parts[1].split(" ")[0].replace(",", "."))
                elif " de " in salary_info:
                    salary_val = (
                        salary_info.split(" de ")[1].split(" ")[0].replace(",", ".")
                    )
                    salary_min = salary_max = float(salary_val)
            except (ValueError, IndexError):
                # En cas d'échec du parsing, laisser à None
                pass

        # Extraire les compétences
        skills = []
        if job.get("competences"):
            skills = [
                comp["libelle"] for comp in job["competences"] if "libelle" in comp
            ]

        # Déterminer l'URL de candidature
        application_url = None
        source_url = None

        if job.get("contact") and job["contact"].get("urlPostulation"):
            application_url = str(job["contact"]["urlPostulation"])

        if job.get("origineOffre") and job["origineOffre"].get("urlOrigine"):
            source_url = str(job["origineOffre"]["urlOrigine"])

        # Déterminer l'accessibilité aux travailleurs handicapés
        is_handicap_accessible = job.get("accessibleTH")

        # Créer l'offre normalisée
        normalized_job = NormalizedJobOffer(
            id=job["id"],
            source="france_travail",
            title=job["intitule"],
            description=job.get("description"),
            company_name=company_name,
            location_name=location_name,
            latitude=latitude,
            longitude=longitude,
            date_created=date_created,
            date_updated=date_updated,
            contract_type=contract_type,
            contract_duration=contract_duration,
            working_hours=working_hours,
            salary_min=salary_min,
            salary_max=salary_max,
            salary_currency=salary_currency,
            salary_period=salary_period,
            experience_required=experience_required,
            category=category,
            sector=sector,
            application_url=application_url,
            source_url=source_url,
            skills=skills if skills else None,
            remote_work=None,  # Il faudrait analyser le texte pour déterminer cela
            is_handicap_accessible=is_handicap_accessible,
        )

        return normalized_job

    async def fetch_and_normalize_adzuna(
        self, search_terms: str, location: str = None, max_results: int = 100
    ) -> List[NormalizedJobOffer]:
        """
        Récupère et normalise les offres d'emploi Adzuna

        Args:
            search_terms: Termes de recherche
            location: Lieu (ville, région)
            max_results: Nombre maximum de résultats

        Returns:
            Liste des offres d'emploi normalisées
        """
        raw_jobs = await self.fetch_adzuna_jobs(search_terms, location, max_results)
        normalized_jobs = [self.normalize_adzuna_job(job) for job in raw_jobs]
        return normalized_jobs

    def fetch_and_normalize_france_travail(
        self, search_terms: str, location: str = None, max_results: int = 100
    ) -> List[NormalizedJobOffer]:
        """
        Récupère et normalise les offres d'emploi France Travail

        Args:
            search_terms: Termes de recherche
            location: Code INSEE de commune ou département
            max_results: Nombre maximum de résultats

        Returns:
            Liste des offres d'emploi normalisées
        """
        raw_jobs = self.fetch_france_travail_jobs(search_terms, location, max_results)
        normalized_jobs = [self.normalize_france_travail_job(job) for job in raw_jobs]
        return normalized_jobs

    async def fetch_and_normalize_all(
        self,
        search_terms: str,
        location_adzuna: str = None,
        location_france_travail: str = None,
        max_results: int = 100,
    ) -> List[NormalizedJobOffer]:
        """
        Récupère et normalise les offres d'emploi des deux sources

        Args:
            search_terms: Termes de recherche
            location_adzuna: Lieu pour Adzuna (ville, région)
            location_france_travail: Code INSEE/département pour France Travail
            max_results: Nombre maximum de résultats par source

        Returns:
            Liste combinée des offres d'emploi normalisées
        """
        # Récupérer les données d'Adzuna
        adzuna_jobs = await self.fetch_and_normalize_adzuna(
            search_terms, location_adzuna, max_results
        )

        # Récupérer les données de France Travail
        france_travail_jobs = self.fetch_and_normalize_france_travail(
            search_terms, location_france_travail, max_results
        )

        # Combiner les résultats
        all_jobs = adzuna_jobs + france_travail_jobs

        return all_jobs

    def create_dataframe(
        self, normalized_jobs: List[NormalizedJobOffer]
    ) -> pd.DataFrame:
        """
        Crée un DataFrame pandas à partir des offres normalisées

        Args:
            normalized_jobs: Liste des offres d'emploi normalisées

        Returns:
            DataFrame pandas
        """
        # Convertir les offres en dictionnaires
        jobs_dicts = [job.model_dump() for job in normalized_jobs]

        # Créer un DataFrame
        df = pd.DataFrame(jobs_dicts)

        # Conversion des colonnes de date en datetime (au cas où)
        for date_col in ["date_created", "date_updated"]:
            if date_col in df.columns:
                df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

        # Sanitize les données textuelles pour éviter les problèmes CSV
        text_columns = [
            "title",
            "description",
            "company_name",
            "location_name",
            "contract_type",
            "contract_duration",
            "working_hours",
            "category",
            "sector",
        ]

        for col in text_columns:
            if col in df.columns:
                # Remplacer les caractères problématiques et les valeurs nulles
                df[col] = df[col].apply(
                    lambda x: self._sanitize_text(x) if x is not None else ""
                )

        # Traiter les listes (comme les compétences)
        if "skills" in df.columns:
            df["skills"] = df["skills"].apply(
                lambda x: (
                    "; ".join(self._sanitize_text(s) for s in x)
                    if isinstance(x, list)
                    else ""
                )
            )

        # S'assurer que les valeurs numériques sont correctes
        numeric_columns = ["salary_min", "salary_max", "latitude", "longitude"]
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # Remplir les valeurs manquantes avec des valeurs appropriées
        df = df.fillna(
            {
                "description": "",
                "company_name": "Non spécifié",
                "location_name": "Non spécifié",
                "contract_type": "Non spécifié",
                "working_hours": "Non spécifié",
                "experience_required": "Non spécifié",
                "category": "Non spécifié",
                "sector": "Non spécifié",
                "salary_min": np.nan,
                "salary_max": np.nan,
                "salary_currency": "",
                "salary_period": "",
                "application_url": "",
                "source_url": "",
            }
        )

        return df

    def _sanitize_text(self, text):
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
        import re

        text = re.sub(r"[\x00-\x1F\x7F]", "", text)

        return text

    def _sanitize_filename(self, filename):
        """
        Nettoie le nom de fichier pour éviter les problèmes de sécurité

        Args:
            filename: Nom de fichier à nettoyer

        Returns:
            Nom de fichier sécurisé
        """
        # Remplacer les caractères dangereux
        import re

        filename = re.sub(r'[\\/*?:"<>|]', "_", filename)

        # Limiter la longueur
        if len(filename) > 200:
            filename = filename[:200]

        return filename

    def save_to_csv(self, df: pd.DataFrame, filename: str) -> str:
        """
        Sauvegarde le DataFrame dans un fichier CSV

        Args:
            df: DataFrame à sauvegarder
            filename: Nom du fichier (sans extension)

        Returns:
            Chemin du fichier sauvegardé
        """
        # Nettoyer le nom de fichier
        safe_filename = self._sanitize_filename(filename)
        filepath = f"{filename}.csv"

        try:
            # Utiliser le mode quoting=csv.QUOTE_ALL pour s'assurer que tous les champs sont bien échappés
            import csv

            df.to_csv(
                filepath,
                index=False,
                encoding="utf-8",
                quoting=csv.QUOTE_ALL,
                escapechar="\\",
            )
            logger.info(f"Données sauvegardées dans {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde du fichier CSV: {e}")
            # Tenter une sauvegarde avec des options plus sécurisées
            try:
                df.to_csv(
                    filepath,
                    index=False,
                    encoding="utf-8-sig",
                    quoting=csv.QUOTE_ALL,
                    escapechar="\\",
                    line_terminator="\n",
                )
                logger.info(
                    f"Données sauvegardées (méthode alternative) dans {filepath}"
                )
                return filepath
            except Exception as e2:
                logger.error(
                    f"Échec de la sauvegarde du fichier CSV (seconde tentative): {e2}"
                )
                return ""

    def process_and_analyze(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Traite et analyse les données du DataFrame

        Args:
            df: DataFrame des offres d'emploi

        Returns:
            Dictionnaire des analyses
        """
        # Copier le DataFrame pour éviter de modifier l'original
        df_analysis = df.copy()

        # Nombre d'offres par source
        source_counts = df_analysis["source"].value_counts().to_dict()

        # Types de contrat les plus courants
        contract_counts = df_analysis["contract_type"].value_counts().head(5).to_dict()

        # Statistiques de salaire
        salary_stats = {}
        if (
            "salary_min" in df_analysis.columns
            and df_analysis["salary_min"].notna().any()
        ):
            # Statistiques pour les salaires minimum
            salary_stats["min"] = {
                "mean": df_analysis["salary_min"].mean(),
                "median": df_analysis["salary_min"].median(),
                "min": df_analysis["salary_min"].min(),
                "max": df_analysis["salary_min"].max(),
            }

        if (
            "salary_max" in df_analysis.columns
            and df_analysis["salary_max"].notna().any()
        ):
            # Statistiques pour les salaires maximum
            salary_stats["max"] = {
                "mean": df_analysis["salary_max"].mean(),
                "median": df_analysis["salary_max"].median(),
                "min": df_analysis["salary_max"].min(),
                "max": df_analysis["salary_max"].max(),
            }

        # Répartition des offres par catégorie
        category_counts = {}
        if "category" in df_analysis.columns:
            category_counts = df_analysis["category"].value_counts().head(10).to_dict()

        # Analyse des expériences requises
        experience_counts = {}
        if "experience_required" in df_analysis.columns:
            experience_counts = (
                df_analysis["experience_required"].value_counts().to_dict()
            )

        # Résultats de l'analyse
        analysis = {
            "total_offers": len(df_analysis),
            "sources": source_counts,
            "contracts": contract_counts,
            "salary_stats": salary_stats,
            "categories": category_counts,
            "experience": experience_counts,
        }

        return analysis

    def _handle_adzuna_error(self, error_message: str) -> None:
        """
        Traite les erreurs spécifiques d'Adzuna et fournit une information utile

        Args:
            error_message: Message d'erreur original
        """
        # Vérifier si l'erreur est liée à un paramètre non supporté
        if "sort_dir" in error_message.lower():
            logger.warning(
                "Le paramètre 'sort_dir' n'est plus supporté par l'API Adzuna. L'erreur a été gérée."
            )
            return True

        # Autres cas d'erreurs spécifiques peuvent être ajoutés ici
        return False


async def main():
    """Fonction principale"""
    # Charger les variables d'environnement depuis un fichier .env si disponible
    dotenv.load_dotenv()

    # Récupérer les identifiants d'API depuis les variables d'environnement
    adzuna_app_id = environ.get("ADZUNA_APP_ID")
    adzuna_app_key = environ.get("ADZUNA_APP_KEY")
    # france_travail_token = environ.get("FRANCE_TRAVAIL_TOKEN")
    france_travail_id = environ.get("FRANCE_TRAVAIL_ID")
    france_travail_key = environ.get("FRANCE_TRAVAIL_KEY")

    # Vérifier que les variables d'environnement sont définies
    if not all([adzuna_app_id, adzuna_app_key, france_travail_id, france_travail_key]):
        missing_vars = []
        if not adzuna_app_id:
            missing_vars.append("ADZUNA_APP_ID")
        if not adzuna_app_key:
            missing_vars.append("ADZUNA_APP_KEY")
        if not france_travail_id:
            missing_vars.append("FRANCE_TRAVAIL_ID")
        if not france_travail_key:
            missing_vars.append("FRANCE_TRAVAIL_KEY")
        # if not france_travail_token:
        #    missing_vars.append("FRANCE_TRAVAIL_TOKEN")

        raise ValueError(
            f"Variables d'environnement manquantes: {', '.join(missing_vars)}. "
            "Veuillez définir ces variables dans un fichier .env ou dans votre environnement."
        )

    # Créer le dossier de sortie si nécessaire
    output = environ.get("OUTPUT_DIR", "./data/")
    output_dir = f"../../{output}"

    os.makedirs(output_dir, exist_ok=True)

    # Paramètres de recherche (avec valeurs par défaut depuis les variables d'environnement)
    search_terms = environ.get("DEFAULT_SEARCH_TERMS", "python data ingénieur")
    location_adzuna = environ.get("DEFAULT_LOCATION_ADZUNA", "Paris")  # Pour Adzuna
    location_france_travail = environ.get(
        "DEFAULT_LOCATION_FRANCE_TRAVAIL", "75"
    )  # Code département Paris pour France Travail
    max_results_per_source = int(environ.get("DEFAULT_MAX_RESULTS", "50"))

    # Initialiser le normalisateur
    async with JobDataNormalizer(
        adzuna_app_id, adzuna_app_key, france_travail_id, france_travail_key
    ) as normalizer:
        # Récupérer et normaliser les données des deux sources
        normalized_jobs = await normalizer.fetch_and_normalize_all(
            search_terms,
            location_adzuna=location_adzuna,
            location_france_travail=location_france_travail,
            max_results=max_results_per_source,
        )

        # Créer un DataFrame pandas
        df = normalizer.create_dataframe(normalized_jobs)

        # Sauvegarder toutes les offres dans un seul fichier CSV
        all_jobs_filepath = normalizer.save_to_csv(
            df,
            os.path.join(output_dir, f"all_jobs_{datetime.now().strftime('%Y%m%d')}"),
        )

        # Sauvegarder les offres de chaque source séparément
        for source in ["adzuna", "france_travail"]:
            source_df = df[df["source"] == source]
            if len(source_df) > 0:
                source_filepath = normalizer.save_to_csv(
                    source_df,
                    os.path.join(
                        output_dir, f"{source}_jobs_{datetime.now().strftime('%Y%m%d')}"
                    ),
                )

        # Analyser les données
        analysis = normalizer.process_and_analyze(df)

        # Afficher un résumé de l'analyse
        print("\n=== Analyse des offres d'emploi ===")
        print(f"Nombre total d'offres: {analysis['total_offers']}")
        print(f"\nRépartition par source:")
        for source, count in analysis["sources"].items():
            print(
                f"- {source}: {count} offres ({count/analysis['total_offers']*100:.1f}%)"
            )

        print(f"\nTypes de contrat les plus courants:")
        for contract, count in analysis["contracts"].items():
            print(f"- {contract}: {count} offres")

        if analysis["salary_stats"]:
            print("\nStatistiques de salaire:")
            if "min" in analysis["salary_stats"]:
                min_stats = analysis["salary_stats"]["min"]
                print(f"- Salaire minimum moyen: {min_stats['mean']:.2f}")
                print(f"- Salaire minimum médian: {min_stats['median']:.2f}")

            if "max" in analysis["salary_stats"]:
                max_stats = analysis["salary_stats"]["max"]
                print(f"- Salaire maximum moyen: {max_stats['mean']:.2f}")
                print(f"- Salaire maximum médian: {max_stats['median']:.2f}")

        # Sauvegarder l'analyse dans un fichier JSON
        analysis_filepath = os.path.join(
            output_dir, f"analysis_{datetime.now().strftime('%Y%m%d')}.json"
        )
        with open(analysis_filepath, "w", encoding="utf-8") as f:
            json.dump(analysis, f, indent=2, default=str)
        print(f"\nAnalyse complète sauvegardée dans {analysis_filepath}")


if __name__ == "__main__":
    asyncio.run(main())

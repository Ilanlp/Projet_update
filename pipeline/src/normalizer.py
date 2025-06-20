"""
Normalisateur de données d'emploi pour les API Adzuna et France Travail
Version simplifiée - Recherche par terme simple
"""

import asyncio
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime
import logging
from pydantic import BaseModel
from dotenv import load_dotenv
from os import environ
from pathlib import Path

from adzuna import AdzunaClient, CountryCode, SortBy
from france_travail import FranceTravailAPI, SearchParams as FranceSearchParams

# Configuration du logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class NormalizedJobOffer(BaseModel):
    """Modèle d'offre d'emploi normalisé"""
    id: str
    source: str
    title: str
    description: Optional[str] = None
    company_name: Optional[str] = None
    location_name: Optional[str] = None
    contract_type: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    application_url: Optional[str] = None
    date_created: Optional[datetime] = None
    date_extraction: Optional[datetime] = None


class JobDataNormalizer:
    """Classe simplifiée pour normaliser les données d'emploi"""

    def __init__(self, adzuna_app_id: str, adzuna_app_key: str, 
                 france_travail_id: str, france_travail_key: str):
        self.adzuna_client = AdzunaClient(adzuna_app_id, adzuna_app_key)
        self.france_travail_api = FranceTravailAPI(france_travail_id, france_travail_key)

    async def close(self):
        await self.adzuna_client.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def fetch_adzuna_jobs(self, search_term: str, max_results: int = 100) -> List[Dict]:
        """Récupère les offres d'emploi depuis Adzuna avec pagination"""
        logger.info(f"Récupération Adzuna pour '{search_term}' (max {max_results})")
        
        all_jobs = []
        page = 1
        results_per_page = 50  # Limite d'Adzuna par page
        
        try:
            while len(all_jobs) < max_results:
                search_results = await self.adzuna_client.search_jobs(
                    country=CountryCode.FR,
                    what=search_term,
                    page=page,
                    results_per_page=results_per_page,
                    sort_by=SortBy.DATE
                )
                
                jobs = [job.model_dump() for job in search_results.results]
                if not jobs:  # Plus de résultats
                    break
                    
                all_jobs.extend(jobs)
                logger.info(f"Page {page}: récupéré {len(jobs)} offres (total: {len(all_jobs)})")
                
                page += 1
                
                # Pause entre les requêtes pour éviter de surcharger l'API
                await asyncio.sleep(0.5)
            
            # Limiter au nombre maximum demandé
            if len(all_jobs) > max_results:
                all_jobs = all_jobs[:max_results]
                
            logger.info(f"Récupéré {len(all_jobs)} offres Adzuna au total")
            return all_jobs
            
        except Exception as e:
            logger.error(f"Erreur Adzuna: {e}")
            return all_jobs

    async def fetch_france_travail_jobs(self, search_term: str, max_results: int = 100) -> List[Dict]:
        """Récupère les offres d'emploi depuis France Travail avec pagination"""
        logger.info(f"Récupération France Travail pour '{search_term}' (max {max_results})")
        
        all_jobs = []
        current_index = 0
        page_size = 150  # Taille maximale recommandée par appel d'API
        
        try:
            while len(all_jobs) < max_results:
                end_index = current_index + page_size - 1
                
                search_params = FranceSearchParams(
                    motsCles=search_term,
                    range=f"{current_index}-{end_index}",
                    sort=1
                )
                
                results = self.france_travail_api.search_offers(search_params)
                jobs = [job.model_dump() for job in results.resultats]
                
                if not jobs:  # Plus de résultats
                    break
                    
                all_jobs.extend(jobs)
                logger.info(f"Range {current_index}-{end_index}: récupéré {len(jobs)} offres (total: {len(all_jobs)})")
                
                current_index = end_index + 1
                
                # Pause entre les requêtes
                await asyncio.sleep(0.5)
            
            # Limiter au nombre maximum demandé
            if len(all_jobs) > max_results:
                all_jobs = all_jobs[:max_results]
                
            logger.info(f"Récupéré {len(all_jobs)} offres France Travail au total")
            return all_jobs
            
        except Exception as e:
            logger.error(f"Erreur France Travail: {e}")
            return all_jobs

    def normalize_adzuna_job(self, job: Dict) -> NormalizedJobOffer:
        """Normalise une offre Adzuna"""
        try:
            # Gestion sécurisée des champs imbriqués
            location_name = None
            if job.get("location") and isinstance(job["location"], dict):
                location_name = job["location"].get("display_name")
            
            company_name = None
            if job.get("company") and isinstance(job["company"], dict):
                company_name = job["company"].get("display_name")
            
            date_created = None
            if job.get("created"):
                try:
                    date_created = datetime.fromisoformat(job["created"].replace("Z", "+00:00"))
                except:
                    pass

            return NormalizedJobOffer(
                id=str(job["id"]),
                source="adzuna",
                title=str(job["title"]),
                description=str(job.get("description", "")) if job.get("description") else None,
                company_name=company_name,
                location_name=location_name,
                contract_type=job.get("contract_type"),
                salary_min=job.get("salary_min"),
                salary_max=job.get("salary_max"),
                application_url=str(job.get("redirect_url", "")) if job.get("redirect_url") else None,
                date_created=date_created,
                date_extraction=datetime.now()
            )
        except Exception as e:
            logger.error(f"Erreur normalisation Adzuna: {e}")
            raise

    def normalize_france_travail_job(self, job: Dict) -> NormalizedJobOffer:
        """Normalise une offre France Travail"""
        try:
            # Gestion sécurisée des champs imbriqués
            location_name = None
            if job.get("lieuTravail") and isinstance(job["lieuTravail"], dict):
                location_name = job["lieuTravail"].get("libelle")
            
            company_name = None
            if job.get("entreprise") and isinstance(job["entreprise"], dict):
                company_name = job["entreprise"].get("nom")
            
            date_created = None
            if job.get("dateCreation"):
                try:
                    date_created = datetime.fromisoformat(str(job["dateCreation"]).replace("Z", "+00:00"))
                except:
                    pass

            # Gestion sécurisée de l'URL de candidature
            application_url = None
            if job.get("contact") and isinstance(job["contact"], dict):
                url_obj = job["contact"].get("urlPostulation")
                if url_obj:
                    # Convertir l'objet HttpUrl en string
                    application_url = str(url_obj)

            return NormalizedJobOffer(
                id=str(job["id"]),
                source="france_travail",
                title=str(job["intitule"]),
                description=str(job.get("description", "")) if job.get("description") else None,
                company_name=company_name,
                location_name=location_name,
                contract_type=job.get("typeContrat"),
                salary_min=None,  # France Travail ne donne pas directement min/max
                salary_max=None,
                application_url=application_url,
                date_created=date_created,
                date_extraction=datetime.now()
            )
        except Exception as e:
            logger.error(f"Erreur normalisation France Travail: {e}")
            raise

    async def fetch_and_normalize_all(self, search_term: str, max_results: int = 100) -> List[NormalizedJobOffer]:
        """Récupère et normalise les offres des deux sources"""
        logger.info(f"Récupération pour '{search_term}' (max {max_results} par source)")
        
        # Récupération parallèle
        adzuna_task = self.fetch_adzuna_jobs(search_term, max_results)
        france_travail_task = self.fetch_france_travail_jobs(search_term, max_results)
        
        adzuna_jobs, france_travail_jobs = await asyncio.gather(adzuna_task, france_travail_task)
        
        # Normalisation
        normalized_jobs = []
        
        for job in adzuna_jobs:
            try:
                normalized_jobs.append(self.normalize_adzuna_job(job))
            except Exception as e:
                logger.error(f"Erreur normalisation Adzuna: {e}")
                continue
                
        for job in france_travail_jobs:
            try:
                normalized_jobs.append(self.normalize_france_travail_job(job))
            except Exception as e:
                logger.error(f"Erreur normalisation France Travail: {e}")
                continue
        
        # Déduplication
        seen = set()
        unique_jobs = []
        for job in normalized_jobs:
            key = f"{job.source}_{job.id}"
            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)
        
        logger.info(f"Total normalisé: {len(unique_jobs)} offres uniques")
        return unique_jobs

    def save_to_csv(self, jobs: List[NormalizedJobOffer], filename: str) -> str:
        """Sauvegarde les offres en CSV"""
        if not jobs:
            logger.warning("Aucune offre à sauvegarder")
            return None
            
        df = pd.DataFrame([job.model_dump() for job in jobs])
        filepath = Path(filename).with_suffix('.csv')
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        df.to_csv(filepath, index=False, encoding='utf-8')
        logger.info(f"Sauvegardé {len(jobs)} offres dans {filepath}")
        return str(filepath)


async def main():
    """Fonction principale simplifiée"""
    try:
        load_dotenv()
        
        # Récupération des identifiants
        adzuna_app_id = environ.get("ADZUNA_APP_ID")
        adzuna_app_key = environ.get("ADZUNA_APP_KEY")
        france_travail_id = environ.get("FRANCE_TRAVAIL_ID")
        france_travail_key = environ.get("FRANCE_TRAVAIL_KEY")
        search_term = environ.get("WHAT", "data")  # Terme de recherche depuis .env
        max_results = 1000
        output_dir = environ.get("OUTPUT_DIR", "data/")
        
        if not all([adzuna_app_id, adzuna_app_key, france_travail_id, france_travail_key]):
            raise ValueError("Variables d'environnement manquantes")
        
        # Création du dossier de sortie
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Recherche: '{search_term}', max {max_results} résultats par source")
        
        async with JobDataNormalizer(adzuna_app_id, adzuna_app_key, france_travail_id, france_travail_key) as normalizer:
            # Récupération et normalisation
            jobs = await normalizer.fetch_and_normalize_all(search_term, max_results)
            
            if not jobs:
                logger.warning("Aucune offre récupérée")
                return
            
            # Sauvegarde
            date_str = datetime.now().strftime("%Y%m%d_%H%M")
            filename = output_path / f"jobs_{search_term}_{date_str}_{len(jobs)}_offers"
            filepath = normalizer.save_to_csv(jobs, filename)
            
            if filepath:
                print(f"\nRésumé:")
                print(f"Total offres: {len(jobs)}")
                print(f"Fichier: {filepath}")
                print(f"Terme recherché: {search_term}")
            
    except Exception as e:
        logger.error(f"Erreur: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main()) 
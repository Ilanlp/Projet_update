"""
Module de collecte historique des données France Travail

Ce module contient la classe FranceTravailHistoricalCollector qui permet de collecter
des offres d'emploi sur France Travail sur une longue période temporelle (plusieurs mois)
en utilisant une approche par départements et périodes pour maximiser la couverture.
"""

import os
import json
import csv
import time
import asyncio
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Set, Any, Tuple, Optional

from france_travail_api import FranceTravailAPI, SearchParams

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
        "01", "02", "03", "04", "05", "06", "07", "08", "09", "10",
        "11", "12", "13", "14", "15", "16", "17", "18", "19", "21", 
        "22", "23", "24", "25", "26", "27", "28", "29", "2A", "2B", 
        "30", "31", "32", "33", "34", "35", "36", "37", "38", "39", 
        "40", "41", "42", "43", "44", "45", "46", "47", "48", "49", 
        "50", "51", "52", "53", "54", "55", "56", "57", "58", "59", 
        "60", "61", "62", "63", "64", "65", "66", "67", "68", "69", 
        "70", "71", "72", "73", "74", "75", "76", "77", "78", "79", 
        "80", "81", "82", "83", "84", "85", "86", "87", "88", "89", 
        "90", "91", "92", "93", "94", "95", 
        "971", "972", "973", "974", "976"  # DOM-TOM
    ]
    
    # Liste des domaines d'emploi pour une recherche exhaustive
    # Ces domaines correspondent aux classifications ROME utilisées par France Travail
    DOMAINES = [
        "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N"
    ]
    
    def __init__(
        self,
        france_travail_api: FranceTravailAPI,
        results_per_page: int = 150,  # 150 est souvent la limite max pour FranceTravail
        retry_count: int = 3,
        retry_delay: int = 5,
        rate_limit_delay: float = 1.0,  # Plus conservateur car l'API est moins tolérante
        checkpoint_interval: int = 100
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
        self.results_per_page = min(results_per_page, 150)  # S'assurer de ne pas dépasser la limite
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self.rate_limit_delay = rate_limit_delay
        self.checkpoint_interval = checkpoint_interval
        
        # État interne
        self.collected_job_ids: Set[str] = set()
        self.total_collected = 0
    
    async def collect_data(
        self, 
        output_file: str, 
        max_months: int = 12,
        search_terms: str = None
    ) -> str:
        """
        Collecte les données d'offres d'emploi et les sauvegarde en CSV
        
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
                with open(checkpoint_file, 'r', encoding='utf-8') as f:
                    checkpoint_data = json.load(f)
                    self.collected_job_ids = set(checkpoint_data.get("collected_job_ids", []))
                    self.total_collected = checkpoint_data.get("total_collected", 0)
                    timestamp = checkpoint_data.get("timestamp")
                    logger.info(f"Point de contrôle chargé du {timestamp}: "
                                f"{self.total_collected} offres déjà collectées")
            except Exception as e:
                logger.warning(f"Erreur lors du chargement du point de contrôle: {e}")
        
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
            
            # Parcourir les départements
            for departement in self.DEPARTEMENTS:
                for domaine in self.DOMAINES:
                    for period_start, period_end in time_periods:
                        # Convertir les dates au format attendu par France Travail (YYYY-MM-DD)
                        date_debut = period_start.strftime('%Y-%m-%d')
                        date_fin = period_end.strftime('%Y-%m-%d')
                        
                        logger.info(
                            f"Collecte des offres pour le département '{departement}', domaine '{domaine}' "
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
                                    departement=departement,
                                    domaine=domaine,
                                    dateCreationMin=date_debut,
                                    dateCreationMax=date_fin,
                                    range=f"{start_index}-{start_index + self.results_per_page - 1}",
                                    sort=1  # Tri par date décroissant
                                )
                                
                                # Effectuer la requête avec retry
                                results = None
                                for retry in range(self.retry_count + 1):
                                    try:
                                        if retry > 0:
                                            logger.info(f"Tentative {retry}/{self.retry_count}...")
                                            await asyncio.sleep(self.retry_delay * (2 ** (retry - 1)))
                                        
                                        # Effectuer la requête
                                        results = self.france_travail_api.search_offers(search_params)
                                        break
                                    except Exception as e:
                                        logger.warning(f"Erreur lors de la recherche: {e}")
                                        if retry == self.retry_count:
                                            logger.error(f"Abandon après {self.retry_count} tentatives")
                                            results = None
                                
                                # Si toutes les tentatives ont échoué, passer à la période suivante
                                if not results or not results.resultats:
                                    logger.info(f"Aucun résultat ou erreur. Passage à la période suivante.")
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
                                
                                # Écrire les offres dans le CSV
                                for job in filtered_jobs:
                                    job_dict = self._job_to_dict(job)
                                    writer.writerow(job_dict)
                                    csv_file.flush()  # S'assurer que les données sont écrites sur le disque
                                    
                                    total_for_period += 1
                                    self.total_collected += 1
                                
                                # Log de progression
                                logger.info(f"Ajouté {len(filtered_jobs)} nouvelles offres. "
                                           f"Total pour cette période: {total_for_period}")
                                
                                # Sauvegarde périodique de l'état
                                if self.total_collected % self.checkpoint_interval == 0:
                                    self._save_checkpoint(checkpoint_file)
                                
                                # Vérifier s'il y a plus de résultats
                                total_results = results.totalResultats
                                start_index += len(jobs)
                                
                                # Si on a récupéré toutes les offres ou si on a atteint la limite de l'API
                                if start_index >= total_results or start_index >= 1000:  # 1000 est souvent la limite max de l'API
                                    has_more_results = False
                                
                            except Exception as e:
                                logger.error(f"Erreur non gérée lors de la collecte: {e}", exc_info=True)
                                # Attendre et continuer avec la période suivante
                                await asyncio.sleep(self.retry_delay)
                                has_more_results = False
                        
                        # Sauvegarde de l'état à la fin de chaque période
                        self._save_checkpoint(checkpoint_file)
        
        logger.info(f"Collecte terminée! {self.total_collected} offres d'emploi collectées au total.")
        return output_file
    
    def _job_to_dict(self, job: Any) -> Dict[str, Any]:
        """
        Convertit un objet d'offre France Travail en dictionnaire plat pour le CSV
        
        Args:
            job: Objet offre France Travail
            
        Returns:
            Dictionnaire avec les données de l'offre d'emploi
        """
        # Convertir l'objet en dictionnaire
        job_dict = {}
        
        # Identifiant et informations de base
        job_dict["id"] = job.id
        job_dict["titre"] = job.intitule
        job_dict["description"] = job.description
        job_dict["date_creation"] = job.dateCreation
        job_dict["date_actualisation"] = job.dateActualisation
        
        # Type de contrat
        job_dict["type_contrat"] = job.typeContrat
        job_dict["type_contrat_libelle"] = job.typeContratLibelle
        
        # Durée du travail
        job_dict["duree_travail"] = job.dureeTravail
        job_dict["duree_travail_libelle"] = job.dureeTravailLibelle
        job_dict["duree_travail_libelle_converti"] = job.dureeTravailLibelleConverti
        
        # Expérience
        job_dict["experience_exige"] = job.experienceExige
        job_dict["experience_libelle"] = job.experienceLibelle
        
        # Localisation
        if job.lieuTravail:
            job_dict["lieu_travail_libelle"] = job.lieuTravail.libelle
            job_dict["lieu_travail_code_postal"] = job.lieuTravail.codePostal
            job_dict["lieu_travail_commune"] = job.lieuTravail.commune
            job_dict["lieu_travail_latitude"] = job.lieuTravail.latitude
            job_dict["lieu_travail_longitude"] = job.lieuTravail.longitude
        
        # Entreprise
        if job.entreprise:
            job_dict["entreprise_nom"] = job.entreprise.nom
            job_dict["entreprise_description"] = job.entreprise.description
            
        # Qualifications et compétences
        job_dict["qualificationLibelle"] = job.qualificationLibelle
        
        job_dict["competences"] = ""
        if job.competences:
            competences = []
            for comp in job.competences:
                if comp.get("libelle"):
                    competences.append(comp["libelle"])
            job_dict["competences"] = "; ".join(competences)
        
        # Salaire
        if job.salaire:
            job_dict["salaire_libelle"] = job.salaire.libelle
            job_dict["salaire_min"] = job.salaire.min
            job_dict["salaire_max"] = job.salaire.max
            job_dict["salaire_complement"] = job.salaire.complement
        
        # Formation
        if job.formation:
            job_dict["formation_libelle"] = job.formation.libelle
            job_dict["formation_code"] = job.formation.codeFormation
            job_dict["formation_domaine"] = job.formation.domaineLibelle
        
        # URLs et contact
        if job.origineOffre and job.origineOffre.urlOrigine:
            job_dict["url_origine"] = job.origineOffre.urlOrigine
            
        if job.contact:
            if job.contact.urlPostulation:
                job_dict["url_postulation"] = job.contact.urlPostulation
            
            contact_infos = []
            if job.contact.nom:
                contact_infos.append(f"Nom: {job.contact.nom}")
            if job.contact.telephone:
                contact_infos.append(f"Tél: {job.contact.telephone}")
            if job.contact.email:
                contact_infos.append(f"Email: {job.contact.email}")
            if job.contact.commentaire:
                contact_infos.append(f"Commentaire: {job.contact.commentaire}")
            
            job_dict["contact_info"] = " | ".join(contact_infos)
        
        # Métadonnées
        job_dict["rome_code"] = job.romeCode
        job_dict["rome_libelle"] = job.romeLibelle
        job_dict["accessible_TH"] = job.accessibleTH
        job_dict["qualite_paris_emploi"] = job.qualitesParisTjm
        
        return job_dict
    
    def _get_csv_fieldnames(self) -> List[str]:
        """
        Définit les noms de champs pour le CSV
        
        Returns:
            Liste des noms de colonnes pour le CSV
        """
        return [
            "id", "titre", "description", "date_creation", "date_actualisation",
            "type_contrat", "type_contrat_libelle", 
            "duree_travail", "duree_travail_libelle", "duree_travail_libelle_converti",
            "experience_exige", "experience_libelle",
            "lieu_travail_libelle", "lieu_travail_code_postal", "lieu_travail_commune", 
            "lieu_travail_latitude", "lieu_travail_longitude",
            "entreprise_nom", "entreprise_description",
            "qualificationLibelle", "competences",
            "salaire_libelle", "salaire_min", "salaire_max", "salaire_complement",
            "formation_libelle", "formation_code", "formation_domaine",
            "url_origine", "url_postulation", "contact_info",
            "rome_code", "rome_libelle", "accessible_TH", "qualite_paris_emploi"
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

#!/usr/bin/env python3
"""
Script pour extraire les offres d'emploi depuis l'API FranceTravail
et sauvegarder les résultats en CSV.

Le script itère sur les codes ROME et utilise une stratégie
de pagination pour maximiser la collecte des données.
"""

import os
import csv
import json
import time
import logging
from datetime import datetime, timedelta
import pandas as pd
from france_travail_api import FranceTravailAPI, SearchParams

# Configuration de la journalisation
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("extraction.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Configuration
TOKEN = "votre_token_ici"  # À remplacer par votre token
OUTPUT_DIR = "data"
DELAY_BETWEEN_REQUESTS = 1  # Délai en secondes entre les requêtes
MONTHS_TO_COLLECT = 12  # Nombre de mois à collecter (maximum recommandé: 12)

# Création du répertoire de sortie s'il n'existe pas
os.makedirs(OUTPUT_DIR, exist_ok=True)


def get_rome_codes():
    """Récupère la liste des codes ROME depuis l'API référentiel"""
    api = FranceTravailAPI(TOKEN)
    try:
        metiers = api.get_referential("metiers")
        return [metier.code for metier in metiers]
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des codes ROME: {e}")
        # Liste de secours avec quelques codes ROME courants
        return ["M1805", "M1802", "M1803", "M1810", "I1401", "M1402"]


def get_date_ranges(months=12):
    """Génère des plages de dates mensuelles à partir d'aujourd'hui jusqu'à x mois en arrière"""
    today = datetime.now()
    date_ranges = []

    for i in range(months):
        end_date = today - timedelta(days=30 * i)
        start_date = end_date - timedelta(days=30)

        # Formatage au format attendu par l'API
        start_str = start_date.strftime("%Y-%m-%dT00:00:00Z")
        end_str = end_date.strftime("%Y-%m-%dT23:59:59Z")

        date_ranges.append((start_str, end_str))

    return date_ranges


def export_to_csv(offers_data, filename):
    """
    Exporte les données des offres en CSV avec un traitement sécurisé
    """
    if not offers_data:
        logger.warning(f"Aucune donnée à exporter pour {filename}")
        return

    # Transformation en DataFrame
    df = pd.DataFrame(offers_data)

    try:
        # Nettoyage des données pour CSV
        df_clean = clean_dataframe(df)

        # Export en CSV
        file_path = os.path.join(OUTPUT_DIR, filename)
        df_clean.to_csv(
            file_path,
            index=False,
            encoding="utf-8-sig",
            quoting=csv.QUOTE_NONNUMERIC,
            escapechar="\\",
            doublequote=True,
            na_rep="",
        )
        logger.info(f"Données exportées vers {file_path}")
    except Exception as e:
        logger.error(f"Erreur lors de l'export CSV: {e}")

        # Tentative de sauvegarde simplifiée
        try:
            file_path = os.path.join(OUTPUT_DIR, f"fallback_{filename}")
            df.to_csv(file_path, index=False, encoding="utf-8-sig")
            logger.info(f"Sauvegarde simplifiée vers {file_path}")
        except Exception as e2:
            logger.error(f"Échec de la sauvegarde simplifiée: {e2}")


def clean_dataframe(df):
    """
    Nettoie un DataFrame pour l'exportation CSV
    """
    df_clean = df.copy()

    for col in df_clean.columns:
        # Traitement des objets complexes (dict, list)
        if df_clean[col].apply(lambda x: isinstance(x, (dict, list))).any():
            df_clean[col] = df_clean[col].apply(
                lambda x: (
                    json.dumps(x, ensure_ascii=False, default=str)
                    if pd.notna(x)
                    else ""
                )
            )

        # Nettoyage des valeurs problématiques
        if df_clean[col].dtype == "object":
            df_clean[col] = df_clean[col].apply(
                lambda x: (
                    str(x).replace("\r", " ").replace("\n", " ").replace("\t", " ")
                    if isinstance(x, str)
                    else ("" if pd.isna(x) else str(x))
                )
            )

    return df_clean


def extract_job_offers(rome_code, start_date, end_date):
    """
    Extrait les offres d'emploi pour un code ROME et une période spécifique
    """
    api = FranceTravailAPI(TOKEN)
    all_offers = []

    # Paramètres de recherche initiaux
    params = SearchParams(
        codeROME=rome_code,
        minCreationDate=start_date,
        maxCreationDate=end_date,
        range="0-99",  # Récupérer les 100 premiers résultats
    )

    try:
        # Récupération de la première page
        results = api.search_offers(params)

        if not results.resultats:
            logger.info(
                f"Aucune offre trouvée pour {rome_code} entre {start_date} et {end_date}"
            )
            return []

        # Ajout des résultats au tableau
        all_offers.extend(offer_to_dict(offer) for offer in results.resultats)
        logger.info(
            f"Récupéré {len(results.resultats)} offres pour {rome_code} (page 1)"
        )

        # Pagination - récupérer les pages suivantes
        page = 1
        max_pages = 20  # Limite pour éviter les boucles infinies

        while results.resultats and page < max_pages:
            page += 1

            # Pause pour respecter les limites de l'API
            time.sleep(DELAY_BETWEEN_REQUESTS)

            # Calcul de la plage pour la page suivante
            start_idx = (page - 1) * 100
            end_idx = page * 100 - 1

            # Mise à jour des paramètres pour la prochaine page
            params = SearchParams(
                codeROME=rome_code,
                minCreationDate=start_date,
                maxCreationDate=end_date,
                range=f"{start_idx}-{end_idx}",
            )

            # Récupération de la page suivante
            try:
                results = api.search_offers(params)

                if results.resultats:
                    all_offers.extend(
                        offer_to_dict(offer) for offer in results.resultats
                    )
                    logger.info(
                        f"Récupéré {len(results.resultats)} offres pour {rome_code} (page {page})"
                    )
                else:
                    break  # Plus de résultats disponibles

            except Exception as e:
                logger.error(f"Erreur lors de la récupération de la page {page}: {e}")
                break

        return all_offers

    except Exception as e:
        logger.error(f"Erreur lors de l'extraction des offres pour {rome_code}: {e}")
        return []


def offer_to_dict(offer):
    """
    Convertit un objet offre en dictionnaire avec les champs principaux
    pour simplifier l'export CSV
    """
    data = {
        "id": offer.id,
        "intitule": offer.intitule,
        "description": offer.description,
        "date_creation": offer.dateCreation,
        "date_actualisation": offer.dateActualisation,
        "rome_code": offer.romeCode,
        "rome_libelle": offer.romeLibelle,
        "type_contrat": offer.typeContrat,
        "type_contrat_libelle": offer.typeContratLibelle,
        "nature_contrat": offer.natureContrat,
        "experience_exige": offer.experienceExige,
        "experience_libelle": offer.experienceLibelle,
        "alternance": offer.alternance,
        "nombre_postes": offer.nombrePostes,
    }

    # Ajout des informations sur le lieu de travail
    if offer.lieuTravail:
        data.update(
            {
                "lieu_travail_libelle": offer.lieuTravail.libelle,
                "lieu_travail_code_postal": offer.lieuTravail.codePostal,
                "lieu_travail_commune": offer.lieuTravail.commune,
                "lieu_travail_latitude": offer.lieuTravail.latitude,
                "lieu_travail_longitude": offer.lieuTravail.longitude,
            }
        )

    # Ajout des informations sur l'entreprise
    if offer.entreprise:
        data.update(
            {
                "entreprise_nom": offer.entreprise.nom,
                "entreprise_description": offer.entreprise.description,
            }
        )

    # Ajout des informations sur le salaire
    if offer.salaire:
        data.update(
            {
                "salaire_libelle": offer.salaire.libelle,
                "salaire_commentaire": offer.salaire.commentaire,
            }
        )

    return data


def main():
    """
    Fonction principale qui exécute l'extraction complète des données
    """
    logger.info("Démarrage de l'extraction des offres d'emploi")

    # Récupération des codes ROME
    rome_codes = get_rome_codes()
    logger.info(f"Nombre de codes ROME récupérés: {len(rome_codes)}")

    # Génération des plages de dates
    date_ranges = get_date_ranges(MONTHS_TO_COLLECT)
    logger.info(f"Périodes à collecter: {len(date_ranges)}")

    # Création du fichier de suivi pour reprendre en cas d'interruption
    progress_file = os.path.join(OUTPUT_DIR, "progress.txt")

    # Vérification s'il y a une progression précédente à reprendre
    completed_items = set()
    if os.path.exists(progress_file):
        with open(progress_file, "r") as f:
            completed_items = set(line.strip() for line in f)

    # Boucle principale d'extraction
    try:
        for i, rome_code in enumerate(rome_codes):
            logger.info(
                f"Traitement du code ROME {rome_code} ({i+1}/{len(rome_codes)})"
            )

            for j, (start_date, end_date) in enumerate(date_ranges):
                # Identifiant unique pour cette combinaison
                item_id = f"{rome_code}_{start_date}_{end_date}"

                # Vérifier si déjà traité
                if item_id in completed_items:
                    logger.info(f"Déjà traité: {item_id}")
                    continue

                logger.info(
                    f"Extraction pour {rome_code} du {start_date} au {end_date}"
                )

                # Extraction des offres
                offers = extract_job_offers(rome_code, start_date, end_date)

                if offers:
                    # Générer un nom de fichier unique
                    period_str = f"{start_date[:10]}_{end_date[:10]}"
                    filename = f"offres_{rome_code}_{period_str}.csv"

                    # Exportation des données en CSV
                    export_to_csv(offers, filename)

                # Marquer comme traité
                with open(progress_file, "a") as f:
                    f.write(f"{item_id}\n")

                # Pause pour respecter les limites de l'API
                time.sleep(DELAY_BETWEEN_REQUESTS)

    except KeyboardInterrupt:
        logger.info("Extraction interrompue par l'utilisateur")
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction: {e}")
    finally:
        logger.info("Fin de l'extraction")


if __name__ == "__main__":
    main()

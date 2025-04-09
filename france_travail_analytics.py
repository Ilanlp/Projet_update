"""
Script d'exemple utilisant le requêteur FranceTravailAPI pour:
- Rechercher des offres d'emploi
- Transformer les résultats en DataFrame pandas
- Analyser les salaires et types de contrats
- Exporter les données dans différents formats
- Générer des visualisations
"""

import os
import re
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import json
from datetime import datetime
from france_travail_api import FranceTravailAPI, SearchParams

# Configuration du style des visualisations
plt.style.use("ggplot")
sns.set_theme(style="whitegrid")


class FranceTravailAnalytics:
    """
    Classe pour analyser les offres d'emploi de France Travail
    """

    def __init__(self, token, output_dir="output"):
        """
        Initialise l'analyseur avec un token d'authentification

        Args:
            token (str): Token d'authentification pour l'API France Travail
            output_dir (str): Répertoire pour sauvegarder les outputs
        """
        self.api = FranceTravailAPI(token)
        self.output_dir = output_dir

        # Création du répertoire de sortie s'il n'existe pas
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Création des sous-répertoires
        for subdir in ["data", "plots", "reports"]:
            path = os.path.join(output_dir, subdir)
            if not os.path.exists(path):
                os.makedirs(path)

    def search_offers(self, **kwargs):
        """
        Recherche des offres d'emploi avec les paramètres spécifiés

        Args:
            **kwargs: Paramètres de recherche à passer à SearchParams

        Returns:
            pandas.DataFrame: DataFrame contenant les offres d'emploi
        """
        # Création des paramètres de recherche
        search_params = SearchParams(**kwargs)

        # Exécution de la recherche
        results = self.api.search_offers(search_params)

        # Transformation des offres en DataFrame
        return self._offers_to_dataframe(results.resultats)

    def _offers_to_dataframe(self, offers):
        """
        Transforme une liste d'offres en DataFrame pandas

        Args:
            offers (List[Offre]): Liste d'objets Offre

        Returns:
            pandas.DataFrame: DataFrame contenant les offres d'emploi
        """
        data = []

        for offer in offers:
            # Extraction des données principales
            offer_data = {
                "id": offer.id,
                "titre": offer.intitule,
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
                "nombre_postes": offer.nombrePostes,
                "accessible_th": offer.accessibleTH,
                "qualification_code": offer.qualificationCode,
                "qualification_libelle": offer.qualificationLibelle,
                "secteur_activite": offer.secteurActivite,
                "secteur_activite_libelle": offer.secteurActiviteLibelle,
                "duree_travail_libelle": offer.dureeTravailLibelle,
                "duree_travail_libelle_converti": offer.dureeTravailLibelleConverti,
                "alternance": offer.alternance,
                "offres_manque_candidats": offer.offresManqueCandidats,
            }

            # Extraction du lieu de travail
            if offer.lieuTravail:
                offer_data.update(
                    {
                        "lieu_travail_libelle": offer.lieuTravail.libelle,
                        "lieu_travail_latitude": offer.lieuTravail.latitude,
                        "lieu_travail_longitude": offer.lieuTravail.longitude,
                        "lieu_travail_code_postal": offer.lieuTravail.codePostal,
                        "lieu_travail_commune": offer.lieuTravail.commune,
                    }
                )

            # Extraction des informations sur l'entreprise
            if offer.entreprise:
                offer_data.update(
                    {
                        "entreprise_nom": offer.entreprise.nom,
                        "entreprise_description": offer.entreprise.description,
                        "entreprise_adaptee": offer.entreprise.entrepriseAdaptee,
                    }
                )

            # Extraction du salaire
            if offer.salaire:
                offer_data.update(
                    {
                        "salaire_libelle": offer.salaire.libelle,
                        "salaire_commentaire": offer.salaire.commentaire,
                        "salaire_complement1": offer.salaire.complement1,
                        "salaire_complement2": offer.salaire.complement2,
                    }
                )

                # Traitement du salaire
                if offer.salaire.libelle:
                    offer_data.update(self._parse_salary_info(offer.salaire.libelle))

            data.append(offer_data)

        # Création du DataFrame
        df = pd.DataFrame(data)

        # Conversion des colonnes de date
        for col in ["date_creation", "date_actualisation"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")

        return df

    def _parse_salary_info(self, salary_text):
        """
        Extrait des informations structurées à partir du texte du salaire

        Args:
            salary_text (str): Texte du salaire (ex: "Mensuel de 2500.00 Euros sur 12 mois")

        Returns:
            dict: Dictionnaire avec les informations du salaire structurées
        """
        result = {
            "salaire_montant_min": None,
            "salaire_montant_max": None,
            "salaire_periode": None,
            "salaire_nb_mois": None,
        }

        if not salary_text:
            return result

        # Extraction de la période (Mensuel, Annuel, Horaire)
        periode_patterns = {
            "Mensuel": "Mensuel",
            "Annuel": "Annuel",
            "Horaire": "Horaire",
            "Journalier": "Journalier",
            "Hebdomadaire": "Hebdomadaire",
        }

        for pattern, periode in periode_patterns.items():
            if pattern in salary_text:
                result["salaire_periode"] = periode
                break

        # Extraction du montant
        amount_pattern = r"de (\d+[\.,]\d+)(?: [àa] (\d+[\.,]\d+))? Euros"
        amount_match = re.search(amount_pattern, salary_text)

        if amount_match:
            min_amount = amount_match.group(1).replace(",", ".")
            result["salaire_montant_min"] = float(min_amount)

            if amount_match.group(2):
                max_amount = amount_match.group(2).replace(",", ".")
                result["salaire_montant_max"] = float(max_amount)

        # Extraction du nombre de mois
        months_pattern = r"sur (\d+) mois"
        months_match = re.search(months_pattern, salary_text)

        if months_match:
            result["salaire_nb_mois"] = int(months_match.group(1))

        return result

    def analyze_salaries(self, df):
        """
        Analyse les salaires des offres d'emploi

        Args:
            df (pandas.DataFrame): DataFrame contenant les offres d'emploi

        Returns:
            pandas.DataFrame: DataFrame avec les statistiques de salaire
        """
        # Filtrer les offres avec des salaires
        df_salary = df.dropna(subset=["salaire_montant_min"]).copy()

        if df_salary.empty:
            print("Aucune information de salaire disponible dans les offres.")
            return pd.DataFrame()

        # Normalisation des salaires (tout convertir en base annuelle)
        def normalize_salary(row):
            amount = row["salaire_montant_min"]
            periode = row["salaire_periode"]

            if periode == "Mensuel":
                # Conversion mensuel -> annuel
                nb_mois = (
                    row["salaire_nb_mois"] if pd.notna(row["salaire_nb_mois"]) else 12
                )
                return amount * nb_mois
            elif periode == "Horaire":
                # Conversion horaire -> annuel (base 35h/semaine, 52 semaines)
                return amount * 35 * 52
            elif periode == "Journalier":
                # Conversion journalier -> annuel (base 5j/semaine, 52 semaines)
                return amount * 5 * 52
            elif periode == "Hebdomadaire":
                # Conversion hebdomadaire -> annuel
                return amount * 52
            else:
                # Déjà annuel ou période non reconnue
                return amount

        df_salary["salaire_annuel_normalise"] = df_salary.apply(
            normalize_salary, axis=1
        )

        # Statistiques par type de contrat
        stats = (
            df_salary.groupby("type_contrat_libelle")
            .agg(
                {
                    "salaire_annuel_normalise": [
                        "count",
                        "mean",
                        "median",
                        "min",
                        "max",
                        "std",
                    ]
                }
            )
            .reset_index()
        )

        # Aplatissement des noms de colonnes
        stats.columns = ["_".join(col).strip() for col in stats.columns.values]

        # Renommage des colonnes
        stats = stats.rename(
            columns={
                "type_contrat_libelle_": "type_contrat",
                "salaire_annuel_normalise_count": "nb_offres",
                "salaire_annuel_normalise_mean": "moyenne",
                "salaire_annuel_normalise_median": "mediane",
                "salaire_annuel_normalise_min": "minimum",
                "salaire_annuel_normalise_max": "maximum",
                "salaire_annuel_normalise_std": "ecart_type",
            }
        )

        return stats

    def analyze_contract_types(self, df):
        """
        Analyse les types de contrat des offres d'emploi

        Args:
            df (pandas.DataFrame): DataFrame contenant les offres d'emploi

        Returns:
            pandas.DataFrame: DataFrame avec les statistiques de types de contrat
        """
        # Préparation des données
        contract_counts = df["type_contrat_libelle"].value_counts().reset_index()
        contract_counts.columns = ["type_contrat", "nombre"]
        contract_counts["pourcentage"] = (
            contract_counts["nombre"] / contract_counts["nombre"].sum() * 100
        )

        return contract_counts

    def plot_salary_distribution(self, df, filename="salary_distribution.png"):
        """
        Génère un graphique de distribution des salaires

        Args:
            df (pandas.DataFrame): DataFrame contenant les offres d'emploi
            filename (str): Nom du fichier pour sauvegarder le graphique
        """
        # Filtrer les offres avec des salaires
        df_salary = df.dropna(subset=["salaire_montant_min"]).copy()

        if df_salary.empty:
            print("Aucune information de salaire disponible pour créer le graphique.")
            return

        # Normalisation des salaires si pas déjà fait
        if "salaire_annuel_normalise" not in df_salary.columns:
            df_salary["salaire_annuel_normalise"] = df_salary.apply(
                lambda row: self._normalize_salary(row), axis=1
            )

        # Création de la figure
        plt.figure(figsize=(12, 8))

        # Distribution des salaires
        sns.histplot(
            df_salary["salaire_annuel_normalise"], bins=30, kde=True, color="steelblue"
        )

        # Ajout des lignes pour la moyenne et la médiane
        mean_salary = df_salary["salaire_annuel_normalise"].mean()
        median_salary = df_salary["salaire_annuel_normalise"].median()

        plt.axvline(
            mean_salary,
            color="red",
            linestyle="--",
            label=f"Moyenne: {mean_salary:.2f} €",
        )
        plt.axvline(
            median_salary,
            color="green",
            linestyle="-",
            label=f"Médiane: {median_salary:.2f} €",
        )

        # Mise en forme
        plt.title("Distribution des salaires annuels", fontsize=16)
        plt.xlabel("Salaire annuel (€)", fontsize=14)
        plt.ylabel("Nombre d'offres", fontsize=14)
        plt.legend()
        plt.grid(True, alpha=0.3)

        # Sauvegarde
        output_path = os.path.join(self.output_dir, "plots", filename)
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close()

        print(f"Graphique de distribution des salaires sauvegardé: {output_path}")

    def plot_contract_types(self, df, filename="contract_types.png"):
        """
        Génère un graphique des types de contrat

        Args:
            df (pandas.DataFrame): DataFrame contenant les offres d'emploi
            filename (str): Nom du fichier pour sauvegarder le graphique
        """
        # Analyse des types de contrat
        contract_data = self.analyze_contract_types(df)

        if contract_data.empty:
            print(
                "Aucune information de type de contrat disponible pour créer le graphique."
            )
            return

        # Sélection des 8 types de contrat les plus fréquents
        top_contracts = contract_data.head(8).copy()

        # Regroupement des autres types de contrat
        if len(contract_data) > 8:
            other_count = contract_data.iloc[8:]["nombre"].sum()
            other_pct = contract_data.iloc[8:]["pourcentage"].sum()

            other_row = pd.DataFrame(
                {
                    "type_contrat": ["Autres"],
                    "nombre": [other_count],
                    "pourcentage": [other_pct],
                }
            )

            top_contracts = pd.concat([top_contracts, other_row], ignore_index=True)

        # Création de la figure
        plt.figure(figsize=(12, 8))

        # Graphique en camembert
        plt.pie(
            top_contracts["nombre"],
            labels=top_contracts["type_contrat"],
            autopct="%1.1f%%",
            startangle=90,
            shadow=False,
            explode=[0.05] * len(top_contracts),
            textprops={"fontsize": 12},
        )

        # Mise en forme
        plt.title("Répartition des types de contrat", fontsize=16)
        plt.axis("equal")  # Equal aspect ratio ensures that pie is drawn as a circle

        # Sauvegarde
        output_path = os.path.join(self.output_dir, "plots", filename)
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close()

        print(f"Graphique des types de contrat sauvegardé: {output_path}")

    def plot_offers_by_region(self, df, filename="offers_by_region.png"):
        """
        Génère un graphique des offres par région

        Args:
            df (pandas.DataFrame): DataFrame contenant les offres d'emploi
            filename (str): Nom du fichier pour sauvegarder le graphique
        """
        # Extraction des régions à partir des codes postaux
        if "lieu_travail_code_postal" in df.columns:
            # Ajout d'une colonne de région basée sur les deux premiers chiffres du code postal
            df["region_code"] = df["lieu_travail_code_postal"].apply(
                lambda x: str(x)[:2] if pd.notna(x) and str(x).isdigit() else None
            )

            # Dictionnaire des régions (codes postaux)
            region_dict = {
                "01": "Ain (Auvergne-Rhône-Alpes)",
                "02": "Aisne (Hauts-de-France)",
                "03": "Allier (Auvergne-Rhône-Alpes)",
                "04": "Alpes-de-Haute-Provence (PACA)",
                "05": "Hautes-Alpes (PACA)",
                "06": "Alpes-Maritimes (PACA)",
                "07": "Ardèche (Auvergne-Rhône-Alpes)",
                "08": "Ardennes (Grand Est)",
                "09": "Ariège (Occitanie)",
                "10": "Aube (Grand Est)",
                "11": "Aude (Occitanie)",
                "12": "Aveyron (Occitanie)",
                "13": "Bouches-du-Rhône (PACA)",
                "14": "Calvados (Normandie)",
                "15": "Cantal (Auvergne-Rhône-Alpes)",
                "16": "Charente (Nouvelle-Aquitaine)",
                "17": "Charente-Maritime (Nouvelle-Aquitaine)",
                "18": "Cher (Centre-Val de Loire)",
                "19": "Corrèze (Nouvelle-Aquitaine)",
                "2A": "Corse-du-Sud (Corse)",
                "2B": "Haute-Corse (Corse)",
                "21": "Côte-d'Or (Bourgogne-Franche-Comté)",
                "22": "Côtes-d'Armor (Bretagne)",
                "23": "Creuse (Nouvelle-Aquitaine)",
                "24": "Dordogne (Nouvelle-Aquitaine)",
                "25": "Doubs (Bourgogne-Franche-Comté)",
                "26": "Drôme (Auvergne-Rhône-Alpes)",
                "27": "Eure (Normandie)",
                "28": "Eure-et-Loir (Centre-Val de Loire)",
                "29": "Finistère (Bretagne)",
                "30": "Gard (Occitanie)",
                "31": "Haute-Garonne (Occitanie)",
                "32": "Gers (Occitanie)",
                "33": "Gironde (Nouvelle-Aquitaine)",
                "34": "Hérault (Occitanie)",
                "35": "Ille-et-Vilaine (Bretagne)",
                "36": "Indre (Centre-Val de Loire)",
                "37": "Indre-et-Loire (Centre-Val de Loire)",
                "38": "Isère (Auvergne-Rhône-Alpes)",
                "39": "Jura (Bourgogne-Franche-Comté)",
                "40": "Landes (Nouvelle-Aquitaine)",
                "41": "Loir-et-Cher (Centre-Val de Loire)",
                "42": "Loire (Auvergne-Rhône-Alpes)",
                "43": "Haute-Loire (Auvergne-Rhône-Alpes)",
                "44": "Loire-Atlantique (Pays de la Loire)",
                "45": "Loiret (Centre-Val de Loire)",
                "46": "Lot (Occitanie)",
                "47": "Lot-et-Garonne (Nouvelle-Aquitaine)",
                "48": "Lozère (Occitanie)",
                "49": "Maine-et-Loire (Pays de la Loire)",
                "50": "Manche (Normandie)",
                "51": "Marne (Grand Est)",
                "52": "Haute-Marne (Grand Est)",
                "53": "Mayenne (Pays de la Loire)",
                "54": "Meurthe-et-Moselle (Grand Est)",
                "55": "Meuse (Grand Est)",
                "56": "Morbihan (Bretagne)",
                "57": "Moselle (Grand Est)",
                "58": "Nièvre (Bourgogne-Franche-Comté)",
                "59": "Nord (Hauts-de-France)",
                "60": "Oise (Hauts-de-France)",
                "61": "Orne (Normandie)",
                "62": "Pas-de-Calais (Hauts-de-France)",
                "63": "Puy-de-Dôme (Auvergne-Rhône-Alpes)",
                "64": "Pyrénées-Atlantiques (Nouvelle-Aquitaine)",
                "65": "Hautes-Pyrénées (Occitanie)",
                "66": "Pyrénées-Orientales (Occitanie)",
                "67": "Bas-Rhin (Grand Est)",
                "68": "Haut-Rhin (Grand Est)",
                "69": "Rhône (Auvergne-Rhône-Alpes)",
                "70": "Haute-Saône (Bourgogne-Franche-Comté)",
                "71": "Saône-et-Loire (Bourgogne-Franche-Comté)",
                "72": "Sarthe (Pays de la Loire)",
                "73": "Savoie (Auvergne-Rhône-Alpes)",
                "74": "Haute-Savoie (Auvergne-Rhône-Alpes)",
                "75": "Paris (Île-de-France)",
                "76": "Seine-Maritime (Normandie)",
                "77": "Seine-et-Marne (Île-de-France)",
                "78": "Yvelines (Île-de-France)",
                "79": "Deux-Sèvres (Nouvelle-Aquitaine)",
                "80": "Somme (Hauts-de-France)",
                "81": "Tarn (Occitanie)",
                "82": "Tarn-et-Garonne (Occitanie)",
                "83": "Var (PACA)",
                "84": "Vaucluse (PACA)",
                "85": "Vendée (Pays de la Loire)",
                "86": "Vienne (Nouvelle-Aquitaine)",
                "87": "Haute-Vienne (Nouvelle-Aquitaine)",
                "88": "Vosges (Grand Est)",
                "89": "Yonne (Bourgogne-Franche-Comté)",
                "90": "Territoire de Belfort (Bourgogne-Franche-Comté)",
                "91": "Essonne (Île-de-France)",
                "92": "Hauts-de-Seine (Île-de-France)",
                "93": "Seine-Saint-Denis (Île-de-France)",
                "94": "Val-de-Marne (Île-de-France)",
                "95": "Val-d'Oise (Île-de-France)",
                "97": "DOM-TOM",
                "98": "Monaco & International",
            }

            # Ajout du nom de la région
            df["region_name"] = df["region_code"].map(region_dict)

            # Comptage des offres par région
            region_counts = df["region_name"].value_counts().reset_index()
            region_counts.columns = ["region", "nombre"]

            # Sélection des 15 premières régions
            top_regions = region_counts.head(15)

            # Création de la figure
            plt.figure(figsize=(14, 10))

            # Graphique en barres horizontales
            bars = plt.barh(
                top_regions["region"], top_regions["nombre"], color="steelblue"
            )

            # Ajout des valeurs à droite des barres
            for i, bar in enumerate(bars):
                plt.text(
                    bar.get_width() + 1,
                    bar.get_y() + bar.get_height() / 2,
                    str(top_regions["nombre"].iloc[i]),
                    va="center",
                )

            # Mise en forme
            plt.title("Nombre d'offres par région (Top 15)", fontsize=16)
            plt.xlabel("Nombre d'offres", fontsize=14)
            plt.ylabel("Région", fontsize=14)
            plt.grid(True, alpha=0.3)

            # Sauvegarde
            output_path = os.path.join(self.output_dir, "plots", filename)
            plt.savefig(output_path, dpi=300, bbox_inches="tight")
            plt.close()

            print(f"Graphique des offres par région sauvegardé: {output_path}")
        else:
            print(
                "Données de code postal manquantes pour créer le graphique par région."
            )

    def _normalize_salary(self, row):
        """
        Normalise un salaire en salaire annuel

        Args:
            row (pandas.Series): Ligne du DataFrame contenant les informations de salaire

        Returns:
            float: Salaire annuel normalisé
        """
        amount = row["salaire_montant_min"]
        periode = row["salaire_periode"]

        if periode == "Mensuel":
            # Conversion mensuel -> annuel
            nb_mois = row["salaire_nb_mois"] if pd.notna(row["salaire_nb_mois"]) else 12
            return amount * nb_mois
        elif periode == "Horaire":
            # Conversion horaire -> annuel (base 35h/semaine, 52 semaines)
            return amount * 35 * 52
        elif periode == "Journalier":
            # Conversion journalier -> annuel (base 5j/semaine, 52 semaines)
            return amount * 5 * 52
        elif periode == "Hebdomadaire":
            # Conversion hebdomadaire -> annuel
            return amount * 52
        else:
            # Déjà annuel ou période non reconnue
            return amount

    def export_data(self, df, format_type="csv", filename="offres_emploi"):
        """
        Exporte les données dans différents formats avec un nettoyage approprié

        Args:
            df (pandas.DataFrame): DataFrame à exporter
            format_type (str): Format d'export ('csv', 'json', 'html')
            filename (str): Nom de base pour le fichier (sans extension)
        """
        import csv

        output_path = os.path.join(self.output_dir, "data", filename)

        # Créer une copie du DataFrame pour éviter de modifier l'original
        df_export = df.copy()

        # Nettoyer le DataFrame pour l'exportation
        df_export = self._clean_dataframe_for_export(df_export)

        if format_type.lower() == "csv":
            try:
                # Utiliser une configuration optimisée pour CSV
                df_export.to_csv(
                    f"{output_path}.csv",
                    index=False,
                    encoding="utf-8-sig",  # Utiliser UTF-8 avec BOM pour une meilleure compatibilité
                    quoting=csv.QUOTE_NONNUMERIC,  # Mettre les chaînes entre guillemets
                    escapechar="\\",  # Caractère d'échappement
                    doublequote=True,  # Doubler les guillemets dans les chaînes
                    na_rep="",  # Représentation des valeurs NA
                )
                print(f"Données exportées en CSV: {output_path}.csv")
            except Exception as e:
                print(f"Erreur lors de l'exportation en CSV: {str(e)}")
                # Tentative de sauvegarde avec des options plus sécurisées
                try:
                    df_export.to_csv(
                        f"{output_path}_fallback.csv",
                        index=False,
                        encoding="utf-8-sig",
                        quoting=csv.QUOTE_ALL,  # Mettre tout entre guillemets
                        escapechar="\\",
                        quotechar='"',
                        na_rep="",
                        sep=";",  # Utiliser un séparateur moins susceptible d'être dans les données
                    )
                    print(f"Sauvegarde fallback réussie: {output_path}_fallback.csv")
                except Exception as e2:
                    print(f"Échec de la sauvegarde fallback: {str(e2)}")

        elif format_type.lower() == "json":
            try:
                # Conversion des dates en chaînes pour JSON
                df_json = df_export.copy()
                for col in df_json.select_dtypes(include=["datetime64"]).columns:
                    df_json[col] = df_json[col].dt.strftime("%Y-%m-%dT%H:%M:%SZ")

                df_json.to_json(
                    f"{output_path}.json",
                    orient="records",
                    force_ascii=False,
                    date_format="iso",
                    indent=4,
                )
                print(f"Données exportées en JSON: {output_path}.json")
            except Exception as e:
                print(f"Erreur lors de l'exportation en JSON: {str(e)}")

        elif format_type.lower() == "html":
            try:
                # Création d'un tableau HTML stylisé
                html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <title>Offres d'emploi France Travail</title>
                    <style>
                        body {{
                            font-family: Arial, sans-serif;
                            margin: 20px;
                        }}
                        h1 {{
                            color: #0056b3;
                        }}
                        table {{
                            border-collapse: collapse;
                            width: 100%;
                            margin-top: 20px;
                        }}
                        th, td {{
                            text-align: left;
                            padding: 8px;
                            border-bottom: 1px solid #ddd;
                        }}
                        th {{
                            background-color: #0056b3;
                            color: white;
                        }}
                        tr:nth-child(even) {{
                            background-color: #f2f2f2;
                        }}
                        tr:hover {{
                            background-color: #ddd;
                        }}
                        .metadata {{
                            margin-bottom: 20px;
                            font-style: italic;
                            color: #666;
                        }}
                    </style>
                </head>
                <body>
                    <h1>Offres d'emploi France Travail</h1>
                    <div class="metadata">
                        <p>Date d'exportation: {datetime.now().strftime("%d/%m/%Y %H:%M")}</p>
                        <p>Nombre d'offres: {len(df_export)}</p>
                    </div>
                    {df_export.to_html(index=False, classes="data-table", na_rep="")}
                </body>
                </html>
                """

                with open(f"{output_path}.html", "w", encoding="utf-8") as file:
                    file.write(html_content)

                print(f"Données exportées en HTML: {output_path}.html")
            except Exception as e:
                print(f"Erreur lors de l'exportation en HTML: {str(e)}")

        else:
            print(
                f"Format '{format_type}' non pris en charge. Formats disponibles: csv, json, html"
            )

    def _clean_dataframe_for_export(self, df):
        """
        Nettoie un DataFrame pour l'exportation

        Args:
            df (pandas.DataFrame): DataFrame à nettoyer

        Returns:
            pandas.DataFrame: DataFrame nettoyé
        """
        # Créer une copie pour éviter de modifier l'original
        df_clean = df.copy()

        # 1. Convertir les colonnes complexes en chaînes JSON
        for col in df_clean.columns:
            # Identifier les colonnes avec des objets complexes (dictionnaires, listes)
            if df_clean[col].apply(lambda x: isinstance(x, (dict, list))).any():
                df_clean[col] = df_clean[col].apply(
                    lambda x: json.dumps(x, ensure_ascii=False, default=str)
                    if pd.notna(x)
                    else None
                )

        # 2. Nettoyer les valeurs non exportables
        for col in df_clean.columns:
            # Convertir les NaN, None, etc.
            df_clean[col] = df_clean[col].apply(lambda x: "" if pd.isna(x) else x)

            # Convertir les autres types complexes en chaînes
            df_clean[col] = df_clean[col].apply(
                lambda x: str(x)
                if not isinstance(x, (str, int, float, bool, type(None)))
                else x
            )

            # Supprimer les caractères problématiques pour CSV
            if df_clean[col].dtype == "object":  # Colonnes textuelles
                df_clean[col] = df_clean[col].apply(
                    lambda x: str(x)
                    .replace("\r", " ")
                    .replace("\n", " ")
                    .replace("\t", " ")
                    if isinstance(x, str)
                    else x
                )

        # 3. Traiter les caractères spéciaux dans les noms de colonnes
        df_clean.columns = [
            col.replace("\r", " ").replace("\n", " ").replace("\t", " ")
            for col in df_clean.columns
        ]

        # 4. Tronquer les valeurs trop longues si nécessaire
        max_length = 32767  # Limite pour une cellule
        for col in df_clean.select_dtypes(include=["object"]).columns:
            df_clean[col] = df_clean[col].apply(
                lambda x: x[:max_length]
                if isinstance(x, str) and len(x) > max_length
                else x
            )

        return df_clean

    def generate_report(self, df, filename="rapport_analyse.html"):
        """
        Génère un rapport d'analyse complet

        Args:
            df (pandas.DataFrame): DataFrame contenant les offres d'emploi
            filename (str): Nom du fichier pour le rapport
        """
        # Calcul des statistiques
        total_offers = len(df)

        # Analyse des contrats
        contract_stats = self.analyze_contract_types(df)

        # Analyse des salaires
        salary_stats = self.analyze_salaries(df)

        # Distribution par département
        dept_distribution = None
        if "lieu_travail_code_postal" in df.columns:
            dept_distribution = (
                df["lieu_travail_code_postal"]
                .apply(
                    lambda x: str(x)[:2] if pd.notna(x) and str(x).isdigit() else None
                )
                .value_counts()
                .reset_index()
            )
            dept_distribution.columns = ["departement", "nombre"]
            dept_distribution = dept_distribution.head(10)  # Top 10

        # Distribution des expériences requises
        exp_distribution = None
        if "experience_libelle" in df.columns:
            exp_distribution = df["experience_libelle"].value_counts().reset_index()
            exp_distribution.columns = ["experience", "nombre"]

        # Génération des graphiques pour le rapport
        self.plot_salary_distribution(df, "salary_dist_report.png")
        self.plot_contract_types(df, "contract_types_report.png")
        self.plot_offers_by_region(df, "region_dist_report.png")

        # Création du contenu HTML
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Rapport d'Analyse des Offres d'Emploi</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    margin: 0;
                    padding: 20px;
                    color: #333;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                }}
                h1, h2, h3 {{
                    color: #0056b3;
                }}
                h1 {{
                    text-align: center;
                    border-bottom: 2px solid #0056b3;
                    padding-bottom: 10px;
                }}
                .summary {{
                    background-color: #f8f9fa;
                    padding: 20px;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .stats-container {{
                    display: flex;
                    flex-wrap: wrap;
                    justify-content: space-between;
                }}
                .stat-box {{
                    background-color: #e9ecef;
                    padding: 15px;
                    margin: 10px 0;
                    border-radius: 5px;
                    width: 48%;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                }}
                th, td {{
                    padding: 10px;
                    text-align: left;
                    border-bottom: 1px solid #ddd;
                }}
                th {{
                    background-color: #0056b3;
                    color: white;
                }}
                tr:nth-child(even) {{
                    background-color: #f2f2f2;
                }}
                .chart {{
                    margin: 30px 0;
                    text-align: center;
                }}
                .chart img {{
                    max-width: 100%;
                    height: auto;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 50px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                    font-size: 0.9em;
                    color: #666;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Rapport d'Analyse des Offres d'Emploi</h1>
                
                <div class="summary">
                    <h2>Résumé</h2>
                    <p>Analyse basée sur <strong>{
            total_offers
        }</strong> offres d'emploi extraites de France Travail.</p>
                    <p>Date de génération du rapport: <strong>{
            datetime.now().strftime("%d/%m/%Y %H:%M")
        }</strong></p>
                </div>
                
                <div class="stats-container">
                    <div class="stat-box">
                        <h3>Types de Contrat</h3>
                        <p>Distribution des offres par type de contrat:</p>
                        <table>
                            <tr>
                                <th>Type de contrat</th>
                                <th>Nombre</th>
                                <th>Pourcentage</th>
                            </tr>
                            {
            "".join(
                f"<tr><td>{row['type_contrat']}</td><td>{row['nombre']}</td><td>{row['pourcentage']:.1f}%</td></tr>"
                for _, row in contract_stats.iterrows()
            )
        }
                        </table>
                    </div>
                    
                    <div class="stat-box">
                        <h3>Analyse des Salaires</h3>
                        <p>Statistiques des salaires par type de contrat:</p>
                        <table>
                            <tr>
                                <th>Type de contrat</th>
                                <th>Nombre</th>
                                <th>Moyenne (€)</th>
                                <th>Médiane (€)</th>
                            </tr>
                            {
            "".join(
                f"<tr><td>{row['type_contrat']}</td><td>{row['nb_offres']}</td><td>{row['moyenne']:.2f}</td><td>{row['mediane']:.2f}</td></tr>"
                for _, row in salary_stats.iterrows()
            )
        }
                        </table>
                    </div>
                </div>
                
                <div class="chart">
                    <h2>Distribution des Salaires</h2>
                    <img src="../plots/salary_dist_report.png" alt="Distribution des salaires">
                </div>
                
                <div class="chart">
                    <h2>Répartition par Type de Contrat</h2>
                    <img src="../plots/contract_types_report.png" alt="Types de contrat">
                </div>
                
                <div class="chart">
                    <h2>Distribution par Région</h2>
                    <img src="../plots/region_dist_report.png" alt="Distribution par région">
                </div>
                
                {
            f'''
                <div class="stat-box">
                    <h3>Top 10 des Départements</h3>
                    <table>
                        <tr>
                            <th>Département</th>
                            <th>Nombre d'offres</th>
                        </tr>
                        {"".join(f"<tr><td>{row['departement']}</td><td>{row['nombre']}</td></tr>" for _, row in dept_distribution.iterrows())}
                    </table>
                </div>
                '''
            if dept_distribution is not None
            else ""
        }
                
                {
            f'''
                <div class="stat-box">
                    <h3>Expérience Requise</h3>
                    <table>
                        <tr>
                            <th>Niveau d'expérience</th>
                            <th>Nombre d'offres</th>
                        </tr>
                        {"".join(f"<tr><td>{row['experience']}</td><td>{row['nombre']}</td></tr>" for _, row in exp_distribution.iterrows())}
                    </table>
                </div>
                '''
            if exp_distribution is not None
            else ""
        }
                
                <div class="footer">
                    <p>Rapport généré avec FranceTravailAnalytics</p>
                    <p>Données extraites via l'API France Travail</p>
                </div>
            </div>
        </body>
        </html>
        """

        # Sauvegarde du rapport
        output_path = os.path.join(self.output_dir, "reports", filename)
        with open(output_path, "w", encoding="utf-8") as file:
            file.write(html_content)

        print(f"Rapport d'analyse sauvegardé: {output_path}")


# Exemple d'utilisation
if __name__ == "__main__":
    # Votre token d'authentification France Travail
    token = "votre_token_ici"

    # Création de l'analyseur
    analyzer = FranceTravailAnalytics(token)

    # Recherche d'offres d'emploi pour des métiers de data science/engineering
    search_params = {
        "motsCles": "python,data",
        "typeContrat": "CDI",
        "experienceExigence": "D",  # Débutant accepté
        "qualification": 9,  # Cadre
        "range": "0-99",  # Récupérer jusqu'à 100 offres
    }

    # Exécution de la recherche et récupération des résultats
    offres_df = analyzer.search_offers(**search_params)

    # Affichage des statistiques sur les données récupérées
    print(f"Nombre d'offres trouvées: {len(offres_df)}")

    # Exportation des données en différents formats
    analyzer.export_data(offres_df, format_type="csv")
    analyzer.export_data(offres_df, format_type="excel")
    analyzer.export_data(offres_df, format_type="json")
    analyzer.export_data(offres_df, format_type="html")

    # Analyse des salaires
    salary_stats = analyzer.analyze_salaries(offres_df)
    if not salary_stats.empty:
        print("\nStatistiques des salaires:")
        print(salary_stats)

    # Analyse des types de contrat
    contract_stats = analyzer.analyze_contract_types(offres_df)
    print("\nStatistiques des types de contrat:")
    print(contract_stats)

    # Génération des visualisations
    analyzer.plot_salary_distribution(offres_df)
    analyzer.plot_contract_types(offres_df)
    analyzer.plot_offers_by_region(offres_df)

    # Génération d'un rapport complet
    analyzer.generate_report(offres_df)

    print("\nAnalyse complète terminée avec succès!")

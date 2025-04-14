"""
Exemple d'application utilisant le client Adzuna pour rechercher et analyser des offres d'emploi
"""

import asyncio
import pandas as pd
import matplotlib.pyplot as plt
from typing import List, Dict, Any, Tuple
import os
from dotenv import load_dotenv
from datetime import datetime
import csv
import argparse
import json
from rich.console import Console
from rich.table import Table

# Importer notre client Adzuna
from adzuna_api import (
    AdzunaClient,
    CountryCode,
    Job,
    AdzunaClientError,
    SortBy,
    SortDirection,
)


class AdzunaDataAnalyzer:
    """
    Classe pour analyser les données d'offres d'emploi provenant de l'API Adzuna

    Cette classe permet de:
    - Rechercher des offres d'emploi via l'API Adzuna
    - Transformer les résultats en DataFrame pandas
    - Analyser les salaires et types de contrats
    - Exporter les données dans différents formats
    - Générer des visualisations
    """

    def __init__(self, app_id: str, app_key: str):
        """
        Initialise l'analyseur de données Adzuna

        Args:
            app_id: Identifiant d'application Adzuna
            app_key: Clé d'API Adzuna
        """
        self.client = AdzunaClient(app_id, app_key)

    async def close(self):
        """Ferme le client"""
        await self.client.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def search_and_analyze(
        self,
        country: CountryCode,
        search_term: str,
        location: str = None,
        max_results: int = 100,
    ) -> pd.DataFrame:
        """
        Recherche des offres d'emploi et les convertit en DataFrame pour analyse

        Args:
            country: Le code pays pour la recherche
            search_term: Le terme de recherche (ex: "python")
            location: La localisation (ex: "Paris")
            max_results: Nombre maximum de résultats à récupérer

        Returns:
            Un DataFrame contenant les offres d'emploi
        """
        current_page = 1
        results_per_page = min(50, max_results)
        all_jobs = []

        while len(all_jobs) < max_results:
            try:
                # Construire les paramètres de recherche
                search_params = {
                    "what": search_term,
                    "results_per_page": results_per_page,
                }

                if location:
                    search_params["where"] = location

                # Effectuer la recherche
                results = await self.client.search_jobs(
                    country=country, page=current_page, **search_params
                )

                # Ajouter les résultats à notre liste
                all_jobs.extend(results.results)

                # Vérifier s'il y a plus de résultats
                if len(results.results) < results_per_page:
                    break

                current_page += 1

            except AdzunaClientError as e:
                print(f"Erreur lors de la recherche: {e}")
                break

        # Limiter au nombre maximum demandé
        all_jobs = all_jobs[:max_results]

        # Convertir en DataFrame
        return self._convert_jobs_to_dataframe(all_jobs)

    def _convert_jobs_to_dataframe(self, jobs: List[Job]) -> pd.DataFrame:
        """
        Convertit une liste d'objets Job en DataFrame pandas

        Args:
            jobs: Liste d'objets Job

        Returns:
            DataFrame pandas
        """
        job_data = []

        for job in jobs:
            # Extraire les informations de base
            job_info = {
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
            }

            # Ajouter des informations de localisation si disponibles
            if job.location:
                job_info["location_display_name"] = job.location.display_name
                if job.location.area:
                    for i, area in enumerate(job.location.area):
                        job_info[f"location_area_{i}"] = area

            # Ajouter des informations de catégorie si disponibles
            if job.category:
                job_info["category_tag"] = job.category.tag
                job_info["category_label"] = job.category.label

            # Ajouter des informations d'entreprise si disponibles
            if job.company:
                job_info["company_display_name"] = job.company.display_name

            job_data.append(job_info)

        return pd.DataFrame(job_data)

    async def get_salary_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyse les salaires des offres d'emploi

        Args:
            df: DataFrame contenant les offres d'emploi

        Returns:
            Dictionnaire avec les statistiques de salaire
        """
        # Filtrer les offres avec des informations de salaire
        salary_df = df[df["salary_min"].notna() & df["salary_max"].notna()].copy()

        if len(salary_df) == 0:
            return {
                "count": 0,
                "mean_min": None,
                "mean_max": None,
                "median_min": None,
                "median_max": None,
                "min": None,
                "max": None,
            }

        # Calculer le salaire moyen
        salary_df["avg_salary"] = (
            salary_df["salary_min"] + salary_df["salary_max"]
        ) / 2

        return {
            "count": len(salary_df),
            "mean_min": salary_df["salary_min"].mean(),
            "mean_max": salary_df["salary_max"].mean(),
            "mean_avg": salary_df["avg_salary"].mean(),
            "median_min": salary_df["salary_min"].median(),
            "median_max": salary_df["salary_max"].median(),
            "median_avg": salary_df["avg_salary"].median(),
            "min": salary_df["salary_min"].min(),
            "max": salary_df["salary_max"].max(),
        }

    async def create_salary_charts(
        self, df: pd.DataFrame, output_dir: str = "./charts"
    ):
        """
        Crée des graphiques pour visualiser les salaires

        Args:
            df: DataFrame contenant les offres d'emploi
            output_dir: Répertoire où enregistrer les graphiques
        """
        # Créer le répertoire de sortie s'il n'existe pas
        os.makedirs(output_dir, exist_ok=True)

        # Filtrer les offres avec des informations de salaire
        salary_df = df[df["salary_min"].notna() & df["salary_max"].notna()].copy()

        if len(salary_df) == 0:
            print("Aucune donnée de salaire disponible pour créer des graphiques")
            return

        # Calculer le salaire moyen
        salary_df["avg_salary"] = (
            salary_df["salary_min"] + salary_df["salary_max"]
        ) / 2

        # 1. Distribution des salaires moyens
        plt.figure(figsize=(10, 6))
        plt.hist(salary_df["avg_salary"], bins=20, edgecolor="black")
        plt.title("Distribution des salaires moyens")
        plt.xlabel("Salaire moyen")
        plt.ylabel("Nombre d'offres")
        plt.grid(True, alpha=0.3)
        plt.savefig(f"{output_dir}/salary_distribution.png")
        plt.close()

        # 2. Boîte à moustaches des salaires min/max
        plt.figure(figsize=(10, 6))
        salary_df[["salary_min", "salary_max"]].boxplot()
        plt.title("Boîte à moustaches des salaires minimum et maximum")
        plt.ylabel("Salaire")
        plt.grid(True, alpha=0.3)
        plt.savefig(f"{output_dir}/salary_boxplot.png")
        plt.close()

        # 3. Salaire par type de contrat si disponible
        if (
            "contract_type" in salary_df.columns
            and salary_df["contract_type"].notna().any()
        ):
            contract_salary = (
                salary_df.groupby("contract_type")["avg_salary"].mean().reset_index()
            )

            plt.figure(figsize=(10, 6))
            plt.bar(contract_salary["contract_type"], contract_salary["avg_salary"])
            plt.title("Salaire moyen par type de contrat")
            plt.xlabel("Type de contrat")
            plt.ylabel("Salaire moyen")
            plt.grid(True, alpha=0.3)
            plt.savefig(f"{output_dir}/salary_by_contract.png")
            plt.close()

    async def export_data(self, df: pd.DataFrame, output_dir: str = "./data"):
        """
        Exporte les données dans différents formats

        Args:
            df: DataFrame contenant les offres d'emploi
            output_dir: Répertoire où enregistrer les données
        """
        # Créer le répertoire de sortie s'il n'existe pas
        os.makedirs(output_dir, exist_ok=True)

        # Obtenir un timestamp pour les noms de fichiers
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 1. Export CSV
        csv_path = f"{output_dir}/jobs_{timestamp}.csv"
        df.to_csv(csv_path, index=False, quoting=csv.QUOTE_NONNUMERIC)
        print(f"Données exportées en CSV: {csv_path}")

        # 2. Export Excel
        # excel_path = f"{output_dir}/jobs_{timestamp}.xlsx"
        # df.to_excel(excel_path, index=False)
        # print(f"Données exportées en Excel: {excel_path}")

        # 3. Export JSON
        json_path = f"{output_dir}/jobs_{timestamp}.json"
        df.to_json(json_path, orient="records", indent=2)
        print(f"Données exportées en JSON: {json_path}")

        # 4. Export synthèse statistique
        stats_path = f"{output_dir}/stats_{timestamp}.json"

        # Générer des statistiques basiques
        salary_stats = await self.get_salary_analysis(df)

        # Compter les types de contrat
        contract_type_counts = (
            df["contract_type"].value_counts().to_dict()
            if "contract_type" in df.columns
            else {}
        )
        contract_time_counts = (
            df["contract_time"].value_counts().to_dict()
            if "contract_time" in df.columns
            else {}
        )

        # Statistiques des entreprises
        company_counts = (
            df["company_display_name"].value_counts().to_dict()
            if "company_display_name" in df.columns
            else {}
        )
        top_companies = {
            k: v
            for k, v in sorted(
                company_counts.items(), key=lambda item: item[1], reverse=True
            )[:10]
        }

        # Créer le rapport de statistiques
        stats = {
            "total_jobs": len(df),
            "salary_stats": salary_stats,
            "contract_type_counts": contract_type_counts,
            "contract_time_counts": contract_time_counts,
            "top_companies": top_companies,
        }

        # Enregistrer les statistiques
        with open(stats_path, "w") as f:
            json.dump(stats, f, indent=2)
        print(f"Statistiques exportées: {stats_path}")

    async def display_top_jobs(self, df: pd.DataFrame, count: int = 10):
        """
        Affiche les meilleures offres d'emploi dans un tableau formaté

        Args:
            df: DataFrame contenant les offres d'emploi
            count: Nombre d'offres à afficher
        """
        console = Console()

        # Créer un tableau
        table = Table(title=f"Top {count} offres d'emploi")

        # Ajouter les colonnes
        table.add_column("Titre", style="cyan")
        table.add_column("Entreprise", style="green")
        table.add_column("Lieu", style="blue")
        table.add_column("Salaire", style="yellow")
        table.add_column("Type", style="magenta")
        table.add_column("Date", style="red")

        # Limiter aux n premières offres
        display_df = df.head(count)

        # Ajouter les lignes au tableau
        for _, row in display_df.iterrows():
            # Formater le salaire
            salary = "Non spécifié"
            if pd.notna(row.get("salary_min")) and pd.notna(row.get("salary_max")):
                currency = "€"  # Par défaut, pourrait être paramétré selon le pays
                salary = f"{row['salary_min']:.0f} - {row['salary_max']:.0f} {currency}"

            # Formater la date
            date = "Non spécifiée"
            if pd.notna(row.get("created")):
                try:
                    date_obj = datetime.fromisoformat(
                        row["created"].replace("Z", "+00:00")
                    )
                    date = date_obj.strftime("%d/%m/%Y")
                except:
                    pass

            # Ajouter la ligne
            table.add_row(
                row.get("title", "N/A"),
                row.get("company_display_name", "Non spécifiée"),
                row.get("location_display_name", "Non spécifié"),
                salary,
                row.get("contract_type", "Non spécifié"),
                date,
            )

        # Afficher le tableau
        console.print(table)

    async def get_trending_skills(
        self, country: CountryCode, job_title: str, top_n: int = 10
    ) -> List[Tuple[str, int]]:
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
            "python",
            "java",
            "javascript",
            "js",
            "typescript",
            "ts",
            "c#",
            "c++",
            "go",
            "golang",
            "rust",
            "php",
            "ruby",
            "swift",
            "sql",
            "mysql",
            "postgresql",
            "mongodb",
            "nosql",
            "oracle",
            "sqlite",
            "aws",
            "azure",
            "gcp",
            "cloud",
            "docker",
            "kubernetes",
            "k8s",
            "git",
            "ci/cd",
            "jenkins",
            "gitlab",
            "github",
            "bitbucket",
            "react",
            "angular",
            "vue",
            "node",
            "express",
            "django",
            "flask",
            "spring",
            "tensorflow",
            "pytorch",
            "scikit-learn",
            "pandas",
            "numpy",
            "spark",
            "hadoop",
            "linux",
            "unix",
            "bash",
            "shell",
            "powershell",
            "windows",
            "agile",
            "scrum",
            "kanban",
            "jira",
            "confluence",
            "rest",
            "graphql",
            "api",
            "microservices",
            "soa",
            "soap",
            "html",
            "css",
            "sass",
            "less",
            "bootstrap",
            "tailwind",
            "etl",
            "data warehouse",
            "data lake",
            "big data",
            "machine learning",
            "ml",
            "ai",
            "deep learning",
            "nlp",
            "devops",
            "sre",
            "security",
            "blockchain",
            "iot",
            "embedded",
        ]

        # Rechercher les offres
        try:
            results = await self.client.search_jobs(
                country=country,
                what=job_title,
                results_per_page=100,
                sort_by=SortBy.DATE,
                sort_dir=SortDirection.DOWN,
                max_days_old=30,  # Limiter aux 30 derniers jours pour les tendances actuelles
            )

            # Compter les occurrences de chaque compétence
            skill_counts = {skill: 0 for skill in skills}

            for job in results.results:
                description_lower = job.description.lower()
                for skill in skills:
                    # Recherche du mot entier (avec délimiteurs avant/après)
                    # Cela évite de compter "java" dans "javascript" par exemple
                    if re.search(r"\b" + re.escape(skill) + r"\b", description_lower):
                        skill_counts[skill] += 1

            # Trier par nombre d'occurrences
            sorted_skills = sorted(
                skill_counts.items(), key=lambda x: x[1], reverse=True
            )

            # Retourner les top N compétences qui apparaissent au moins une fois
            return [(skill, count) for skill, count in sorted_skills if count > 0][
                :top_n
            ]

        except AdzunaClientError as e:
            print(f"Erreur lors de la recherche des compétences tendance: {e}")
            return []

    async def compare_locations(
        self, country: CountryCode, job_title: str, locations: List[str]
    ) -> pd.DataFrame:
        """
        Compare les statistiques d'emploi pour un même poste dans différentes localisations

        Args:
            country: Le code pays pour la recherche
            job_title: Le titre de poste à rechercher
            locations: Liste des localisations à comparer

        Returns:
            DataFrame avec les statistiques comparatives
        """
        results = []

        for location in locations:
            try:
                # Rechercher les offres pour cette localisation
                search_results = await self.client.search_jobs(
                    country=country,
                    what=job_title,
                    where=location,
                    results_per_page=100,
                )

                # Convertir en DataFrame
                df = self._convert_jobs_to_dataframe(search_results.results)

                # Calculer les statistiques
                count = len(df)

                # Statistiques de salaire
                salary_stats = await self.get_salary_analysis(df)

                results.append(
                    {
                        "location": location,
                        "job_count": count,
                        "avg_salary": salary_stats.get("mean_avg"),
                        "median_salary": salary_stats.get("median_avg"),
                        "min_salary": salary_stats.get("min"),
                        "max_salary": salary_stats.get("max"),
                        "salary_count": salary_stats.get("count"),
                    }
                )

            except AdzunaClientError as e:
                print(f"Erreur lors de la comparaison pour {location}: {e}")

        return pd.DataFrame(results)


async def main():
    """Fonction principale"""
    # Charger les variables d'environnement
    load_dotenv()

    # Récupérer les identifiants d'API depuis les variables d'environnement
    app_id = os.getenv("ADZUNA_APP_ID")
    app_key = os.getenv("ADZUNA_APP_KEY")

    # Vérifier que les identifiants sont présents
    if not app_id or not app_key:
        print(
            "Erreur: Les identifiants ADZUNA_APP_ID et ADZUNA_APP_KEY doivent être définis dans le fichier .env"
        )
        return

    # Parser les arguments de ligne de commande
    parser = argparse.ArgumentParser(description="Analyseur d'offres d'emploi Adzuna")

    # Sous-commandes
    subparsers = parser.add_subparsers(dest="command", help="Commande à exécuter")

    # Commande de recherche
    search_parser = subparsers.add_parser(
        "search", help="Rechercher des offres d'emploi"
    )
    search_parser.add_argument(
        "--country", type=str, default="fr", help="Code pays ISO (ex: fr, us, gb)"
    )
    search_parser.add_argument(
        "--what",
        type=str,
        required=True,
        help="Terme de recherche (ex: 'python developer')",
    )
    search_parser.add_argument("--where", type=str, help="Localisation (ex: 'Paris')")
    search_parser.add_argument(
        "--max-results", type=int, default=100, help="Nombre maximum de résultats"
    )
    search_parser.add_argument(
        "--export", action="store_true", help="Exporter les résultats"
    )
    search_parser.add_argument(
        "--charts", action="store_true", help="Générer des graphiques"
    )

    # Commande d'analyse des compétences tendance
    skills_parser = subparsers.add_parser(
        "skills", help="Analyser les compétences tendance"
    )
    skills_parser.add_argument(
        "--country", type=str, default="fr", help="Code pays ISO (ex: fr, us, gb)"
    )
    skills_parser.add_argument(
        "--job-title",
        type=str,
        required=True,
        help="Titre du poste (ex: 'data scientist')",
    )
    skills_parser.add_argument(
        "--top", type=int, default=10, help="Nombre de compétences à afficher"
    )

    # Commande de comparaison de localisations
    compare_parser = subparsers.add_parser(
        "compare", help="Comparer les statistiques d'emploi par localisation"
    )
    compare_parser.add_argument(
        "--country", type=str, default="fr", help="Code pays ISO (ex: fr, us, gb)"
    )
    compare_parser.add_argument(
        "--job-title",
        type=str,
        required=True,
        help="Titre du poste (ex: 'software engineer')",
    )
    compare_parser.add_argument(
        "--locations",
        type=str,
        nargs="+",
        required=True,
        help="Liste des localisations à comparer",
    )

    # Commande pour obtenir les catégories
    categories_parser = subparsers.add_parser(
        "categories", help="Lister les catégories disponibles"
    )
    categories_parser.add_argument(
        "--country", type=str, default="fr", help="Code pays ISO (ex: fr, us, gb)"
    )

    # Analyser les arguments
    args = parser.parse_args()

    # Initialiser l'analyseur
    async with AdzunaDataAnalyzer(app_id, app_key) as analyzer:
        # Exécuter la commande appropriée
        if args.command == "search":
            try:
                country_code = CountryCode(args.country.lower())
            except ValueError:
                print(f"Code pays invalide: {args.country}")
                return

            print(
                f"Recherche d'offres d'emploi pour '{args.what}' dans {args.country.upper()}..."
            )

            # Effectuer la recherche
            df = await analyzer.search_and_analyze(
                country=country_code,
                search_term=args.what,
                location=args.where,
                max_results=args.max_results,
            )

            print(f"Nombre d'offres trouvées: {len(df)}")

            # Afficher les meilleures offres
            await analyzer.display_top_jobs(df)

            # Analyser les salaires
            salary_stats = await analyzer.get_salary_analysis(df)

            if salary_stats["count"] > 0:
                print("\nStatistiques de salaire:")
                print(f"Nombre d'offres avec salaire: {salary_stats['count']}")
                print(f"Salaire moyen: {salary_stats['mean_avg']:.2f}")
                print(f"Salaire médian: {salary_stats['median_avg']:.2f}")
                print(
                    f"Fourchette: {salary_stats['min']:.2f} - {salary_stats['max']:.2f}"
                )
            else:
                print("\nAucune information de salaire disponible dans les résultats.")

            # Exporter les données si demandé
            if args.export:
                await analyzer.export_data(df)

            # Générer des graphiques si demandé
            if args.charts:
                await analyzer.create_salary_charts(df)

        elif args.command == "skills":
            try:
                country_code = CountryCode(args.country.lower())
            except ValueError:
                print(f"Code pays invalide: {args.country}")
                return

            print(
                f"Analyse des compétences tendance pour '{args.job_title}' dans {args.country.upper()}..."
            )

            # Obtenir les compétences tendance
            skills = await analyzer.get_trending_skills(
                country=country_code, job_title=args.job_title, top_n=args.top
            )

            # Afficher les résultats
            console = Console()
            table = Table(
                title=f"Top {len(skills)} compétences pour '{args.job_title}'"
            )

            table.add_column("Compétence", style="cyan")
            table.add_column("Occurrences", style="green", justify="right")

            for skill, count in skills:
                table.add_row(skill, str(count))

            console.print(table)

        elif args.command == "compare":
            try:
                country_code = CountryCode(args.country.lower())
            except ValueError:
                print(f"Code pays invalide: {args.country}")
                return

            print(
                f"Comparaison des statistiques pour '{args.job_title}' dans différentes localisations..."
            )

            # Comparer les localisations
            comparison_df = await analyzer.compare_locations(
                country=country_code, job_title=args.job_title, locations=args.locations
            )

            # Afficher les résultats
            console = Console()
            table = Table(title=f"Comparaison pour '{args.job_title}'")

            table.add_column("Localisation", style="cyan")
            table.add_column("Nombre d'offres", style="green", justify="right")
            table.add_column("Salaire moyen", style="yellow", justify="right")
            table.add_column("Salaire médian", style="yellow", justify="right")

            for _, row in comparison_df.iterrows():
                avg_salary = (
                    f"{row['avg_salary']:.2f}" if pd.notna(row["avg_salary"]) else "N/A"
                )
                median_salary = (
                    f"{row['median_salary']:.2f}"
                    if pd.notna(row["median_salary"])
                    else "N/A"
                )

                table.add_row(
                    row["location"], str(row["job_count"]), avg_salary, median_salary
                )

            console.print(table)

            # Créer un graphique pour comparer visuellement
            if len(comparison_df) > 1:
                plt.figure(figsize=(12, 6))

                # Graphique pour le nombre d'offres
                plt.subplot(1, 2, 1)
                plt.bar(comparison_df["location"], comparison_df["job_count"])
                plt.title("Nombre d'offres par localisation")
                plt.xlabel("Localisation")
                plt.ylabel("Nombre d'offres")
                plt.xticks(rotation=45)

                # Graphique pour les salaires moyens
                plt.subplot(1, 2, 2)
                plt.bar(comparison_df["location"], comparison_df["avg_salary"])
                plt.title("Salaire moyen par localisation")
                plt.xlabel("Localisation")
                plt.ylabel("Salaire moyen")
                plt.xticks(rotation=45)

                plt.tight_layout()
                plt.savefig("comparison.png")
                print("Graphique de comparaison enregistré dans 'comparison.png'")

        elif args.command == "categories":
            try:
                country_code = CountryCode(args.country.lower())
            except ValueError:
                print(f"Code pays invalide: {args.country}")
                return

            print(f"Récupération des catégories pour {args.country.upper()}...")

            # Obtenir les catégories
            categories = await analyzer.client.get_categories(country_code)

            # Afficher les résultats
            console = Console()
            table = Table(title=f"Catégories disponibles pour {args.country.upper()}")

            table.add_column("Tag", style="cyan")
            table.add_column("Libellé", style="green")

            for category in categories.results:
                table.add_row(category.tag, category.label)

            console.print(table)

        else:
            # Si aucune commande n'est spécifiée, afficher l'aide
            parser.print_help()


if __name__ == "__main__":
    import re  # Pour la recherche de compétences avec regex

    asyncio.run(main())

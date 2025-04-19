from .analytics import FranceTravailAnalytics
from dotenv import load_dotenv
import os

# Chargement des variables d'environnements
load_dotenv()

client_id = os.getenv("FRANCE_TRAVAIL_ID")
client_secret = os.getenv("FRANCE_TRAVAIL_KEY")

# Initialisation de l'analyseur
analyzer = FranceTravailAnalytics("TOKEN")

# Recherche d'offres avec des critères spécifiques
offres_df = analyzer.search_offers(
    motsCles="python,data,ingénieur",
    typeContrat="CDI",
    qualification=9,  # Cadre
    range="0-99",  # Récupérer jusqu'à 100 offres
)

# Exportation des données en différents formats
analyzer.export_data(offres_df, format_type="csv")
analyzer.export_data(offres_df, format_type="json")

# Analyse des salaires
salary_stats = analyzer.analyze_salaries(offres_df)
print(salary_stats)

# Analyse des types de contrat
contract_stats = analyzer.analyze_contract_types(offres_df)
print(contract_stats)

# Génération des visualisations
analyzer.plot_salary_distribution(offres_df)
analyzer.plot_contract_types(offres_df)
analyzer.plot_offers_by_region(offres_df)

# Génération d'un rapport complet
analyzer.generate_report(offres_df)

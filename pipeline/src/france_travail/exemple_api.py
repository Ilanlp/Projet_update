import os
from dotenv import load_dotenv

from .france_travail_api import FranceTravailAPI, SearchParams

# Chargement des variables d'environnements
load_dotenv()

client_id = os.getenv("FRANCE_TRAVAIL_ID")
client_secret = os.getenv("FRANCE_TRAVAIL_KEY")

# Initialisation avec votre token
api = FranceTravailAPI(client_id, client_secret)

# Création des paramètres de recherche
params = SearchParams(
    motsCles="devops",
    typeContrat="CDI",
    experience=2,  # De 1 à 3 ans d'expérience
    range="0-49",  # 50 premiers résultats
    departement="92",
)

# Recherche d'offres
resultats = api.search_offers(params)

# Accès aux offres trouvées
for offre in resultats.resultats:
    print(
        f"{offre.id} - {offre.intitule} - {offre.lieuTravail.libelle if offre.lieuTravail else 'Non précisé'}"
    )

# Récupération détaillée d'une offre
offre_detail = api.get_offer_details("4913098")
offre_detail.model_dump_json(indent=2)
print(offre_detail.model_dump_json(indent=2))

# Accès aux référentiels
# types_contrats = api.get_referential("typesContrats")
# departements = api.get_referential("departements")

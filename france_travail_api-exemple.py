from france_travail_api import FranceTravailAPI, SearchParams

# Initialisation avec votre token
api = FranceTravailAPI("votre_token_ici")

# Création des paramètres de recherche
params = SearchParams(
    motsCles="python,data",
    typeContrat="CDI",
    experience=2,  # De 1 à 3 ans d'expérience
    range="0-49",  # 50 premiers résultats
)

# Recherche d'offres
resultats = api.search_offers(params)

# Accès aux offres trouvées
for offre in resultats.resultats:
    print(
        f"{offre.id} - {offre.intitule} - {offre.lieuTravail.libelle if offre.lieuTravail else 'Non précisé'}"
    )

# Récupération détaillée d'une offre
# offre_detail = api.get_offer_details("123456")

# Accès aux référentiels
types_contrats = api.get_referential("typesContrats")
departements = api.get_referential("departements")

"""
Récupère les données des référentiels

Args:
ref_type (str): Type de référentiel (appellations, nafs, communes, continents,
departements, domaines, langues, metiers, naturesContrats,
niveauxFormations, pays, permis, regions, secteursActivites,
themes, typesContrats)

Returns:
List[Referentiel]: Liste des éléments du référentiel
"""

import os
from dotenv import load_dotenv
import pandas as pd
from pprint import pprint
from collections import defaultdict
from pathlib import Path

from .france_travail_api import FranceTravailAPI

# Chargement des variables d'environnements
load_dotenv()

client_id = os.getenv("FRANCE_TRAVAIL_ID")
client_secret = os.getenv("FRANCE_TRAVAIL_KEY")
OUTPUT_DIR = os.getenv("OUTPUT_DIR")

path_absolu = Path(__file__).resolve()
OUTPUT_DIR = f"{path_absolu.parents[3]}/{OUTPUT_DIR}"

# Initialisation avec votre token
api = FranceTravailAPI(client_id, client_secret)


def flatten_list_by_shema(L):
    flat_dict = defaultdict(list)

    for l in L:
        for key, value in l.model_dump().items():
            flat_dict[key].append(value)
    return dict(flat_dict)


def flat_list_by_shema(L):
    return [(key, value) for el in L for key, value in el.model_dump().items()]


def save_to_csv(libelle, ref):
    pprint(ref)
    ref_dict = flatten_list_by_shema(ref)
    ref_df = pd.DataFrame(ref_dict)
    pprint(ref_df.head(5))
    ref_df.to_csv(f"{OUTPUT_DIR}{libelle}.csv", sep=",")


appellations = api.get_referential("appellations")
save_to_csv("france_travail_appellations", appellations)

nafs = api.get_referential("nafs")
save_to_csv("france_travail_nafs", nafs)

communes = api.get_referential("communes")
save_to_csv("france_travail_communes", communes)

continents = api.get_referential("continents")
save_to_csv("france_travail_continents", continents)

departements = api.get_referential("departements")
save_to_csv("france_travail_departements", departements)

# langues = api.get_referential("langues")
# print(langues)
# save_to_csv('france_travail_langues', langues)

metiers = api.get_referential("metiers")
save_to_csv("france_travail_metiers", metiers)

naturesContrats = api.get_referential("naturesContrats")
save_to_csv("france_travail_natures_contrats", naturesContrats)

niveauxFormations = api.get_referential("niveauxFormations")
save_to_csv("france_travail_niveaux_formations", niveauxFormations)

pays = api.get_referential("pays")
save_to_csv("france_travail_pays", pays)

permis = api.get_referential("permis")
save_to_csv("france_travail_permis", permis)

regions = api.get_referential("regions")
save_to_csv("france_travail_regions", regions)

secteursActivites = api.get_referential("secteursActivites")
save_to_csv("france_travail_secteurs_activites", secteursActivites)

themes = api.get_referential("themes")
save_to_csv("france_travail_themes", themes)

typesContrats = api.get_referential("typesContrats")
save_to_csv("france_travail_types_contrats", typesContrats)

domaines = api.get_referential("domaines")
save_to_csv("france_travail_domaines", domaines)

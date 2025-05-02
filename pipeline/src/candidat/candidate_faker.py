import pandas as pd
import numpy as np
from dotenv import load_dotenv
from faker import Faker
from faker.providers import BaseProvider
import random
import csv, re, shutil, os
from typing import Any

load_dotenv()


# Chargement des données de référence depuis les fichiers CSV
data_dir = '../data/'
seeds_dir = '../../../snowflake/DBT/Projet_DBT/seeds'

shutil.copytree(seeds_dir,data_dir,dirs_exist_ok=True)

df_dim_competences = pd.read_csv(data_dir+"DIM_COMPETENCE.csv")
df_dim_domaines = pd.read_csv(data_dir+"DIM_DOMAINE.csv")
df_dim_seniorites = pd.read_csv(data_dir+"DIM_SENIORITE.csv")
df_dim_contrats = pd.read_csv(data_dir+"DIM_CONTRAT.csv")
df_dim_teletravails = pd.read_csv(data_dir+"DIM_TELETRAVAIL.csv")
df_dim_lieux = pd.read_csv(data_dir+"DIM_LIEU.csv")
df_raw_metiers = pd.read_csv(data_dir+"RAW_METIER.csv")
df_dim_metiers = pd.read_csv(data_dir+"DIM_METIER.csv")
df_dim_type_entreprises = pd.read_csv(data_dir+'DIM_TYPE_ENTREPRISE.csv')
df_dim_solf_skill = pd.read_csv(data_dir+'DIM_SOFTSKILL.csv')

class CustomListProvider(BaseProvider):
    """
    Fournisseur personnalisé pour Faker qui génère des données spécifiques
    au contexte de l'emploi et du recrutement en France.
    """

    def __init__(self, generator):
        """
        Initialise le fournisseur avec des listes de données métier.

        Args:
            generator: L'instance Faker principale
        """ 
        super().__init__(generator)

        # Liste de compétences techniques courantes en informatique
        self.skills = df_dim_competences['id_competence'].tolist()
        self.softSkills = df_dim_solf_skill['id_softskill'].tolist()

        # Liste des métiers de l'informatique et du numérique
        self.code_rome_it = os.getenv('CODE_ROME').split(',')
        self.metiers = []
        for code in self.code_rome_it:
            metiers_it = df_raw_metiers[df_raw_metiers['code_rome']==code]['code_appellation']
            for m in metiers_it:
                id_metier = df_dim_metiers[df_dim_metiers['ID_APPELLATION']==m]['id_metier']
                for i in id_metier:
                    self.metiers.append(i)

        # Récupération des données depuis les DataFrames chargés
        self.contracts = df_dim_contrats["id_contrat"].tolist()
        self.domainEntreprises = df_dim_domaines["id_domaine"].tolist()

        # Définition de listes personnalisées supplémentaires
        self.typeEntreprises = df_dim_type_entreprises['id_type_entreprise'].tolist()
        self.seniorites = df_dim_seniorites['id_seniorite'].tolist()
        self.teletravails = df_dim_teletravails['id_teletravail'].tolist()

        self.lieux = df_dim_lieux['ID_LIEU'].tolist()

        self.salaire_min = np.arange(20000,80000,5000)

    def lieu_unique(self):
        """Génère une liste aléatoire de lieux"""
        return self.random_element(self.lieux)

    def lieu(self):
        """Génère une liste aléatoire de lieux"""
        count = random.randint(0, 5)
        return random.sample(self.lieux,count)

    def salaire(self):
        """Retourne un salaire minimal aléatoire"""
        return self.random_element(self.salaire_min)
    
    def skill(self):
        """Génère une liste aléatoire de compétences techniques"""
        count = random.randint(0, 10)
        return random.sample(self.skills, count)

    def softSkill(self):
        """Génère une liste aléatoire de compétences techniques"""
        count = random.randint(0, 10)
        return random.sample(self.softSkills, count)

    def domain(self):
        """Génère une liste aléatoire de domaines d'activité"""
        count = random.randint(0, len(self.domaines))
        return random.sample(self.domaines, count)

    def metier(self):
        """Génère une liste aléatoire de 1 à 3 métiers"""
        count = random.randint(1, 3)
        return random.sample(self.metiers, count)

    def contract(self):
        """Génère une liste aléatoire de types de contrats"""
        count = random.randint(0, len(self.contracts))
        return random.sample(self.contracts, count)

    def typeEntreprise(self):
        """Génère une liste aléatoire de types d'entreprises"""
        count = random.randint(0, len(self.typeEntreprises))
        return random.sample(self.typeEntreprises, count)

    def seniorite(self):
        """Génère une liste aléatoire de niveaux de séniorité"""
        count = random.randint(0, len(self.seniorites))
        return random.sample(self.seniorites, count)

    def teletravail(self):
        """Génère une liste aléatoire de modalités de télétravail"""
        count = random.randint(0, len(self.teletravails))
        return random.sample(self.teletravails, count)

    def domainEntreprise(self):
        """Génère une liste aléatoire de domaines d'entreprise"""
        count = random.randint(0, 5)
        return random.sample(self.domainEntreprises, count)


def _sanitize_text(text: Any) -> str:
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


# Initialisation du générateur Faker avec la locale française
fake = Faker("fr_FR")
# Ajout du fournisseur personnalisé à l'instance Faker
fake.add_provider(CustomListProvider(fake))

# Génération de données fictives pour 50 candidats
data = []
for i in range(50):

    person = {
        "id_candidat":i,
        "nom": fake.last_name(),
        "prenom": fake.first_name(),
        "adresse": fake.lieu_unique(),
        "email": fake.email(),
        "tel": fake.phone_number(),
        "id_competence": fake.skill(),
        "id_softskill": fake.softSkill(),
        "id_metier": fake.metier(),
        "id_lieu": fake.lieu(),
        #"Departement de Recherche d'Emploi": fake.departement(),
        #"Region de Recherche d'Emploi": fake.region(),
        "id_contrat": fake.contract(),
        "id_type_entreprise": fake.typeEntreprise(),
        "id_seniorite": fake.seniorite(),
        "id_teletravail": fake.teletravail(),
        "id_domaine": fake.domainEntreprise(),
        "salaire_min": fake.salaire()
    }
    data.append(person)

# Écriture des données dans un fichier CSV dans data
with open(
    data_dir+"/RAW_CANDIDAT.csv", mode="w", newline="", encoding="utf-8"
) as file:
    writer = csv.DictWriter(file, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)

# Écriture des données dans un fichier CSV dans DBT seeds
with open(
    seeds_dir+"/RAW_CANDIDAT.csv", mode="w", newline="", encoding="utf-8"
) as file:
    writer = csv.DictWriter(file, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)

print(
    "Base de données fictive créée et enregistrée dans 'RAW_CANDIDAT.csv'."
)

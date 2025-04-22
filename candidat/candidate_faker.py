import pandas as pd
from faker import Faker
from faker.providers import BaseProvider
import random
import csv

# Chargement des données de référence depuis les fichiers CSV
df_communes = pd.read_csv('data/france_travail_communes.csv')
df_departements = pd.read_csv('data/france_travail_departements.csv')
df_regions = pd.read_csv('data/france_travail_regions.csv')
df_formation = pd.read_csv('data/france_travail_niveaux_formations.csv')
df_contracts = pd.read_csv('data/france_travail_types_contrats.csv')
df_permis = pd.read_csv('data/france_travail_permis.csv')
df_metiers = pd.read_csv('data/france_travail_metiers.csv')
df_domaines = pd.read_csv('data/france_travail_domaines.csv')
df_secteurs_activites = pd.read_csv('data/france_travail_secteurs_activites.csv')

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

        # Initialisation des listes de données à partir des fichiers chargés
        self.formations = df_formation['libelle'].tolist()

        # Liste de compétences techniques courantes en informatique
        self.skills = [
            "python", "java", "javascript", "js", "typescript", "ts", 
            "c#", "c++", "go", "golang", "rust", "php", "ruby", "swift",
            "sql", "mysql", "postgresql", "mongodb", "nosql", "oracle", "sqlite",
            "aws", "azure", "gcp", "cloud", "docker", "kubernetes", "k8s",
            "git", "ci/cd", "jenkins", "gitlab", "github", "bitbucket",
            "react", "angular", "vue", "node", "express", "django", "flask", "spring",
            "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy", "spark", "hadoop",
            "linux", "unix", "bash", "shell", "powershell", "windows",
            "agile", "scrum", "kanban", "jira", "confluence",
            "rest", "graphql", "api", "microservices", "soa", "soap",
            "html", "css", "sass", "less", "bootstrap", "tailwind",
            "etl", "data warehouse", "data lake", "big data",
            "machine learning", "ml", "ai", "deep learning", "nlp", 
            "devops", "sre", "security", "blockchain", "iot", "embedded"
        ]

        # Liste des métiers de l'informatique et du numérique
        self.metiers = [
            "Développeur / Développeuse web",
            "Développeur / Développeuse multimédia",
            "Analyste Concepteur / Conceptrice informatique",
            "Analyste d'étude",
            "Ingénieur / Ingénieure d'étude informatique",
            "Ingénieur / Ingénieure systèmes et réseaux informatiques",
            "Ingénieur / Ingénieure concepteur / conceptrice informatique",
            "Architecte systèmes et réseaux des territoires connectés",
            "Architecte cloud",
            "Architecte IoT - Internet des Objets",
            "Administrateur / Administratrice réseau informatique",
            "Administrateur / Administratrice sécurité informatique",
            "Ingénieur / Ingénieure sécurité informatique",
            "Ingénieur / Ingénieure sécurité web",
            "Expert / Experte en cybersécurité",
            "Ingénieur / Ingénieure Cybersécurité Datacenter",
            "Technicien / Technicienne Datacenter",
            "Urbaniste Datacenter",
            "Ingénieur / Ingénieure supervision IT Datacenter",
            "Délégué / Déléguée à la protection des données - Data Protection Officer",
            "Chef / Cheffe de projet étude et développement informatique",
            "Chef / Cheffe de projet maîtrise d'œuvre informatique",
            "Qualiticien / Qualiticienne logiciel en informatique",
            "Responsable Green IT",
            "Technicien / Technicienne réseaux informatiques et télécoms",
            "Responsable de maintenance réseaux des territoires connectés",
            "Ingénieur / Ingénieure systèmes et réseaux des territoires connectés",
            "Technicien / Technicienne de maintenance en informatique"
        ]

        # Récupération des données depuis les DataFrames chargés
        self.code_permis = df_permis['code'].tolist()
        self.communes = df_communes['libelle'].tolist()
        self.departements = df_departements['libelle'].tolist()
        self.regions = df_regions['libelle'].tolist()
        self.contracts = df_contracts['code'].tolist()
        self.domainEntreprises = df_domaines['libelle'].tolist()

        # Définition de listes personnalisées supplémentaires
        self.typeEntreprises = ['TPE', 'PME', 'ETI', 'GRANDE ENTREPRISE']
        self.seniorites = ['Junior', 'Confirmé', 'Senior', 'Expert']
        self.teletravails = ['Télétravail à 100%', 'Télétravail hybride', 'Télétravail occasionnel', 'Télétravail flexible', 'Télétravail fixe']

    def commune(self):
        """Génère une liste aléatoire de 0 à 5 communes"""
        count = random.randint(0, 5)
        return random.sample(self.communes, count)
    
    def departement(self):
        """Génère une liste aléatoire de 0 à 2 départements"""
        count = random.randint(0, 2)
        return random.sample(self.departements, count)
    
    def region(self):
        """Génère une liste aléatoire de 0 à 2 régions"""
        count = random.randint(0, 2)
        return random.sample(self.regions, count)

    def formation(self):
        """Retourne un niveau de formation aléatoire"""
        return self.random_element(self.formations)

    def skill(self):
        """Génère une liste aléatoire de compétences techniques"""
        count = random.randint(0, len(self.skills))
        return random.sample(self.skills, count)

    def domain(self):
        """Génère une liste aléatoire de domaines d'activité"""
        count = random.randint(0, len(self.domaines))
        return random.sample(self.domaines, count)

    def metier(self):
        """Génère une liste aléatoire de 1 à 3 métiers"""
        count = random.randint(1, 3)
        return random.sample(self.metiers, count)
    
    def permis(self):
        """Génère une liste aléatoire de permis de conduire"""
        count = random.randint(0, len(self.code_permis))
        return random.sample(self.code_permis, count)
    
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
        count = random.randint(0, len(self.domainEntreprises))
        return random.sample(self.domainEntreprises, count)
    

# Initialisation du générateur Faker avec la locale française
fake = Faker('fr_FR')
# Ajout du fournisseur personnalisé à l'instance Faker
fake.add_provider(CustomListProvider(fake))

# Génération de données fictives pour 50 candidats
data = []
for _ in range(50):  
    
    person = {
        "Nom": fake.last_name(),
        "Prénom": fake.first_name(),
        "Adresse": fake.address(),
        "Adresse Mail": fake.email(),
        "Numéro de Téléphone": fake.phone_number(),
        "Compétences": fake.skill(),  
        "Formation": fake.formation(),
        "Permis": fake.permis(),
        "Ancien Emploi": fake.job(),
        "Emploi Recherché": fake.metier(),
        "Ville de Recherche d'Emploi": fake.commune(),
        "Departement de Recherche d'Emploi": fake.departement(),
        "Region de Recherche d'Emploi": fake.region(),
        "Contrat de Travail Recherché": fake.contract(),
        "Type d'entreprise": fake.typeEntreprise(),
        "Seniorité": fake.seniorite(),
        "Teletravail": fake.teletravail(),
        "Domain de l'entreprise": fake.domainEntreprise()
    }
    data.append(person)

# Écriture des données dans un fichier CSV
with open("candidat/base_de_donnees_fictive.csv", mode="w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)

print("Base de données fictive créée et enregistrée dans 'base_de_donnees_fictive.csv'.")
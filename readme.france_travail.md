# Extraction et Analyse des Offres d'Emploi France Travail

![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![Pydantic](https://img.shields.io/badge/pydantic-v2-green)
![Pandas](https://img.shields.io/badge/pandas-latest-orange)
![Matplotlib](https://img.shields.io/badge/matplotlib-latest-red)

Suite d'outils pour extraire, transformer et analyser les données d'offres d'emploi de l'API France Travail (anciennement Pôle Emploi).

## 📋 Composants

L'ensemble applicatif comprend trois modules principaux :

1. **API Client** (`france_travail_api.py`) : Requêteur pour l'API France Travail basé sur Pydantic V2
2. **Analyseur de données** (`france_travail_analytics.py`) : Outils d'analyse et de visualisation des offres d'emploi
3. **Script d'extraction** (`extract_job_data.py`) : Script autonome pour l'extraction massive de données

## 🔧 Installation

1. Clonez ce dépôt :
```bash
git clone https://github.com/votre-nom/france-travail-tools.git
cd france-travail-tools
```

2. Installez les dépendances :
```bash
pip install -r requirements.txt
```

3. Configurez votre token d'authentification France Travail dans les scripts.

## 📊 Fonctionnalités

### 1. Requêteur API France Travail

Interface Python complète pour l'API des offres d'emploi France Travail :

- Modèles de données validés avec Pydantic V2
- Recherche d'offres avec filtres multiples
- Accès aux détails des offres
- Consultation des référentiels (métiers, régions, etc.)

Exemple d'utilisation :
```python
from france_travail_api import FranceTravailAPI, SearchParams

# Initialisation
api = FranceTravailAPI("votre_token_ici")

# Recherche d'offres
params = SearchParams(
    motsCles="python,data",
    typeContrat="CDI",
    departement="75"
)
resultats = api.search_offers(params)

# Affichage des résultats
for offre in resultats.resultats:
    print(f"{offre.id} - {offre.intitule}")
```

### 2. Analyseur de Données

Permet d'analyser et visualiser les offres d'emploi :

- Transformation des offres en DataFrame pandas
- Analyse des salaires et types de contrat
- Visualisations (distribution des salaires, répartition géographique)
- Export dans différents formats (CSV, JSON, HTML)
- Génération de rapports d'analyse

Exemple d'utilisation :
```python
from france_travail_analytics import FranceTravailAnalytics

# Initialisation
analyzer = FranceTravailAnalytics("votre_token_ici")

# Recherche et analyse
offres_df = analyzer.search_offers(motsCles="python,data", typeContrat="CDI")

# Analyse des salaires
stats = analyzer.analyze_salaries(offres_df)
print(stats)

# Génération de visualisations
analyzer.plot_salary_distribution(offres_df)
analyzer.plot_contract_types(offres_df)
analyzer.plot_offers_by_region(offres_df)

# Export des données
analyzer.export_data(offres_df, format_type="csv")
analyzer.export_data(offres_df, format_type="json")

# Génération d'un rapport
analyzer.generate_report(offres_df)
```

### 3. Script d'Extraction Massive

Script autonome pour extraire de grandes quantités de données :

- Extraction sur de longues périodes (jusqu'à 12 mois)
- Segmentation par code ROME
- Gestion de la pagination
- Sauvegarde automatique en CSV
- Mécanisme de reprise en cas d'interruption

Configuration et utilisation :
```bash
# Configurer dans le script :
TOKEN = "votre_token_ici"
OUTPUT_DIR = "donnees_offres"
MONTHS_TO_COLLECT = 12

# Exécuter le script
python extract_job_data.py
```

## 🔍 Structure des Données

Les principales données extraites pour chaque offre :

| Champ | Description |
|-------|-------------|
| `id` | Identifiant unique de l'offre |
| `intitule` | Titre du poste |
| `description` | Description détaillée |
| `date_creation` | Date de création de l'offre |
| `type_contrat` | Type de contrat (CDI, CDD, etc.) |
| `lieu_travail_code_postal` | Code postal du lieu de travail |
| `entreprise_nom` | Nom de l'entreprise |
| `salaire_libelle` | Information sur le salaire |

## 📈 Exemples de Visualisations

Les visualisations générées incluent :

- **Distribution des salaires** : Histogramme montrant la répartition des salaires
- **Types de contrat** : Graphique circulaire des différents types de contrat
- **Répartition géographique** : Carte des offres par région
- **Rapports HTML** : Tableaux de bord interactifs

## ⚙️ Paramètres de Recherche Disponibles

Le requêteur prend en charge de nombreux paramètres de recherche :

| Paramètre | Description | Exemple |
|-----------|-------------|---------|
| `motsCles` | Mots-clés de recherche | `"python,data"` |
| `typeContrat` | Type de contrat | `"CDI"` |
| `departement` | Département(s) | `"75,92,93"` |
| `experience` | Niveau d'expérience | `2` (1-3 ans) |
| `qualification` | Qualification | `9` (Cadre) |
| `distance` | Rayon de recherche (km) | `20` |
| `publieeDepuis` | Offres publiées depuis x jours | `7` |

## 🚀 Cas d'Utilisation

### Veille du marché de l'emploi
```python
# Analyser les tendances des offres Data Science
analyzer = FranceTravailAnalytics(TOKEN)
df = analyzer.search_offers(motsCles="data science,machine learning", publieeDepuis=30)
analyzer.plot_salary_distribution(df)
```

### Extraction hebdomadaire automatisée
```python
# Configuration pour une tâche cron hebdomadaire
python extract_job_data.py --months=1 --output=offres_hebdo
```

### Analyse sectorielle
```python
# Comparer les offres dans différents secteurs
sectors = ["informatique", "finance", "marketing"]
for sector in sectors:
    df = analyzer.search_offers(motsCles=sector, typeContrat="CDI")
    analyzer.export_data(df, f"rapport_{sector}")
```

## 📝 Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 👥 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à ouvrir une issue ou à soumettre une pull request.

## 🔗 Ressources Utiles

- [Documentation API France Travail](https://francetravail.io/data/api/offres-emploi)
- [Guide des codes ROME](https://www.francetravail.fr/rome/rome-code.html)
- [Documentation Pydantic V2](https://docs.pydantic.dev/latest/)
- [Pandas Documentation](https://pandas.pydata.org/docs/)

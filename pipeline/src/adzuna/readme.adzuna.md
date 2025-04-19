# Adzuna Data Collection Toolkit

Un ensemble d'outils Python pour collecter, traiter et analyser des données d'offres d'emploi depuis l'API Adzuna.

## 📝 Présentation

Ce projet contient un client API Adzuna robuste et un collecteur de données configurables qui permettent de récupérer des offres d'emploi à grande échelle et de manière fiable. Développés avec Python, ces outils utilisent des approches modernes comme les types statiques, la programmation asynchrone et la validation de données avec Pydantic.

### Principaux composants

1. **Client API Adzuna** (`adzuna_client.py`) - Un client complet pour l'API Adzuna avec validation des données via Pydantic
2. **Collecteur de données** (`adzuna-data-collector.py`) - Un script performant pour collecter les offres d'emploi et les sauvegarder au format CSV
3. **Application d'analyse** (`adzuna_app.py`) - Une interface en ligne de commande pour rechercher, analyser et visualiser les données d'emploi

## 🚀 Fonctionnalités

### Client API

- Support complet des points de terminaison de l'API Adzuna :
  - Recherche d'offres d'emploi
  - Catégories
  - Données géographiques
  - Histogrammes de salaires
  - Historique des salaires
  - Top entreprises
- Validation automatique des données via Pydantic (v2)
- Gestion correcte des énumérations
- Support pour les requêtes asynchrones via httpx
- Typé statiquement avec mypy

### Collecteur de données

- Collecte d'offres d'emploi sur une longue période temporelle
- Découpage en périodes d'un mois pour optimiser la récupération
- Filtrage par catégories pour maximiser la couverture
- Contrôle du débit pour éviter les limitations d'API
- Mécanisme de reprise après erreur
- Points de contrôle automatiques pour reprendre une collecte interrompue
- Filtrage des doublons
- Export en CSV

### Application d'analyse

- Interface en ligne de commande avec plusieurs commandes (search, skills, compare, categories)
- Visualisation des données avec Matplotlib (distribution des salaires, boxplots, etc.)
- Analyse des tendances de compétences dans les offres d'emploi
- Comparaison des statistiques d'emploi entre différentes villes
- Export des données en multiples formats (CSV, JSON)
- Affichage formaté des résultats dans le terminal via Rich

## 🛠️ Installation

### Prérequis

- Python 3.8+
- pip ou poetry

### Installation via pip

```bash
# Cloner le dépôt
git clone https://github.com/votre-username/adzuna-data-toolkit.git
cd adzuna-data-toolkit

# Créer un environnement virtuel (optionnel mais recommandé)
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt
```

### Dépendances

Le projet nécessite les bibliothèques Python suivantes :
- httpx
- pydantic (v2+)
- pandas
- matplotlib
- rich
- python-dotenv
- asyncio

### Fichier de configuration

Créez un fichier `.env` à la racine du projet avec vos identifiants Adzuna :

```env
ADZUNA_APP_ID=votre_app_id
ADZUNA_APP_KEY=votre_app_key
```

## 📊 Utilisation

### Client API

```python
import asyncio
from adzuna_client import AdzunaClient, CountryCode, SortBy, SortDirection

async def example():
    async with AdzunaClient("YOUR_APP_ID", "YOUR_APP_KEY") as client:
        # Rechercher des jobs de data science à Paris
        results = await client.search_jobs(
            country=CountryCode.FR,
            what="data science",
            where="Paris",
            results_per_page=50,
            sort_by=SortBy.DATE,
            sort_dir=SortDirection.DOWN
        )
        
        print(f"Nombre d'offres trouvées: {len(results.results)}")
        
        # Afficher les titres des 5 premières offres
        for job in results.results[:5]:
            print(f"- {job.title} ({job.company.display_name if job.company else 'Entreprise inconnue'})")

if __name__ == "__main__":
    asyncio.run(example())
```

### Collecteur de données

```bash
# Collecter les offres d'emploi en France sur les 12 derniers mois
python adzuna-data-collector.py --country fr --output data/jobs_fr.csv --months 12

# Collecter les offres d'emploi au Royaume-Uni sur les 6 derniers mois avec un débit plus lent
python adzuna-data-collector.py --country gb --output data/jobs_gb.csv --months 6 --rate-limit-delay 1.0
```

#### Options disponibles :

- `--country` : Code pays (ex: fr, gb, us)
- `--output` : Chemin du fichier CSV de sortie
- `--months` : Nombre de mois à remonter dans le temps
- `--results-per-page` : Nombre de résultats par page (max 50)
- `--retry-count` : Nombre de tentatives en cas d'erreur
- `--retry-delay` : Délai initial entre les tentatives (en secondes)
- `--rate-limit-delay` : Délai entre les requêtes (en secondes)

## 🔍 Analyse des données collectées

Une fois les données collectées, vous pouvez les analyser avec pandas :

```python
import pandas as pd

# Charger le CSV
df = pd.read_csv('data/jobs_fr.csv')

# Afficher les informations de base
print(f"Nombre total d'offres : {len(df)}")
print(f"Période couverte : de {df['created'].min()} à {df['created'].max()}")

# Statistiques sur les salaires
salaries = df[df['salary_min'].notna() & df['salary_max'].notna()]
print(f"Salaire moyen minimum : {salaries['salary_min'].mean():.2f}")
print(f"Salaire moyen maximum : {salaries['salary_max'].mean():.2f}")

# Top catégories
print("\nTop 5 catégories :")
print(df['category_label'].value_counts().head(5))

# Top entreprises
print("\nTop 5 entreprises qui recrutent :")
print(df['company_display_name'].value_counts().head(5))
```

## 🔄 Fonctionnalité d'analyse des tendances

Le collecteur inclut aussi une fonctionnalité pour analyser les compétences les plus demandées :

```python
import asyncio
from adzuna_client import CountryCode
from adzuna-data-collector import AdzunaDataCollector

async def analyze_trends():
    collector = AdzunaDataCollector(
        app_id="YOUR_APP_ID",
        app_key="YOUR_APP_KEY",
        country=CountryCode.FR,
        output_file="data/jobs.csv"
    )
    
    # Initialiser le client
    await collector.initialize()
    
    # Analyser les compétences tendance pour les data scientists
    trends = await collector.get_trending_skills(
        country=CountryCode.FR,
        job_title="data scientist",
        top_n=15
    )
    
    print("Compétences les plus demandées pour les Data Scientists :")
    for skill, count in trends:
        print(f"- {skill}: {count} mentions")
    
    await collector.close()

if __name__ == "__main__":
    asyncio.run(analyze_trends())
```

## 📊 Application d'analyse des offres d'emploi

Le script `analytics.py` fournit une interface en ligne de commande pour analyser facilement les offres d'emploi. Il propose plusieurs commandes pour rechercher, analyser et visualiser les données d'emploi.

### Exemples d'utilisation

```bash
# Rechercher des offres d'emploi
python -m adzuna.analytics search --what "data engineer" --where "Paris" --max-results 50 --export --charts

# Analyser les compétences les plus demandées pour un poste
python -m adzuna.analytics skills --job-title "devops engineer" --top 15

# Comparer les statistiques d'emploi entre différentes villes
python -m adzuna.analytics compare --job-title "software developer" --locations "Paris" "Lyon" "Marseille" "Toulouse"

# Lister les catégories d'emploi disponibles
python -m adzuna.analytics categories
```

### Fonctionnalités de l'application

- **Recherche d'offres d'emploi** : Recherche et affiche les offres correspondant aux critères spécifiés
- **Analyse de salaire** : Calcule des statistiques sur les salaires (moyenne, médiane, min, max)
- **Visualisation** : Génère des graphiques pour l'analyse des données (histogrammes, boîtes à moustaches)
- **Export de données** : Sauvegarde les résultats en CSV et JSON
- **Analyse des compétences** : Identifie les compétences les plus demandées dans les offres d'emploi
- **Comparaison géographique** : Compare les statistiques d'emploi entre différentes localisations

### Options globales

- `--country` : Code pays ISO (ex: fr, us, gb)
- `--max-results` : Nombre maximum de résultats à récupérer

### Visualisations générées

L'application peut générer plusieurs types de visualisations :

1. Distribution des salaires
2. Boîtes à moustaches des salaires minimum et maximum
3. Salaire moyen par type de contrat
4. Comparaison du nombre d'offres par localisation
5. Comparaison des salaires moyens par localisation

## 📐 Architecture

### Diagramme des classes

```
AdzunaClient
├── search_jobs(country, **kwargs) -> JobSearchResults
├── get_categories(country) -> Categories
├── get_salary_histogram(country, **kwargs) -> SalaryHistogram
├── get_top_companies(country, **kwargs) -> TopCompanies
├── get_geodata(country, **kwargs) -> JobGeoData
├── get_historical_salary(country, months, **kwargs) -> HistoricalSalary
└── get_api_version() -> ApiVersion

AdzunaDataCollector
├── initialize()
├── collect_data()
├── get_trending_skills(country, job_title, top_n) -> List[Tuple[str, int]]
└── close()

AdzunaDataAnalyzer
├── search_and_analyze(country, search_term, location, max_results) -> pd.DataFrame
├── get_salary_analysis(df) -> Dict[str, Any]
├── create_salary_charts(df, output_dir)
├── export_data(df, output_dir)
├── display_top_jobs(df, count)
├── get_trending_skills(country, job_title, top_n) -> List[Tuple[str, int]]
└── compare_locations(country, job_title, locations) -> pd.DataFrame
```

## 🔒 Gestion des erreurs et limites de l'API

- Backoff exponentiel en cas d'erreur
- Points de contrôle réguliers pour reprendre une collecte interrompue
- Respect des limites de l'API Adzuna grâce au contrôle de débit

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à ouvrir une issue ou à soumettre une pull request.

## 📄 Licence

Ce projet est sous licence MIT - voir le fichier LICENSE pour plus de détails.

## 📮 Contact

Pour toute question ou suggestion, veuillez contacter [votre-email@exemple.com].

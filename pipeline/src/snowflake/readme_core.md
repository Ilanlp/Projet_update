# SnowflakeCore

Une classe Python pour faciliter le chargement de fichiers CSV et Parquet vers Snowflake.

## Table des matières

- [Installation](#installation)
- [Configuration](#configuration)
- [Fonctionnalités](#fonctionnalités)
- [Utilisation de base](#utilisation-de-base)
- [Exemples avancés](#exemples-avancés)
- [Documentation des méthodes](#documentation-des-méthodes)
- [Bonnes pratiques](#bonnes-pratiques)
- [Dépannage](#dépannage)

## Installation

### Prérequis

- Python 3.8 ou supérieur
- Le package `snowflake-connector-python`
- Le package `pandas`
- Le package `python-dotenv`
- (Optionnel) `pyarrow` pour une meilleure gestion des fichiers Parquet

```bash
pip install snowflake-connector-python pandas python-dotenv
# Optionnel pour la gestion avancée des fichiers Parquet
pip install pyarrow
```

## Configuration

Créez un fichier `.env` à la racine de votre projet avec les informations de connexion Snowflake :

```env
SNOWFLAKE_USER=votre_utilisateur
SNOWFLAKE_PASSWORD=votre_mot_de_passe
SNOWFLAKE_ACCOUNT=votre_compte
SNOWFLAKE_WAREHOUSE=votre_warehouse
SNOWFLAKE_DATABASE=votre_database
SNOWFLAKE_SCHEMA=votre_schema
```

## Fonctionnalités

- Chargement de fichiers CSV vers des tables Snowflake
- Chargement de fichiers Parquet avec inférence automatique du schéma
- Support de deux méthodes pour les fichiers Parquet : PyArrow ou VARIANT
- Création automatique de tables basées sur le schéma des fichiers
- Gestion des formats de fichiers personnalisés
- Possibilité d'ignorer l'import si la table contient déjà des données
- Nettoyage automatique des ressources temporaires

## Utilisation de base

### Importer un fichier CSV

```python
from snowflake_csv_loader import SnowflakeCSVLoader

# Créer une instance du chargeur
loader = SnowflakeCSVLoader()

# Importer un fichier CSV vers une table
success = loader.process_file_with_copy(
    database="MA_DATABASE",
    schema_name="MON_SCHEMA",
    table_name="MA_TABLE",
    file_path="/chemin/vers/mon_fichier.csv"
)

if success:
    print("Import réussi!")
else:
    print("Échec de l'import.")
```

### Importer un fichier Parquet

```python
# Créer une instance du chargeur
loader = SnowflakeCSVLoader()

# Importer un fichier Parquet vers une table
success = loader.process_file_with_copy(
    database="MA_DATABASE",
    schema_name="MON_SCHEMA",
    table_name="MA_TABLE",
    file_path="/chemin/vers/mon_fichier.parquet"
)
```

## Exemples avancés

### Utiliser un format de fichier personnalisé

```python
# Définir des options personnalisées pour un CSV avec séparateur point-virgule
csv_options = {
    "FIELD_DELIMITER": ";",
    "SKIP_HEADER": 1,
    "DATE_FORMAT": "DD/MM/YYYY",
    "NULL_IF": "('NULL', 'N/A')",
    "FIELD_OPTIONALLY_ENCLOSED_BY": '"'
}

loader = SnowflakeCSVLoader()
success = loader.process_file_with_copy(
    database="MA_DATABASE",
    schema_name="MON_SCHEMA",
    table_name="MA_TABLE",
    file_path="/chemin/vers/mon_fichier.csv",
    format_options=csv_options
)
```

### Importer un fichier Parquet avec PyArrow

```python
loader = SnowflakeCSVLoader()
success = loader.process_file_with_copy(
    database="MA_DATABASE",
    schema_name="MON_SCHEMA",
    table_name="MA_TABLE",
    file_path="/chemin/vers/mon_fichier.parquet",
    use_pyarrow=True  # Utiliser PyArrow pour l'analyse du schéma
)
```

### Ignorer l'import si la table contient déjà des données

```python
loader = SnowflakeCSVLoader()
success = loader.process_file_with_copy(
    database="MA_DATABASE",
    schema_name="MON_SCHEMA",
    table_name="MA_TABLE",
    file_path="/chemin/vers/mon_fichier.csv",
    skip_if_data_exists=True  # Ne pas importer si la table existe et contient des données
)
```

### Supprimer le stage après utilisation

```python
loader = SnowflakeCSVLoader()
success = loader.process_file_with_copy(
    database="MA_DATABASE",
    schema_name="MON_SCHEMA",
    table_name="MA_TABLE",
    file_path="/chemin/vers/mon_fichier.csv",
    drop_stage_after=True  # Supprime le stage après un import réussi
)
```

### Traitement par lots de plusieurs fichiers

```python
import os
import glob

# Fonction pour traiter tous les fichiers d'un dossier
def process_directory(directory_path, target_db, target_schema):
    # Récupérer tous les fichiers CSV et Parquet du dossier
    csv_files = glob.glob(os.path.join(directory_path, "*.csv"))
    parquet_files = glob.glob(os.path.join(directory_path, "*.parquet"))
    
    print(f"Fichiers trouvés: {len(csv_files)} CSV et {len(parquet_files)} Parquet")
    
    # Traiter tous les fichiers CSV
    for csv_file in csv_files:
        file_name = os.path.basename(csv_file).split(".")[0].upper()
        table_name = f"CSV_{file_name}"
        
        loader = SnowflakeCSVLoader()
        success = loader.process_file_with_copy(
            database=target_db,
            schema_name=target_schema,
            table_name=table_name,
            file_path=csv_file,
            drop_stage_after=True
        )
        
        if success:
            print(f"✅ {csv_file} chargé avec succès dans {table_name}")
        else:
            print(f"❌ Échec du chargement de {csv_file}")
    
    # Traiter tous les fichiers Parquet
    for parquet_file in parquet_files:
        file_name = os.path.basename(parquet_file).split(".")[0].upper()
        table_name = f"PARQUET_{file_name}"
        
        loader = SnowflakeCSVLoader()
        success = loader.process_file_with_copy(
            database=target_db,
            schema_name=target_schema,
            table_name=table_name,
            file_path=parquet_file,
            drop_stage_after=True
        )
        
        if success:
            print(f"✅ {parquet_file} chargé avec succès dans {table_name}")
        else:
            print(f"❌ Échec du chargement de {parquet_file}")

# Utilisation de la fonction
process_directory(
    directory_path="/path/to/data_exports",
    target_db="DATA_LAKE",
    target_schema="EXTERNAL_SOURCES"
)
```

## Documentation des méthodes

### `process_file_with_copy`

La méthode principale pour charger un fichier dans Snowflake.

```python
def process_file_with_copy(
    self,
    database,
    schema_name,
    table_name,
    file_path,
    file_format_name=None,
    file_format_schema=None,
    format_options=None,
    use_pyarrow=False,
    skip_if_data_exists=True,
    drop_stage_after=False
):
    """
    Charge un fichier CSV ou Parquet dans Snowflake.
    
    Args:
        database (str): Nom de la base de données cible
        schema_name (str): Nom du schéma de la table cible
        table_name (str): Nom de la table cible
        file_path (str): Chemin complet du fichier à charger
        file_format_name (str): Nom du format de fichier à utiliser
        file_format_schema (str): Nom du schéma contenant le format de fichier
        format_options (dict): Options spécifiques pour le format de fichier
        use_pyarrow (bool): Si True, utilise PyArrow pour les fichiers Parquet
        skip_if_data_exists (bool): Si True, ignore l'import si la table existe et contient des données
        drop_stage_after (bool): Si True, supprime le stage après le chargement
        
    Returns:
        bool: True si le traitement réussit, False en cas d'erreur
    """
```

### `create_file_format`

Crée un format de fichier dans Snowflake.

```python
def create_file_format(
    self,
    format_name,
    format_type="CSV",
    schema_name=None,
    options=None
):
    """
    Crée un format de fichier dans Snowflake.
    
    Args:
        format_name (str): Nom du format à créer
        format_type (str): Type de format (CSV, PARQUET, etc.)
        schema_name (str): Nom du schéma où créer le format
        options (dict): Options spécifiques au format
        
    Returns:
        tuple: (schema_name, format_name)
    """
```

### `drop_stage`

Supprime un stage Snowflake.

```python
def drop_stage(self, stage_name=None):
    """
    Supprime un stage Snowflake.
    
    Args:
        stage_name (str): Nom du stage à supprimer (utilise self.filename si None)
        
    Returns:
        bool: True si la suppression réussit, False sinon
    """
```

### `table_exists_and_has_data`

Vérifie si une table existe et contient des données.

```python
def table_exists_and_has_data(self, database, schema_name, table_name):
    """
    Vérifie si une table existe et contient des données.
    
    Args:
        database (str): Nom de la base de données
        schema_name (str): Nom du schéma
        table_name (str): Nom de la table
        
    Returns:
        bool: True si la table existe et contient des données, False sinon
    """
```

## Bonnes pratiques

1. **Gestion des ressources** : Utilisez l'option `drop_stage_after=True` pour nettoyer les stages après utilisation.

2. **Optimisation des performances** :
   - Pour les grands fichiers CSV, ajustez les options de format comme `SKIP_BLANK_LINES` et `NULL_IF`.
   - Pour les fichiers Parquet volumineux, utilisez PyArrow pour une meilleure performance.

3. **Sécurité** :
   - Stockez toujours vos informations de connexion dans un fichier `.env` et ne les incluez jamais dans le code.
   - Utilisez des rôles avec des privilèges limités pour les opérations d'import.

4. **Gestion des erreurs** :
   - Vérifiez toujours la valeur de retour des méthodes (`success = loader.process_file_with_copy(...)`).
   - Utilisez des blocs try/except pour gérer les erreurs spécifiques.

5. **Monitoring** :
   - La classe utilise déjà le logging pour tracer les opérations. Consultez le fichier `snowflake.log`.

## Dépannage

### Problèmes courants et solutions

1. **Erreur de connexion Snowflake** :
   - Vérifiez les informations d'identification dans le fichier `.env`.
   - Assurez-vous que le warehouse est actif et a suffisamment de crédits.

2. **Erreur lors de l'analyse d'un fichier Parquet** :
   - Si l'erreur est liée à FLATTEN dans le SQL, utilisez l'option `use_pyarrow=True`.
   - Si PyArrow n'est pas disponible, installez-le avec `pip install pyarrow`.

3. **Échec du chargement CSV avec erreur de format** :
   - Vérifiez le délimiteur et les options d'encadrement dans `format_options`.
   - Examinez les premières lignes du CSV pour confirmer le format.

4. **La table existe mais l'import échoue** :
   - Vérifiez que le schéma du fichier correspond à celui de la table existante.
   - Utilisez `skip_if_data_exists=False` pour forcer le chargement dans la table existante.

5. **Stage non trouvé ou inaccessible** :
   - Vérifiez les droits d'accès de l'utilisateur Snowflake.
   - Assurez-vous que le chemin du fichier est correct et accessible.
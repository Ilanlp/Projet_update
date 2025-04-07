## L'utilisation de Pydantic pour la validation des données

### Pourquoi Pydantic?

[Pydantic](https://docs.pydantic.dev/) est une bibliothèque Python qui permet la validation des données et la gestion des paramètres à l'aide d'annotations de type Python. Dans ce projet, nous utilisons Pydantic V2 pour plusieurs raisons essentielles:

1. **Validation robuste des données** - Pydantic vérifie automatiquement que les données reçues des API correspondent aux types attendus, ce qui nous permet de détecter immédiatement les incohérences.

2. **Conversion automatique des types** - Pydantic convertit intelligemment les chaînes de caractères en entiers, dates, URLs, etc., selon les annotations de type.

3. **Documentation intégrée** - Les modèles Pydantic sont autodocumentés grâce aux annotations de type et aux descriptions de champs.

4. **Sérialisation et désérialisation** - Conversion facile entre objets Python et formats comme JSON, nécessaire pour communiquer avec les API.

5. **Performance** - Pydantic V2 utilise Rust en arrière-plan, ce qui lui confère d'excellentes performances, essentielles pour traiter de grands volumes de données.

### Comment nous utilisons Pydantic

Dans notre script, nous utilisons Pydantic à trois niveaux:

1. **Modèles de requête** - Pour structurer et valider les paramètres envoyés aux API:
   ```python
   class SearchParams(FranceTravailModel):
       motsCles: Optional[str] = Field(default=None, description="Mots clés de recherche")
       range: Optional[str] = Field(default="0-49", description="Pagination des données")
   ```

2. **Modèles de réponse** - Pour valider et structurer les données reçues des API:
   ```python
   class Offre(FranceTravailModel):
       id: str = Field(description="Identifiant de l'offre d'emploi")
       intitule: str = Field(description="Intitulé de l'offre")
   ```

3. **Modèle normalisé** - Pour uniformiser les données des différentes sources:
   ```python
   class NormalizedJobOffer(BaseModel):
       id: str
       source: str  # 'adzuna' ou 'france_travail'
       title: str
   ```

Cette approche nous permet de:
- Détecter rapidement les changements dans la structure des API
- Assurer l'intégrité des données tout au long du processus
- Gérer proprement les valeurs manquantes ou mal formatées
- Fournir une base de code maintenable et évolutive
- Documenter clairement la structure des données

Pour les développeurs qui souhaitent étendre ce script, la compréhension des modèles Pydantic est essentielle car ils définissent la structure et les contraintes de tous les échanges de données.

## Dépannage

### Problèmes avec l'API Adzuna
- **Erreur liée au paramètre sort_dir** : Si vous obtenez une erreur concernant le paramètre `sort_dir`, assurez-vous d'utiliser la dernière version du script qui n'utilise plus ce paramètre.
- **Limitations de requêtes** : L'API Adzuna peut limiter le nombre de requêtes par minute. Si vous rencontrez des erreurs 429, réduisez le nombre de requêtes ou attendez avant de réessayer.

### Problèmes avec l'API France Travail
- **Erreur d'authentification** : Si vous recevez une erreur 401, vérifiez que votre token est valide et n'a pas expiré.
- **Erreur de plage** : Si vous obtenez une erreur sur le paramètre `range`, assurez-vous que les valeurs respectent les limites (0-3000 pour le début, maximum 3149 pour la fin).

### Problèmes de données
- **Valeurs manquantes** : Certains champs peuvent être vides selon la source. Le script remplace les valeurs null par des valeurs appropriées.
- **Format de date** : Si vous rencontrez des problèmes avec les dates, vérifiez que votre version de pandas gère correctement la conversion des dates ISO.## Particularités des API

### API Adzuna
- **Changement important** : Le paramètre `sort_dir` n'est plus supporté par l'API Adzuna depuis sa dernière mise à jour. Le script a été modifié pour utiliser uniquement le paramètre `sort_by` pour le tri.
- **Pagination** : L'API Adzuna utilise un système de pagination basé sur des numéros de page (commençant à 1). Chaque page peut contenir jusqu'à 50 résultats maximum.
- **Limitations** : 
  - Maximum de 50 résultats par page
  - Le script gère automatiquement la récupération de plusieurs pages pour atteindre le nombre total de résultats demandés
  - L'accès aux pages au-delà de la limite fixée par Adzuna peut générer des erreurs

### API France Travail
- **Pagination** : L'API France Travail utilise un système de pagination par plage (range) au format `p-d` où `p` est l'index (débutant à 0) du premier élément et `d` est l'index du dernier élément.
- **Limitations** : 
  - La plage de résultats est limitée à 150 résultats maximum par requête
  - L'index du premier élément ne doit pas dépasser 3000
  - L'index du dernier élément ne doit pas dépasser 3149
  - Le script gère ces limitations en ajustant automatiquement les paramètres de recherche

### Gestion de la pagination dans le script
Le script intègre un mécanisme qui :
1. Récupère d'abord une page de résultats (50 pour Adzuna, jusqu'à 150 pour France Travail)
2. Continue à récupérer les pages suivantes si nécessaire jusqu'à atteindre le nombre maximum de résultats demandé
3. Gère les erreurs spécifiques liées à la pagination (dépassement de limite, etc.)
4. Combine tous les résultats dans un ensemble unifié## Sécurité des données

Le script applique les mesures de sécurité suivantes pour garantir l'intégrité des données :

1. **Nettoyage des données textuelles** : Suppression des caractères problématiques (retours à la ligne, caractères de contrôle) et échappement des guillemets.

2. **Validation des valeurs numériques** : Conversion et validation des valeurs numériques (salaires, coordonnées géographiques).

3. **Protection contre l'injection CSV** : Les caractères spéciaux sont échappés pour éviter les injections dans les fichiers CSV.

4. **Gestion des valeurs manquantes** : Remplacement des valeurs nulles par des valeurs appropriées au contexte.

5. **Sanitization des noms de fichiers** : Nettoyage des noms de fichiers pour éviter les problèmes de sécurité.

6. **Chemins de fichiers sécurisés** : Conversion des chemins relatifs en chemins absolus et vérification de l'existence des dossiers.

7. **Repli sur des solutions alternatives** : En cas d'échec lors de la sauvegarde, utilisation de méthodes alternatives pour préserver les données.

8. **Protection des identifiants API** : Aucun identifiant d'API n'est stocké dans le code (utilisation de variables d'environnement).# Normalisateur de données d'emploi

Ce script permet de récupérer, normaliser et analyser des offres d'emploi provenant des API Adzuna et France Travail (anciennement Pôle Emploi).

## Introduction aux API et à la pagination

### Qu'est-ce qu'une API?

Une **API** (Application Programming Interface ou Interface de Programmation d'Application) est un ensemble de règles et de protocoles qui permettent à différentes applications de communiquer entre elles. Dans le contexte des offres d'emploi, les API comme celles d'Adzuna et France Travail permettent aux développeurs d'accéder aux bases de données d'offres d'emploi de manière structurée.

### Pourquoi la pagination est-elle nécessaire?

Lorsqu'une API doit renvoyer un grand nombre de résultats (comme des milliers d'offres d'emploi), il n'est pas pratique de tout renvoyer en une seule fois pour plusieurs raisons :
- Charge réseau excessive
- Temps de réponse trop long
- Utilisation mémoire importante
- Risque de timeout

C'est pourquoi les API implémentent différentes stratégies de pagination pour découper les résultats en "pages" plus petites.

### Méthodes courantes de pagination des API

1. **Pagination par numéro de page** (utilisée par Adzuna)
   - Paramètres courants : `page` (numéro de page) et `per_page` (nombre d'éléments par page)
   - Exemple : `/search?page=2&per_page=50`
   - Avantages : Simple à comprendre et à implémenter
   - Inconvénients : Moins efficace pour les datasets très grands

2. **Pagination par offset et limite** (variante utilisée par France Travail)
   - Paramètres courants : `offset` (décalage) et `limit` (nombre d'éléments à retourner)
   - France Travail utilise un format `range=p-d` où `p` est l'offset et `d` est l'offset+limit-1
   - Exemple : `/search?range=50-99` (équivaut à offset=50, limit=50)
   - Avantages : Flexible, permet de sauter directement à un point précis
   - Inconvénients : Peut devenir inefficace pour de grands offset

3. **Pagination par curseur**
   - Utilise un "pointeur" ou un ID vers le dernier élément récupéré
   - Exemple : `/search?cursor=abc123xyz`
   - Avantages : Très efficace pour les grands datasets, résistant aux modifications entre les appels
   - Inconvénients : Plus complexe à implémenter, souvent unidirectionnelle

4. **Pagination par timestamp**
   - Filtre les résultats par date/heure, en demandant les éléments après un certain timestamp
   - Exemple : `/search?created_after=2023-01-01T12:00:00Z`
   - Avantages : Excellent pour les flux chronologiques comme les offres d'emploi récentes
   - Inconvénients : Nécessite un champ de date bien indexé

5. **Pagination avec liens hypermedia** (HATEOAS)
   - L'API fournit des liens vers la page suivante/précédente dans sa réponse
   - Exemple : Liens dans les en-têtes HTTP ou dans le corps JSON
   - Avantages : Autodescriptif, facilite la navigation
   - Inconvénients : Requiert plus de traitement côté client

Notre script implémente les méthodes appropriées pour chaque API : pagination par numéro de page pour Adzuna et pagination par plage (offset-limite) pour France Travail.

## Nouveautés de la version 1.1
- Mise à jour pour tenir compte des changements de l'API Adzuna (retrait du paramètre `sort_dir`)
- Ajout d'un mécanisme de gestion des erreurs spécifiques aux API
- Correction du traitement des URLs pour les offres France Travail
- Amélioration de la sécurité et du nettoyage des données avant l'export CSV
- Meilleure gestion des noms de fichiers et des chemins

## Installation

1. Clonez ce dépôt:
   ```bash
   git clone https://github.com/votre-nom/job-data-normalizer.git
   cd job-data-normalizer
   ```

2. Installez les dépendances requises:
   ```bash
   pip install pandas pydantic httpx python-dotenv
   ```

3. Configurez les variables d'environnement:
   ```bash
   cp .env.example .env
   ```
   
   Modifiez ensuite le fichier `.env` avec vos propres identifiants d'API.

## Configuration des API

### Adzuna
1. Créez un compte sur [Adzuna for Developers](https://developer.adzuna.com/)
2. Obtenez vos identifiants d'API (Application ID et API Key)
3. Ajoutez-les dans votre fichier `.env`

### France Travail
1. Inscrivez-vous à l'[Emploi Store Développeurs](https://www.emploi-store-dev.fr/)
2. Créez une application et demandez l'accès à l'API Offres d'emploi
3. Obtenez un token d'accès et ajoutez-le dans votre fichier `.env`

## Utilisation

### Exécution simple
```bash
python job_data_normalizer.py
```

### Variables d'environnement

Vous pouvez configurer les paramètres suivants dans votre fichier `.env`:

- **ADZUNA_APP_ID**: Votre identifiant d'application Adzuna (obligatoire)
- **ADZUNA_APP_KEY**: Votre clé API Adzuna (obligatoire)
- **FRANCE_TRAVAIL_TOKEN**: Votre token d'accès France Travail (obligatoire)
- **DEFAULT_SEARCH_TERMS**: Termes de recherche par défaut (optionnel)
- **DEFAULT_LOCATION_ADZUNA**: Localisation par défaut pour Adzuna (optionnel)
- **DEFAULT_LOCATION_FRANCE_TRAVAIL**: Localisation par défaut pour France Travail (optionnel)
- **DEFAULT_MAX_RESULTS**: Nombre maximum de résultats par source (optionnel)
- **OUTPUT_DIR**: Dossier de sortie pour les fichiers générés (optionnel, par défaut: "job_data")

## Structure des données normalisées

Les données sont normalisées selon le modèle suivant:

| Champ | Description |
|-------|-------------|
| id | Identifiant unique de l'offre |
| source | Source de données ('adzuna' ou 'france_travail') |
| title | Titre de l'offre |
| description | Description de l'offre |
| company_name | Nom de l'entreprise |
| location_name | Nom de la localisation |
| latitude | Latitude géographique |
| longitude | Longitude géographique |
| date_created | Date de création de l'offre |
| date_updated | Date de mise à jour de l'offre |
| contract_type | Type de contrat (CDI, CDD, etc.) |
| contract_duration | Durée du contrat |
| working_hours | Temps de travail (Temps plein, Temps partiel) |
| salary_min | Salaire minimum |
| salary_max | Salaire maximum |
| salary_currency | Devise du salaire |
| salary_period | Période du salaire (mensuel, annuel, horaire) |
| experience_required | Expérience requise |
| category | Catégorie/Métier |
| sector | Secteur d'activité |
| application_url | URL pour postuler |
| source_url | URL source de l'offre |
| skills | Compétences requises |
| remote_work | Télétravail possible |
| is_handicap_accessible | Accessible aux travailleurs handicapés |

## Mapping entre les sources

Le normalisateur utilise un système de correspondance pour harmoniser les données entre les différentes sources. Voici les principaux mappings mis en œuvre :

### Correspondance des champs

| Champ normalisé | Adzuna | France Travail |
|-----------------|--------|----------------|
| id | id | id |
| title | title | intitule |
| description | description | description |
| company_name | company.display_name | entreprise.nom |
| location_name | location.display_name | lieuTravail.libelle |
| latitude | latitude | lieuTravail.latitude |
| longitude | longitude | lieuTravail.longitude |
| date_created | created | dateCreation |
| date_updated | created (identique) | dateActualisation |
| contract_type | contract_type | typeContrat |
| contract_duration | N/A | typeContratLibelle |
| working_hours | contract_time | dureeTravailLibelleConverti |
| salary_min | salary_min | Extrait de salaire.libelle |
| salary_max | salary_max | Extrait de salaire.libelle |
| category | category.label | romeLibelle |
| sector | N/A | secteurActiviteLibelle |
| application_url | redirect_url | contact.urlPostulation |
| source_url | redirect_url | origineOffre.urlOrigine |
| skills | N/A | competences[].libelle |
| is_handicap_accessible | N/A | accessibleTH |

### Normalisation des valeurs

#### Types de contrat
| Valeur normalisée | Adzuna | France Travail |
|-------------------|--------|----------------|
| CDI | permanent | CDI |
| CDD | contract | CDD |
| Mission intérimaire | N/A | MIS |
| Travail saisonnier | N/A | SAI |
| Profession libérale | N/A | LIB |

#### Horaires de travail
| Valeur normalisée | Adzuna | France Travail |
|-------------------|--------|----------------|
| Temps plein | full_time | Temps plein |
| Temps partiel | part_time | Temps partiel |

#### Expérience requise
| Valeur normalisée | Adzuna | France Travail |
|-------------------|--------|----------------|
| Débutant accepté | N/A | D |
| Expérience souhaitée | N/A | S |
| Expérience exigée | N/A | E |

#### Périodes de salaire
| Valeur normalisée | Adzuna | France Travail |
|-------------------|--------|----------------|
| annuel | Par défaut | Détecté via "Annuel" dans salaire.libelle |
| mensuel | N/A | Détecté via "Mensuel" dans salaire.libelle |
| horaire | N/A | Détecté via "Horaire" dans salaire.libelle |

## Résultats

Le script génère trois types de fichiers dans le dossier `job_data`:

1. `all_jobs_[DATE].csv`: Toutes les offres d'emploi normalisées
2. `adzuna_jobs_[DATE].csv`: Offres d'emploi provenant d'Adzuna
3. `france_travail_jobs_[DATE].csv`: Offres d'emploi provenant de France Travail
4. `analysis_[DATE].json`: Analyse statistique des offres d'emploi

## Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.

Documentation d'Authentification API JobMarket
Vue d'ensemble
L'API JobMarket implémente un système d'authentification HTTP Basic pour sécuriser les opérations de modification des données. Cette approche garantit que seuls les utilisateurs autorisés peuvent effectuer des actions sensibles sur la base de données.

Scope de sécurité
Méthodes protégées : POST, PUT, DELETE, PATCH
Méthodes publiques : GET (accès en lecture seule)
Mécanisme : HTTP Basic Authentication
Configuration : Variables d'environnement
Architecture technique
Structure des fichiers
backend/
├── app/
│   ├── auth.py              # Module d'authentification
│   ├── config.py            # Configuration centralisée
│   ├── main.py              # Application principale avec middleware
│   └── api/
│       ├── routes.py        # Routes avec opérations CRUD
│       ├── routes_competence.py
│       └── autres_routes.py
├── .env                     # Variables d'environnement
├── .env.example             # Template de configuration
└── requirements.txt         # Dépendances
Flux d'authentification
Le middleware d'authentification intercepte toutes les requêtes HTTP entrantes et applique la logique suivante :

Analyse de la méthode HTTP : Vérification si la méthode nécessite une authentification
Extraction des credentials : Récupération de l'en-tête Authorization
Validation : Comparaison sécurisée avec les credentials configurés
Autorisation : Passage à la route ou retour d'erreur 401
Configuration
Variables d'environnement
Ajoutez les variables suivantes à votre fichier .env :

env
# Configuration Snowflake (existante)
SNOWFLAKE_ACCOUNT=votre_account
SNOWFLAKE_USER=votre_user
SNOWFLAKE_PASSWORD=votre_password
SNOWFLAKE_DATABASE=votre_database

# Configuration API
API_TITLE=JobMarket API
API_VERSION=1.0.0

# Authentification (nouveau)
AUTH_USERNAME=admin_jobmarket
AUTH_PASSWORD=VotreMotDePasseSecurise2024
Fichier de configuration
Le fichier app/config.py centralise tous les paramètres :

python
class Settings(BaseSettings):
    # Paramètres Snowflake
    SNOWFLAKE_ACCOUNT: str
    SNOWFLAKE_USER: str
    # ...
    
    # Authentification
    AUTH_USERNAME: str = voir auth.py
    AUTH_PASSWORD: str = voir auth.py
    
    model_config = SettingsConfigDict(env_file=".env")
Utilisation
Accès aux routes publiques
Les requêtes GET ne nécessitent aucune authentification :

bash
curl -X GET http://localhost:8000/api/offres
curl -X GET http://localhost:8000/api/competences
Accès aux routes protégées
Avec curl
bash
# Création d'une ressource
curl -X POST http://localhost:8000/api/offres \
  -u admin_jobmarket:VotreMotDePasseSecurise2024 \
  -H "Content-Type: application/json" \
  -d '{"title": "Data Engineer", "description": "Poste de data engineer"}'

# Mise à jour
curl -X PUT http://localhost:8000/api/offres/1 \
  -u admin_jobmarket:VotreMotDePasseSecurise2024 \
  -H "Content-Type: application/json" \
  -d '{"title": "Senior Data Engineer"}'

# Suppression
curl -X DELETE http://localhost:8000/api/offres/1 \
  -u admin_jobmarket:VotreMotDePasseSecurise2024
Avec Python
python
import requests
from requests.auth import HTTPBasicAuth

auth = HTTPBasicAuth('admin_jobmarket', 'VotreMotDePasseSecurise2024')

response = requests.post(
    'http://localhost:8000/api/offres',
    json={'title': 'Data Engineer', 'description': 'Description'},
    auth=auth
)
Avec JavaScript
javascript
const credentials = btoa('admin_jobmarket:VotreMotDePasseSecurise2024');

fetch('http://localhost:8000/api/offres', {
    method: 'POST',
    headers: {
        'Authorization': `Basic ${credentials}`,
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        title: 'Data Engineer',
        description: 'Description du poste'
    })
});
Documentation interactive
L'authentification est intégrée dans la documentation Swagger disponible à l'adresse http://localhost:8000/docs.

Pour tester les endpoints protégés :

Cliquez sur le bouton "Authorize" en haut à droite
Sélectionnez "HTTP Basic"
Saisissez vos identifiants
Les endpoints protégés afficheront un cadenas indiquant la sécurisation
Codes de réponse
Succès
200 OK : Opération réussie (PUT, PATCH, DELETE)
201 Created : Ressource créée avec succès (POST)
Erreurs d'authentification
401 Unauthorized : Credentials manquants ou invalides
Exemple de réponse d'erreur :

json
{
    "success": false,
    "message": "Authentification requise pour cette opération",
    "data": null
}
Dépannage
Erreur 401 avec des credentials valides
Vérifiez l'encodage Base64 des credentials
Assurez-vous que les variables d'environnement sont correctement chargées
Consultez les logs du serveur pour identifier l'origine du problème
Middleware non fonctionnel
Vérifiez que l'import from app.auth import verify_basic_auth est présent dans main.py
Assurez-vous que le middleware est placé après le middleware CORS
Contrôlez que le fichier app/auth.py existe et est accessible
Routes GET protégées par erreur
Le middleware ne doit protéger que les méthodes POST, PUT, DELETE et PATCH. Si vos routes GET nécessitent une authentification, vérifiez la configuration du middleware.

Sécurité en production
Recommandations essentielles
Changement des credentials par défaut : Utilisez des identifiants robustes en production
HTTPS obligatoire : Chiffrement de toutes les communications
Variables d'environnement : Stockage sécurisé des credentials
Rotation des mots de passe : Mise à jour périodique des credentials
Logs de sécurité : Surveillance des tentatives d'authentification
Configuration sécurisée
python
# Exemple de configuration avancée avec hashage
import hashlib
import secrets

def verify_password_hash(password: str, stored_hash: str) -> bool:
    """Vérification sécurisée avec hash SHA-256"""
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    return secrets.compare_digest(password_hash, stored_hash)
Support technique
Pour toute question concernant l'authentification :

Documentation API : http://localhost:8000/docs
Logs applicatifs : Consultez les logs du serveur pour le debugging
Configuration : Vérifiez le fichier .env et app/config.py
Notes de version
v1.0 : Implémentation HTTP Basic Authentication
Support : Python 3.8+, FastAPI 0.100+

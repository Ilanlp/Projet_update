import secrets
import base64
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration depuis .env avec valeurs par défaut
ADMIN_USERNAME = os.getenv("AUTH_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("AUTH_PASSWORD", "password123")

def verify_basic_auth(auth_header: str) -> bool:
    # ... le reste du code reste identique
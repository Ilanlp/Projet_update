import requests

# 🔁 Paramètres à personnaliser
TOKEN_URL = "https://entreprise.francetravail.fr/connexion/oauth2/access_token?realm=/partenaire"
CLIENT_ID = "PAR_dataingest_784cb5f0f51af729ec2d4262dc547490cbccbd830aff2f5149cb78501c07a72a"
CLIENT_SECRET = "2cba7f018868b2dedc7b1fccad8f97cd18c333c46ada9fe29e19ca7876d57eea"
SCOPE = "api_offresdemploiv2 o2dsoffre"

# 🔐 Corps de la requête
data = {
    "grant_type": "client_credentials",
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "scope": SCOPE
}

# 📄 En-têtes
headers = {
    "Content-Type": "application/x-www-form-urlencoded"
}

# 📡 Envoi de la requête
response = requests.post(TOKEN_URL, headers=headers, data=data)

# ✅ Traitement de la réponse
if response.status_code == 200:
    token = response.json()["access_token"]
    print("✅ Token généré avec succès :")
    print(token)
else:
    print("❌ Erreur lors de la génération du token")
    print(f"Code : {response.status_code}")
    print(response.text)

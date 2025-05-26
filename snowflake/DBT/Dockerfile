FROM python:3.10.17-slim

# Créer un utilisateur non-root
RUN groupadd -r node && useradd -r -g node node

#variables envrionnements qui facilent la vie
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /usr/src/DBT

COPY requirements.txt ./

# Installer les dépendances et nettoyer en une seule couche
RUN apt-get update -y
RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    chown -R node:node /usr/src/

# Copier le code de l'application (exclure les fichiers sensibles et temporaires)
COPY --chown=node:node Projet_DBT/ Projet_DBT/

# Préparation du dossier dbt caché 
RUN mkdir /usr/.dbt
RUN chmod 757 /usr/.dbt

USER node
WORKDIR /usr/src/DBT/Projet_DBT

# Configuration du fichier profiles.yml et exécution dbt
CMD python3 config.py | dbt run --profiles-dir /usr/.dbt 



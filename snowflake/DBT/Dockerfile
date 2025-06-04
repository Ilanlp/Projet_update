FROM python:3.10.17-slim

# Créer un utilisateur avec un UID/GID spécifique
RUN groupadd -g 1000 node && \
    useradd -u 1000 -g node -s /bin/bash -m node

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
RUN apt-get install -y git
RUN apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    chown -R node:node /usr/src/

# Copier le code de l'application (exclure les fichiers sensibles et temporaires)
COPY --chown=node:node --chmod=755 Projet_DBT/ Projet_DBT/

# Préparation du dossier dbt caché 
RUN mkdir /usr/.dbt
RUN chown node /usr/.dbt

USER node
WORKDIR /usr/src/DBT/Projet_DBT

# Configuration du fichier profiles.yml et exécution dbt
CMD python3 config.py && \
    dbt debug --profiles-dir /usr/.dbt && \
    dbt run --select bronze --profiles-dir /usr/.dbt && \
    dbt run --select silver --profiles-dir /usr/.dbt && \
    dbt run --select liaison_Rome_Metier_gold_sql liaison_Rome_Soft_Skill_gold_sql --profiles-dir /usr/.dbt && \
    dbt run --select fait_offre --profiles-dir /usr/.dbt && \
    dbt run --select liaison_Offre_Competence --profiles-dir /usr/.dbt 






# Base image
FROM python:3.10-slim

# Set work directory
WORKDIR /app

# Copy all files
COPY normalizer.py ./
COPY adzuna/ ./adzuna/
COPY france_travail/ ./france_travail/
COPY /data ./data/        
COPY requirements.txt ./        

# 4. Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# 5. Spécifier la commande de démarrage
CMD ["python", "normalizer.py"]

FROM python:3.10.17-slim

# Créer un utilisateur non-root
RUN groupadd -r node && useradd -r -g node node

#variables envrionnements qui facilent la vie
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /usr/src/

COPY requirements.txt ./

# Installer les dépendances et nettoyer en une seule couche
RUN apt-get update -y
RUN pip3 install --no-cache-dir -r requirements.txt
RUN apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    chown -R node:node /usr/src/

# Copier le code de l'application (exclure les fichiers sensibles et temporaires)
COPY --chown=node:node snowflake/ snowflake/

RUN mkdir /usr/src/logs
RUN chown node /usr/src/logs

USER node
WORKDIR /usr/src/snowflake

CMD python3 snowflake_init.py && \
    python3 snowflake_core.py




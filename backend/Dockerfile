FROM python:3.10.17-slim

# Créer un utilisateur non-root
RUN groupadd -r node && useradd -r -g node node

#variables envrionnements qui facilent la vie
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

    #? 
WORKDIR /usr/src/backend

COPY requirements.txt ./

# Installer les dépendances et nettoyer en une seule couche
RUN apt-get update -y
RUN apt-get install -y --no-install-recommends libpq-dev gcc curl
RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get purge -y gcc && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    chown -R node:node /usr/src/backend
# Copier le code de l'application (exclure les fichiers sensibles et temporaires)
COPY --chown=node:node app/ app/
COPY --chown=node:node sql/ sql/


USER node

EXPOSE 8081

# Configurer le healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8081 || exit 1

#reload pour le dev
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8081", "--reload"]
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
# CMD ["fastapi", "run", "app/main.py", "--proxy-headers", "--port", "80"]
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.routes import router
from app.api.routes2 import router2
import time
import uvicorn

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Création de l'application FastAPI
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    openapi_tags=[
        {"name": "Système", "description": "Opérations système"},
        {"name": "Références", "description": "Tables de références"},
        {"name": "Relationnels", "description": "Tables relationnels"},
        {"name": "Modèles", "description": "Accès au version du modèle"},
    ],
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "Équipe de support Jobmarket",
        "email": "support@jobmarket.com",
        "url": "https://api.jobmarket/support",
    },
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # A ajuster pour la production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware pour le logging des requêtes
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    process_time = time.time() - start_time
    logger.info(
        f"{request.method} {request.url.path} - Status: {response.status_code} - Duration: {process_time:.4f}s"
    )

    return response


# Gestionnaire d'exceptions global
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Exception non gérée: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Une erreur interne s'est produite",
            "data": None,
        },
    )


# Inclusion des routes
app.include_router(router, prefix="/api")
app.include_router(router2, prefix="/api2")


# Route de santé
@app.get("/", tags=["Système"])
async def root():
    return {"status": "ok", "version": settings.API_VERSION}


# Route de santé
@app.get("/health_check", tags=["Système"])
async def health_check():
    return {"status": "ok", "version": settings.API_VERSION}


# Route de santé
@app.get("/health/modele/v1", tags=["Système"])
async def health_v1():
    return {"status": "ok", "version": settings.API_VERSION}


# Route de santé
@app.get("/health/modele/v2", tags=["Système"])
async def health_v2():
    return {"status": "ok", "version": settings.API_VERSION}


# Pour lancer l'application directement avec python
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

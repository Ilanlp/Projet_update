from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import httpx
from typing import List, Optional
from app.config import settings
from app.services.query_service import execute_query
from app.models.schemas import Offre

router = APIRouter(
    prefix="/api/model",
    tags=["model"],
    responses={404: {"description": "Not found"}},
)

class ProfileText(BaseModel):
    text: str

class ProfileMatch(BaseModel):
    title: str
    company: str
    location: str
    score: float
    description: Optional[str] = None
    type_contrat: Optional[str] = None
    type_seniorite: Optional[str] = None
    competences: Optional[str] = None
    types_competences: Optional[str] = None
    softskills_summary: Optional[str] = None
    softskills_details: Optional[str] = None
    nom_metier: Optional[str] = None
    code_rome: Optional[str] = None
    type_teletravail: Optional[str] = None
    nom_domaine: Optional[str] = None

class ModelResponse(BaseModel):
    matches: List[ProfileMatch]

@router.post("/match", response_model=ModelResponse)
async def match_profile(profile: ProfileText):
    """
    Match un profil avec les offres d'emploi disponibles.
    
    Args:
        profile (ProfileText): Le texte du profil à matcher
        
    Returns:
        ModelResponse: Les meilleures offres correspondantes
    """
    try:
        # Préparation des données pour MLflow
        data = {
            "dataframe_records": [
                {
                    "TEXT": profile.text
                }
            ]
        }
        
        # Appel au service MLflow
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.MLFLOW_MODEL_URL}/invocations",
                json=data,
                timeout=30.0
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Erreur lors de l'appel au modèle MLflow"
                )
            
            # Traitement de la réponse
            predictions = response.json()
            
            if not predictions or "predictions" not in predictions:
                raise HTTPException(
                    status_code=500,
                    detail="Format de réponse du modèle invalide"
                )
            
            # Récupération des indices des offres
            offer_indices = [int(pred[0]) for pred in predictions["predictions"]]
            
            # Récupération des détails des offres depuis la base de données
            offers = []
            for idx in offer_indices:
                query = """
                SELECT 
                    id,
                    title,
                    nom_entreprise,
                    ville,
                    description,
                    type_contrat,
                    type_seniorite,
                    competences,
                    types_competences,
                    softskills_summary,
                    softskills_details,
                    nom_metier,
                    code_rome,
                    type_teletravail,
                    nom_domaine
                FROM ONE_BIG_TABLE
                WHERE id = :id
                """
                result = await execute_query(query, {"id": idx})
                if result:
                    offers.append(result[0])
            
            # Formatage de la réponse
            formatted_matches = []
            for i, offer in enumerate(offers):
                score = float(predictions["predictions"][i][1]) if i < len(predictions["predictions"]) else 0.0
                formatted_matches.append(
                    ProfileMatch(
                        title=offer["TITLE"],
                        company=offer["NOM_ENTREPRISE"],
                        location=offer["VILLE"],
                        score=score,
                        description=offer.get("DESCRIPTION"),
                        type_contrat=offer.get("TYPE_CONTRAT"),
                        type_seniorite=offer.get("TYPE_SENIORITE"),
                        competences=offer.get("COMPETENCES"),
                        types_competences=offer.get("TYPES_COMPETENCES"),
                        softskills_summary=offer.get("SOFTSKILLS_SUMMARY"),
                        softskills_details=offer.get("SOFTSKILLS_DETAILS"),
                        nom_metier=offer.get("NOM_METIER"),
                        code_rome=offer.get("CODE_ROME"),
                        type_teletravail=offer.get("TYPE_TELETRAVAIL"),
                        nom_domaine=offer.get("NOM_DOMAINE")
                    )
                )
            
            return ModelResponse(matches=formatted_matches)
            
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Erreur de connexion au service MLflow: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur interne: {str(e)}"
        )

@router.get("/health")
async def check_model_health():
    """
    Vérifie l'état du service MLflow.
    
    Returns:
        dict: État du service
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.MLFLOW_MODEL_URL}/health",
                timeout=5.0
            )
            
            if response.status_code != 200:
                return {"status": "unhealthy", "detail": "Service MLflow indisponible"}
                
            return {"status": "healthy", "detail": "Service MLflow opérationnel"}
            
    except Exception as e:
        return {"status": "unhealthy", "detail": str(e)} 
import pytest
from fastapi.testclient import TestClient
from app.main import app
from typing import Dict, Any


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sample_offre() -> Dict[str, Any]:
    return {
        "ID_LOCAL": "TEST123",
        "TITLE": "Test Data Engineer",
        "DESCRIPTION": "Test description",
        "TYPE_CONTRAT": "CDI",
        "CODE_DOMAINE": "INFO",
        "NOM_DOMAINE": "Informatique",
        "CODE_POSTAL": 75001,
        "VILLE": "Paris",
        "DEPARTEMENT": "Paris",
        "REGION": "Île-de-France",
        "PAYS": "France",
        "LATITUDE": 48.8566,
        "LONGITUDE": 2.3522,
        "POPULATION": 2148271,
        "TYPE_TELETRAVAIL": "Hybride",
        "TYPE_SENIORITE": "Senior",
        "CODE_ROME": "M1805",
        "NOM_ENTREPRISE": "Test Company",
        "CATEGORIE_ENTREPRISE": "PME",
        "COMPETENCES": "Python, SQL",
        "TYPES_COMPETENCES": "Technique",
        "SOFTSKILLS_SUMMARY": "Communication",
        "SOFTSKILLS_DETAILS": "Travail en équipe",
        "NOM_METIER": "Data Engineer",
    }

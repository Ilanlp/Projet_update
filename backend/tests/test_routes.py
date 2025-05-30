import pytest
from fastapi.testclient import TestClient
from typing import Dict, Any


def test_get_offres(client: TestClient):
    response = client.get("/offres")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert "items" in data["data"]
    assert "total" in data["data"]
    assert "page" in data["data"]
    assert "page_size" in data["data"]


def test_get_offres_pagination(client: TestClient):
    # Test avec des paramètres de pagination spécifiques
    response = client.get("/offres?page=2&page_size=5")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["page"] == 2
    assert data["data"]["page_size"] == 5


def test_get_offre_by_id(client: TestClient):
    # Test avec un ID existant (à adapter selon votre base de données)
    response = client.get("/offres/1")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert isinstance(data["data"], dict)


def test_get_offre_not_found(client: TestClient):
    # Test avec un ID inexistant
    response = client.get("/offres/999999")
    assert response.status_code == 404


def test_create_offre(client: TestClient, sample_offre: Dict[str, Any]):
    response = client.post("/offres", json=sample_offre)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert data["data"]["TITLE"] == sample_offre["TITLE"]

    # Nettoyer après le test
    created_id = data["data"]["ID"]
    client.delete(f"/offres/{created_id}")


def test_create_offre_invalid_data(client: TestClient):
    invalid_offre = {"TITLE": "Test"}  # Données incomplètes
    response = client.post("/offres", json=invalid_offre)
    assert response.status_code == 422  # Validation error


def test_update_offre(client: TestClient, sample_offre: Dict[str, Any]):
    # D'abord créer une offre
    create_response = client.post("/offres", json=sample_offre)
    assert create_response.status_code == 201
    created_id = create_response.json()["data"]["ID"]

    # Mettre à jour l'offre
    update_data = {
        **sample_offre,
        "TITLE": "Updated Test Title",
        "DESCRIPTION": "Updated description",
    }
    response = client.put(f"/offres/{created_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["TITLE"] == "Updated Test Title"

    # Nettoyer après le test
    client.delete(f"/offres/{created_id}")


def test_update_offre_not_found(client: TestClient, sample_offre: Dict[str, Any]):
    response = client.put("/offres/999999", json=sample_offre)
    assert response.status_code == 404


def test_delete_offre(client: TestClient, sample_offre: Dict[str, Any]):
    # D'abord créer une offre
    create_response = client.post("/offres", json=sample_offre)
    assert create_response.status_code == 201
    created_id = create_response.json()["data"]["ID"]

    # Supprimer l'offre
    response = client.delete(f"/offres/{created_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

    # Vérifier que l'offre n'existe plus
    get_response = client.get(f"/offres/{created_id}")
    assert get_response.status_code == 404


def test_delete_offre_not_found(client: TestClient):
    response = client.delete("/offres/999999")
    assert response.status_code == 404

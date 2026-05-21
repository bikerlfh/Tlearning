import pytest


@pytest.mark.django_db
def test_health_endpoint_returns_200(api_client):
    response = api_client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["database"] == "ok"

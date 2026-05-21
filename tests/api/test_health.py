from unittest.mock import patch

import pytest


@pytest.mark.django_db
def test_health_endpoint_returns_200_when_all_dependencies_up(api_client):
    response = api_client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["checks"] == {"db": True, "redis": True}


@pytest.mark.django_db
def test_health_endpoint_returns_503_when_db_down(api_client):
    with patch("api.views.connection.cursor", side_effect=RuntimeError("db down")):
        response = api_client.get("/api/v1/health")
    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "degraded"
    assert body["checks"]["db"] is False


@pytest.mark.django_db
def test_health_endpoint_returns_503_when_redis_down(api_client):
    import redis

    with patch.object(redis.Redis, "ping", side_effect=ConnectionError("redis down")):
        response = api_client.get("/api/v1/health")
    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "degraded"
    assert body["checks"]["redis"] is False


@pytest.mark.django_db
def test_debug_sentry_404s_when_debug_is_false(api_client, settings):
    settings.DEBUG = False
    response = api_client.get("/api/v1/_debug/sentry")
    assert response.status_code == 404


@pytest.mark.django_db
def test_debug_sentry_raises_when_debug_is_true(api_client, settings):
    settings.DEBUG = True
    # DRF re-raises uncaught exceptions through the test client by default,
    # which is exactly what tells us Sentry's middleware would have captured it.
    api_client.raise_request_exception = False
    response = api_client.get("/api/v1/_debug/sentry")
    assert response.status_code == 500

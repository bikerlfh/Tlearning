import re

import pytest

UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


@pytest.mark.django_db
def test_request_id_header_is_added_to_response(api_client):
    response = api_client.get("/api/v1/health")
    rid = response.headers.get("X-Request-Id")
    assert rid is not None
    assert UUID_RE.match(rid)


@pytest.mark.django_db
def test_request_id_honors_incoming_header(api_client):
    incoming = "trace-from-edge-proxy-42"
    response = api_client.get("/api/v1/health", HTTP_X_REQUEST_ID=incoming)
    assert response.headers.get("X-Request-Id") == incoming


@pytest.mark.django_db
def test_distinct_requests_get_distinct_ids(api_client):
    r1 = api_client.get("/api/v1/health")
    r2 = api_client.get("/api/v1/health")
    assert r1.headers["X-Request-Id"] != r2.headers["X-Request-Id"]

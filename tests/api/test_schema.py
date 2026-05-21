def test_openapi_schema_endpoint(api_client):
    response = api_client.get("/api/v1/schema/")
    assert response.status_code == 200
    assert "Tlearning API" in response.content.decode()

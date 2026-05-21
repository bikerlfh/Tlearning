import pytest


@pytest.mark.django_db
class TestApiTokenEndpoints:
    def test_create_token_returns_raw_token_once(self, authed_client):
        response = authed_client.post(
            "/api/v1/auth/api-tokens", {"name": "Claude Desktop"}, format="json"
        )
        assert response.status_code == 201
        body = response.json()
        assert body["name"] == "Claude Desktop"
        assert body["token"].startswith("tl_live_")
        assert "id" in body

    def test_list_tokens_does_not_include_raw(self, authed_client):
        authed_client.post("/api/v1/auth/api-tokens", {"name": "A"}, format="json")
        authed_client.post("/api/v1/auth/api-tokens", {"name": "B"}, format="json")
        response = authed_client.get("/api/v1/auth/api-tokens")
        assert response.status_code == 200
        for item in response.json()["results"]:
            assert "token" not in item
            assert "token_hash" not in item

    def test_revoke_token(self, authed_client):
        created = authed_client.post("/api/v1/auth/api-tokens", {"name": "A"}, format="json").json()
        response = authed_client.delete(f"/api/v1/auth/api-tokens/{created['id']}")
        assert response.status_code == 204

    def test_user_cannot_see_other_users_tokens(self, authed_client, other_user):
        from accounts.models import ApiToken
        from accounts.tokens import generate_token, hash_token

        ApiToken.objects.create(
            user=other_user, token_hash=hash_token(generate_token()), name="hidden"
        )
        response = authed_client.get("/api/v1/auth/api-tokens")
        assert response.status_code == 200
        assert all("hidden" not in t["name"] for t in response.json()["results"])

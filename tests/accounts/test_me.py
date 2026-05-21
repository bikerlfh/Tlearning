import pytest


@pytest.mark.django_db
class TestMe:
    def test_me_returns_current_user(self, authed_client, user):
        response = authed_client.get("/api/v1/auth/me")
        assert response.status_code == 200
        assert response.json()["email"] == user.email

    def test_me_returns_401_when_unauthenticated(self, api_client):
        response = api_client.get("/api/v1/auth/me")
        assert response.status_code in (401, 403)

    def test_patch_me_updates_profile_fields(self, authed_client):
        response = authed_client.patch(
            "/api/v1/auth/me",
            {"name": "Luis", "timezone": "America/Bogota"},
            format="json",
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Luis"
        assert response.json()["timezone"] == "America/Bogota"

    def test_patch_me_ignores_email_change(self, authed_client, user):
        response = authed_client.patch(
            "/api/v1/auth/me", {"email": "hacker@example.com"}, format="json"
        )
        assert response.status_code == 200
        user.refresh_from_db()
        assert user.email != "hacker@example.com"

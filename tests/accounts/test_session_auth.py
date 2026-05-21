import pytest


@pytest.mark.django_db
class TestSessionAuth:
    def test_login_with_valid_credentials_returns_200_and_sets_session(self, api_client, user):
        response = api_client.post(
            "/api/v1/auth/login", {"email": user.email, "password": "testpass1"}, format="json"
        )
        assert response.status_code == 200
        assert response.json()["email"] == user.email
        assert "sessionid" in response.cookies

    def test_login_with_invalid_password_returns_401(self, api_client, user):
        response = api_client.post(
            "/api/v1/auth/login", {"email": user.email, "password": "wrong"}, format="json"
        )
        assert response.status_code == 401

    def test_login_with_unknown_email_returns_401(self, api_client):
        response = api_client.post(
            "/api/v1/auth/login",
            {"email": "ghost@example.com", "password": "anything"},
            format="json",
        )
        assert response.status_code == 401

    def test_logout_clears_session(self, authed_client):
        response = authed_client.post("/api/v1/auth/logout")
        assert response.status_code == 204

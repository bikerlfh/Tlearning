import pytest

from accounts.models import User


@pytest.mark.django_db
class TestSignup:
    url = "/api/v1/auth/signup"

    def test_signup_creates_user_and_returns_201(self, api_client):
        response = api_client.post(
            self.url,
            {"email": "new@example.com", "password": "securepass1"},
            format="json",
        )
        assert response.status_code == 201
        assert response.json()["email"] == "new@example.com"
        assert "id" in response.json()
        assert "password" not in response.json()
        assert User.objects.filter(email="new@example.com").exists()

    def test_signup_returns_400_on_short_password(self, api_client):
        response = api_client.post(
            self.url,
            {"email": "new@example.com", "password": "short"},
            format="json",
        )
        assert response.status_code == 400
        assert "password" in str(response.json()).lower()

    def test_signup_returns_400_on_duplicate_email(self, api_client, user):
        response = api_client.post(
            self.url,
            {"email": user.email, "password": "securepass1"},
            format="json",
        )
        assert response.status_code == 400

    def test_signup_returns_400_on_invalid_email(self, api_client):
        response = api_client.post(
            self.url,
            {"email": "not-an-email", "password": "securepass1"},
            format="json",
        )
        assert response.status_code == 400

import pytest

from accounts.models import ApiToken
from accounts.tokens import generate_token, hash_token


@pytest.mark.django_db
class TestApiTokenAuth:
    def test_valid_token_authenticates_request(self, api_client, user):
        raw = generate_token()
        ApiToken.objects.create(user=user, token_hash=hash_token(raw), name="t")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {raw}")
        response = api_client.get("/api/v1/auth/me")
        assert response.status_code == 200
        assert response.json()["email"] == user.email

    def test_invalid_token_returns_401(self, api_client):
        api_client.credentials(HTTP_AUTHORIZATION="Bearer tl_live_invalidtoken123")
        response = api_client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_missing_prefix_skips_token_auth(self, api_client):
        api_client.credentials(HTTP_AUTHORIZATION="Bearer just-a-string")
        response = api_client.get("/api/v1/auth/me")
        assert response.status_code in (401, 403)

    def test_revoked_token_rejected(self, api_client, user):
        from django.utils import timezone

        raw = generate_token()
        ApiToken.objects.create(
            user=user, token_hash=hash_token(raw), name="t", revoked_at=timezone.now()
        )
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {raw}")
        response = api_client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_valid_token_updates_last_used_at(self, api_client, user):
        raw = generate_token()
        token = ApiToken.objects.create(user=user, token_hash=hash_token(raw), name="t")
        assert token.last_used_at is None
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {raw}")
        api_client.get("/api/v1/auth/me")
        token.refresh_from_db()
        assert token.last_used_at is not None

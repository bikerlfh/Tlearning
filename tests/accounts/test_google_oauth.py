from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

import pytest
from allauth.socialaccount.models import SocialAccount

from accounts import oauth
from accounts.models import User

PROVIDER_OVERRIDE = {
    "google": {
        "APP": {"client_id": "test-client-id", "secret": "test-secret", "key": ""},
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {"access_type": "online"},
    },
}


@pytest.fixture
def google_provider(settings):
    settings.SOCIALACCOUNT_PROVIDERS = PROVIDER_OVERRIDE
    settings.FRONTEND_URL = "http://localhost:3000"
    return PROVIDER_OVERRIDE


@pytest.mark.django_db
class TestGoogleBegin:
    url = "/api/v1/auth/google/begin"

    def test_returns_auth_url_and_state_cookie(self, api_client, google_provider):
        response = api_client.get(self.url)
        assert response.status_code == 200
        url = response.json()["url"]
        assert url.startswith("https://accounts.google.com/o/oauth2/v2/auth?")
        params = parse_qs(urlparse(url).query)
        assert params["client_id"] == ["test-client-id"]
        assert params["redirect_uri"][0].endswith("/api/v1/auth/google/callback")
        assert params["response_type"] == ["code"]
        assert "openid" in params["scope"][0]
        assert "state" in params
        assert "oauth_state" in response.cookies
        assert response.cookies["oauth_state"].value == params["state"][0]

    def test_state_is_signed_and_round_trippable(self, api_client, google_provider):
        response = api_client.get(self.url)
        state = response.cookies["oauth_state"].value
        payload = oauth.verify_state(state)
        assert "nonce" in payload


@pytest.mark.django_db
class TestGoogleCallback:
    url = "/api/v1/auth/google/callback"

    def _stub_google(
        self, code="auth-code", email="newuser@example.com", sub="g-sub-123", verified=True
    ):
        return (
            patch.object(
                oauth,
                "exchange_code_for_token",
                return_value={"access_token": "at-test", "token_type": "Bearer"},
            ),
            patch.object(
                oauth,
                "fetch_userinfo",
                return_value={
                    "sub": sub,
                    "email": email,
                    "email_verified": verified,
                    "name": "New User",
                },
            ),
        )

    def _begin(self, api_client):
        return api_client.get("/api/v1/auth/google/begin").cookies["oauth_state"].value

    def test_happy_path_new_user(self, api_client, google_provider):
        state = self._begin(api_client)
        p_token, p_userinfo = self._stub_google()
        with p_token, p_userinfo:
            response = api_client.get(self.url, {"code": "auth-code", "state": state})
        assert response.status_code == 302
        assert response.url.endswith("/dashboard")
        assert User.objects.filter(email="newuser@example.com").exists()
        assert SocialAccount.objects.filter(provider="google", uid="g-sub-123").exists()

    def test_happy_path_existing_user_by_email(self, api_client, user, google_provider):
        state = self._begin(api_client)
        p_token, p_userinfo = self._stub_google(email=user.email, sub="g-sub-existing")
        with p_token, p_userinfo:
            response = api_client.get(self.url, {"code": "auth-code", "state": state})
        assert response.status_code == 302
        assert response.url.endswith("/dashboard")
        assert User.objects.filter(email=user.email).count() == 1
        assert SocialAccount.objects.filter(user=user, provider="google").exists()

    def test_missing_code_redirects_with_error(self, api_client, google_provider):
        response = api_client.get(self.url, {"state": "anything"})
        assert response.status_code == 302
        assert "oauth_state" in response.url

    def test_state_mismatch_redirects_with_error(self, api_client, google_provider):
        self._begin(api_client)
        response = api_client.get(self.url, {"code": "auth-code", "state": "wrong-state"})
        assert response.status_code == 302
        assert "oauth_state" in response.url

    def test_unverified_email_redirects_with_error(self, api_client, google_provider):
        state = self._begin(api_client)
        p_token, p_userinfo = self._stub_google(verified=False)
        with p_token, p_userinfo:
            response = api_client.get(self.url, {"code": "auth-code", "state": state})
        assert response.status_code == 302
        assert "oauth_email" in response.url

"""Google OAuth helpers — direct HTTP against Google's OAuth2 endpoints.

We rely on django-allauth for the `SocialAccount` data model and admin
integration but call Google's well-known endpoints directly to avoid
allauth's evolving high-level API.
"""

from __future__ import annotations

import secrets
from typing import Any
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.core import signing

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

STATE_MAX_AGE = 600  # 10 minutes


def sign_state(nonce: str | None = None) -> str:
    return signing.dumps({"nonce": nonce or secrets.token_urlsafe(16)})


def verify_state(state: str) -> dict[str, Any]:
    """Returns the decoded state payload. Raises ``signing.BadSignature`` /
    ``signing.SignatureExpired`` on invalid/expired tokens."""
    return signing.loads(state, max_age=STATE_MAX_AGE)


def build_auth_url(redirect_uri: str, state: str) -> str:
    provider_cfg = settings.SOCIALACCOUNT_PROVIDERS.get("google", {})
    client_id = provider_cfg.get("APP", {}).get("client_id", "")
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "online",
        "prompt": "select_account",
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


def exchange_code_for_token(code: str, redirect_uri: str) -> dict[str, Any]:
    provider_cfg = settings.SOCIALACCOUNT_PROVIDERS.get("google", {})
    client_id = provider_cfg.get("APP", {}).get("client_id", "")
    client_secret = provider_cfg.get("APP", {}).get("secret", "")
    resp = requests.post(
        GOOGLE_TOKEN_URL,
        data={
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        },
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def fetch_userinfo(access_token: str) -> dict[str, Any]:
    resp = requests.get(
        GOOGLE_USERINFO_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()

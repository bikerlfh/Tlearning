import pytest

from accounts.models import ApiToken
from accounts.tokens import generate_token, hash_token
from mcp_server.middleware import set_user_from_auth_header


@pytest.mark.django_db
def test_set_user_from_auth_header_sets_user(user):
    raw = generate_token()
    ApiToken.objects.create(user=user, token_hash=hash_token(raw), name="t")
    assert set_user_from_auth_header(f"Bearer {raw}") == user


@pytest.mark.django_db
def test_set_user_from_auth_header_invalid_returns_none():
    assert set_user_from_auth_header("Bearer tl_live_invalid") is None


def test_set_user_from_auth_header_missing_returns_none():
    assert set_user_from_auth_header("") is None
    assert set_user_from_auth_header(None) is None

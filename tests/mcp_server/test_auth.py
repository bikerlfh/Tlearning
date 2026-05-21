import pytest

from accounts.models import ApiToken
from accounts.tokens import generate_token, hash_token
from mcp_server.auth import authenticate_token, current_user


@pytest.mark.django_db
def test_authenticate_token_returns_user(user):
    raw = generate_token()
    ApiToken.objects.create(user=user, token_hash=hash_token(raw), name="t")
    assert authenticate_token(raw) == user


@pytest.mark.django_db
def test_authenticate_token_invalid_returns_none():
    assert authenticate_token("tl_live_nope") is None


@pytest.mark.django_db
def test_authenticate_token_revoked_returns_none(user):
    from django.utils import timezone

    raw = generate_token()
    ApiToken.objects.create(
        user=user,
        token_hash=hash_token(raw),
        name="t",
        revoked_at=timezone.now(),
    )
    assert authenticate_token(raw) is None


@pytest.mark.django_db
def test_current_user_contextvar_get_set(user):
    from mcp_server.auth import set_current_user

    set_current_user(user)
    assert current_user() == user


def test_current_user_set_none_returns_none():
    from mcp_server.auth import set_current_user

    set_current_user(None)
    assert current_user() is None

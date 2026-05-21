"""Authentication for MCP server.

Bearer token validated against ApiToken table (same model as REST API).
ContextVar stores the User so tool functions read it without explicit args.
"""

import contextvars

from django.utils import timezone

from accounts.models import ApiToken
from accounts.tokens import TOKEN_PREFIX, hash_token

_current_user: contextvars.ContextVar = contextvars.ContextVar("mcp_current_user")


def authenticate_token(raw: str):
    if not raw or not raw.startswith(TOKEN_PREFIX):
        return None
    try:
        tok = ApiToken.objects.select_related("user").get(
            token_hash=hash_token(raw), revoked_at__isnull=True
        )
    except ApiToken.DoesNotExist:
        return None
    tok.last_used_at = timezone.now()
    tok.save(update_fields=["last_used_at"])
    return tok.user


def set_current_user(user) -> None:
    _current_user.set(user)


def current_user():
    return _current_user.get()

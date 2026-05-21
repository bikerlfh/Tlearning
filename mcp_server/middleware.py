"""HTTP middleware helper: extracts Bearer token, sets current_user contextvar."""

from .auth import authenticate_token, set_current_user

BEARER_PREFIX = "Bearer "


def set_user_from_auth_header(authorization):
    """Validate the Authorization header, return user (and set contextvar)."""
    if not authorization or not authorization.startswith(BEARER_PREFIX):
        set_current_user(None)
        return None
    raw = authorization[len(BEARER_PREFIX) :]
    user = authenticate_token(raw)
    set_current_user(user)
    return user

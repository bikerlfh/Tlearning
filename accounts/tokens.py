import hashlib
import secrets

TOKEN_PREFIX = "tl_live_"
TOKEN_RANDOM_LEN = 32


def generate_token() -> str:
    return TOKEN_PREFIX + secrets.token_urlsafe(TOKEN_RANDOM_LEN)[:TOKEN_RANDOM_LEN]


def hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()

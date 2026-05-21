import pytest

from accounts.models import ApiToken
from accounts.tokens import generate_token, hash_token


@pytest.mark.django_db
class TestApiToken:
    def test_generate_token_has_prefix_and_length(self):
        raw = generate_token()
        assert raw.startswith("tl_live_")
        assert len(raw) == len("tl_live_") + 32

    def test_hash_token_is_deterministic(self):
        raw = "tl_live_" + "a" * 32
        assert hash_token(raw) == hash_token(raw)
        assert hash_token(raw) != hash_token("tl_live_" + "b" * 32)

    def test_apitoken_create_stores_hash_only(self, user):
        raw = generate_token()
        token = ApiToken.objects.create(user=user, token_hash=hash_token(raw), name="Test")
        assert token.token_hash != raw
        assert len(token.token_hash) == 64  # sha256 hex

    def test_apitoken_str(self, user):
        token = ApiToken.objects.create(user=user, token_hash="x" * 64, name="Claude Desktop")
        assert "Claude Desktop" in str(token)

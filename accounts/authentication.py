from django.utils import timezone
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from .models import ApiToken
from .tokens import TOKEN_PREFIX, hash_token


class ApiTokenAuthentication(BaseAuthentication):
    keyword = "Bearer"

    def authenticate(self, request):
        header = request.META.get("HTTP_AUTHORIZATION", "")
        if not header.startswith(f"{self.keyword} "):
            return None
        raw = header[len(self.keyword) + 1 :].strip()
        if not raw.startswith(TOKEN_PREFIX):
            return None  # let other auth handlers try

        try:
            token = ApiToken.objects.select_related("user").get(
                token_hash=hash_token(raw), revoked_at__isnull=True
            )
        except ApiToken.DoesNotExist as e:
            raise AuthenticationFailed("Invalid or revoked token.") from e

        token.last_used_at = timezone.now()
        token.save(update_fields=["last_used_at"])
        return (token.user, token)

    def authenticate_header(self, request) -> str:
        return self.keyword

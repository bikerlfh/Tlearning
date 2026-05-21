from django.conf import settings
from django.db import connection
from django.http import Http404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes: list = []

    def get(self, request):
        checks = {"db": False, "redis": False}
        try:
            with connection.cursor() as cur:
                cur.execute("SELECT 1")
            checks["db"] = True
        except Exception:
            pass
        try:
            import redis as redis_lib

            broker_url = getattr(settings, "CELERY_BROKER_URL", "")
            if broker_url:
                client = redis_lib.Redis.from_url(broker_url, socket_connect_timeout=1)
                client.ping()
                checks["redis"] = True
        except Exception:
            pass
        all_ok = all(checks.values())
        body = {
            "status": "ok" if all_ok else "degraded",
            "checks": checks,
        }
        return Response(
            body, status=status.HTTP_200_OK if all_ok else status.HTTP_503_SERVICE_UNAVAILABLE
        )


class SentryDebugView(APIView):
    """Dev-only: deliberately raises to verify Sentry plumbing.

    Only enabled when ``DEBUG=True`` so it can never leak into production traffic.
    """

    permission_classes = [permissions.AllowAny]
    authentication_classes: list = []

    def get(self, request):
        if not settings.DEBUG:
            raise Http404()
        raise RuntimeError("Sentry smoke test from /api/v1/_debug/sentry")

"""Project-wide Django middleware."""

from __future__ import annotations

import uuid
from collections.abc import Callable

from django.http import HttpRequest, HttpResponse


class RequestIdMiddleware:
    """Attach a stable request id to every request/response.

    - Honors an incoming ``X-Request-Id`` header (if present) so an upstream
      proxy / observability layer can propagate the same id.
    - Generates a fresh UUIDv4 otherwise.
    - Exposes the id on ``request.request_id`` for in-process consumers.
    - Echoes the id back as the ``X-Request-Id`` response header.
    - Sets a Sentry tag when ``sentry_sdk`` is installed and initialized.
    """

    HEADER = "X-Request-Id"
    REQUEST_ATTR = "request_id"

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        rid = request.headers.get(self.HEADER) or str(uuid.uuid4())
        setattr(request, self.REQUEST_ATTR, rid)

        try:
            from sentry_sdk import set_tag  # type: ignore[import-not-found]

            set_tag("request_id", rid)
        except Exception:
            pass

        response = self.get_response(request)
        response[self.HEADER] = rid
        return response

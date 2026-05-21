"""Run the Tlearning MCP server over streamable-HTTP with bearer auth.

Usage:
  uv run python -m mcp_server [--host 0.0.0.0] [--port 8765]

For local dev, run alongside the Django web server (different terminals).
For production, deploy as a second Fly machine sharing DATABASE_URL.
"""

import argparse
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tlearning.settings.dev")
django.setup()

from mcp_server.middleware import set_user_from_auth_header  # noqa: E402
from mcp_server.server import mcp  # noqa: E402


def _build_app():
    from starlette.middleware import Middleware
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.responses import JSONResponse

    class AuthMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            user = set_user_from_auth_header(request.headers.get("authorization"))
            if user is None:
                return JSONResponse({"error": "unauthorized"}, status_code=401)
            return await call_next(request)

    # fastmcp 3.3.1: http_app() accepts a `middleware` kwarg (list[ASGIMiddleware])
    # and returns a StarletteWithLifespan instance.
    return mcp.http_app(
        transport="streamable-http",
        middleware=[Middleware(AuthMiddleware)],
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    import uvicorn

    app = _build_app()
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()

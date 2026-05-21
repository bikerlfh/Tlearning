# Multi-stage build: uv installs deps into .venv, runtime is a slim Python image.
# The same image runs the Django web server, Celery worker/beat, and the MCP server —
# differentiated only by the CMD chosen in docker-compose.yml (or `fly.toml` in prod).

FROM python:3.12-slim AS builder

# Pull the uv binary from its official image.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# Build deps for native wheels (e.g. cryptography for pywebpush) — keep tiny.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install only runtime deps (no dev group) into /app/.venv from the lockfile.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev


FROM python:3.12-slim AS runtime

# Runtime libs only — psycopg needs libpq5; curl is handy for healthchecks.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Bring in the prepared virtualenv from the builder.
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DJANGO_SETTINGS_MODULE=tlearning.settings.dev

# Application source. docker-compose's bind mount will overlay this in dev,
# but copying ensures the image is self-contained (works on Fly or any host).
COPY . .

# Default ports used by web (8000) and MCP server (8765).
EXPOSE 8000 8765

# Default command runs the Django web server. docker-compose overrides this
# for worker/beat/mcp services.
CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn tlearning.wsgi:application --bind 0.0.0.0:8000 --workers 2 --access-logfile -"]

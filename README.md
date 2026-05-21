# Tlearning

Language learning review app with MCP ingestion. Words/idioms/phrasal_verbs you encounter while talking to Claude or Cursor land in your review queue automatically.

## Local dev — Docker (recommended)

Brings up the whole stack (Postgres, Redis, Django web, Celery worker, Celery beat, MCP server) with one command:

```bash
docker compose up -d --build
```

Services exposed on the host:

| Service | URL / port | Purpose |
|---|---|---|
| `web` | http://localhost:8000 | Django REST API + Swagger UI at `/api/v1/docs/` |
| `mcp` | http://localhost:8765/mcp | MCP server (bearer-auth) for Claude Desktop / Cursor |
| `postgres` | localhost:5432 | DB |
| `redis` | localhost:6379 | Celery broker |
| `worker` | (no port) | Celery worker — processes notifications |
| `beat` | (no port) | Celery beat — fires `schedule_notifications_tick` every minute |

```bash
docker compose ps              # health overview
docker compose logs -f web     # tail web logs
docker compose down            # stop everything (data persists in postgres_data volume)
docker compose down -v         # nuke including DB
```

The image bind-mounts the project source for hot reload (`gunicorn --reload`). An anonymous volume keeps `/app/.venv` from being shadowed by the host's `.venv`.

A superuser for the admin:

```bash
docker compose exec web python manage.py createsuperuser
```

## Local dev — without Docker (host)

If you'd rather run Django on the host (faster iteration on tests):

```bash
docker compose up -d postgres redis   # just the data services
uv sync
cp .env.example .env
uv run python manage.py migrate
uv run python manage.py runserver
```

Run the MCP server in a separate terminal:

```bash
uv run python -m mcp_server --port 8765
```

This validates the same `tl_live_` API tokens used by the REST API.

### Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "tlearning": {
      "url": "http://localhost:8765/mcp",
      "headers": {
        "Authorization": "Bearer tl_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
      }
    }
  }
}
```

Restart Claude Desktop. The tools `remember_word`, `find_word`, `mark_as_known`, `list_due_today` will be available.

### Cursor

Add to `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "tlearning": {
      "url": "http://localhost:8765/mcp",
      "headers": {
        "Authorization": "Bearer tl_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
      }
    }
  }
}
```

### Generating a token

Via curl after logging in (cookie-jar `cookies.txt`):

```bash
curl -X POST http://localhost:8000/api/v1/auth/api-tokens \
  -b cookies.txt -H "Content-Type: application/json" \
  -d '{"name":"Claude Desktop"}'
```

The raw token is shown ONCE in the response. Can't be recovered later — only regenerated.

## Frontend (Next.js PWA)

The user-facing app lives in `frontend/` — a separate Next.js 16 codebase that talks to Django at `NEXT_PUBLIC_API_BASE_URL` (default `http://localhost:8000`).

```bash
cd frontend
pnpm install
pnpm dev
```

Open <http://localhost:3000>. Sign up, then visit `/settings/api-tokens` to generate a Bearer token for Claude Desktop / Cursor (see the MCP section above).

To enable web push on this device, copy the backend's `VAPID_PUBLIC_KEY` into `frontend/.env.local` as `NEXT_PUBLIC_VAPID_PUBLIC_KEY` and click "Enable push notifications" in `/settings/notifications`.

Builds and dev use webpack explicitly (`--webpack`) because `next-pwa@5` is not yet Turbopack-compatible.

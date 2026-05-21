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

### Routes shipped

| Path | Purpose |
|---|---|
| `/login`, `/signup` | Cookie session auth (+ Continue with Google) |
| `/forgot-password`, `/reset-password` | Email-based password reset |
| `/dashboard` | Greeting, due-today, stat cards, recently added |
| `/study` | FSRS flashcard mode (Space + 1-4 keyboard, swipe gestures on mobile, accepts `?deck_id=`) |
| `/library`, `/library/[id]` | Browse + filter + detail/edit (rename, examples, mark learned, suspend, delete) |
| `/decks`, `/decks/[id]` | CRUD + per-deck study link |
| `/stats` | KPIs, 90-day heatmap, retention curve, type/status distributions |
| `/settings` | Hub linking to profile, account (linked providers), api-tokens, integrations, notifications |

Mobile layout (<768px) replaces the sidebar with a bottom tab bar.

### PWA icons

```bash
cd frontend
pnpm icons   # regenerates public/icon-192.png and public/icon-512.png from public/icon.svg
```

### Offline behavior

`/study` works offline:

- Each review answer made while `navigator.onLine === false` is queued in IndexedDB (`tlearning.pending_answers`).
- The 20 cards loaded on /study mount are cached (`tlearning.cached_queue`) so the deck can be studied without network.
- When connectivity returns, the queue is flushed automatically — once via the Service Worker's `sync` event (Chrome/Android), and as a fallback once via `window.addEventListener("online")` (Safari/Firefox).

Push notifications post a click-through ping to `POST /api/v1/notifications/{log_id}/clicked` when the user taps the notification — used to track open rates.

### Text-to-speech

`/study` shows a speaker icon next to the lemma and binds the `A` key to it. Uses the browser's built-in Web Speech API (no extra dependency or cost). Voice is picked by mapping the artifact's `target_language` (e.g. `es`) to a BCP-47 tag (`es-ES`).

### Frontend testing

```bash
cd frontend
pnpm test                              # vitest watch mode
pnpm test:run                          # CI mode (single run)
pnpm test:coverage                     # HTML report at coverage/index.html
```

End-to-end (needs `docker compose up -d` postgres+redis+web):

```bash
pnpm exec playwright install chromium  # one-time
pnpm exec playwright test
pnpm exec playwright show-report
```

CI runs both vitest (`unit` job) and Playwright (`e2e` job) on every PR via `.github/workflows/frontend.yml`.

## Authentication

Email + password (`POST /api/v1/auth/{signup,login,logout}`) is the default. Two more flows are available:

### Google OAuth

1. Create an OAuth client at <https://console.cloud.google.com/apis/credentials> (type: "Web application").
2. Authorized JavaScript origins: `http://localhost:8000`, `http://localhost:3000`.
3. Authorized redirect URI: `http://localhost:8000/api/v1/auth/google/callback`.
4. Drop the values into `.env`:

```bash
GOOGLE_OAUTH_CLIENT_ID=...
GOOGLE_OAUTH_CLIENT_SECRET=...
FRONTEND_URL=http://localhost:3000
```

The frontend's "Continue with Google" button on `/login` and `/signup` calls `GET /api/v1/auth/google/begin`, gets the auth URL, redirects the browser to Google, and Google calls back to `/api/v1/auth/google/callback` which logs the user in and redirects to `${FRONTEND_URL}/dashboard`.

Linked providers can be viewed and disconnected from `/settings/account`. Disconnecting your only sign-in method is blocked — set a password first via "Forgot password" if needed.

### Password reset

`POST /api/v1/auth/password-reset/request` always returns 204 (never confirms whether an email exists). In dev, the reset link prints to the Django server's stdout. The frontend pages are `/forgot-password` and `/reset-password`. Email backend defaults to console in dev; in prod (`tlearning.settings.prod`) it switches to Resend SMTP.

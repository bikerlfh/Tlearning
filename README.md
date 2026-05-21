# Tlearning

Language learning review app with MCP ingestion. Words/idioms/phrasal_verbs you encounter while talking to Claude or Cursor land in your review queue automatically.

## Local dev

```bash
docker compose up -d postgres
uv sync
cp .env.example .env
uv run python manage.py migrate
uv run python manage.py runserver
```

Web API: http://localhost:8000/api/v1/docs/

## MCP server (Claude Desktop, Cursor, Continue, etc.)

In a separate terminal:

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

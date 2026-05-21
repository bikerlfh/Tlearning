"use client";

import Link from "next/link";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

const CLAUDE_DESKTOP_CONFIG = `{
  "mcpServers": {
    "tlearning": {
      "url": "${API_BASE}/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_TOKEN_HERE"
      }
    }
  }
}`;

const CURSOR_CONFIG = `{
  "mcpServers": {
    "tlearning": {
      "url": "${API_BASE}/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_TOKEN_HERE"
      }
    }
  }
}`;

const CUSTOM_GPT_INSTRUCTIONS = `1. In ChatGPT, create a new GPT and go to "Configure" → "Actions".
2. Set the API endpoint to: ${API_BASE}/api/v1
3. Authentication: API Key, Auth Type: Bearer
4. Paste your token from the API tokens page.
5. Import the OpenAPI schema from: ${API_BASE}/api/v1/schema/`;

function CopyButton({ value, label }: { value: string; label: string }) {
  return (
    <Button
      size="sm"
      variant="outline"
      onClick={() => {
        navigator.clipboard.writeText(value);
        toast.success(`${label} copied`);
      }}
    >
      Copy
    </Button>
  );
}

export default function IntegrationsPage() {
  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Integrations</h1>
        <p className="text-slate-600">
          Connect Tlearning to MCP clients. First,{" "}
          <Link href="/settings/api-tokens" className="underline">
            generate an API token
          </Link>{" "}
          and replace <code>YOUR_TOKEN_HERE</code> below.
        </p>
      </div>

      <Card className="p-4 space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="font-bold">Claude Desktop</h2>
          <CopyButton value={CLAUDE_DESKTOP_CONFIG} label="Claude Desktop config" />
        </div>
        <p className="text-sm text-slate-600">
          Add this to your <code>claude_desktop_config.json</code>:
        </p>
        <pre className="text-xs bg-slate-900 text-slate-100 p-3 rounded overflow-x-auto">
          {CLAUDE_DESKTOP_CONFIG}
        </pre>
      </Card>

      <Card className="p-4 space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="font-bold">Cursor</h2>
          <CopyButton value={CURSOR_CONFIG} label="Cursor config" />
        </div>
        <p className="text-sm text-slate-600">
          Add this to <code>~/.cursor/mcp.json</code>:
        </p>
        <pre className="text-xs bg-slate-900 text-slate-100 p-3 rounded overflow-x-auto">
          {CURSOR_CONFIG}
        </pre>
      </Card>

      <Card className="p-4 space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="font-bold">Custom GPT (ChatGPT Actions)</h2>
          <CopyButton
            value={CUSTOM_GPT_INSTRUCTIONS}
            label="Custom GPT setup steps"
          />
        </div>
        <pre className="text-xs bg-slate-50 border p-3 rounded whitespace-pre-wrap">
          {CUSTOM_GPT_INSTRUCTIONS}
        </pre>
      </Card>
    </div>
  );
}

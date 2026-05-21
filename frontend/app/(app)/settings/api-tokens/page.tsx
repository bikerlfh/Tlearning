"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { api, ApiError } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

interface Token {
  id: string;
  name: string;
  last_used_at: string | null;
  created_at: string;
}

interface CreatedToken extends Token {
  token: string;
}

interface TokenList {
  count: number;
  results: Token[];
}

export default function ApiTokensPage() {
  const qc = useQueryClient();
  const [name, setName] = useState("");
  const [newToken, setNewToken] = useState<string | null>(null);

  const list = useQuery({
    queryKey: ["api-tokens"],
    queryFn: () => api.get<TokenList>("/api/v1/auth/api-tokens"),
  });

  const create = useMutation({
    mutationFn: (data: { name: string }) =>
      api.post<CreatedToken>("/api/v1/auth/api-tokens", data),
    onSuccess: (data) => {
      setNewToken(data.token);
      setName("");
      qc.invalidateQueries({ queryKey: ["api-tokens"] });
    },
    onError: (err) => {
      const msg =
        err instanceof ApiError ? err.message : "Failed to create token";
      toast.error(msg);
    },
  });

  const revoke = useMutation({
    mutationFn: (id: string) => api.delete(`/api/v1/auth/api-tokens/${id}`),
    onSuccess: () => {
      toast.success("Token revoked");
      qc.invalidateQueries({ queryKey: ["api-tokens"] });
    },
  });

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">API tokens</h1>
      <p className="text-slate-600">
        Use these to connect Claude Desktop, Cursor, or any MCP client. The raw
        token is shown only ONCE on creation — copy it immediately.
      </p>

      <Card className="p-4 space-y-3">
        <h2 className="font-bold">New token</h2>
        <div className="flex gap-2">
          <Input
            placeholder="e.g. 'Claude Desktop laptop'"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <Button
            type="button"
            onClick={() => create.mutate({ name })}
            disabled={!name.trim() || create.isPending}
          >
            {create.isPending ? "Generating…" : "Generate"}
          </Button>
        </div>
        {newToken && (
          <div className="p-3 bg-amber-50 border border-amber-300 rounded">
            <p className="text-xs font-bold text-amber-800 mb-1">
              ⚠️ Copy this token NOW — it won&apos;t be shown again.
            </p>
            <code className="block break-all text-sm bg-white p-2 rounded">
              {newToken}
            </code>
            <Button
              size="sm"
              variant="outline"
              className="mt-2"
              onClick={() => {
                navigator.clipboard.writeText(newToken);
                toast.success("Copied to clipboard");
              }}
            >
              Copy
            </Button>
          </div>
        )}
      </Card>

      <Card>
        <div className="p-4">
          <h2 className="font-bold">Your tokens</h2>
        </div>
        {list.isLoading && (
          <p className="px-4 pb-4 text-sm text-slate-500">Loading…</p>
        )}
        {list.data && list.data.results.length === 0 && (
          <p className="px-4 pb-4 text-sm text-slate-500">No tokens yet.</p>
        )}
        {list.data?.results.map((t) => (
          <div
            key={t.id}
            className="flex items-center justify-between px-4 py-3 border-t"
          >
            <div>
              <div className="font-medium">{t.name}</div>
              <div className="text-xs text-slate-500">
                Last used:{" "}
                {t.last_used_at
                  ? new Date(t.last_used_at).toLocaleString()
                  : "never"}
              </div>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => revoke.mutate(t.id)}
              disabled={revoke.isPending}
            >
              Revoke
            </Button>
          </div>
        ))}
      </Card>
    </div>
  );
}

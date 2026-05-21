"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { StatusBadge, TypeBadge } from "@/components/Badges";

interface Artifact {
  id: string;
  lemma: string;
  type: string;
  status: string;
  data: { meaning?: string };
  created_at: string;
  source: string;
}

interface ArtifactList {
  count: number;
  results: Artifact[];
}

const STATUSES = ["all", "pending", "in_progress", "learned", "suspended"] as const;
type Status = (typeof STATUSES)[number];

export default function LibraryPage() {
  const [q, setQ] = useState("");
  const [status, setStatus] = useState<Status>("all");

  const params = new URLSearchParams();
  if (q) params.set("q", q);
  if (status !== "all") params.set("status", status);

  const { data, isLoading } = useQuery({
    queryKey: ["library", q, status],
    queryFn: () =>
      api.get<ArtifactList>(`/api/v1/artifacts?${params.toString()}`),
  });

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold">Library</h1>
        <p className="text-slate-600">
          {data ? `${data.count} artifacts` : "—"}
        </p>
      </div>
      <Input
        placeholder="🔍 Search lemma or meaning…"
        value={q}
        onChange={(e) => setQ(e.target.value)}
      />
      <div className="flex gap-2 text-xs flex-wrap">
        {STATUSES.map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => setStatus(s)}
            className={`px-3 py-1 rounded-full font-semibold ${
              status === s
                ? "bg-indigo-600 text-white"
                : "bg-white border border-slate-200 hover:border-slate-300"
            }`}
          >
            {s.replace("_", " ")}
          </button>
        ))}
      </div>
      <Card className="overflow-hidden">
        {isLoading && <p className="p-4 text-sm text-slate-500">Loading…</p>}
        {data && data.results.length === 0 && (
          <p className="p-4 text-sm text-slate-500">No results.</p>
        )}
        {data?.results.map((a) => (
          <Link
            key={a.id}
            href={`/library/${a.id}`}
            className="grid grid-cols-[2fr_1fr_1fr_auto] gap-4 p-3 hover:bg-slate-50 border-b last:border-b-0 items-center"
          >
            <div className="min-w-0">
              <div className="font-semibold truncate">{a.lemma}</div>
              <div className="text-xs text-slate-500 truncate">
                {a.data?.meaning ?? ""}
              </div>
            </div>
            <TypeBadge type={a.type} />
            <StatusBadge status={a.status} />
            <span className="text-xs text-slate-400 self-center">
              {a.source}
            </span>
          </Link>
        ))}
      </Card>
    </div>
  );
}

"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useMe } from "@/hooks/useAuth";
import { StatusBadge, TypeBadge } from "@/components/Badges";

interface Artifact {
  id: string;
  lemma: string;
  type: string;
  status: string;
  created_at: string;
}

interface ArtifactList {
  count: number;
  results: Artifact[];
  next?: string | null;
  previous?: string | null;
}

interface QueueResult {
  count: number;
  results: Array<{ id: string; lemma: string }>;
}

export default function DashboardPage() {
  const { data: me } = useMe();
  const queue = useQuery({
    queryKey: ["queue", "summary"],
    queryFn: () => api.get<QueueResult>("/api/v1/reviews/queue?limit=1"),
  });
  const pending = useQuery({
    queryKey: ["artifacts", "pending"],
    queryFn: () =>
      api.get<ArtifactList>("/api/v1/artifacts?status=pending"),
  });
  const inProgress = useQuery({
    queryKey: ["artifacts", "in_progress"],
    queryFn: () =>
      api.get<ArtifactList>("/api/v1/artifacts?status=in_progress"),
  });
  const learned = useQuery({
    queryKey: ["artifacts", "learned"],
    queryFn: () =>
      api.get<ArtifactList>("/api/v1/artifacts?status=learned"),
  });
  const recent = useQuery({
    queryKey: ["artifacts", "recent"],
    queryFn: () =>
      api.get<ArtifactList>("/api/v1/artifacts?page_size=5"),
  });

  const displayName = me?.name?.trim() || me?.email;
  const dueCount = queue.data?.count ?? 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Hi, {displayName}!</h1>
          {dueCount > 0 ? (
            <p className="text-slate-600">
              You have <strong>{dueCount} cards due</strong> today.
            </p>
          ) : (
            <p className="text-slate-600">Nothing due right now. 🎉</p>
          )}
        </div>
        <Link href="/study">
          <Button size="lg">▶ Study now</Button>
        </Link>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <Card className="p-4">
          <div className="text-xs uppercase text-slate-500">Pending</div>
          <div className="text-3xl font-bold text-indigo-600">
            {pending.data?.count ?? "—"}
          </div>
        </Card>
        <Card className="p-4">
          <div className="text-xs uppercase text-slate-500">In progress</div>
          <div className="text-3xl font-bold text-orange-600">
            {inProgress.data?.count ?? "—"}
          </div>
        </Card>
        <Card className="p-4">
          <div className="text-xs uppercase text-slate-500">Learned</div>
          <div className="text-3xl font-bold text-green-600">
            {learned.data?.count ?? "—"}
          </div>
        </Card>
      </div>

      <Card className="p-4">
        <h2 className="font-bold mb-2">Recently added</h2>
        {recent.isLoading && (
          <p className="text-sm text-slate-500">Loading…</p>
        )}
        {recent.data && recent.data.results.length === 0 && (
          <p className="text-sm text-slate-500">
            No artifacts yet. Connect Claude Desktop and start chatting.
          </p>
        )}
        <div className="space-y-2">
          {recent.data?.results.slice(0, 5).map((a) => (
            <div
              key={a.id}
              className="flex items-center justify-between p-2 hover:bg-slate-50 rounded"
            >
              <Link href={`/library/${a.id}`} className="font-medium">
                {a.lemma}
              </Link>
              <div className="flex gap-2">
                <TypeBadge type={a.type} />
                <StatusBadge status={a.status} />
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

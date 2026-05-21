"use client";

import { use } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { StatusBadge, TypeBadge } from "@/components/Badges";
import { useDeck } from "@/hooks/useDecks";

interface Artifact {
  id: string;
  lemma: string;
  type: string;
  status: string;
  data: { meaning?: string };
}

interface ArtifactList {
  count: number;
  results: Artifact[];
}

export default function DeckDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const deck = useDeck(id);
  const artifacts = useQuery({
    queryKey: ["deck-artifacts", id],
    queryFn: () => api.get<ArtifactList>(`/api/v1/artifacts?deck_id=${id}`),
    enabled: Boolean(id),
  });

  if (deck.isLoading) return <p className="text-sm text-slate-500">Loading…</p>;
  if (deck.isError || !deck.data) {
    return (
      <div className="space-y-3">
        <p className="text-sm text-red-600">Deck not found.</p>
        <Link href="/decks" className="underline text-sm">
          Back to decks
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-4">
      <Link href="/decks" className="text-sm underline text-slate-600">
        ← Decks
      </Link>
      <Card className="p-6 space-y-2">
        <h1 className="text-2xl font-bold">{deck.data.name}</h1>
        <div className="text-sm text-slate-600">
          {deck.data.source_language} → {deck.data.target_language}
          {deck.data.is_default ? " · default" : ""}
        </div>
        <div className="text-sm text-slate-600">
          {deck.data.artifact_count} artifacts
        </div>
        <Link href={`/study?deck_id=${id}`} className="inline-block pt-2">
          <Button>▶ Study this deck</Button>
        </Link>
      </Card>

      <Card>
        <div className="p-4">
          <h2 className="font-bold">
            Artifacts {artifacts.data ? `(${artifacts.data.count})` : ""}
          </h2>
        </div>
        {artifacts.isLoading && (
          <p className="px-4 pb-4 text-sm text-slate-500">Loading…</p>
        )}
        {artifacts.data && artifacts.data.count === 0 && (
          <p className="px-4 pb-4 text-sm text-slate-500">
            No artifacts in this deck yet.
          </p>
        )}
        {artifacts.data?.results.map((a) => (
          <Link
            key={a.id}
            href={`/library/${a.id}`}
            className="grid grid-cols-[2fr_1fr_1fr] gap-4 p-3 hover:bg-slate-50 border-t items-center"
          >
            <div className="min-w-0">
              <div className="font-semibold truncate">{a.lemma}</div>
              <div className="text-xs text-slate-500 truncate">
                {a.data?.meaning ?? ""}
              </div>
            </div>
            <TypeBadge type={a.type} />
            <StatusBadge status={a.status} />
          </Link>
        ))}
      </Card>
    </div>
  );
}

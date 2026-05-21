"use client";

import { useState } from "react";
import Link from "next/link";
import { toast } from "sonner";
import { ApiError } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  useCreateDeck,
  useDecks,
  useDeleteDeck,
  useUpdateDeck,
} from "@/hooks/useDecks";

const LANG_DEFAULTS = { source: "en", target: "es" };

function NewDeckForm({ onCreated }: { onCreated: () => void }) {
  const [name, setName] = useState("");
  const [src, setSrc] = useState(LANG_DEFAULTS.source);
  const [tgt, setTgt] = useState(LANG_DEFAULTS.target);
  const create = useCreateDeck();

  return (
    <Card className="p-4 space-y-3">
      <h2 className="font-bold">New deck</h2>
      <div className="grid grid-cols-1 md:grid-cols-[2fr_1fr_1fr_auto] gap-2 items-end">
        <div className="grid gap-1">
          <Label htmlFor="deck-name">Name</Label>
          <Input
            id="deck-name"
            placeholder="e.g. Spanish daily"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
        </div>
        <div className="grid gap-1">
          <Label htmlFor="deck-src">From</Label>
          <Input
            id="deck-src"
            value={src}
            onChange={(e) => setSrc(e.target.value.trim().toLowerCase())}
          />
        </div>
        <div className="grid gap-1">
          <Label htmlFor="deck-tgt">To</Label>
          <Input
            id="deck-tgt"
            value={tgt}
            onChange={(e) => setTgt(e.target.value.trim().toLowerCase())}
          />
        </div>
        <Button
          type="button"
          onClick={() =>
            create.mutate(
              { name: name.trim(), source_language: src, target_language: tgt },
              {
                onSuccess: () => {
                  setName("");
                  toast.success("Deck created");
                  onCreated();
                },
                onError: (err) => {
                  if (err instanceof ApiError) toast.error(err.message);
                  else toast.error("Could not create deck");
                },
              },
            )
          }
          disabled={!name.trim() || create.isPending}
        >
          {create.isPending ? "Creating…" : "Create"}
        </Button>
      </div>
    </Card>
  );
}

function DeckRow({ id, name, source_language, target_language, is_default, artifact_count }: {
  id: string;
  name: string;
  source_language: string;
  target_language: string;
  is_default: boolean;
  artifact_count: number;
}) {
  const update = useUpdateDeck(id);
  const remove = useDeleteDeck();
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(name);

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-3 border-t">
      {editing ? (
        <div className="flex flex-1 min-w-[200px] gap-2">
          <Input value={draft} onChange={(e) => setDraft(e.target.value)} />
          <Button
            type="button"
            onClick={() =>
              update.mutate(
                { name: draft.trim() },
                {
                  onSuccess: () => {
                    setEditing(false);
                    toast.success("Renamed");
                  },
                  onError: () => toast.error("Rename failed"),
                },
              )
            }
            disabled={!draft.trim() || update.isPending}
          >
            {update.isPending ? "Saving…" : "Save"}
          </Button>
          <Button variant="outline" type="button" onClick={() => setEditing(false)}>
            Cancel
          </Button>
        </div>
      ) : (
        <>
          <div className="flex-1 min-w-[200px]">
            <Link href={`/decks/${id}`} className="font-medium hover:underline">
              {name}
            </Link>
            <div className="text-xs text-slate-500">
              {source_language} → {target_language} · {artifact_count} artifacts
              {is_default ? " · default" : ""}
            </div>
          </div>
          <div className="flex gap-2">
            <Link href={`/study?deck_id=${id}`}>
              <Button size="sm">Study</Button>
            </Link>
            <Button size="sm" variant="outline" onClick={() => setEditing(true)}>
              Rename
            </Button>
            <Button
              size="sm"
              variant="outline"
              className="text-red-600 hover:bg-red-50"
              onClick={() => {
                if (is_default) {
                  toast.error("Can't delete the default deck.");
                  return;
                }
                if (!window.confirm(`Delete "${name}" and its artifacts?`)) return;
                remove.mutate(id, {
                  onSuccess: () => toast.success("Deleted"),
                  onError: () => toast.error("Delete failed"),
                });
              }}
              disabled={remove.isPending}
            >
              Delete
            </Button>
          </div>
        </>
      )}
    </div>
  );
}

export default function DecksPage() {
  const { data, isLoading } = useDecks();

  return (
    <div className="max-w-3xl mx-auto space-y-4">
      <div>
        <h1 className="text-2xl font-bold">Decks</h1>
        <p className="text-slate-600">
          Group artifacts by source and target language. Each user gets a
          default deck created automatically.
        </p>
      </div>
      <NewDeckForm onCreated={() => {}} />
      <Card>
        <div className="p-4">
          <h2 className="font-bold">
            Your decks {data ? `(${data.count})` : ""}
          </h2>
        </div>
        {isLoading && <p className="px-4 pb-4 text-sm text-slate-500">Loading…</p>}
        {data && data.count === 0 && (
          <p className="px-4 pb-4 text-sm text-slate-500">No decks yet.</p>
        )}
        {data?.results.map((d) => (
          <DeckRow
            key={d.id}
            id={d.id}
            name={d.name}
            source_language={d.source_language}
            target_language={d.target_language}
            is_default={d.is_default}
            artifact_count={d.artifact_count}
          />
        ))}
      </Card>
    </div>
  );
}

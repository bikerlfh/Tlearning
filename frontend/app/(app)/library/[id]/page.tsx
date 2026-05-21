"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { StatusBadge, TypeBadge } from "@/components/Badges";
import { ApiError } from "@/lib/api";
import {
  useArtifact,
  useDeleteArtifact,
  useMarkLearned,
  useSuspendArtifact,
  useUpdateArtifact,
} from "@/hooks/useArtifact";

interface DraftFields {
  lemma: string;
  meaning: string;
  examples: string;
}

function blankDraft(): DraftFields {
  return { lemma: "", meaning: "", examples: "" };
}

export default function ArtifactDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const router = useRouter();
  const { data: artifact, isLoading, isError } = useArtifact(id);
  const update = useUpdateArtifact(id);
  const markLearned = useMarkLearned(id);
  const suspend = useSuspendArtifact(id);
  const remove = useDeleteArtifact(id);

  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState<DraftFields>(blankDraft);

  useEffect(() => {
    if (artifact && !editing) {
      setDraft({
        lemma: artifact.lemma,
        meaning:
          typeof artifact.data?.meaning === "string"
            ? (artifact.data.meaning as string)
            : "",
        examples: Array.isArray(artifact.data?.examples)
          ? ((artifact.data.examples as unknown[]).filter(
              (e): e is string => typeof e === "string",
            ) as string[]).join("\n")
          : "",
      });
    }
  }, [artifact, editing]);

  if (isLoading) {
    return <p className="text-sm text-slate-500">Loading…</p>;
  }
  if (isError || !artifact) {
    return (
      <div className="space-y-3">
        <p className="text-sm text-red-600">Artifact not found.</p>
        <Link href="/library" className="underline text-sm">
          Back to library
        </Link>
      </div>
    );
  }

  const meaning =
    typeof artifact.data?.meaning === "string" ? artifact.data.meaning : "";
  const examples = Array.isArray(artifact.data?.examples)
    ? ((artifact.data.examples as unknown[]).filter(
        (e): e is string => typeof e === "string",
      ) as string[])
    : [];

  function save() {
    if (!artifact) return;
    update.mutate(
      {
        lemma: draft.lemma,
        data: {
          ...(artifact.data ?? {}),
          meaning: draft.meaning,
          examples: draft.examples
            .split("\n")
            .map((x) => x.trim())
            .filter(Boolean),
        },
      },
      {
        onSuccess: () => {
          setEditing(false);
          toast.success("Saved");
        },
        onError: (err) => {
          if (err instanceof ApiError) toast.error(err.message);
          else toast.error("Save failed");
        },
      },
    );
  }

  function onMarkLearned() {
    markLearned.mutate(undefined, {
      onSuccess: () => toast.success("Marked as learned"),
      onError: () => toast.error("Could not mark as learned"),
    });
  }
  function onSuspend() {
    suspend.mutate(undefined, {
      onSuccess: () => toast.success("Suspended"),
      onError: () => toast.error("Could not suspend"),
    });
  }
  function onDelete() {
    if (!window.confirm(`Delete "${artifact?.lemma}"? This cannot be undone.`)) {
      return;
    }
    remove.mutate(undefined, {
      onSuccess: () => {
        toast.success("Deleted");
        router.push("/library");
      },
      onError: () => toast.error("Delete failed"),
    });
  }

  return (
    <div className="max-w-2xl mx-auto space-y-4">
      <Link href="/library" className="text-sm underline text-slate-600">
        ← Library
      </Link>

      <Card className="p-6 space-y-3">
        <div className="flex flex-wrap items-center gap-3">
          {editing ? (
            <Input
              className="text-2xl font-bold flex-1 min-w-[200px]"
              value={draft.lemma}
              onChange={(e) => setDraft({ ...draft, lemma: e.target.value })}
            />
          ) : (
            <h1 className="text-2xl font-bold flex-1">{artifact.lemma}</h1>
          )}
          <TypeBadge type={artifact.type} />
          <StatusBadge status={artifact.status} />
        </div>

        {editing ? (
          <div className="space-y-3">
            <div className="grid gap-2">
              <Label htmlFor="meaning">Meaning</Label>
              <Input
                id="meaning"
                value={draft.meaning}
                onChange={(e) => setDraft({ ...draft, meaning: e.target.value })}
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="examples">Examples (one per line)</Label>
              <textarea
                id="examples"
                className="border rounded p-2 min-h-[110px] text-sm"
                value={draft.examples}
                onChange={(e) =>
                  setDraft({ ...draft, examples: e.target.value })
                }
              />
            </div>
            <div className="flex gap-2">
              <Button
                type="button"
                onClick={save}
                disabled={update.isPending}
              >
                {update.isPending ? "Saving…" : "Save"}
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => setEditing(false)}
              >
                Cancel
              </Button>
            </div>
          </div>
        ) : (
          <>
            {meaning && (
              <p className="text-slate-700 italic">{meaning}</p>
            )}
            {examples.length > 0 && (
              <div className="space-y-1">
                <div className="text-xs uppercase text-slate-500">Examples</div>
                {examples.map((ex, i) => (
                  <p key={i} className="text-sm">
                    • {ex}
                  </p>
                ))}
              </div>
            )}
          </>
        )}
      </Card>

      {!editing && (
        <Card className="p-4 space-y-2">
          <div className="text-xs uppercase text-slate-500 mb-1">Actions</div>
          <div className="flex flex-wrap gap-2">
            <Button type="button" onClick={() => setEditing(true)}>
              Edit
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={onMarkLearned}
              disabled={markLearned.isPending || artifact.status === "learned"}
            >
              Mark learned
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={onSuspend}
              disabled={suspend.isPending || artifact.status === "suspended"}
            >
              Suspend
            </Button>
            <Button
              type="button"
              variant="outline"
              className="text-red-600 hover:bg-red-50"
              onClick={onDelete}
              disabled={remove.isPending}
            >
              Delete
            </Button>
          </div>
        </Card>
      )}

      <Card className="p-4 text-xs text-slate-500 grid grid-cols-2 gap-y-1 gap-x-4">
        <span>Source</span>
        <span>{artifact.source}</span>
        <span>Languages</span>
        <span>
          {artifact.source_language} → {artifact.target_language}
        </span>
        <span>Created</span>
        <span>{new Date(artifact.created_at).toLocaleString()}</span>
        <span>Updated</span>
        <span>{new Date(artifact.updated_at).toLocaleString()}</span>
      </Card>
    </div>
  );
}

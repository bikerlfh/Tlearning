"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { StatusBadge, TypeBadge } from "@/components/Badges";

interface ReviewState {
  state: string;
  status: string;
  due_at: string;
  reps: number;
  lapses: number;
}

interface QueueCard {
  id: string;
  lemma: string;
  type: string;
  data: Record<string, unknown>;
  review_state: ReviewState;
}

interface QueueResult {
  count: number;
  results: QueueCard[];
}

interface AnswerResult {
  review_state: ReviewState;
  next_card: QueueCard | null;
}

const RATING_BUTTONS: Array<{ rating: 1 | 2 | 3 | 4; label: string; color: string }> = [
  { rating: 1, label: "Again", color: "bg-red-600 hover:bg-red-700" },
  { rating: 2, label: "Hard", color: "bg-orange-600 hover:bg-orange-700" },
  { rating: 3, label: "Good", color: "bg-green-600 hover:bg-green-700" },
  { rating: 4, label: "Easy", color: "bg-cyan-600 hover:bg-cyan-700" },
];

export default function StudyPage() {
  const qc = useQueryClient();
  const [revealed, setRevealed] = useState(false);
  const [current, setCurrent] = useState<QueueCard | null>(null);
  const [bootstrapped, setBootstrapped] = useState(false);
  const [sessionCount, setSessionCount] = useState(0);

  const queue = useQuery({
    queryKey: ["queue", "session"],
    queryFn: () => api.get<QueueResult>("/api/v1/reviews/queue?limit=20"),
    refetchOnMount: true,
  });

  useEffect(() => {
    if (!bootstrapped && queue.data) {
      setCurrent(queue.data.results[0] ?? null);
      setBootstrapped(true);
    }
  }, [queue.data, bootstrapped]);

  const answer = useMutation({
    mutationFn: ({ id, rating }: { id: string; rating: number }) =>
      api.post<AnswerResult>(`/api/v1/reviews/${id}/answer`, { rating }),
    onSuccess: (data) => {
      setSessionCount((n) => n + 1);
      setRevealed(false);
      setCurrent(data.next_card);
      qc.invalidateQueries({ queryKey: ["artifacts"] });
      qc.invalidateQueries({ queryKey: ["queue"] });
    },
  });

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (!current) return;
      if (e.key === " " && !revealed) {
        e.preventDefault();
        setRevealed(true);
      } else if (revealed && ["1", "2", "3", "4"].includes(e.key)) {
        const rating = Number.parseInt(e.key, 10);
        if (!answer.isPending) {
          answer.mutate({ id: current.id, rating });
        }
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [revealed, current, answer]);

  if (queue.isLoading) {
    return <p className="text-sm text-slate-500">Loading queue…</p>;
  }
  if (!current) {
    return (
      <div className="text-center py-20">
        <h2 className="text-2xl font-bold">All done! 🎉</h2>
        <p className="text-slate-600 mt-2">Reviewed {sessionCount} cards.</p>
        <Link href="/dashboard" className="inline-block mt-6">
          <Button>Back to dashboard</Button>
        </Link>
      </div>
    );
  }

  const meaning = typeof current.data?.meaning === "string" ? current.data.meaning : "";
  const examples = Array.isArray(current.data?.examples)
    ? (current.data.examples as unknown[]).filter(
        (e): e is string => typeof e === "string",
      )
    : [];

  return (
    <div className="max-w-2xl mx-auto space-y-4">
      <div className="flex justify-between text-sm text-slate-600">
        <span>Session: {sessionCount + 1}</span>
        <span>Cards in queue: {queue.data?.count ?? 0}</span>
      </div>
      <Card className="p-8 min-h-[280px] flex flex-col items-center justify-center">
        <div className="flex gap-2 mb-4">
          <TypeBadge type={current.type} />
          <StatusBadge status={current.review_state.status} />
        </div>
        <h1 className="text-3xl font-bold mb-4">{current.lemma}</h1>
        {revealed && (
          <div className="w-full text-center mt-4">
            {meaning && (
              <p className="text-slate-700 italic mb-2">{meaning}</p>
            )}
            {examples.length > 0 && (
              <div className="text-left mt-4 text-sm space-y-1">
                <div className="text-xs uppercase text-slate-500">Examples</div>
                {examples.map((ex, i) => (
                  <p key={i}>• {ex}</p>
                ))}
              </div>
            )}
          </div>
        )}
      </Card>

      {!revealed ? (
        <Button
          size="lg"
          className="w-full"
          onClick={() => setRevealed(true)}
        >
          Tap to reveal · Space
        </Button>
      ) : (
        <div className="grid grid-cols-4 gap-2">
          {RATING_BUTTONS.map((b) => (
            <button
              key={b.rating}
              type="button"
              onClick={() =>
                answer.mutate({ id: current.id, rating: b.rating })
              }
              className={`${b.color} text-white py-3 rounded font-bold disabled:opacity-50`}
              disabled={answer.isPending}
            >
              <div>{b.label}</div>
              <div className="text-xs opacity-80">{b.rating}</div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, ApiError } from "@/lib/api";
import {
  cacheQueue,
  enqueueAnswer,
  loadCachedQueue,
  removeCachedCard,
} from "@/lib/offline-queue";
import { Volume2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { StatusBadge, TypeBadge } from "@/components/Badges";
import { speak, ttsAvailable } from "@/lib/tts";

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
  target_language?: string;
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

function StudyView() {
  const qc = useQueryClient();
  const searchParams = useSearchParams();
  const deckId = searchParams.get("deck_id");
  const [revealed, setRevealed] = useState(false);
  const [current, setCurrent] = useState<QueueCard | null>(null);
  const [bootstrapped, setBootstrapped] = useState(false);
  const [sessionCount, setSessionCount] = useState(0);
  const [offlineCards, setOfflineCards] = useState<QueueCard[]>([]);
  const [isOnline, setIsOnline] = useState(
    typeof navigator === "undefined" ? true : navigator.onLine,
  );

  useEffect(() => {
    if (typeof window === "undefined") return;
    const goOnline = () => setIsOnline(true);
    const goOffline = () => setIsOnline(false);
    window.addEventListener("online", goOnline);
    window.addEventListener("offline", goOffline);
    return () => {
      window.removeEventListener("online", goOnline);
      window.removeEventListener("offline", goOffline);
    };
  }, []);

  const queue = useQuery({
    queryKey: ["queue", "session", deckId],
    queryFn: async () => {
      const params = new URLSearchParams({ limit: "20" });
      if (deckId) params.set("deck_id", deckId);
      try {
        const data = await api.get<QueueResult>(
          `/api/v1/reviews/queue?${params.toString()}`,
        );
        // Cache the live queue for offline fallback (only when not deck-scoped
        // to avoid contaminating the global offline cache with a partial view).
        if (!deckId) {
          try {
            await cacheQueue(data.results);
          } catch {
            /* IndexedDB unavailable — ignore */
          }
        }
        return data;
      } catch (err) {
        if (err instanceof ApiError) throw err; // server error — propagate
        const cached = await loadCachedQueue<QueueCard>();
        return { count: cached.length, results: cached } satisfies QueueResult;
      }
    },
    refetchOnMount: true,
  });

  useEffect(() => {
    if (!bootstrapped && queue.data) {
      setCurrent(queue.data.results[0] ?? null);
      setOfflineCards(queue.data.results.slice(1));
      setBootstrapped(true);
    }
  }, [queue.data, bootstrapped]);

  const answer = useMutation({
    mutationFn: async ({ id, rating }: { id: string; rating: 1 | 2 | 3 | 4 }) => {
      try {
        const data = await api.post<AnswerResult>(
          `/api/v1/reviews/${id}/answer`,
          { rating },
        );
        return { result: data, queued: false as const };
      } catch (err) {
        if (err instanceof ApiError) throw err; // server error — propagate
        // Network failure: queue locally and advance via the cached buffer.
        await enqueueAnswer(id, rating);
        await removeCachedCard(id);
        return { queued: true as const };
      }
    },
    onSuccess: (outcome, vars) => {
      setSessionCount((n) => n + 1);
      setRevealed(false);
      qc.invalidateQueries({ queryKey: ["artifacts"] });
      qc.invalidateQueries({ queryKey: ["queue"] });
      if (outcome.queued) {
        setCurrent(offlineCards[0] ?? null);
        setOfflineCards((cards) => cards.slice(1));
      } else {
        const next = outcome.result.next_card;
        setCurrent(next);
        // Resync offline buffer to drop the card we just answered
        setOfflineCards((cards) => cards.filter((c) => c.id !== vars.id));
      }
    },
  });

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (!current) return;
      if (e.key === " " && !revealed) {
        e.preventDefault();
        setRevealed(true);
      } else if (revealed && ["1", "2", "3", "4"].includes(e.key)) {
        const rating = Number.parseInt(e.key, 10) as 1 | 2 | 3 | 4;
        if (!answer.isPending) {
          answer.mutate({ id: current.id, rating });
        }
      } else if (e.key.toLowerCase() === "a") {
        speak(current.lemma, current.target_language ?? null);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [revealed, current, answer]);

  // Swipe-to-rate on touch devices (only after the card is revealed).
  // left = Again(1), right = Good(3), up = Easy(4), down = Hard(2).
  useEffect(() => {
    if (typeof window === "undefined") return;
    if (window.matchMedia("(min-width: 768px)").matches) return;
    if (!revealed || !current) return;

    let startX = 0;
    let startY = 0;
    const THRESHOLD = 50;

    function onStart(e: PointerEvent) {
      startX = e.clientX;
      startY = e.clientY;
    }
    function onEnd(e: PointerEvent) {
      if (!current || answer.isPending) return;
      const dx = e.clientX - startX;
      const dy = e.clientY - startY;
      if (Math.abs(dx) < THRESHOLD && Math.abs(dy) < THRESHOLD) return;
      let rating: 1 | 2 | 3 | 4;
      if (Math.abs(dx) > Math.abs(dy)) {
        rating = dx < 0 ? 1 : 3;
      } else {
        rating = dy < 0 ? 4 : 2;
      }
      answer.mutate({ id: current.id, rating });
    }
    window.addEventListener("pointerdown", onStart);
    window.addEventListener("pointerup", onEnd);
    return () => {
      window.removeEventListener("pointerdown", onStart);
      window.removeEventListener("pointerup", onEnd);
    };
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
      {!isOnline && (
        <div className="rounded border border-amber-300 bg-amber-50 text-amber-900 text-xs px-3 py-2">
          Offline — answers will sync when you&apos;re back online.
        </div>
      )}
      <div className="flex justify-between text-sm text-slate-600">
        <span>Session: {sessionCount + 1}</span>
        <span>Cards in queue: {queue.data?.count ?? 0}</span>
      </div>
      <Card className="p-8 min-h-[280px] flex flex-col items-center justify-center">
        <div className="flex gap-2 mb-4">
          <TypeBadge type={current.type} />
          <StatusBadge status={current.review_state.status} />
        </div>
        <div className="flex items-center gap-3 mb-4">
          <h1 className="text-3xl font-bold">{current.lemma}</h1>
          {ttsAvailable() && (
            <button
              type="button"
              onClick={() => speak(current.lemma, current.target_language ?? null)}
              className="text-slate-500 hover:text-indigo-600"
              aria-label="Speak"
              title="Speak (A)"
            >
              <Volume2 size={20} />
            </button>
          )}
        </div>
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

export default function StudyPage() {
  return (
    <Suspense fallback={<p className="text-sm text-slate-500">Loading…</p>}>
      <StudyView />
    </Suspense>
  );
}

import { type CachedCard, getDB, type PendingAnswer } from "./offline-db";
import { api, ApiError } from "./api";

const SYNC_TAG = "flush-answers";

type SyncManager = { register(tag: string): Promise<void> };
type SyncRegistration = ServiceWorkerRegistration & { sync?: SyncManager };

async function registerBackgroundSync(): Promise<void> {
  if (typeof navigator === "undefined" || !("serviceWorker" in navigator)) return;
  try {
    const reg = (await navigator.serviceWorker.ready) as SyncRegistration;
    if (reg.sync && typeof reg.sync.register === "function") {
      await reg.sync.register(SYNC_TAG);
    }
  } catch {
    // Background Sync isn't supported on this platform (Safari, Firefox); fall
    // back to the "online" event listener wired in app/providers.tsx.
  }
}

export async function enqueueAnswer(
  artifact_id: string,
  rating: 1 | 2 | 3 | 4,
): Promise<void> {
  const db = await getDB();
  const entry: PendingAnswer = {
    id: crypto.randomUUID(),
    artifact_id,
    rating,
    queued_at: Date.now(),
  };
  await db.put("pending_answers", entry);
  await registerBackgroundSync();
}

export async function pendingCount(): Promise<number> {
  const db = await getDB();
  return db.count("pending_answers");
}

export async function flushPending(): Promise<{ ok: number; failed: number }> {
  const db = await getDB();
  const all = await db.getAll("pending_answers");
  let ok = 0;
  let failed = 0;
  for (const pa of all) {
    try {
      await api.post(`/api/v1/reviews/${pa.artifact_id}/answer`, {
        rating: pa.rating,
      });
      await db.delete("pending_answers", pa.id);
      ok += 1;
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) {
        // artifact deleted server-side — drop the queued answer
        await db.delete("pending_answers", pa.id);
      } else {
        failed += 1;
      }
    }
  }
  return { ok, failed };
}

export async function cacheQueue(
  cards: ReadonlyArray<{ id: string }>,
): Promise<void> {
  const db = await getDB();
  const tx = db.transaction("cached_queue", "readwrite");
  await tx.store.clear();
  const now = Date.now();
  for (const card of cards) {
    await tx.store.put({ id: card.id, payload: card, cached_at: now });
  }
  await tx.done;
}

export async function loadCachedQueue<T = unknown>(): Promise<T[]> {
  const db = await getDB();
  const rows = await db.getAll("cached_queue");
  return rows
    .sort((a: CachedCard, b: CachedCard) => a.cached_at - b.cached_at)
    .map((row: CachedCard) => row.payload as T);
}

export async function removeCachedCard(id: string): Promise<void> {
  const db = await getDB();
  await db.delete("cached_queue", id);
}

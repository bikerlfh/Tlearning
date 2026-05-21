import { type DBSchema, type IDBPDatabase, openDB } from "idb";

export interface PendingAnswer {
  id: string; // uuid generated client-side
  artifact_id: string;
  rating: 1 | 2 | 3 | 4;
  queued_at: number; // epoch ms
}

export interface CachedCard {
  id: string;
  payload: unknown;
  cached_at: number;
}

interface Schema extends DBSchema {
  pending_answers: { key: string; value: PendingAnswer };
  cached_queue: { key: string; value: CachedCard };
}

let dbPromise: Promise<IDBPDatabase<Schema>> | null = null;

export function getDB(): Promise<IDBPDatabase<Schema>> {
  if (typeof window === "undefined") {
    return Promise.reject(new Error("IndexedDB only available in the browser"));
  }
  if (!dbPromise) {
    dbPromise = openDB<Schema>("tlearning", 1, {
      upgrade(db) {
        if (!db.objectStoreNames.contains("pending_answers")) {
          db.createObjectStore("pending_answers", { keyPath: "id" });
        }
        if (!db.objectStoreNames.contains("cached_queue")) {
          db.createObjectStore("cached_queue", { keyPath: "id" });
        }
      },
    });
  }
  return dbPromise;
}

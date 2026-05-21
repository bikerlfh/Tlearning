"use client";

import { useEffect, useState } from "react";
import { QueryClient, QueryClientProvider, useQueryClient } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/sonner";
import { flushPending, pendingCount } from "@/lib/offline-queue";

function OfflineSyncBridge() {
  const qc = useQueryClient();

  useEffect(() => {
    if (typeof window === "undefined") return;

    let cancelled = false;

    async function flushAndRefresh() {
      try {
        const before = await pendingCount();
        if (before === 0) return;
        const { ok } = await flushPending();
        if (cancelled) return;
        if (ok > 0) {
          qc.invalidateQueries({ queryKey: ["queue"] });
          qc.invalidateQueries({ queryKey: ["artifacts"] });
        }
      } catch {
        /* offline-db unavailable — ignore */
      }
    }

    // Service Worker postMessage from the background sync handler
    function onMessage(e: MessageEvent) {
      if (e.data && e.data.type === "flush-answers") {
        void flushAndRefresh();
      }
    }
    if ("serviceWorker" in navigator) {
      navigator.serviceWorker.addEventListener("message", onMessage);
    }

    // Fallback for browsers without Background Sync (Safari, Firefox)
    function onOnline() {
      void flushAndRefresh();
    }
    window.addEventListener("online", onOnline);

    // Also try once on mount in case there's a pending queue from a previous session
    void flushAndRefresh();

    return () => {
      cancelled = true;
      if ("serviceWorker" in navigator) {
        navigator.serviceWorker.removeEventListener("message", onMessage);
      }
      window.removeEventListener("online", onOnline);
    };
  }, [qc]);

  return null;
}

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: { retry: 1, refetchOnWindowFocus: false },
        },
      }),
  );
  return (
    <QueryClientProvider client={queryClient}>
      <OfflineSyncBridge />
      {children}
      <Toaster richColors />
    </QueryClientProvider>
  );
}

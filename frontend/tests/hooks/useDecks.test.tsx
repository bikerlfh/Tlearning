import { describe, expect, it } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";
import { API_BASE } from "../msw-handlers";
import { server } from "../setup";
import { useCreateDeck, useDecks } from "@/hooks/useDecks";

function makeWrapper() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  function Wrapper({ children }: { children: React.ReactNode }) {
    return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
  }
  return { qc, Wrapper };
}

describe("useDecks", () => {
  it("returns the deck list", async () => {
    server.use(
      http.get(`${API_BASE}/api/v1/decks`, () =>
        HttpResponse.json({
          count: 1,
          results: [
            {
              id: "deck-1",
              name: "Default",
              source_language: "en",
              target_language: "es",
              is_default: true,
              created_at: "2026-01-01T00:00:00Z",
              artifact_count: 3,
            },
          ],
        }),
      ),
    );
    const { Wrapper } = makeWrapper();
    const { result } = renderHook(() => useDecks(), { wrapper: Wrapper });
    await waitFor(() => expect(result.current.data?.count).toBe(1));
    expect(result.current.data?.results[0].artifact_count).toBe(3);
  });
});

describe("useCreateDeck", () => {
  it("posts and invalidates ['decks']", async () => {
    server.use(
      http.post(`${API_BASE}/api/v1/decks`, async ({ request }) => {
        const body = (await request.json()) as { name: string };
        return HttpResponse.json(
          {
            id: "deck-new",
            name: body.name,
            source_language: "en",
            target_language: "es",
            is_default: false,
            created_at: "2026-01-01T00:00:00Z",
            artifact_count: 0,
          },
          { status: 201 },
        );
      }),
    );
    const { qc, Wrapper } = makeWrapper();
    let invalidated = false;
    const orig = qc.invalidateQueries.bind(qc);
    qc.invalidateQueries = ((args: Parameters<typeof orig>[0]) => {
      if (args && (args as { queryKey?: unknown[] }).queryKey?.[0] === "decks") {
        invalidated = true;
      }
      return orig(args);
    }) as typeof orig;
    const { result } = renderHook(() => useCreateDeck(), { wrapper: Wrapper });
    result.current.mutate({
      name: "Spanish daily",
      source_language: "en",
      target_language: "es",
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.name).toBe("Spanish daily");
    expect(invalidated).toBe(true);
  });
});

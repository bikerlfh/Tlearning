import { describe, expect, it } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";
import { API_BASE } from "../msw-handlers";
import { server } from "../setup";
import {
  useArtifact,
  useMarkLearned,
  useUpdateArtifact,
} from "@/hooks/useArtifact";

function makeWrapper() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  function Wrapper({ children }: { children: React.ReactNode }) {
    return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
  }
  return { qc, Wrapper };
}

const ARTIFACT_ID = "art-1";
const baseArtifact = {
  id: ARTIFACT_ID,
  deck: "deck-1",
  type: "word",
  lemma: "serendipity",
  source_language: "en",
  target_language: "es",
  data: { meaning: "a happy accident" },
  status: "pending",
  source: "manual",
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

describe("useArtifact", () => {
  it("fetches by id", async () => {
    server.use(
      http.get(`${API_BASE}/api/v1/artifacts/${ARTIFACT_ID}`, () =>
        HttpResponse.json(baseArtifact),
      ),
    );
    const { Wrapper } = makeWrapper();
    const { result } = renderHook(() => useArtifact(ARTIFACT_ID), { wrapper: Wrapper });
    await waitFor(() =>
      expect(result.current.data?.lemma).toBe("serendipity"),
    );
  });

  it("does not fetch when id is empty", () => {
    const { Wrapper } = makeWrapper();
    const { result } = renderHook(() => useArtifact(""), { wrapper: Wrapper });
    expect(result.current.fetchStatus).toBe("idle");
  });
});

describe("useUpdateArtifact", () => {
  it("PATCHes and refreshes ['artifact', id]", async () => {
    server.use(
      http.patch(`${API_BASE}/api/v1/artifacts/${ARTIFACT_ID}`, async () =>
        HttpResponse.json({ ...baseArtifact, lemma: "renamed" }),
      ),
    );
    const { qc, Wrapper } = makeWrapper();
    qc.setQueryData(["artifact", ARTIFACT_ID], baseArtifact);
    const { result } = renderHook(() => useUpdateArtifact(ARTIFACT_ID), {
      wrapper: Wrapper,
    });
    result.current.mutate({ lemma: "renamed" });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(
      (qc.getQueryData(["artifact", ARTIFACT_ID]) as { lemma: string })?.lemma,
    ).toBe("renamed");
  });
});

describe("useMarkLearned", () => {
  it("posts to /mark-learned", async () => {
    let hit = false;
    server.use(
      http.post(
        `${API_BASE}/api/v1/artifacts/${ARTIFACT_ID}/mark-learned`,
        () => {
          hit = true;
          return new HttpResponse(null, { status: 204 });
        },
      ),
    );
    const { Wrapper } = makeWrapper();
    const { result } = renderHook(() => useMarkLearned(ARTIFACT_ID), {
      wrapper: Wrapper,
    });
    result.current.mutate();
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(hit).toBe(true);
  });
});

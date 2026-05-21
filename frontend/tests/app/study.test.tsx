import { describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";
import { API_BASE } from "../msw-handlers";
import { server } from "../setup";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
  useSearchParams: () => ({ get: () => null }),
}));

// Avoid pulling actual IndexedDB into tests
vi.mock("@/lib/offline-queue", () => ({
  cacheQueue: vi.fn(async () => {}),
  enqueueAnswer: vi.fn(async () => {}),
  loadCachedQueue: vi.fn(async () => []),
  removeCachedCard: vi.fn(async () => {}),
  pendingCount: vi.fn(async () => 0),
  flushPending: vi.fn(async () => ({ ok: 0, failed: 0 })),
}));

import StudyPage from "@/app/(app)/study/page";

const cardA = {
  id: "art-a",
  lemma: "serendipity",
  type: "word",
  target_language: "en",
  data: { meaning: "a happy accident", examples: ["it was pure serendipity"] },
  review_state: { state: "new", status: "pending", due_at: "", reps: 0, lapses: 0 },
};
const cardB = {
  id: "art-b",
  lemma: "ephemeral",
  type: "word",
  target_language: "en",
  data: { meaning: "lasting briefly" },
  review_state: { state: "new", status: "pending", due_at: "", reps: 0, lapses: 0 },
};

function withQueryClient(ui: React.ReactNode) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{ui}</QueryClientProvider>;
}

describe("StudyPage", () => {
  it("reveals the meaning on Space then advances to the next card after rating", async () => {
    server.use(
      http.get(`${API_BASE}/api/v1/reviews/queue`, () =>
        HttpResponse.json({ count: 2, results: [cardA, cardB] }),
      ),
      http.post(
        `${API_BASE}/api/v1/reviews/${cardA.id}/answer`,
        () =>
          HttpResponse.json({
            review_state: { ...cardA.review_state, reps: 1 },
            next_card: cardB,
          }),
      ),
    );
    const user = userEvent.setup();
    render(withQueryClient(<StudyPage />));

    await waitFor(() => expect(screen.getByText("serendipity")).toBeInTheDocument());
    // Before reveal the meaning is hidden
    expect(screen.queryByText("a happy accident")).not.toBeInTheDocument();

    await user.keyboard(" ");
    await waitFor(() => expect(screen.getByText("a happy accident")).toBeInTheDocument());

    // Rate "Good" (3)
    await user.keyboard("3");
    await waitFor(() => expect(screen.getByText("ephemeral")).toBeInTheDocument());
    expect(screen.queryByText("serendipity")).not.toBeInTheDocument();
  });

  it("shows All done when the queue is empty", async () => {
    server.use(
      http.get(`${API_BASE}/api/v1/reviews/queue`, () =>
        HttpResponse.json({ count: 0, results: [] }),
      ),
    );
    render(withQueryClient(<StudyPage />));
    await waitFor(() => expect(screen.getByText(/All done/i)).toBeInTheDocument());
  });
});

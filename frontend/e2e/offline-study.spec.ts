import { expect, test } from "@playwright/test";

/**
 * TODO(phase10-followup): exercise the full offline-answer flow end-to-end.
 *
 * The plan calls for: load /study online, toggle context.setOffline(true), rate 2 cards,
 * toggle back online, assert the backend now reflects the answers. The mechanics
 * (Service Worker registration timing under Playwright, IndexedDB cleanup between
 * runs, race between the 'online' event and the SW sync handler) make this test
 * brittle. We're deferring it until we have a Phase 10b iteration with retries
 * and a deterministic clock.
 *
 * For now this file is a placeholder so the regression hook (`pnpm exec playwright test`)
 * picks up future additions without a new config change.
 */

test.skip("offline answers sync when connectivity returns", async () => {
  // intentionally empty
  expect(true).toBe(true);
});

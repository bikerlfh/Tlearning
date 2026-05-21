import { expect, test } from "@playwright/test";

/**
 * Critical-path e2e: signup → API token → ingest via REST → study → rate → done.
 *
 * Requires the Django backend reachable at API_BASE (default http://localhost:8000).
 * Run: docker compose up -d  (postgres, redis, web) then `pnpm exec playwright test`.
 */

const API_BASE = process.env.E2E_API_BASE ?? "http://localhost:8000";

test("signup → dashboard → token → ingest → study → rate", async ({ page, request }) => {
  test.setTimeout(120_000);

  const email = `e2e-${Date.now()}@example.com`;
  const password = "supersecret123";

  // 1) Signup
  await page.goto("/signup");
  await page.locator("input#email").fill(email);
  await page.locator("input#password").fill(password);
  await page.locator('button[type="submit"]:has-text("Sign up")').click();
  await expect(page).toHaveURL(/dashboard/);

  // 2) Generate API token via the UI
  await page.goto("/settings/api-tokens");
  await page.locator('input[placeholder*="laptop"]').fill("e2e");
  await page.getByRole("button", { name: /generate/i }).click();
  const token = (await page.locator("code").first().innerText()).trim();
  expect(token).toMatch(/^tl_live_/);

  // 3) Use the token via REST to seed a deck + artifact
  const decksRes = await request.post(`${API_BASE}/api/v1/decks`, {
    headers: { Authorization: `Bearer ${token}` },
    data: { name: "e2e", source_language: "en", target_language: "es" },
  });
  expect(decksRes.ok()).toBeTruthy();
  const deck = await decksRes.json();

  const artRes = await request.post(`${API_BASE}/api/v1/artifacts`, {
    headers: { Authorization: `Bearer ${token}` },
    data: {
      deck_id: deck.id,
      type: "word",
      lemma: "serendipity",
      source_language: "en",
      target_language: "es",
      data: { meaning: "a happy accident", part_of_speech: "noun" },
    },
  });
  expect(artRes.ok()).toBeTruthy();

  // 4) Study the new card
  await page.goto("/study");
  await expect(page.locator("h1", { hasText: "serendipity" })).toBeVisible();
  await page.keyboard.press(" ");
  await expect(page.getByText("a happy accident")).toBeVisible();
  await page.keyboard.press("3"); // Good

  await expect(page.getByRole("heading", { name: /All done/i })).toBeVisible();
});

import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";
import { API_BASE, defaultUser } from "../msw-handlers";
import { server } from "../setup";

const pushMock = vi.fn();
const searchParamsGet = vi.fn(() => null) as unknown as (key: string) => string | null;

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock, replace: pushMock }),
  useSearchParams: () => ({ get: searchParamsGet }),
}));

import LoginPage from "@/app/login/page";

function withQueryClient(ui: React.ReactNode) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{ui}</QueryClientProvider>;
}

beforeEach(() => {
  pushMock.mockClear();
});

describe("LoginPage", () => {
  it("does not log in when email is invalid", async () => {
    const user = userEvent.setup();
    render(withQueryClient(<LoginPage />));
    // Empty email + valid-length password: zod min(8) passes for password
    // but email validation fails -> handleSubmit blocks the mutation.
    await user.type(screen.getByLabelText("Password"), "longenough");
    await user.click(screen.getByRole("button", { name: /log in/i }));
    // Give react-hook-form a tick to settle
    await new Promise((r) => setTimeout(r, 50));
    expect(pushMock).not.toHaveBeenCalled();
  });

  it("posts credentials and pushes to /dashboard on success", async () => {
    server.use(
      http.post(`${API_BASE}/api/v1/auth/login`, () =>
        HttpResponse.json(defaultUser),
      ),
    );
    const user = userEvent.setup();
    render(withQueryClient(<LoginPage />));
    await user.type(screen.getByLabelText("Email"), defaultUser.email);
    await user.type(screen.getByLabelText("Password"), "supersecret");
    await user.click(screen.getByRole("button", { name: /log in/i }));
    await waitFor(() =>
      expect(pushMock).toHaveBeenCalledWith("/dashboard"),
    );
  });
});

import { describe, expect, it } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";
import { API_BASE, defaultUser } from "../msw-handlers";
import { server } from "../setup";
import { useLogin, useLogout, useMe } from "@/hooks/useAuth";

function makeWrapper() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  function Wrapper({ children }: { children: React.ReactNode }) {
    return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
  }
  return { qc, Wrapper };
}

describe("useMe", () => {
  it("returns the authenticated user", async () => {
    const { Wrapper } = makeWrapper();
    const { result } = renderHook(() => useMe(), { wrapper: Wrapper });
    await waitFor(() => expect(result.current.data?.email).toBe(defaultUser.email));
  });

  it("isError when /me returns 401", async () => {
    server.use(
      http.get(`${API_BASE}/api/v1/auth/me`, () => new HttpResponse(null, { status: 401 })),
    );
    const { Wrapper } = makeWrapper();
    const { result } = renderHook(() => useMe(), { wrapper: Wrapper });
    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.data).toBeUndefined();
  });
});

describe("useLogin", () => {
  it("posts credentials and seeds the ['me'] cache on success", async () => {
    server.use(
      http.post(`${API_BASE}/api/v1/auth/login`, async () =>
        HttpResponse.json({
          ...defaultUser,
          id: "user-2",
          email: "x@y.z",
          name: "X",
        }),
      ),
    );
    const { qc, Wrapper } = makeWrapper();
    const { result } = renderHook(() => useLogin(), { wrapper: Wrapper });
    result.current.mutate({ email: "x@y.z", password: "pw12345678" });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(qc.getQueryData(["me"])).toMatchObject({ email: "x@y.z" });
  });

  it("isError on 401 invalid credentials", async () => {
    server.use(
      http.post(
        `${API_BASE}/api/v1/auth/login`,
        () => new HttpResponse(null, { status: 401 }),
      ),
    );
    const { Wrapper } = makeWrapper();
    const { result } = renderHook(() => useLogin(), { wrapper: Wrapper });
    result.current.mutate({ email: "bad@example.com", password: "wrongpass1" });
    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

describe("useLogout", () => {
  it("clears the query cache on success", async () => {
    server.use(
      http.post(`${API_BASE}/api/v1/auth/logout`, () => new HttpResponse(null, { status: 204 })),
    );
    const { qc, Wrapper } = makeWrapper();
    qc.setQueryData(["me"], defaultUser);
    qc.setQueryData(["library"], { count: 1, results: [] });
    const { result } = renderHook(() => useLogout(), { wrapper: Wrapper });
    result.current.mutate();
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(qc.getQueryData(["me"])).toBeUndefined();
    expect(qc.getQueryData(["library"])).toBeUndefined();
  });
});

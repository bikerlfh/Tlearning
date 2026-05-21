import { http, HttpResponse } from "msw";

export const API_BASE = "http://localhost:8000";

export const defaultUser = {
  id: "user-1",
  email: "user@example.com",
  name: "User",
  timezone: "UTC",
  preferred_ui_language: "en",
  date_joined: "2026-01-01T00:00:00Z",
};

export const handlers = [
  http.get(`${API_BASE}/api/v1/auth/me`, () => HttpResponse.json(defaultUser)),
];

"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface User {
  id: string;
  email: string;
  name: string;
  timezone: string;
  preferred_ui_language: string;
  date_joined?: string;
}

export function useMe() {
  return useQuery({
    queryKey: ["me"],
    queryFn: () => api.get<User>("/api/v1/auth/me"),
    retry: false,
  });
}

export function useLogin() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { email: string; password: string }) =>
      api.post<User>("/api/v1/auth/login", data),
    onSuccess: (user) => qc.setQueryData(["me"], user),
  });
}

export function useLogout() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api.post("/api/v1/auth/logout", {}),
    onSuccess: () => qc.clear(),
  });
}

export interface SignupInput {
  email: string;
  password: string;
  name?: string;
  timezone?: string;
  preferred_ui_language?: string;
}

export function useSignup() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: SignupInput) => api.post<User>("/api/v1/auth/signup", data),
    onSuccess: (user) => qc.setQueryData(["me"], user),
  });
}

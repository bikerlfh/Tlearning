"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface Deck {
  id: string;
  name: string;
  source_language: string;
  target_language: string;
  is_default: boolean;
  created_at: string;
  artifact_count: number;
}

export interface DeckList {
  count: number;
  results: Deck[];
}

export interface DeckInput {
  name: string;
  source_language: string;
  target_language: string;
}

export function useDecks() {
  return useQuery({
    queryKey: ["decks"],
    queryFn: () => api.get<DeckList>("/api/v1/decks"),
  });
}

export function useDeck(id: string) {
  return useQuery({
    queryKey: ["deck", id],
    queryFn: () => api.get<Deck>(`/api/v1/decks/${id}`),
    enabled: Boolean(id),
  });
}

export function useCreateDeck() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: DeckInput) => api.post<Deck>("/api/v1/decks", data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["decks"] }),
  });
}

export function useUpdateDeck(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (patch: Partial<DeckInput>) =>
      api.patch<Deck>(`/api/v1/decks/${id}`, patch),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["decks"] });
      qc.invalidateQueries({ queryKey: ["deck", id] });
    },
  });
}

export function useDeleteDeck() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.delete(`/api/v1/decks/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["decks"] }),
  });
}

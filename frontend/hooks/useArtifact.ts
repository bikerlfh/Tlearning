"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface ArtifactDetail {
  id: string;
  deck: string;
  type: string;
  lemma: string;
  source_language: string;
  target_language: string;
  data: Record<string, unknown>;
  status: string;
  source: string;
  created_at: string;
  updated_at: string;
}

export function useArtifact(id: string) {
  return useQuery({
    queryKey: ["artifact", id],
    queryFn: () => api.get<ArtifactDetail>(`/api/v1/artifacts/${id}`),
    enabled: Boolean(id),
  });
}

export function useUpdateArtifact(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (patch: Partial<ArtifactDetail>) =>
      api.patch<ArtifactDetail>(`/api/v1/artifacts/${id}`, patch),
    onSuccess: (data) => {
      qc.setQueryData(["artifact", id], data);
      qc.invalidateQueries({ queryKey: ["library"] });
      qc.invalidateQueries({ queryKey: ["artifacts"] });
    },
  });
}

export function useMarkLearned(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api.post(`/api/v1/artifacts/${id}/mark-learned`, {}),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["artifact", id] });
      qc.invalidateQueries({ queryKey: ["library"] });
      qc.invalidateQueries({ queryKey: ["artifacts"] });
    },
  });
}

export function useSuspendArtifact(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api.post(`/api/v1/artifacts/${id}/suspend`, {}),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["artifact", id] });
      qc.invalidateQueries({ queryKey: ["library"] });
      qc.invalidateQueries({ queryKey: ["artifacts"] });
    },
  });
}

export function useDeleteArtifact(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api.delete(`/api/v1/artifacts/${id}`),
    onSuccess: () => {
      qc.removeQueries({ queryKey: ["artifact", id] });
      qc.invalidateQueries({ queryKey: ["library"] });
      qc.invalidateQueries({ queryKey: ["artifacts"] });
    },
  });
}

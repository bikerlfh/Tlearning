"use client";

import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { api, ApiError } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

interface SocialAccount {
  id: string;
  provider: string;
  uid: string;
  email: string | null;
  name: string | null;
  connected_at: string | null;
}

interface SocialAccountList {
  count: number;
  results: SocialAccount[];
}

const PROVIDER_LABELS: Record<string, string> = {
  google: "Google",
};

export default function AccountSettingsPage() {
  const qc = useQueryClient();
  const list = useQuery({
    queryKey: ["social-accounts"],
    queryFn: () => api.get<SocialAccountList>("/api/v1/auth/social-accounts"),
  });

  const disconnect = useMutation({
    mutationFn: (id: string) =>
      api.post(`/api/v1/auth/social-accounts/${id}/disconnect`, {}),
    onSuccess: () => {
      toast.success("Disconnected");
      qc.invalidateQueries({ queryKey: ["social-accounts"] });
    },
    onError: (err) => {
      if (err instanceof ApiError && err.body && typeof err.body === "object") {
        const detail = (err.body as { detail?: string }).detail;
        toast.error(detail ?? "Failed to disconnect");
      } else {
        toast.error("Failed to disconnect");
      }
    },
  });

  return (
    <div className="max-w-2xl mx-auto space-y-4">
      <h1 className="text-2xl font-bold">Account</h1>
      <p className="text-slate-600">
        Sign-in methods linked to your Tlearning account.
      </p>

      <Card>
        <div className="p-4">
          <h2 className="font-bold">Linked providers</h2>
        </div>
        {list.isLoading && (
          <p className="px-4 pb-4 text-sm text-slate-500">Loading…</p>
        )}
        {list.data && list.data.count === 0 && (
          <p className="px-4 pb-4 text-sm text-slate-500">
            No social accounts linked. Sign in with Google to add one.
          </p>
        )}
        {list.data?.results.map((sa) => (
          <div
            key={sa.id}
            className="flex items-center justify-between px-4 py-3 border-t"
          >
            <div>
              <div className="font-medium">
                {PROVIDER_LABELS[sa.provider] ?? sa.provider}
              </div>
              <div className="text-xs text-slate-500">
                {sa.email ?? sa.uid}
              </div>
            </div>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => disconnect.mutate(sa.id)}
              disabled={disconnect.isPending}
            >
              Disconnect
            </Button>
          </div>
        ))}
      </Card>

      <p className="text-sm text-slate-600">
        Need to add or change a password before disconnecting your only sign-in
        method? Use{" "}
        <Link href="/forgot-password" className="underline">
          forgot password
        </Link>{" "}
        to set one.
      </p>
    </div>
  );
}

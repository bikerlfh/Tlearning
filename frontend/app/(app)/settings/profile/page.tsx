"use client";

import { useEffect, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { api, ApiError } from "@/lib/api";
import { useMe, type User } from "@/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const LANGUAGES = [
  { value: "en", label: "English" },
  { value: "es", label: "Español" },
];

const FALLBACK_TIMEZONES = [
  "UTC",
  "America/New_York",
  "America/Los_Angeles",
  "America/Mexico_City",
  "Europe/Madrid",
  "Europe/London",
  "Europe/Berlin",
  "Asia/Tokyo",
];

function supportedTimezones(): string[] {
  if (typeof Intl === "undefined") return FALLBACK_TIMEZONES;
  const supported = (
    Intl as unknown as { supportedValuesOf?: (key: string) => string[] }
  ).supportedValuesOf;
  if (typeof supported === "function") {
    try {
      return supported("timeZone");
    } catch {
      return FALLBACK_TIMEZONES;
    }
  }
  return FALLBACK_TIMEZONES;
}

export default function ProfilePage() {
  const me = useMe();
  const qc = useQueryClient();
  const [draft, setDraft] = useState<User | null>(null);

  useEffect(() => {
    if (me.data && !draft) setDraft(me.data);
  }, [me.data, draft]);

  const save = useMutation({
    mutationFn: (patch: Partial<User>) =>
      api.patch<User>("/api/v1/auth/me", patch),
    onSuccess: (user) => {
      qc.setQueryData(["me"], user);
      toast.success("Profile saved");
    },
    onError: (err) => {
      const msg =
        err instanceof ApiError ? err.message : "Failed to save profile";
      toast.error(msg);
    },
  });

  if (me.isLoading || !draft) {
    return <p className="text-sm text-slate-500">Loading…</p>;
  }

  const zones = supportedTimezones();

  return (
    <div className="max-w-xl mx-auto space-y-4">
      <h1 className="text-2xl font-bold">Profile</h1>
      <Card className="p-4 space-y-4">
        <div className="grid gap-2">
          <Label htmlFor="email">Email</Label>
          <Input id="email" value={draft.email} disabled />
        </div>
        <div className="grid gap-2">
          <Label htmlFor="name">Name</Label>
          <Input
            id="name"
            value={draft.name ?? ""}
            onChange={(e) => setDraft({ ...draft, name: e.target.value })}
          />
        </div>
        <div className="grid gap-2">
          <Label htmlFor="timezone">Timezone</Label>
          <select
            id="timezone"
            className="border rounded p-2 bg-white"
            value={draft.timezone}
            onChange={(e) =>
              setDraft({ ...draft, timezone: e.target.value })
            }
          >
            {zones.map((tz) => (
              <option key={tz} value={tz}>
                {tz}
              </option>
            ))}
          </select>
        </div>
        <div className="grid gap-2">
          <Label htmlFor="language">UI language</Label>
          <select
            id="language"
            className="border rounded p-2 bg-white"
            value={draft.preferred_ui_language}
            onChange={(e) =>
              setDraft({ ...draft, preferred_ui_language: e.target.value })
            }
          >
            {LANGUAGES.map((l) => (
              <option key={l.value} value={l.value}>
                {l.label}
              </option>
            ))}
          </select>
        </div>
        <Button
          type="button"
          onClick={() =>
            save.mutate({
              name: draft.name,
              timezone: draft.timezone,
              preferred_ui_language: draft.preferred_ui_language,
            })
          }
          disabled={save.isPending}
        >
          {save.isPending ? "Saving…" : "Save"}
        </Button>
      </Card>
    </div>
  );
}

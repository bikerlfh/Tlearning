"use client";

import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { api, ApiError } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { enablePush } from "@/lib/push";

interface Preference {
  enabled: boolean;
  frequency_per_day: number;
  min_interval_minutes: number;
  quiet_hours_start: string | null;
  quiet_hours_end: string | null;
  weekdays_only: boolean;
}

export default function NotificationsSettingsPage() {
  const qc = useQueryClient();
  const [draft, setDraft] = useState<Preference | null>(null);

  const prefs = useQuery({
    queryKey: ["notification-prefs"],
    queryFn: () => api.get<Preference>("/api/v1/notifications/preferences"),
  });

  useEffect(() => {
    if (prefs.data && !draft) setDraft(prefs.data);
  }, [prefs.data, draft]);

  const save = useMutation({
    mutationFn: (data: Preference) =>
      api.patch<Preference>("/api/v1/notifications/preferences", data),
    onSuccess: (data) => {
      qc.setQueryData(["notification-prefs"], data);
      toast.success("Preferences saved");
    },
    onError: (err) => {
      const msg =
        err instanceof ApiError ? err.message : "Failed to save preferences";
      toast.error(msg);
    },
  });

  const sendTest = useMutation({
    mutationFn: () => api.post("/api/v1/notifications/test", {}),
    onSuccess: () => toast.success("Test push queued"),
    onError: (err) => {
      const msg =
        err instanceof ApiError ? err.message : "Failed to send test";
      toast.error(msg);
    },
  });

  const handleEnablePush = async () => {
    try {
      const ok = await enablePush();
      if (ok) toast.success("Push enabled on this device");
      else toast.error("Permission denied or unsupported");
    } catch (err) {
      console.error(err);
      toast.error("Failed to register push subscription");
    }
  };

  if (prefs.isLoading || !draft) {
    return <p className="text-sm text-slate-500">Loading…</p>;
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">Notifications</h1>

      <Card className="p-4 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <Label className="font-bold">Enabled</Label>
            <p className="text-sm text-slate-600">
              Master toggle for all push notifications.
            </p>
          </div>
          <input
            type="checkbox"
            checked={draft.enabled}
            onChange={(e) =>
              setDraft({ ...draft, enabled: e.target.checked })
            }
            className="h-5 w-5"
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="grid gap-1">
            <Label>Frequency per day</Label>
            <Input
              type="number"
              min={1}
              max={20}
              value={draft.frequency_per_day}
              onChange={(e) =>
                setDraft({
                  ...draft,
                  frequency_per_day: Number(e.target.value),
                })
              }
            />
          </div>
          <div className="grid gap-1">
            <Label>Min interval (minutes)</Label>
            <Input
              type="number"
              min={5}
              max={1440}
              value={draft.min_interval_minutes}
              onChange={(e) =>
                setDraft({
                  ...draft,
                  min_interval_minutes: Number(e.target.value),
                })
              }
            />
          </div>
          <div className="grid gap-1">
            <Label>Quiet hours start</Label>
            <Input
              type="time"
              value={draft.quiet_hours_start ?? ""}
              onChange={(e) =>
                setDraft({
                  ...draft,
                  quiet_hours_start: e.target.value || null,
                })
              }
            />
          </div>
          <div className="grid gap-1">
            <Label>Quiet hours end</Label>
            <Input
              type="time"
              value={draft.quiet_hours_end ?? ""}
              onChange={(e) =>
                setDraft({
                  ...draft,
                  quiet_hours_end: e.target.value || null,
                })
              }
            />
          </div>
        </div>

        <div className="flex items-center gap-2">
          <input
            id="weekdays_only"
            type="checkbox"
            checked={draft.weekdays_only}
            onChange={(e) =>
              setDraft({ ...draft, weekdays_only: e.target.checked })
            }
          />
          <Label htmlFor="weekdays_only">Weekdays only</Label>
        </div>

        <div className="flex gap-2 pt-2">
          <Button
            type="button"
            onClick={() => save.mutate(draft)}
            disabled={save.isPending}
          >
            {save.isPending ? "Saving…" : "Save preferences"}
          </Button>
          <Button
            type="button"
            variant="outline"
            onClick={() => sendTest.mutate()}
            disabled={sendTest.isPending}
          >
            {sendTest.isPending ? "Sending…" : "Send test push"}
          </Button>
        </div>
      </Card>

      <Card className="p-4 space-y-3">
        <h2 className="font-bold">Push on this device</h2>
        <p className="text-sm text-slate-600">
          Subscribes this browser to web push. Requires a VAPID public key
          configured via <code>NEXT_PUBLIC_VAPID_PUBLIC_KEY</code>.
        </p>
        <Button type="button" variant="outline" onClick={handleEnablePush}>
          Enable push notifications
        </Button>
      </Card>
    </div>
  );
}

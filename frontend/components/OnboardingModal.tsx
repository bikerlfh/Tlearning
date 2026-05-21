"use client";

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { useMe, type User } from "@/hooks/useAuth";
import { enablePush } from "@/lib/push";

const FALLBACK_TIMEZONES = [
  "UTC",
  "America/New_York",
  "America/Los_Angeles",
  "America/Mexico_City",
  "Europe/Madrid",
  "Europe/London",
  "Asia/Tokyo",
];

function detectedTimezone(): string {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";
  } catch {
    return "UTC";
  }
}

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

export function OnboardingModal({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const me = useMe();
  const qc = useQueryClient();
  const [step, setStep] = useState<0 | 1 | 2>(0);
  const [tz, setTz] = useState<string>(detectedTimezone());

  const saveTz = useMutation({
    mutationFn: (timezone: string) =>
      api.patch<User>("/api/v1/auth/me", { timezone }),
    onSuccess: (user) => qc.setQueryData(["me"], user),
  });

  const advance = () => setStep((s) => (s === 2 ? s : ((s + 1) as 0 | 1 | 2)));
  const finish = () => {
    if (typeof window !== "undefined") {
      window.localStorage.setItem("tlearning_onboarded", "1");
    }
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={(o) => !o && finish()}>
      <DialogContent className="max-w-md">
        {step === 0 && (
          <>
            <DialogHeader>
              <DialogTitle>Welcome to Tlearning 👋</DialogTitle>
              <DialogDescription>
                Hi {me.data?.name || me.data?.email?.split("@")[0] || "there"} — quick
                30-second setup before you start.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-2 text-sm text-slate-700 py-2">
              <p>
                Tlearning captures words, idioms, and phrases you encounter
                while chatting with Claude, Cursor, or any MCP client, and
                schedules reviews using the FSRS algorithm.
              </p>
              <p>
                We&apos;ll ask two things and you&apos;re in.
              </p>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button type="button" variant="outline" onClick={finish}>
                Skip
              </Button>
              <Button type="button" onClick={advance}>
                Next
              </Button>
            </div>
          </>
        )}

        {step === 1 && (
          <>
            <DialogHeader>
              <DialogTitle>Pick your timezone</DialogTitle>
              <DialogDescription>
                Notifications and the daily streak are computed in your local time.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-2 py-2">
              <Label htmlFor="onboarding-tz">Timezone</Label>
              <select
                id="onboarding-tz"
                className="border rounded p-2 bg-white w-full"
                value={tz}
                onChange={(e) => setTz(e.target.value)}
              >
                {supportedTimezones().map((zone) => (
                  <option key={zone} value={zone}>
                    {zone}
                  </option>
                ))}
              </select>
              <p className="text-xs text-slate-500">
                Detected: <code>{detectedTimezone()}</code>
              </p>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  saveTz.mutate(tz);
                  advance();
                }}
              >
                Skip
              </Button>
              <Button
                type="button"
                onClick={() => {
                  saveTz.mutate(tz, {
                    onSuccess: () => advance(),
                    onError: () => {
                      toast.error("Could not save timezone — continuing");
                      advance();
                    },
                  });
                }}
                disabled={saveTz.isPending}
              >
                {saveTz.isPending ? "Saving…" : "Continue"}
              </Button>
            </div>
          </>
        )}

        {step === 2 && (
          <>
            <DialogHeader>
              <DialogTitle>Daily reminders?</DialogTitle>
              <DialogDescription>
                A small push when cards are due. You can change this any time
                in Settings → Notifications.
              </DialogDescription>
            </DialogHeader>
            <div className="flex justify-end gap-2 pt-2">
              <Button type="button" variant="outline" onClick={finish}>
                Not now
              </Button>
              <Button
                type="button"
                onClick={async () => {
                  try {
                    const ok = await enablePush();
                    if (ok) toast.success("Push enabled");
                    else toast.error("Permission denied or unsupported");
                  } catch {
                    toast.error("Could not register push");
                  } finally {
                    finish();
                  }
                }}
              >
                Enable
              </Button>
            </div>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}

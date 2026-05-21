"use client";

import { Suspense, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { api, ApiError } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const schema = z
  .object({
    password: z.string().min(8),
    confirm: z.string().min(8),
  })
  .refine((d) => d.password === d.confirm, {
    message: "Passwords do not match",
    path: ["confirm"],
  });

type FormData = z.infer<typeof schema>;

function ResetForm() {
  const router = useRouter();
  const params = useSearchParams();
  const uid = params.get("uid") ?? "";
  const token = params.get("token") ?? "";
  const linkInvalid = !uid || !token;

  const [done, setDone] = useState(false);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setError,
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  const onSubmit = async (data: FormData) => {
    try {
      await api.post("/api/v1/auth/password-reset/confirm", {
        uid,
        token,
        password: data.password,
      });
      setDone(true);
      setTimeout(() => router.push("/login?reset=ok"), 1500);
    } catch (err) {
      if (err instanceof ApiError && err.body && typeof err.body === "object") {
        const body = err.body as Record<string, unknown>;
        if (Array.isArray(body.password)) {
          setError("password", { message: String(body.password[0]) });
        } else if (typeof body.detail === "string") {
          toast.error(body.detail);
        } else {
          toast.error("Reset failed");
        }
      } else {
        toast.error("Reset failed");
      }
    }
  };

  if (linkInvalid) {
    return (
      <Card className="w-full max-w-sm p-6 space-y-3">
        <h1 className="text-2xl font-bold">Invalid link</h1>
        <p className="text-sm text-slate-600">
          The link is missing the required parameters. Request a new one.
        </p>
        <Link href="/forgot-password" className="underline text-sm">
          Send a new reset link
        </Link>
      </Card>
    );
  }

  if (done) {
    return (
      <Card className="w-full max-w-sm p-6 space-y-3">
        <h1 className="text-2xl font-bold">Password updated</h1>
        <p className="text-sm text-slate-600">Redirecting to login…</p>
      </Card>
    );
  }

  return (
    <Card className="w-full max-w-sm p-6 space-y-4">
      <h1 className="text-2xl font-bold">Choose a new password</h1>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div className="grid gap-2">
          <Label htmlFor="password">New password</Label>
          <Input
            id="password"
            type="password"
            autoComplete="new-password"
            {...register("password")}
          />
          {errors.password && (
            <p className="text-sm text-red-600">{errors.password.message}</p>
          )}
        </div>
        <div className="grid gap-2">
          <Label htmlFor="confirm">Confirm</Label>
          <Input
            id="confirm"
            type="password"
            autoComplete="new-password"
            {...register("confirm")}
          />
          {errors.confirm && (
            <p className="text-sm text-red-600">{errors.confirm.message}</p>
          )}
        </div>
        <Button type="submit" className="w-full" disabled={isSubmitting}>
          {isSubmitting ? "Updating…" : "Update password"}
        </Button>
      </form>
    </Card>
  );
}

export default function ResetPasswordPage() {
  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <Suspense fallback={<p className="text-sm text-slate-500">Loading…</p>}>
        <ResetForm />
      </Suspense>
    </div>
  );
}

"use client";

import { useState } from "react";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const schema = z.object({ email: z.string().email() });
type FormData = z.infer<typeof schema>;

export default function ForgotPasswordPage() {
  const [submitted, setSubmitted] = useState(false);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  const onSubmit = async ({ email }: FormData) => {
    try {
      await api.post("/api/v1/auth/password-reset/request", { email });
      setSubmitted(true);
    } catch {
      // The backend always responds 204 to avoid leaking which emails exist —
      // so any error here is a network/connectivity failure.
      toast.error("Could not reach the server. Try again.");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <Card className="w-full max-w-sm p-6 space-y-4">
        <h1 className="text-2xl font-bold">Forgot password</h1>
        {submitted ? (
          <>
            <p className="text-sm text-slate-600">
              If an account exists for that email, you&apos;ll get a reset link
              in a minute. Check your inbox (and spam folder).
            </p>
            <Link href="/login" className="block text-sm underline text-center">
              Back to login
            </Link>
          </>
        ) : (
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <p className="text-sm text-slate-600">
              Enter the email you used to sign up — we&apos;ll send a link to
              choose a new password.
            </p>
            <div className="grid gap-2">
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" autoComplete="email" {...register("email")} />
              {errors.email && (
                <p className="text-sm text-red-600">{errors.email.message}</p>
              )}
            </div>
            <Button type="submit" className="w-full" disabled={isSubmitting}>
              {isSubmitting ? "Sending…" : "Send reset link"}
            </Button>
            <p className="text-sm text-center">
              <Link href="/login" className="underline">
                Back to login
              </Link>
            </p>
          </form>
        )}
      </Card>
    </div>
  );
}

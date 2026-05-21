"use client";

import { Suspense, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useLogin } from "@/hooks/useAuth";

const OAUTH_ERROR_MESSAGES: Record<string, string> = {
  oauth_state: "Sign-in was interrupted. Please try again.",
  oauth_expired: "Sign-in link expired. Please try again.",
  oauth_no_token: "Google did not return an access token. Try again.",
  oauth_exchange: "Could not complete Google sign-in. Try again.",
  oauth_email: "Google account email is not verified.",
  oauth_inactive: "This account has been deactivated.",
};

const schema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
});

type FormData = z.infer<typeof schema>;

function FlashFromQuery() {
  const searchParams = useSearchParams();
  useEffect(() => {
    const err = searchParams.get("error");
    if (err) toast.error(OAUTH_ERROR_MESSAGES[err] ?? "Sign-in failed");
    if (searchParams.get("reset") === "ok") {
      toast.success("Password updated — please log in.");
    }
  }, [searchParams]);
  return null;
}

function LoginForm() {
  const router = useRouter();
  const login = useLogin();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  const startGoogle = async () => {
    try {
      const { url } = await api.get<{ url: string }>(
        "/api/v1/auth/google/begin",
      );
      window.location.href = url;
    } catch {
      toast.error("Could not start Google sign-in");
    }
  };

  const onSubmit = (data: FormData) => {
    login.mutate(data, {
      onSuccess: () => {
        toast.success("Welcome back!");
        router.push("/dashboard");
      },
      onError: () => toast.error("Invalid credentials"),
    });
  };

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      className="w-full max-w-sm space-y-4"
    >
      <h1 className="text-2xl font-bold">Log in to Tlearning</h1>
      <div className="grid gap-2">
        <Label htmlFor="email">Email</Label>
        <Input id="email" type="email" autoComplete="email" {...register("email")} />
        {errors.email && (
          <p className="text-sm text-red-600">{errors.email.message}</p>
        )}
      </div>
      <div className="grid gap-2">
        <Label htmlFor="password">Password</Label>
        <Input
          id="password"
          type="password"
          autoComplete="current-password"
          {...register("password")}
        />
        {errors.password && (
          <p className="text-sm text-red-600">{errors.password.message}</p>
        )}
      </div>
      <Button type="submit" className="w-full" disabled={login.isPending}>
        {login.isPending ? "Logging in…" : "Log in"}
      </Button>

      <div className="flex items-center gap-3 text-xs text-slate-400 my-2">
        <div className="h-px flex-1 bg-slate-200" />
        <span>or</span>
        <div className="h-px flex-1 bg-slate-200" />
      </div>

      <Button
        type="button"
        variant="outline"
        className="w-full"
        onClick={startGoogle}
      >
        Continue with Google
      </Button>

      <div className="text-sm text-center space-y-1">
        <p>
          <Link href="/forgot-password" className="underline text-slate-600">
            Forgot password?
          </Link>
        </p>
        <p>
          Don&apos;t have an account?{" "}
          <Link href="/signup" className="underline">
            Sign up
          </Link>
        </p>
      </div>
    </form>
  );
}

export default function LoginPage() {
  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <Suspense fallback={null}>
        <FlashFromQuery />
      </Suspense>
      <LoginForm />
    </div>
  );
}

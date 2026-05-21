"use client";

import { useRouter } from "next/navigation";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useSignup } from "@/hooks/useAuth";
import { api, ApiError } from "@/lib/api";

const schema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
  name: z.string().optional(),
});

type FormData = z.infer<typeof schema>;

export default function SignupPage() {
  const router = useRouter();
  const signup = useSignup();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  const startGoogle = async () => {
    try {
      const { url } = await api.get<{ url: string }>("/api/v1/auth/google/begin");
      window.location.href = url;
    } catch {
      toast.error("Could not start Google sign-up");
    }
  };

  const onSubmit = (data: FormData) => {
    const timezone =
      typeof Intl !== "undefined"
        ? Intl.DateTimeFormat().resolvedOptions().timeZone
        : undefined;
    signup.mutate(
      { ...data, timezone },
      {
        onSuccess: () => {
          toast.success("Account created!");
          router.push("/dashboard");
        },
        onError: (err) => {
          if (err instanceof ApiError && err.body) {
            const body = err.body as Record<string, unknown>;
            const firstField = Object.keys(body)[0];
            const firstValue = body[firstField];
            const message = Array.isArray(firstValue)
              ? String(firstValue[0])
              : typeof firstValue === "string"
                ? firstValue
                : "Sign-up failed";
            toast.error(message);
          } else {
            toast.error("Sign-up failed");
          }
        },
      },
    );
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <form
        onSubmit={handleSubmit(onSubmit)}
        className="w-full max-w-sm space-y-4"
      >
        <h1 className="text-2xl font-bold">Create your Tlearning account</h1>
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
            autoComplete="new-password"
            {...register("password")}
          />
          {errors.password && (
            <p className="text-sm text-red-600">{errors.password.message}</p>
          )}
        </div>
        <div className="grid gap-2">
          <Label htmlFor="name">Name (optional)</Label>
          <Input id="name" type="text" autoComplete="name" {...register("name")} />
        </div>
        <Button type="submit" className="w-full" disabled={signup.isPending}>
          {signup.isPending ? "Creating account…" : "Sign up"}
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

        <p className="text-sm text-center">
          Already have an account?{" "}
          <Link href="/login" className="underline">
            Log in
          </Link>
        </p>
      </form>
    </div>
  );
}

"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/components/AuthProvider";
import { createClient } from "@/lib/supabase/client";

export default function LoginForm() {
  const router = useRouter();
  const params = useSearchParams();
  const next = params.get("next") || "/";
  const { authConfigured, authConfig } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!authConfigured || !authConfig) return;
    setBusy(true);
    setError(null);
    try {
      const supabase = createClient(authConfig);
      const { error: err } = await supabase.auth.signInWithPassword({ email, password });
      if (err) throw err;
      router.replace(next);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign in failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-paper px-4">
      <div className="card w-full max-w-md p-6 shadow-panel">
        <div className="mb-6">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-moss text-sm font-bold text-white">
            A
          </div>
          <h1 className="mt-4 text-xl font-semibold tracking-tight text-slate-900">Sign in to AdzMate</h1>
          <p className="mt-1 text-sm text-slate-500">Access your workspace campaigns and approvals.</p>
        </div>

        {!authConfigured ? (
          <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-950">
            Supabase is not configured. Add{" "}
            <code className="rounded bg-white px-1">SUPABASE_URL</code> and{" "}
            <code className="rounded bg-white px-1">SUPABASE_ANON_KEY</code> to{" "}
            <code className="rounded bg-white px-1">apps/web/.env.local</code> (or{" "}
            <code className="rounded bg-white px-1">apps/web/.env</code>), then restart the
            web app. Without them, the API runs in local demo mode (no login).
          </div>
        ) : (
          <form onSubmit={onSubmit} className="space-y-4">
            <label className="label">
              Email
              <input
                type="email"
                required
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input"
              />
            </label>
            <label className="label">
              Password
              <input
                type="password"
                required
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input"
              />
            </label>
            {error && (
              <div className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-900">
                {error}
              </div>
            )}
            <button type="submit" disabled={busy} className="btn-primary w-full">
              {busy ? "Signing in…" : "Sign in"}
            </button>
          </form>
        )}

        <p className="mt-5 text-center text-sm text-slate-500">
          No account?{" "}
          <Link href="/signup" className="font-medium text-moss hover:underline">
            Create one
          </Link>
        </p>
      </div>
    </div>
  );
}

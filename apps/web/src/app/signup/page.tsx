"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { createClient, isSupabaseConfigured } from "@/lib/supabase/client";

export default function SignupPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const configured = isSupabaseConfigured();

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!configured) return;
    setBusy(true);
    setError(null);
    setInfo(null);
    try {
      const supabase = createClient();
      const { data, error: err } = await supabase.auth.signUp({ email, password });
      if (err) throw err;
      if (data.session) {
        router.replace("/");
        router.refresh();
        return;
      }
      setInfo("Check your email to confirm your account, then sign in.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign up failed");
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
          <h1 className="mt-4 text-xl font-semibold tracking-tight text-slate-900">Create your account</h1>
          <p className="mt-1 text-sm text-slate-500">
            A personal workspace is created automatically on first sign-in.
          </p>
        </div>

        {!configured ? (
          <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-950">
            Configure Supabase env vars before creating accounts.
          </div>
        ) : (
          <form onSubmit={onSubmit} className="space-y-4">
            <label className="label">
              Work email
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
                minLength={6}
                autoComplete="new-password"
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
            {info && (
              <div className="rounded-lg border border-sky-200 bg-sky-50 px-3 py-2 text-sm text-sky-950">
                {info}
              </div>
            )}
            <button type="submit" disabled={busy} className="btn-primary w-full">
              {busy ? "Creating…" : "Create account"}
            </button>
          </form>
        )}

        <p className="mt-5 text-center text-sm text-slate-500">
          Already have an account?{" "}
          <Link href="/login" className="font-medium text-moss hover:underline">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}

"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuth } from "@/components/AuthProvider";

export function AuthGate({ children }: { children: React.ReactNode }) {
  const { loading, authConfigured, session } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  const isAuthPage = pathname === "/login" || pathname === "/signup";

  useEffect(() => {
    if (loading) return;
    if (!authConfigured) return;
    if (!session && !isAuthPage) {
      router.replace(`/login?next=${encodeURIComponent(pathname)}`);
    }
    if (session && isAuthPage) {
      router.replace("/");
    }
  }, [authConfigured, isAuthPage, loading, pathname, router, session]);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-paper text-sm text-slate-500">
        Loading workspace…
      </div>
    );
  }

  if (authConfigured && !session && !isAuthPage) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-3 bg-paper px-4 text-center">
        <p className="text-sm text-slate-600">Redirecting to sign in…</p>
        <Link href="/login" className="btn-primary">
          Sign in
        </Link>
      </div>
    );
  }

  return <>{children}</>;
}

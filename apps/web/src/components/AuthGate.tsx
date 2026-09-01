"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuth } from "@/components/AuthProvider";
import { APP_HOME, isAuthRoute, isPublicRoute } from "@/lib/routes";

export function AuthGate({ children }: { children: React.ReactNode }) {
  const { loading, authConfigured, session } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  const isAuthPage = isAuthRoute(pathname);
  const isPublic = isPublicRoute(pathname);

  useEffect(() => {
    if (loading) return;
    if (!authConfigured) return;
    if (!session && !isPublic) {
      router.replace(`/login?next=${encodeURIComponent(pathname)}`);
    }
    if (session && isAuthPage) {
      router.replace(APP_HOME);
    }
  }, [authConfigured, isAuthPage, isPublic, loading, pathname, router, session]);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-paper text-sm text-slate-500">
        Loading workspace…
      </div>
    );
  }

  if (authConfigured && !session && !isPublic) {
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

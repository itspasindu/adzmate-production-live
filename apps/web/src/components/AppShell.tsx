"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { useAuth } from "@/components/AuthProvider";
import { createWorkspace } from "@/lib/api";
import { APP_HOME, isAuthRoute, isMarketingRoute } from "@/lib/routes";

const nav = [
  {
    href: APP_HOME,
    label: "My ads",
    description: "See & manage campaigns",
    icon: (
      <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="1.75">
        <path d="M4 6h16M4 12h16M4 18h10" strokeLinecap="round" />
      </svg>
    ),
  },
  {
    href: "/campaigns/new",
    label: "Publish ads",
    description: "Simple 3-step setup",
    icon: (
      <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="1.75">
        <path d="M12 5v14M5 12h14" strokeLinecap="round" />
      </svg>
    ),
  },
  {
    href: "/approvals",
    label: "Review queue",
    description: "Approve before going live",
    icon: (
      <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="1.75">
        <path d="M9 11l3 3L22 4" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11" strokeLinecap="round" />
      </svg>
    ),
  },
  {
    href: "/agents",
    label: "Agents & workflows",
    description: "How the AI works",
    icon: (
      <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="1.75">
        <path
          d="M12 3l1.5 4.5L18 9l-4.5 1.5L12 15l-1.5-4.5L6 9l4.5-1.5L12 3zM5 16l.8 2.2L8 19l-2.2.8L5 22l-.8-2.2L2 19l2.2-.8L5 16zM18 14l.6 1.8L20.4 16.4 18.6 17 18 18.8l-.6-1.8L15.6 16.4l1.8-.6L18 14z"
          strokeLinejoin="round"
        />
      </svg>
    ),
  },
  {
    href: "/settings",
    label: "Account",
    description: "Business & Facebook",
    icon: (
      <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="1.75">
        <path
          d="M12 15a3 3 0 100-6 3 3 0 000 6zM19.4 15a1.7 1.7 0 00.3 1.8l.1.1a2 2 0 11-2.8 2.8l-.1-.1a1.7 1.7 0 00-1.8-.3 1.7 1.7 0 00-1 1.5V21a2 2 0 11-4 0v-.1a1.7 1.7 0 00-1.1-1.5 1.7 1.7 0 00-1.8.3l-.1.1a2 2 0 11-2.8-2.8l.1-.1a1.7 1.7 0 00.3-1.8 1.7 1.7 0 00-1.5-1H3a2 2 0 110-4h.1a1.7 1.7 0 001.5-1 1.7 1.7 0 00-.3-1.8l-.1-.1a2 2 0 112.8-2.8l.1.1a1.7 1.7 0 001.8.3H9a1.7 1.7 0 001-1.5V3a2 2 0 114 0v.1a1.7 1.7 0 001 1.5 1.7 1.7 0 001.8-.3l.1-.1a2 2 0 112.8 2.8l-.1.1a1.7 1.7 0 00-.3 1.8V9c.2.6.7 1 1.5 1H21a2 2 0 110 4h-.1a1.7 1.7 0 00-1.5 1z"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    ),
  },
];
function isActive(pathname: string, href: string) {
  if (href === APP_HOME) return pathname === APP_HOME;
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [creatingWs, setCreatingWs] = useState(false);
  const {
    authConfigured,
    user,
    me,
    workspaces,
    workspaceId,
    workspace,
    setWorkspaceId,
    signOut,
    getAccessToken,
    refreshMe,
  } = useAuth();

  const isAuthPage = isAuthRoute(pathname);
  const isMarketingPage = isMarketingRoute(pathname);
  if (isAuthPage || isMarketingPage) {
    return <>{children}</>;
  }

  async function onCreateWorkspace() {
    const name = window.prompt("Workspace name", "New Workspace");
    if (!name?.trim()) return;
    setCreatingWs(true);
    try {
      const token = await getAccessToken();
      const ws = await createWorkspace(name.trim(), token);
      await refreshMe();
      setWorkspaceId(ws.id);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to create workspace");
    } finally {
      setCreatingWs(false);
    }
  }

  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[240px_1fr]">
      {mobileOpen && (
        <button
          aria-label="Close navigation"
          className="fixed inset-0 z-40 bg-slate-900/40 lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-50 flex w-[240px] flex-col bg-sidebar text-white transition-transform lg:static lg:translate-x-0 ${
          mobileOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex h-14 items-center gap-2.5 border-b border-white/10 px-5">
          <div className="flex h-7 w-7 items-center justify-center rounded-md bg-moss text-xs font-bold tracking-tight">
            A
          </div>
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold tracking-tight">AdzMate</p>
            <p className="truncate text-[11px] text-[var(--sidebar-muted)]">Publish ads easily</p>
          </div>
        </div>

        <div className="border-b border-white/10 px-3 py-3">
          <p className="mb-1.5 px-2 text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-500">
            Workspace
          </p>
          <select
            value={workspaceId || ""}
            onChange={(e) => setWorkspaceId(e.target.value)}
            className="w-full rounded-lg border border-white/10 bg-white/5 px-2.5 py-2 text-sm text-white outline-none focus:border-moss"
          >
            {workspaces.map((w) => (
              <option key={w.id} value={w.id} className="text-slate-900">
                {w.name}
              </option>
            ))}
          </select>
          <button
            type="button"
            disabled={creatingWs}
            onClick={onCreateWorkspace}
            className="mt-2 w-full rounded-lg px-2.5 py-1.5 text-left text-xs font-medium text-slate-400 transition hover:bg-white/5 hover:text-white"
          >
            + New workspace
          </button>
        </div>

        <nav className="flex-1 space-y-1 px-3 py-4">
          <p className="mb-2 px-2 text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-500">
            Navigate
          </p>
          {nav.map((item) => {
            const active = isActive(pathname, item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setMobileOpen(false)}
                className={`flex items-start gap-3 rounded-lg px-2.5 py-2.5 transition ${
                  active
                    ? "bg-[var(--sidebar-active)] text-white"
                    : "text-slate-300 hover:bg-[var(--sidebar-hover)] hover:text-white"
                }`}
              >
                <span className={`mt-0.5 ${active ? "text-moss" : "text-slate-400"}`}>{item.icon}</span>
                <span className="min-w-0">
                  <span className="block text-sm font-medium">{item.label}</span>
                  <span className="block text-[11px] text-slate-500">{item.description}</span>
                </span>
              </Link>
            );
          })}
        </nav>

        <div className="border-t border-white/10 px-4 py-4">
          <div className="rounded-lg bg-white/5 px-3 py-2.5">
            <p className="text-[11px] font-medium text-slate-400">
              {authConfigured ? "Signed in" : "Local demo mode"}
            </p>
            <p className="mt-0.5 truncate text-sm font-medium text-white">
              {user?.email || me?.email || "demo@local.dev"}
            </p>
            <p className="mt-0.5 truncate text-[11px] text-slate-500">
              {workspace ? `${workspace.name} · ${workspace.role}` : "No workspace"}
            </p>
            {authConfigured && (
              <button
                type="button"
                onClick={() => signOut()}
                className="mt-2 text-xs font-medium text-slate-400 hover:text-white"
              >
                Sign out
              </button>
            )}
          </div>
        </div>
      </aside>

      <div className="flex min-w-0 flex-col">
        <header className="sticky top-0 z-30 flex h-14 items-center justify-between gap-3 border-b border-[var(--line)] bg-white/90 px-4 backdrop-blur-md lg:px-8">
          <div className="flex items-center gap-3">
            <button
              type="button"
              className="btn-ghost -ml-1 px-2 lg:hidden"
              onClick={() => setMobileOpen(true)}
              aria-label="Open navigation"
            >
              <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.75">
                <path d="M4 7h16M4 12h16M4 17h16" strokeLinecap="round" />
              </svg>
            </button>
            <div className="hidden text-sm text-slate-500 sm:block">
              Upload a product → we create & publish ads
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="hidden items-center gap-1.5 rounded-full border border-[var(--line)] bg-paper px-2.5 py-1 text-[11px] font-medium text-slate-600 sm:inline-flex">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
              {authConfigured ? "Signed in" : "Demo mode"}
            </span>
            <Link href="/campaigns/new" className="btn-primary">
              Publish ads
            </Link>
          </div>
        </header>
        <main className="flex-1 animate-fade-in px-4 py-6 lg:px-8 lg:py-8">{children}</main>
      </div>
    </div>
  );
}

"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { APP_HOME } from "@/lib/routes";
import { FOOTER_LINKS, NAV_LINKS, SITE } from "@/lib/marketing";

function NavLink({ href, label }: { href: string; label: string }) {
  const pathname = usePathname();
  const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
  return (
    <Link
      href={href}
      className={`text-sm font-medium transition ${
        active ? "text-[var(--moss)]" : "text-slate-600 hover:text-slate-900"
      }`}
    >
      {label}
    </Link>
  );
}

export function MarketingShell({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-50 border-b border-[var(--line)] bg-white/90 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-4 lg:px-6">
          <Link href="/" className="flex items-center gap-2.5">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--moss)] text-sm font-bold text-white">
              A
            </span>
            <span className="text-base font-semibold tracking-tight text-slate-900">{SITE.name}</span>
          </Link>

          <nav className="hidden items-center gap-8 md:flex">
            {NAV_LINKS.map((link) => (
              <NavLink key={link.href} href={link.href} label={link.label} />
            ))}
          </nav>

          <div className="hidden items-center gap-2 md:flex">
            <Link href="/login" className="btn-ghost">
              Sign in
            </Link>
            <Link href="/signup" className="btn-primary">
              Get started
            </Link>
          </div>

          <button
            type="button"
            className="btn-ghost px-2 md:hidden"
            aria-label="Open menu"
            onClick={() => setOpen(true)}
          >
            <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.75">
              <path d="M4 7h16M4 12h16M4 17h16" strokeLinecap="round" />
            </svg>
          </button>
        </div>

        {open && (
          <>
            <button
              type="button"
              className="fixed inset-0 z-40 bg-slate-900/40 md:hidden"
              aria-label="Close menu"
              onClick={() => setOpen(false)}
            />
            <div className="fixed inset-y-0 right-0 z-50 w-[min(100%,280px)] border-l border-[var(--line)] bg-white p-5 shadow-xl md:hidden">
              <div className="mb-6 flex items-center justify-between">
                <span className="font-semibold text-slate-900">Menu</span>
                <button type="button" className="btn-ghost px-2" onClick={() => setOpen(false)}>
                  ✕
                </button>
              </div>
              <nav className="flex flex-col gap-4">
                {NAV_LINKS.map((link) => (
                  <Link
                    key={link.href}
                    href={link.href}
                    onClick={() => setOpen(false)}
                    className="text-base font-medium text-slate-700"
                  >
                    {link.label}
                  </Link>
                ))}
              </nav>
              <div className="mt-8 flex flex-col gap-2">
                <Link href="/login" className="btn-secondary w-full" onClick={() => setOpen(false)}>
                  Sign in
                </Link>
                <Link href="/signup" className="btn-primary w-full" onClick={() => setOpen(false)}>
                  Get started
                </Link>
              </div>
            </div>
          </>
        )}
      </header>

      <main className="flex-1">{children}</main>

      <footer className="border-t border-[var(--line)] bg-white">
        <div className="mx-auto max-w-6xl px-4 py-12 lg:px-6">
          <div className="grid gap-10 sm:grid-cols-2 lg:grid-cols-4">
            <div className="sm:col-span-2 lg:col-span-1">
              <Link href="/" className="flex items-center gap-2">
                <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--moss)] text-sm font-bold text-white">
                  A
                </span>
                <span className="font-semibold text-slate-900">{SITE.name}</span>
              </Link>
              <p className="mt-3 max-w-xs text-sm text-slate-500">{SITE.description}</p>
              <p className="mt-2 text-xs text-slate-400">{SITE.team}</p>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Product</p>
              <ul className="mt-3 space-y-2">
                {FOOTER_LINKS.product.map((link) => (
                  <li key={link.href}>
                    <Link href={link.href} className="text-sm text-slate-600 hover:text-[var(--moss)]">
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Company</p>
              <ul className="mt-3 space-y-2">
                {FOOTER_LINKS.company.map((link) => (
                  <li key={link.href}>
                    <Link href={link.href} className="text-sm text-slate-600 hover:text-[var(--moss)]">
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Legal</p>
              <ul className="mt-3 space-y-2">
                {FOOTER_LINKS.legal.map((link) => (
                  <li key={link.href}>
                    <Link href={link.href} className="text-sm text-slate-600 hover:text-[var(--moss)]">
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          </div>
          <div className="mt-10 flex flex-wrap items-center justify-between gap-3 border-t border-[var(--line)] pt-6 text-xs text-slate-400">
            <p>© {new Date().getFullYear()} AdzMate · Team SUDO</p>
            <div className="flex gap-4">
              <a href={`mailto:${SITE.email}`} className="hover:text-slate-600">
                {SITE.email}
              </a>
              <Link href={APP_HOME} className="hover:text-slate-600">
                Open app
              </Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

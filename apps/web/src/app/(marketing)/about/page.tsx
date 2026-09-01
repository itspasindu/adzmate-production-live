import type { Metadata } from "next";
import Link from "next/link";
import { CtaBand } from "@/components/marketing/CtaBand";
import { PageHero } from "@/components/marketing/PageHero";
import { SITE, TEAM } from "@/lib/marketing";

export const metadata: Metadata = {
  title: "About — AdzMate",
  description: "Team SUDO built AdzMate for IDEALIZE 2026 — multi-agent marketing automation for digital agencies.",
};

export default function AboutPage() {
  return (
    <>
      <PageHero
        eyebrow="About"
        title="We build tools that give agency managers their time back"
        description="AdzMate started at IDEALIZE 2026 as an Open Category project — a real, deployable platform, not a slide-deck prototype."
      />

      <section className="border-b border-[var(--line)] bg-white py-16 lg:py-20">
        <div className="mx-auto max-w-6xl px-4 lg:px-6">
          <div className="grid gap-10 lg:grid-cols-2">
            <div>
              <h2 className="text-2xl font-bold text-slate-900">Our mission</h2>
              <p className="mt-4 text-slate-600">
                Digital agencies manage dozens of client campaigns across Meta, Google, and TikTok. Managers spend
                hours switching dashboards, writing copy, and deciding when to pause spend — often too late.
              </p>
              <p className="mt-4 text-slate-600">
                AdzMate replaces that chaos with specialist AI agents that produce one clear recommendation, plus a
                human approval step before anything goes live. We believe automation should be transparent,
                auditable, and under your control.
              </p>
            </div>
            <div className="card p-6">
              <h3 className="font-semibold text-slate-900">By the numbers</h3>
              <dl className="mt-4 space-y-4">
                <div>
                  <dt className="text-xs font-medium uppercase tracking-wide text-slate-400">Event</dt>
                  <dd className="font-medium text-slate-900">IDEALIZE 2026 · Open Category</dd>
                </div>
                <div>
                  <dt className="text-xs font-medium uppercase tracking-wide text-slate-400">Host</dt>
                  <dd className="font-medium text-slate-900">AIESEC in University of Moratuwa</dd>
                </div>
                <div>
                  <dt className="text-xs font-medium uppercase tracking-wide text-slate-400">Stack</dt>
                  <dd className="font-medium text-slate-900">Next.js · FastAPI · Gemini · Meta API</dd>
                </div>
                <div>
                  <dt className="text-xs font-medium uppercase tracking-wide text-slate-400">Status</dt>
                  <dd className="font-medium text-emerald-600">Live on Vercel + Render</dd>
                </div>
              </dl>
            </div>
          </div>
        </div>
      </section>

      <section className="py-16 lg:py-20">
        <div className="mx-auto max-w-6xl px-4 lg:px-6">
          <h2 className="text-2xl font-bold text-slate-900">Team SUDO</h2>
          <p className="mt-2 text-slate-600">{SITE.team}</p>
          <div className="mt-8 grid gap-5 sm:grid-cols-3">
            {TEAM.map((member) => (
              <div key={member.name} className="card p-5">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[var(--moss)]/10 text-lg font-bold text-[var(--moss)]">
                  {member.name.charAt(0)}
                </div>
                <h3 className="mt-4 font-semibold text-slate-900">{member.name}</h3>
                <p className="mt-1 text-sm text-slate-600">{member.role}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="border-t border-[var(--line)] bg-white py-16 lg:py-20">
        <div className="mx-auto max-w-3xl px-4 text-center lg:px-6">
          <h2 className="text-2xl font-bold text-slate-900">Open source & transparent</h2>
          <p className="mt-3 text-slate-600">
            Our Agents & Workflows page labels every layer as real, optional, or simulated — because trust matters
            more than hype.
          </p>
          <Link href={SITE.github} className="btn-secondary mt-6 inline-flex" target="_blank" rel="noopener noreferrer">
            View on GitHub
          </Link>
        </div>
      </section>

      <CtaBand />
    </>
  );
}

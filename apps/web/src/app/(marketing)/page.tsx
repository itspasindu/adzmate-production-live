import type { Metadata } from "next";
import Link from "next/link";
import { CtaBand } from "@/components/marketing/CtaBand";
import { FeatureIcon } from "@/components/marketing/FeatureIcon";
import { APP_HOME } from "@/lib/routes";
import {
  AGENTS,
  FEATURES,
  PROBLEMS,
  SITE,
  STATS,
  TESTIMONIALS,
  WORKFLOW_STEPS,
} from "@/lib/marketing";

export const metadata: Metadata = {
  title: "AdzMate — Campaign Auto-Pilot for Digital Agencies",
  description: SITE.description,
};

export default function LandingPage() {
  return (
    <>
      {/* Hero */}
      <section className="relative overflow-hidden border-b border-[var(--line)]">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_60%_at_50%_-10%,rgba(24,119,242,0.12),transparent)]" />
        <div className="relative mx-auto max-w-6xl px-4 py-20 lg:px-6 lg:py-28">
          <p className="inline-flex items-center gap-2 rounded-full border border-[var(--line)] bg-white px-3 py-1 text-xs font-medium text-slate-600">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
            Multi-agent AI · Human approval · Meta publish
          </p>
          <h1 className="mt-6 max-w-3xl text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl lg:text-6xl">
            Turn ad chaos into one clear decision
          </h1>
          <p className="mt-5 max-w-2xl text-lg text-slate-600 lg:text-xl">
            {SITE.description} Paste a product brief — specialist agents collaborate, you approve, then AdzMate
            drafts creatives, deploys landing pages, and publishes to Meta Ads Manager.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link href="/signup" className="btn-primary px-5 py-2.5 text-base">
              Start free — no card required
            </Link>
            <Link href="/features" className="btn-secondary px-5 py-2.5 text-base">
              See how it works
            </Link>
            <Link href={APP_HOME} className="btn-ghost px-5 py-2.5 text-base">
              Open dashboard →
            </Link>
          </div>

          <div className="mt-16 grid gap-4 sm:grid-cols-3">
            {STATS.map((stat) => (
              <div key={stat.label} className="card p-5">
                <p className="text-3xl font-bold text-[var(--moss)]">{stat.value}</p>
                <p className="mt-1 font-semibold text-slate-900">{stat.label}</p>
                <p className="mt-0.5 text-sm text-slate-500">{stat.hint}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Problem */}
      <section className="border-b border-[var(--line)] bg-white py-16 lg:py-20">
        <div className="mx-auto max-w-6xl px-4 lg:px-6">
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[var(--moss)]">The problem</p>
          <h2 className="mt-2 max-w-2xl text-3xl font-bold tracking-tight text-slate-900">
            Agency managers drown in dashboards — not insights
          </h2>
          <div className="mt-10 grid gap-5 sm:grid-cols-2">
            {PROBLEMS.map((item) => (
              <div key={item.title} className="rounded-xl border border-[var(--line)] bg-[var(--paper)] p-5">
                <h3 className="font-semibold text-slate-900">{item.title}</h3>
                <p className="mt-2 text-sm text-slate-600">{item.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Agents */}
      <section className="border-b border-[var(--line)] py-16 lg:py-20">
        <div className="mx-auto max-w-6xl px-4 lg:px-6">
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[var(--moss)]">Multi-agent AI</p>
          <h2 className="mt-2 max-w-2xl text-3xl font-bold tracking-tight text-slate-900">
            Four specialists, one recommendation
          </h2>
          <p className="mt-3 max-w-2xl text-slate-600">
            Not a single chatbot — parallel agents with auditable rule gates produce LAUNCH, HOLD, or HALT.
          </p>
          <div className="mt-10 grid gap-5 sm:grid-cols-2">
            {AGENTS.map((agent) => (
              <div key={agent.name} className="card p-6">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h3 className="font-semibold text-slate-900">{agent.name}</h3>
                    <p className="text-xs font-medium uppercase tracking-wide text-[var(--moss)]">{agent.role}</p>
                  </div>
                </div>
                <p className="mt-3 text-sm text-slate-600">{agent.body}</p>
                <ul className="mt-4 flex flex-wrap gap-2">
                  {agent.outputs.map((o) => (
                    <li
                      key={o}
                      className="rounded-md bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600"
                    >
                      {o}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Workflow */}
      <section className="border-b border-[var(--line)] bg-white py-16 lg:py-20">
        <div className="mx-auto max-w-6xl px-4 lg:px-6">
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[var(--moss)]">Workflow</p>
          <h2 className="mt-2 text-3xl font-bold tracking-tight text-slate-900">Brief to live ads in five steps</h2>
          <ol className="mt-10 space-y-0">
            {WORKFLOW_STEPS.map((step, i) => (
              <li key={step.step} className="relative flex gap-6 pb-10 last:pb-0">
                {i < WORKFLOW_STEPS.length - 1 && (
                  <span className="absolute left-[1.125rem] top-10 h-full w-px bg-[var(--line)]" />
                )}
                <span className="relative z-10 flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[var(--moss)] text-xs font-bold text-white">
                  {step.step}
                </span>
                <div className="pt-1">
                  <h3 className="font-semibold text-slate-900">{step.title}</h3>
                  <p className="mt-1 text-sm text-slate-600">{step.body}</p>
                </div>
              </li>
            ))}
          </ol>
        </div>
      </section>

      {/* Features preview */}
      <section className="border-b border-[var(--line)] py-16 lg:py-20">
        <div className="mx-auto max-w-6xl px-4 lg:px-6">
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[var(--moss)]">Platform</p>
              <h2 className="mt-2 text-3xl font-bold tracking-tight text-slate-900">Everything agencies need</h2>
            </div>
            <Link href="/features" className="text-sm font-medium text-[var(--moss)] hover:underline">
              All features →
            </Link>
          </div>
          <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURES.slice(0, 6).map((f) => (
              <div key={f.title} className="card p-5">
                <FeatureIcon name={f.icon} />
                <h3 className="mt-3 font-semibold text-slate-900">{f.title}</h3>
                <p className="mt-1.5 text-sm text-slate-600">{f.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Decision badges */}
      <section className="border-b border-[var(--line)] bg-[var(--sidebar)] py-16 text-white lg:py-20">
        <div className="mx-auto max-w-6xl px-4 text-center lg:px-6">
          <h2 className="text-3xl font-bold tracking-tight">One signal. Three outcomes.</h2>
          <p className="mx-auto mt-3 max-w-xl text-slate-300">
            The Signal Aggregator combines creative readiness, brand sentiment, and ROAS into a single actionable
            decision — always with human approval before publish.
          </p>
          <div className="mt-10 flex flex-wrap justify-center gap-4">
            <span className="rounded-lg bg-emerald-500/20 px-5 py-3 text-lg font-bold text-emerald-300 ring-1 ring-emerald-500/30">
              LAUNCH
            </span>
            <span className="rounded-lg bg-amber-500/20 px-5 py-3 text-lg font-bold text-amber-300 ring-1 ring-amber-500/30">
              HOLD
            </span>
            <span className="rounded-lg bg-rose-500/20 px-5 py-3 text-lg font-bold text-rose-300 ring-1 ring-rose-500/30">
              HALT
            </span>
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="border-b border-[var(--line)] bg-white py-16 lg:py-20">
        <div className="mx-auto max-w-6xl px-4 lg:px-6">
          <h2 className="text-center text-2xl font-bold text-slate-900">Built for real agency workflows</h2>
          <div className="mt-10 grid gap-6 sm:grid-cols-2">
            {TESTIMONIALS.map((t) => (
              <blockquote key={t.author} className="card p-6">
                <p className="text-slate-700">&ldquo;{t.quote}&rdquo;</p>
                <footer className="mt-4 text-sm">
                  <p className="font-semibold text-slate-900">{t.author}</p>
                  <p className="text-slate-500">{t.role}</p>
                </footer>
              </blockquote>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing teaser */}
      <section className="border-b border-[var(--line)] py-16 lg:py-20">
        <div className="mx-auto max-w-6xl px-4 text-center lg:px-6">
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[var(--moss)]">Pricing</p>
          <h2 className="mt-2 text-3xl font-bold text-slate-900">Plans from $49/month</h2>
          <p className="mx-auto mt-3 max-w-lg text-slate-600">
            Starter for freelancers, Pro for growing agencies, custom Agency for teams at scale.
          </p>
          <Link href="/pricing" className="btn-primary mt-8 inline-flex">
            View pricing
          </Link>
        </div>
      </section>

      <CtaBand />
    </>
  );
}

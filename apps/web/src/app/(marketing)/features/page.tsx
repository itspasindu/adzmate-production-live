import type { Metadata } from "next";
import Link from "next/link";
import { CtaBand } from "@/components/marketing/CtaBand";
import { FeatureIcon } from "@/components/marketing/FeatureIcon";
import { PageHero } from "@/components/marketing/PageHero";
import { AGENTS, FEATURES, WORKFLOW_STEPS } from "@/lib/marketing";

export const metadata: Metadata = {
  title: "Features — AdzMate",
  description: "Multi-agent orchestration, Meta publish, landing deploy, optimization rules, and human-in-the-loop approvals.",
};

export default function FeaturesPage() {
  return (
    <>
      <PageHero
        eyebrow="Features"
        title="Every layer of campaign automation — with humans in control"
        description="From parallel AI agents to Meta Ads Manager publish, AdzMate covers the full launch lifecycle for digital agencies."
      >
        <Link href="/signup" className="btn-primary">
          Get started
        </Link>
        <Link href="/pricing" className="btn-secondary">
          View pricing
        </Link>
      </PageHero>

      <section className="py-16 lg:py-20">
        <div className="mx-auto max-w-6xl px-4 lg:px-6">
          <h2 className="text-2xl font-bold text-slate-900">Platform capabilities</h2>
          <div className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map((f) => (
              <div key={f.title} className="card p-6">
                <FeatureIcon name={f.icon} />
                <h3 className="mt-3 font-semibold text-slate-900">{f.title}</h3>
                <p className="mt-2 text-sm text-slate-600">{f.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="border-y border-[var(--line)] bg-white py-16 lg:py-20">
        <div className="mx-auto max-w-6xl px-4 lg:px-6">
          <h2 className="text-2xl font-bold text-slate-900">Agent architecture</h2>
          <p className="mt-2 max-w-2xl text-slate-600">
            Each agent is a specialist module. They run concurrently via asyncio.gather — one failure does not
            stop the pipeline.
          </p>
          <div className="mt-8 grid gap-5 sm:grid-cols-2">
            {AGENTS.map((agent) => (
              <div key={agent.name} className="rounded-xl border border-[var(--line)] p-5">
                <h3 className="font-semibold text-slate-900">{agent.name}</h3>
                <p className="text-xs font-medium text-[var(--moss)]">{agent.role}</p>
                <p className="mt-2 text-sm text-slate-600">{agent.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="py-16 lg:py-20">
        <div className="mx-auto max-w-6xl px-4 lg:px-6">
          <h2 className="text-2xl font-bold text-slate-900">End-to-end workflow</h2>
          <div className="mt-8 grid gap-4 lg:grid-cols-5">
            {WORKFLOW_STEPS.map((step) => (
              <div key={step.step} className="card p-4">
                <span className="text-xs font-bold text-[var(--moss)]">{step.step}</span>
                <h3 className="mt-2 text-sm font-semibold text-slate-900">{step.title}</h3>
                <p className="mt-1 text-xs text-slate-600">{step.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <CtaBand title="See AdzMate in action" description="Create your first campaign in minutes — upload a product photo and let agents do the rest." />
    </>
  );
}

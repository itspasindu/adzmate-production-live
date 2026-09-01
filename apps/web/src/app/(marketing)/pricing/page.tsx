import type { Metadata } from "next";
import Link from "next/link";
import { CtaBand } from "@/components/marketing/CtaBand";
import { PageHero } from "@/components/marketing/PageHero";
import { PRICING_TIERS } from "@/lib/marketing";

export const metadata: Metadata = {
  title: "Pricing — AdzMate",
  description: "Starter, Pro, and Agency plans for digital marketing teams. From $49/month.",
};

export default function PricingPage() {
  return (
    <>
      <PageHero
        eyebrow="Pricing"
        title="Simple plans for agencies of every size"
        description="Start with a free trial. Upgrade when you're ready to publish live to Meta and scale across clients."
      />

      <section className="pb-16 lg:pb-20">
        <div className="mx-auto max-w-6xl px-4 lg:px-6">
          <div className="grid gap-6 lg:grid-cols-3">
            {PRICING_TIERS.map((tier) => (
              <div
                key={tier.id}
                className={`card flex flex-col p-6 ${
                  tier.highlighted ? "ring-2 ring-[var(--moss)] shadow-[var(--shadow-md)]" : ""
                }`}
              >
                {tier.highlighted && (
                  <span className="mb-3 inline-flex w-fit rounded-full bg-[var(--moss)] px-2.5 py-0.5 text-xs font-semibold text-white">
                    Most popular
                  </span>
                )}
                <h3 className="text-xl font-bold text-slate-900">{tier.name}</h3>
                <p className="mt-2 text-sm text-slate-600">{tier.description}</p>
                <div className="mt-6">
                  {tier.price != null ? (
                    <>
                      <span className="text-4xl font-bold text-slate-900">${tier.price}</span>
                      <span className="text-slate-500">/{tier.period}</span>
                    </>
                  ) : (
                    <span className="text-2xl font-bold text-slate-900">Custom</span>
                  )}
                </div>
                <ul className="mt-6 flex-1 space-y-2.5">
                  {tier.features.map((f) => (
                    <li key={f} className="flex gap-2 text-sm text-slate-700">
                      <span className="text-emerald-500">✓</span>
                      {f}
                    </li>
                  ))}
                </ul>
                <Link
                  href={tier.id === "agency" ? "/contact" : "/signup"}
                  className={`mt-8 w-full text-center ${tier.highlighted ? "btn-primary" : "btn-secondary"}`}
                >
                  {tier.cta}
                </Link>
              </div>
            ))}
          </div>

          <p className="mt-10 text-center text-sm text-slate-500">
            All plans include SSL, workspace isolation, and agent pipeline access. Meta OAuth required for live
            publish on Pro and above.{" "}
            <Link href="/faq" className="font-medium text-[var(--moss)] hover:underline">
              FAQ →
            </Link>
          </p>
        </div>
      </section>

      <CtaBand />
    </>
  );
}

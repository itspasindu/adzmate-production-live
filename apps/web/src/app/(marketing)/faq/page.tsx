import type { Metadata } from "next";
import Link from "next/link";
import { CtaBand } from "@/components/marketing/CtaBand";
import { PageHero } from "@/components/marketing/PageHero";
import { FAQ_ITEMS } from "@/lib/marketing";

export const metadata: Metadata = {
  title: "FAQ — AdzMate",
  description: "Frequently asked questions about AdzMate multi-agent campaigns, Meta publish, and pricing.",
};

export default function FaqPage() {
  return (
    <>
      <PageHero
        eyebrow="FAQ"
        title="Frequently asked questions"
        description="Everything you need to know about agents, approvals, Meta integration, and getting started."
      />

      <section className="pb-16 lg:pb-20">
        <div className="mx-auto max-w-3xl px-4 lg:px-6">
          <dl className="space-y-4">
            {FAQ_ITEMS.map((item) => (
              <div key={item.q} className="card p-5">
                <dt className="font-semibold text-slate-900">{item.q}</dt>
                <dd className="mt-2 text-sm text-slate-600">{item.a}</dd>
              </div>
            ))}
          </dl>
          <p className="mt-8 text-center text-sm text-slate-500">
            Still have questions?{" "}
            <Link href="/contact" className="font-medium text-[var(--moss)] hover:underline">
              Contact us
            </Link>
          </p>
        </div>
      </section>

      <CtaBand />
    </>
  );
}

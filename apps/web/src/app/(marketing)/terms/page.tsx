import type { Metadata } from "next";
import { PageHero } from "@/components/marketing/PageHero";
import { SITE } from "@/lib/marketing";

export const metadata: Metadata = {
  title: "Terms of Service — AdzMate",
  description: "Terms governing use of the AdzMate marketing automation platform.",
};

export default function TermsPage() {
  return (
    <>
      <PageHero eyebrow="Legal" title="Terms of Service" description={`Last updated: September 2026 · ${SITE.name}`} />

      <article className="mx-auto max-w-3xl px-4 pb-20 lg:px-6">
        <section className="space-y-4 text-sm text-slate-600">
          <h2 className="text-lg font-semibold text-slate-900">1. Acceptance</h2>
          <p>
            By accessing or using AdzMate, you agree to these Terms. If you use AdzMate on behalf of an agency or
            organization, you represent that you have authority to bind that entity.
          </p>

          <h2 className="text-lg font-semibold text-slate-900">2. Service description</h2>
          <p>
            AdzMate provides AI-assisted campaign creation, recommendation, approval workflows, landing page
            deployment, and optional Meta ad publishing. Features may be labeled as beta, simulated, or optional in
            the product UI.
          </p>

          <h2 className="text-lg font-semibold text-slate-900">3. Your responsibilities</h2>
          <ul className="list-disc space-y-2 pl-5">
            <li>You are responsible for all ad content, budgets, and compliance with Meta and local advertising laws.</li>
            <li>You must review and approve recommendations before publish when human-in-the-loop is enabled.</li>
            <li>You must not use AdzMate for illegal, misleading, or prohibited ad categories.</li>
            <li>You must keep account credentials secure and notify us of unauthorized access.</li>
          </ul>

          <h2 className="text-lg font-semibold text-slate-900">4. AI-generated content</h2>
          <p>
            Agent outputs (copy, images, recommendations) are suggestions — not guaranteed to perform or comply with
            platform policies. You remain solely responsible for published ads and spend.
          </p>

          <h2 className="text-lg font-semibold text-slate-900">5. Meta & third-party platforms</h2>
          <p>
            Use of Meta Marketing API is subject to Meta&apos;s Platform Terms and Advertising Policies. AdzMate is
            not affiliated with Meta. Service interruptions caused by third-party API changes are outside our
            control.
          </p>

          <h2 className="text-lg font-semibold text-slate-900">6. Payment & subscriptions</h2>
          <p>
            Paid plans are billed monthly per the pricing page. Usage limits (campaigns, workspaces, ad accounts)
            apply per tier. Refunds are handled case-by-case for beta users.
          </p>

          <h2 className="text-lg font-semibold text-slate-900">7. Limitation of liability</h2>
          <p>
            AdzMate is provided &ldquo;as is&rdquo; during beta and hackathon phases. We are not liable for ad spend,
            lost revenue, or platform account actions resulting from use of the service, auto-pause settings, or
            AI recommendations.
          </p>

          <h2 className="text-lg font-semibold text-slate-900">8. Termination</h2>
          <p>
            We may suspend accounts that violate these Terms or abuse the API. You may stop using the service at any
            time and request data deletion.
          </p>

          <h2 className="text-lg font-semibold text-slate-900">9. Contact</h2>
          <p>
            Legal inquiries:{" "}
            <a href={`mailto:${SITE.email}`} className="text-[var(--moss)] hover:underline">
              {SITE.email}
            </a>
          </p>
        </section>
      </article>
    </>
  );
}

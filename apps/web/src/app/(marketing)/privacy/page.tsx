import type { Metadata } from "next";
import { PageHero } from "@/components/marketing/PageHero";
import { SITE } from "@/lib/marketing";

export const metadata: Metadata = {
  title: "Privacy Policy — AdzMate",
  description: "How AdzMate collects, uses, and protects your data.",
};

export default function PrivacyPage() {
  return (
    <>
      <PageHero eyebrow="Legal" title="Privacy Policy" description={`Last updated: September 2026 · ${SITE.name}`} />

      <article className="prose-adzmate mx-auto max-w-3xl px-4 pb-20 lg:px-6">
        <section className="space-y-4 text-sm text-slate-600">
          <h2 className="text-lg font-semibold text-slate-900">1. Overview</h2>
          <p>
            AdzMate (&ldquo;we&rdquo;, &ldquo;our&rdquo;, &ldquo;us&rdquo;) operates a marketing automation platform
            for digital agencies. This policy explains what data we collect when you use our web application, API,
            and Meta integration.
          </p>

          <h2 className="text-lg font-semibold text-slate-900">2. Data we collect</h2>
          <ul className="list-disc space-y-2 pl-5">
            <li>
              <strong>Account data:</strong> email address, name, workspace membership (via Supabase Auth).
            </li>
            <li>
              <strong>Campaign data:</strong> product briefs, images, budgets, targeting, agent outputs, and
              recommendations you create in the platform.
            </li>
            <li>
              <strong>Meta integration data:</strong> OAuth tokens (encrypted at rest), ad account IDs, page IDs,
              and campaign structure when you connect Meta.
            </li>
            <li>
              <strong>Usage data:</strong> server logs, API request metadata, and error reports for reliability.
            </li>
            <li>
              <strong>AI processing:</strong> brief text and comments may be sent to Google Gemini when LLM features
              are enabled.
            </li>
          </ul>

          <h2 className="text-lg font-semibold text-slate-900">3. How we use data</h2>
          <p>We use your data to:</p>
          <ul className="list-disc space-y-2 pl-5">
            <li>Run the multi-agent campaign pipeline and store results</li>
            <li>Publish and manage ads via Meta Marketing API when you authorize it</li>
            <li>Authenticate users and isolate workspaces</li>
            <li>Improve reliability, security, and product features</li>
          </ul>
          <p>We do not sell your personal data to third parties.</p>

          <h2 className="text-lg font-semibold text-slate-900">4. Third-party services</h2>
          <p>AdzMate integrates with:</p>
          <ul className="list-disc space-y-2 pl-5">
            <li>Supabase (authentication)</li>
            <li>Meta / Facebook (Marketing API, OAuth)</li>
            <li>Google Gemini (optional LLM enrichment)</li>
            <li>Vercel, Render, Cloudflare (hosting and storage)</li>
          </ul>
          <p>Each provider has its own privacy policy governing their handling of data.</p>

          <h2 className="text-lg font-semibold text-slate-900">5. Data retention & deletion</h2>
          <p>
            Campaign and workspace data is retained while your account is active. You may request workspace deletion
            by contacting {SITE.email}. Meta tokens are revoked when you disconnect your account.
          </p>

          <h2 className="text-lg font-semibold text-slate-900">6. Security</h2>
          <p>
            We encrypt Meta access tokens at rest, use HTTPS for all traffic, and scope API access by workspace.
            No system is 100% secure — report concerns to {SITE.email}.
          </p>

          <h2 className="text-lg font-semibold text-slate-900">7. Contact</h2>
          <p>
            Questions about this policy:{" "}
            <a href={`mailto:${SITE.email}`} className="text-[var(--moss)] hover:underline">
              {SITE.email}
            </a>
          </p>
        </section>
      </article>
    </>
  );
}

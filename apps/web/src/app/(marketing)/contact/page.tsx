"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { PageHero } from "@/components/marketing/PageHero";
import { SITE } from "@/lib/marketing";

export default function ContactPage() {
  const [sent, setSent] = useState(false);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    await new Promise((r) => setTimeout(r, 800));
    setSent(true);
    setBusy(false);
  }

  return (
    <>
      <PageHero
        eyebrow="Contact"
        title="Get in touch"
        description="Questions about AdzMate, Agency pricing, or a demo for your team? We'd love to hear from you."
      />

      <section className="pb-20">
        <div className="mx-auto grid max-w-6xl gap-10 px-4 lg:grid-cols-2 lg:px-6">
          <div className="card p-6 lg:p-8">
            {sent ? (
              <div className="py-8 text-center">
                <p className="text-lg font-semibold text-slate-900">Message received</p>
                <p className="mt-2 text-sm text-slate-600">
                  Thanks for reaching out. We&apos;ll get back to you at the email you provided.
                </p>
                <button type="button" className="btn-secondary mt-6" onClick={() => setSent(false)}>
                  Send another
                </button>
              </div>
            ) : (
              <form onSubmit={onSubmit} className="space-y-4">
                <label className="label">
                  Name
                  <input name="name" required className="input" placeholder="Your name" />
                </label>
                <label className="label">
                  Email
                  <input name="email" type="email" required className="input" placeholder="you@agency.com" />
                </label>
                <label className="label">
                  Company
                  <input name="company" className="input" placeholder="Agency or brand name" />
                </label>
                <label className="label">
                  Message
                  <textarea
                    name="message"
                    required
                    rows={5}
                    className="input resize-y"
                    placeholder="Tell us about your use case…"
                  />
                </label>
                <button type="submit" disabled={busy} className="btn-primary w-full">
                  {busy ? "Sending…" : "Send message"}
                </button>
              </form>
            )}
          </div>

          <div className="space-y-6">
            <div className="card p-6">
              <h3 className="font-semibold text-slate-900">Email</h3>
              <a href={`mailto:${SITE.email}`} className="mt-2 block text-[var(--moss)] hover:underline">
                {SITE.email}
              </a>
            </div>
            <div className="card p-6">
              <h3 className="font-semibold text-slate-900">Sales & Agency plans</h3>
              <p className="mt-2 text-sm text-slate-600">
                For custom Agency pricing, white-label, or onboarding multiple workspaces, use the form or email us
                directly.
              </p>
            </div>
            <div className="card p-6">
              <h3 className="font-semibold text-slate-900">Support</h3>
              <p className="mt-2 text-sm text-slate-600">
                Existing users: check the{" "}
                <Link href="/faq" className="font-medium text-[var(--moss)] hover:underline">
                  FAQ
                </Link>{" "}
                or open the{" "}
                <Link href="/dashboard" className="font-medium text-[var(--moss)] hover:underline">
                  dashboard
                </Link>
                .
              </p>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}

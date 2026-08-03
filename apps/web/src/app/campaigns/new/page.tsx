"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import { createCampaignForm } from "@/lib/api";
import { Alert, PageHeader } from "@/components/ui";
import { useApiAuth } from "@/lib/useApiAuth";

const OBJECTIVES = [
  { value: "sales", label: "Get sales", hint: "People buy your product" },
  { value: "leads", label: "Get leads", hint: "People leave their contact" },
  { value: "traffic", label: "Get website visits", hint: "Send people to your link" },
  { value: "engagement", label: "Get engagement", hint: "Likes, comments, shares" },
] as const;

const STEPS = ["Your product", "Who should see it", "Budget & goal"] as const;

export default function NewCampaignPage() {
  const router = useRouter();
  const { withAuth } = useApiAuth();
  const [step, setStep] = useState(0);
  const [files, setFiles] = useState<File[]>([]);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [objective, setObjective] = useState("sales");
  const [showMore, setShowMore] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!files[0]) {
      setPreviewUrl(null);
      return;
    }
    const url = URL.createObjectURL(files[0]);
    setPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [files]);

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!files[0]) {
      setError("Please add a product photo first.");
      setStep(0);
      return;
    }
    setBusy(true);
    setError(null);
    const fd = new FormData(e.currentTarget);
    const productTitle = String(fd.get("product_name") || "");
    const brand = String(fd.get("brand_name") || productTitle);
    const description = String(fd.get("product_description") || "");
    const campaignName =
      String(fd.get("name") || "").trim() ||
      `${productTitle} ads`.trim();

    const payload = {
      name: campaignName,
      client_name: brand,
      brand_name: brand,
      product_name: productTitle,
      product_description: description,
      brief: description,
      product_url: String(fd.get("product_url") || "") || null,
      objective,
      goal: objective === "sales" ? "conversions" : objective,
      daily_budget: Number(fd.get("daily_budget") || 20),
      duration_days: Number(fd.get("duration_days") || 14),
      target_country: String(fd.get("target_country") || "United States"),
      target_location: String(fd.get("target_location") || ""),
      age_min: Number(fd.get("age_min") || 18),
      age_max: Number(fd.get("age_max") || 55),
      gender: String(fd.get("gender") || "all"),
      language: String(fd.get("language") || "en"),
      brand_primary: String(fd.get("brand_primary") || "#1877F2"),
      brand_accent: String(fd.get("brand_accent") || "#0866FF"),
      scenario: String(fd.get("scenario") || "healthy"),
      platforms: ["meta", "google", "tiktok"],
    };
    try {
      const opts = await withAuth();
      const campaign = await createCampaignForm(payload, files[0], opts);
      router.push(`/campaigns/${campaign.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create ads");
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl">
      <PageHeader
        breadcrumb={
          <Link href="/" className="text-sm text-slate-500 hover:text-moss">
            ← My ads
          </Link>
        }
        title="Publish ads"
        description="Three simple steps. We write the ad copy, pick audiences, and prepare everything for Facebook & Instagram."
      />

      <ol className="mb-6 grid grid-cols-3 gap-2">
        {STEPS.map((label, i) => (
          <li key={label}>
            <button
              type="button"
              onClick={() => setStep(i)}
              className={`w-full rounded-xl border px-2 py-2.5 text-left transition ${
                step === i
                  ? "border-moss/40 bg-blue-50"
                  : i < step
                    ? "border-emerald-200 bg-emerald-50"
                    : "border-[var(--line)] bg-white"
              }`}
            >
              <span className="block text-[10px] font-semibold uppercase tracking-wide text-slate-400">
                Step {i + 1}
              </span>
              <span className="mt-0.5 block text-xs font-semibold text-slate-800 sm:text-sm">{label}</span>
            </button>
          </li>
        ))}
      </ol>

      <form onSubmit={onSubmit} className="space-y-4">
        <section className={`card p-5 ${step === 0 ? "" : "hidden"}`}>
          <h2 className="text-lg font-semibold text-slate-900">What are you advertising?</h2>
          <p className="mt-1 text-sm text-slate-500">Add a clear photo — we turn it into ready-to-run ads.</p>

          <label className="mt-5 flex cursor-pointer flex-col items-center justify-center rounded-xl border border-dashed border-[var(--line)] bg-slate-50 px-4 py-10 text-center transition hover:border-moss/40 hover:bg-white">
            <input
              type="file"
              accept="image/png,image/jpeg,image/webp,image/gif"
              className="hidden"
              onChange={(e) => {
                const next = Array.from(e.target.files || []);
                if (next.some((f) => f.size > 8 * 1024 * 1024)) {
                  setError("Photo must be under 8MB");
                  return;
                }
                setError(null);
                setFiles(next);
              }}
            />
            {previewUrl ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={previewUrl} alt="Product" className="mb-3 h-40 w-auto rounded-lg object-contain" />
            ) : (
              <span className="mb-2 flex h-12 w-12 items-center justify-center rounded-full bg-white text-2xl text-moss ring-1 ring-[var(--line)]">
                +
              </span>
            )}
            <span className="text-sm font-medium text-slate-800">
              {files[0] ? files[0].name : "Tap to upload product photo"}
            </span>
            <span className="mt-1 text-xs text-slate-500">PNG or JPG · plain background works best</span>
          </label>

          <div className="mt-4 space-y-3">
            <label className="label">
              Product name
              <input name="product_name" required className="input" placeholder="e.g. Running Shoes" defaultValue="Summit Watch" />
            </label>
            <label className="label">
              Short description
              <textarea
                name="product_description"
                required
                rows={3}
                className="input"
                placeholder="What makes it special? Who is it for?"
                defaultValue="Rugged smartwatch for trail runners with multi-day battery and night visibility."
              />
            </label>
            <label className="label">
              Website or shop link
              <input name="product_url" type="url" className="input" placeholder="https://yoursite.com/product" defaultValue="https://example.com/summit-watch" />
            </label>
            <label className="label">
              Brand name
              <input name="brand_name" className="input" placeholder="Your brand" defaultValue="Atlas" />
            </label>
          </div>

          <div className="mt-5 flex justify-end">
            <button type="button" className="btn-primary" onClick={() => setStep(1)}>
              Next: Who should see it
            </button>
          </div>
        </section>

        <section className={`card p-5 ${step === 1 ? "" : "hidden"}`}>
          <h2 className="text-lg font-semibold text-slate-900">Who should see your ads?</h2>
          <p className="mt-1 text-sm text-slate-500">Tell us roughly who to reach — we suggest smarter audiences automatically.</p>
          <div className="mt-5 grid gap-3 sm:grid-cols-2">
            <label className="label sm:col-span-2">
              Country
              <input name="target_country" required className="input" defaultValue="United States" />
            </label>
            <label className="label sm:col-span-2">
              City or region (optional)
              <input name="target_location" className="input" placeholder="e.g. California" defaultValue="California" />
            </label>
            <label className="label">
              Youngest age
              <input name="age_min" type="number" className="input" defaultValue="25" min={13} max={65} />
            </label>
            <label className="label">
              Oldest age
              <input name="age_max" type="number" className="input" defaultValue="45" min={13} max={65} />
            </label>
            <label className="label">
              Gender
              <select name="gender" className="input" defaultValue="all">
                <option value="all">Everyone</option>
                <option value="female">Women</option>
                <option value="male">Men</option>
              </select>
            </label>
            <label className="label">
              Language
              <select name="language" className="input" defaultValue="en">
                <option value="en">English</option>
                <option value="es">Spanish</option>
                <option value="fr">French</option>
                <option value="hi">Hindi</option>
                <option value="si">Sinhala</option>
              </select>
            </label>
          </div>
          <div className="mt-5 flex justify-between gap-2">
            <button type="button" className="btn-secondary" onClick={() => setStep(0)}>
              Back
            </button>
            <button type="button" className="btn-primary" onClick={() => setStep(2)}>
              Next: Budget
            </button>
          </div>
        </section>

        <section className={`card p-5 ${step === 2 ? "" : "hidden"}`}>
          <h2 className="text-lg font-semibold text-slate-900">Budget & goal</h2>
          <p className="mt-1 text-sm text-slate-500">How much to spend each day, and what success looks like.</p>

          <div className="mt-5 grid gap-3 sm:grid-cols-2">
            <label className="label">
              Daily budget (USD)
              <input name="daily_budget" type="number" required className="input" defaultValue="20" min={1} />
            </label>
            <label className="label">
              Run for (days)
              <input name="duration_days" type="number" required className="input" defaultValue="14" min={1} />
            </label>
          </div>

          <p className="mt-5 text-sm font-medium text-slate-800">What do you want?</p>
          <div className="mt-2 grid gap-2 sm:grid-cols-2">
            {OBJECTIVES.map((opt) => (
              <button
                key={opt.value}
                type="button"
                onClick={() => setObjective(opt.value)}
                className={`rounded-xl border px-3 py-3 text-left transition ${
                  objective === opt.value ? "border-moss/50 bg-blue-50" : "border-[var(--line)] hover:border-moss/30"
                }`}
              >
                <span className="block text-sm font-semibold text-slate-900">{opt.label}</span>
                <span className="mt-0.5 block text-xs text-slate-500">{opt.hint}</span>
              </button>
            ))}
          </div>
          <input type="hidden" name="objective" value={objective} />

          <button
            type="button"
            className="mt-5 text-sm font-medium text-moss hover:underline"
            onClick={() => setShowMore((v) => !v)}
          >
            {showMore ? "Hide extra options" : "Show extra options (optional)"}
          </button>
          {showMore && (
            <div className="mt-3 grid gap-3 rounded-xl border border-[var(--line)] bg-slate-50 p-4 sm:grid-cols-2">
              <label className="label">
                Campaign name
                <input name="name" className="input" placeholder="Auto-named if empty" />
              </label>
              <label className="label">
                Demo scenario
                <select name="scenario" className="input" defaultValue="healthy">
                  <option value="healthy">Healthy</option>
                  <option value="poor_roas">Poor ROAS</option>
                  <option value="mixed_sentiment">Mixed sentiment</option>
                </select>
              </label>
              <label className="label">
                Primary color
                <input name="brand_primary" className="input" defaultValue="#1877F2" />
              </label>
              <label className="label">
                Accent color
                <input name="brand_accent" className="input" defaultValue="#0866FF" />
              </label>
            </div>
          )}

          {error && (
            <div className="mt-4">
              <Alert>{error}</Alert>
            </div>
          )}

          <div className="mt-6 flex flex-wrap items-center justify-between gap-3">
            <button type="button" className="btn-secondary" onClick={() => setStep(1)}>
              Back
            </button>
            <button type="submit" disabled={busy} className="btn-primary min-w-[180px]">
              {busy ? "Creating your ads…" : "Create my ads"}
            </button>
          </div>
          <p className="mt-3 text-center text-xs text-slate-500">
            Next you&apos;ll review the ads and tap Publish — nothing goes live until you say so.
          </p>
        </section>
      </form>
    </div>
  );
}

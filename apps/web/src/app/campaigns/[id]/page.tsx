"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import {
  actOnRecommendation,
  assetUrl,
  CampaignDetail,
  demoTick,
  eventsUrl,
  getCampaign,
  publishMetaCampaign,
  rebuildMetaDraft,
  recommendAudiences,
  runOptimizationTick,
  selectAudiences,
  setAutoPause,
  submitMetaReview,
  syncMetaMetrics,
} from "@/lib/api";
import { Alert, PageHeader, StatusBadge } from "@/components/ui";
import { useApiAuth } from "@/lib/useApiAuth";
import { useAuth } from "@/components/AuthProvider";
import {
  friendlyCampaignStatus,
  friendlyPublishStatus,
  nextSimpleAction,
} from "@/lib/friendly";

export default function CampaignDetailPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;
  const { withAuth, workspaceId } = useApiAuth();
  const { loading: authLoading } = useAuth();
  const [detail, setDetail] = useState<CampaignDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [view, setView] = useState<"simple" | "advanced">("simple");

  const refresh = useCallback(async () => {
    try {
      const opts = await withAuth();
      setDetail(await getCampaign(id, opts));
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    }
  }, [id, withAuth]);

  useEffect(() => {
    if (authLoading) return;

    let cancelled = false;
    let es: EventSource | null = null;
    let poll: ReturnType<typeof setInterval> | null = null;

    (async () => {
      await refresh();
      if (cancelled) return;
      poll = setInterval(() => {
        void refresh();
      }, 2500);
      const opts = await withAuth();
      if (cancelled) return;
      es = new EventSource(eventsUrl(id, opts));
      es.onmessage = () => void refresh();
      es.addEventListener("decision", () => void refresh());
      es.addEventListener("agents_finished", () => void refresh());
      es.addEventListener("deployed", () => void refresh());
      es.addEventListener("demo_tick", () => void refresh());
      es.addEventListener("status", () => void refresh());
    })();

    return () => {
      cancelled = true;
      if (poll) clearInterval(poll);
      es?.close();
    };
  }, [authLoading, workspaceId, id, refresh, withAuth]);

  async function onDemo(event: string) {
    setBusy(true);
    try {
      const opts = await withAuth();
      await demoTick(id, event, opts);
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Demo tick failed");
    } finally {
      setBusy(false);
    }
  }

  async function approvePrimary() {
    const pending = detail?.recommendations.find(
      (r) => r.status === "pending" && ["launch", "halt", "deploy"].includes(r.type),
    );
    if (!pending) return;
    setBusy(true);
    try {
      const opts = await withAuth();
      await actOnRecommendation(pending.id, "approve", opts);
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Approval failed");
    } finally {
      setBusy(false);
    }
  }

  if (!detail && !error) {
    return <p className="py-16 text-center text-sm text-slate-500">Loading campaign…</p>;
  }
  if (error && !detail) {
    return (
      <div className="mx-auto max-w-3xl py-10">
        <Alert>{error}</Alert>
      </div>
    );
  }
  if (!detail) return null;

  const { campaign, agents, signals, recommendations, timeline = [] } = detail;
  const autoPauseOn = campaign.auto_pause_enabled !== false;
  const creative = agents.find((a) => a.agent === "creative");
  const assets =
    (creative?.payload?.assets as Array<{
      format: string;
      headline: string;
      primary_text?: string;
      description?: string;
      cta?: string;
      url: string;
    }>) || [];
  const copyVariations =
    (creative?.payload?.copy_variations as Array<{
      angle?: string;
      headline: string;
      primary_text?: string;
      description?: string;
      cta?: string;
    }>) || [];
  const audiences =
    (creative?.payload?.audience_suggestions as Array<{
      name: string;
      rationale?: string;
      age_min?: number;
      age_max?: number;
      gender?: string;
      locations?: string[];
      languages?: string[];
      interests?: string[];
      estimated_reach?: string;
    }>) || [];
  const pendingDecision = recommendations.find(
    (r) => r.status === "pending" && ["launch", "halt", "deploy"].includes(r.type),
  );
  const action = nextSimpleAction(campaign);
  const selectedAudiences = (campaign.audiences?.selected || campaign.audiences?.recommended?.filter((a) => a.selected) || []).slice(0, 4);
  const simpleSteps = [
    {
      label: "Ads created",
      done: !["received", "agents_running", "aggregating"].includes(campaign.status) || assets.length > 0,
    },
    {
      label: "Ready to review",
      done: campaign.status === "awaiting_approval" || campaign.publish_status === "draft" || campaign.publish_status === "published" || campaign.status === "live",
    },
    {
      label: "Published",
      done: campaign.publish_status === "published" || campaign.status === "live",
    },
  ];

  return (
    <div className="mx-auto max-w-5xl">
      <PageHeader
        breadcrumb={
          <Link href="/" className="text-sm text-slate-500 hover:text-moss">
            ← My ads
          </Link>
        }
        title={campaign.product_name || campaign.name}
        description={campaign.product_description || campaign.brief}
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-full border border-[var(--line)] bg-white px-3 py-1.5 text-xs font-medium text-slate-700">
              {friendlyCampaignStatus(campaign.status)}
            </span>
            <div className="inline-flex rounded-lg border border-[var(--line)] bg-white p-0.5 text-xs font-medium">
              <button
                type="button"
                onClick={() => setView("simple")}
                className={`rounded-md px-3 py-1.5 ${view === "simple" ? "bg-moss text-white" : "text-slate-600"}`}
              >
                Simple
              </button>
              <button
                type="button"
                onClick={() => setView("advanced")}
                className={`rounded-md px-3 py-1.5 ${view === "advanced" ? "bg-moss text-white" : "text-slate-600"}`}
              >
                Technical
              </button>
            </div>
          </div>
        }
      />

      {error && (
        <div className="mb-4">
          <Alert>{error}</Alert>
        </div>
      )}

      {view === "simple" ? (
        <>
          <section className="card overflow-hidden p-0">
            <div className="bg-gradient-to-br from-blue-50 to-white px-5 py-6 sm:px-8">
              <p className="text-xs font-semibold uppercase tracking-wide text-moss">Your next step</p>
              <h2 className="mt-2 text-2xl font-semibold tracking-tight text-slate-900">{action.label}</h2>
              <p className="mt-2 max-w-xl text-sm text-slate-600">
                {action.kind === "wait" && "We're writing ad copy, designing creatives, and choosing audiences. This usually takes under a minute."}
                {action.kind === "publish" && "Your ads are ready as a draft. Nothing is live yet — tap Publish when you like what you see."}
                {action.kind === "done" && "Your ads are running. We'll automatically spend more on the ones that work best."}
                {action.kind === "done" &&
                  (campaign.meta_structure as { mode?: string; ads_manager_url?: string })?.mode ===
                    "meta_live" &&
                  (campaign.meta_structure as { ads_manager_url?: string })?.ads_manager_url && (
                    <>
                      {" "}
                      <a
                        href={(campaign.meta_structure as { ads_manager_url?: string }).ads_manager_url}
                        target="_blank"
                        rel="noreferrer"
                        className="font-medium text-moss underline"
                      >
                        Open in Meta Ads Manager
                      </a>
                    </>
                  )}
                {action.kind === "pause" && "Ads are paused or a pause was recommended. Check the review queue if needed."}
                {action.kind === "fix" && "Something failed while creating ads. Try creating again or open Technical for details."}
              </p>
              <div className="mt-5 flex flex-wrap gap-2">
                {pendingDecision && campaign.status === "awaiting_approval" && (
                  <button disabled={busy} onClick={approvePrimary} className="btn-primary text-base px-5 py-2.5">
                    {campaign.decision === "HALT" ? "Confirm pause" : "Publish to Ads Manager"}
                  </button>
                )}
                {campaign.publish_status !== "published" && campaign.meta_structure && campaign.status !== "awaiting_approval" && (
                  <button
                    disabled={busy}
                    className="btn-primary"
                    onClick={async () => {
                      setBusy(true);
                      try {
                        const opts = await withAuth();
                        await publishMetaCampaign(id, opts);
                        await refresh();
                      } catch (e) {
                        setError(e instanceof Error ? e.message : "Publish failed");
                      } finally {
                        setBusy(false);
                      }
                    }}
                  >
                    Publish to Ads Manager
                  </button>
                )}
                {campaign.landing_page_url && (
                  <a className="btn-secondary" href={campaign.landing_page_url} target="_blank" rel="noreferrer">
                    Preview landing page
                  </a>
                )}
                <Link href="/agents" className="btn-secondary">
                  See how AI works
                </Link>
              </div>
            </div>
            <div className="grid grid-cols-3 divide-x divide-[var(--line)] border-t border-[var(--line)]">
              {simpleSteps.map((s) => (
                <div key={s.label} className="px-3 py-3 text-center sm:px-4">
                  <p className={`text-xs font-semibold sm:text-sm ${s.done ? "text-emerald-700" : "text-slate-400"}`}>
                    {s.done ? "✓ " : ""}
                    {s.label}
                  </p>
                </div>
              ))}
            </div>
          </section>

          <section className="mt-5 grid gap-3 sm:grid-cols-3">
            <div className="card p-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Daily budget</p>
              <p className="mt-1 text-xl font-semibold text-slate-900">
                ${Number(campaign.daily_budget || 0).toFixed(0)}
                <span className="text-sm font-normal text-slate-500"> / day</span>
              </p>
            </div>
            <div className="card p-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Goal</p>
              <p className="mt-1 text-xl font-semibold capitalize text-slate-900">
                {campaign.objective || campaign.goal}
              </p>
            </div>
            <div className="card p-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Publish status</p>
              <p className="mt-1 text-sm font-semibold text-slate-900">
                {friendlyPublishStatus(campaign.publish_status)}
              </p>
            </div>
          </section>

          {assets.length > 0 && (
            <section className="mt-6">
              <h3 className="text-lg font-semibold text-slate-900">Your ad previews</h3>
              <p className="mt-1 text-sm text-slate-500">These are the creatives people will see.</p>
              <div className="mt-4 grid gap-3 sm:grid-cols-3">
                {assets.map((a) => (
                  <figure key={a.format} className="card overflow-hidden">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={assetUrl(a.url)} alt={a.headline} className="aspect-square w-full object-cover" />
                    <figcaption className="space-y-1 px-3 py-3">
                      <p className="text-sm font-semibold text-slate-900">{a.headline}</p>
                      {a.primary_text && <p className="text-xs text-slate-600">{a.primary_text}</p>}
                      {a.cta && (
                        <span className="inline-block rounded-md bg-blue-50 px-2 py-1 text-[11px] font-semibold text-moss">
                          Button: {a.cta}
                        </span>
                      )}
                    </figcaption>
                  </figure>
                ))}
              </div>
            </section>
          )}

          {selectedAudiences.length > 0 && (
            <section className="mt-6">
              <h3 className="text-lg font-semibold text-slate-900">Who we&apos;ll show ads to</h3>
              <p className="mt-1 text-sm text-slate-500">
                Suggested from your product. Switch to Technical to change selections.
              </p>
              <div className="mt-3 flex flex-wrap gap-2">
                {selectedAudiences.map((a) => (
                  <span
                    key={a.id || a.name}
                    className="rounded-full border border-[var(--line)] bg-white px-3 py-1.5 text-xs font-medium text-slate-700"
                  >
                    {a.name}
                  </span>
                ))}
              </div>
            </section>
          )}

          <section className="mt-6 card p-5">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h3 className="text-lg font-semibold text-slate-900">Auto-pause on ROAS drop</h3>
                <p className="mt-1 text-sm text-slate-500">
                  When on, a spend spike or negative flood pauses ads immediately and logs the action.
                </p>
              </div>
              <button
                type="button"
                role="switch"
                aria-checked={autoPauseOn}
                disabled={busy}
                className={`relative h-7 w-12 shrink-0 rounded-full transition-colors ${
                  autoPauseOn ? "bg-moss" : "bg-slate-300"
                }`}
                onClick={async () => {
                  setBusy(true);
                  try {
                    const opts = await withAuth();
                    await setAutoPause(id, !autoPauseOn, opts);
                    await refresh();
                  } catch (e) {
                    setError(e instanceof Error ? e.message : "Failed to update auto-pause");
                  } finally {
                    setBusy(false);
                  }
                }}
              >
                <span
                  className={`absolute top-0.5 h-6 w-6 rounded-full bg-white shadow transition-transform ${
                    autoPauseOn ? "left-5" : "left-0.5"
                  }`}
                />
              </button>
            </div>
            {campaign.publish_status === "published" && (
              <div className="mt-4 border-t border-[var(--line)] pt-4">
                <p className="text-sm font-medium text-slate-800">Simulate a problem (demo)</p>
                <div className="mt-2 flex flex-wrap gap-2">
                  <button disabled={busy} onClick={() => onDemo("spend_spike")} className="btn-secondary">
                    Spend spike / ROAS drop
                  </button>
                  <button disabled={busy} onClick={() => onDemo("negative_flood")} className="btn-secondary">
                    Negative comments
                  </button>
                  <button disabled={busy} onClick={() => onDemo("recover")} className="btn-secondary">
                    Recover
                  </button>
                </div>
              </div>
            )}
          </section>

          {campaign.publish_status === "published" && (
            <section className="mt-6 card p-5">
              <h3 className="text-lg font-semibold text-slate-900">Auto-optimize</h3>
              <p className="mt-1 text-sm text-slate-500">
                Simulate a few days to see budget move to winning ads (demo).
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                <button
                  type="button"
                  disabled={busy}
                  className="btn-secondary"
                  onClick={async () => {
                    setBusy(true);
                    try {
                      const opts = await withAuth();
                      await runOptimizationTick(id, { days: 1 }, opts);
                      await refresh();
                    } catch (e) {
                      setError(e instanceof Error ? e.message : "Failed");
                    } finally {
                      setBusy(false);
                    }
                  }}
                >
                  Run 1 day
                </button>
                <button
                  type="button"
                  disabled={busy}
                  className="btn-primary"
                  onClick={async () => {
                    setBusy(true);
                    try {
                      const opts = await withAuth();
                      await runOptimizationTick(id, { days: 3 }, opts);
                      await refresh();
                    } catch (e) {
                      setError(e instanceof Error ? e.message : "Failed");
                    } finally {
                      setBusy(false);
                    }
                  }}
                >
                  Run 3 days
                </button>
              </div>
              {campaign.optimization?.ads && campaign.optimization.ads.length > 0 && (
                <ul className="mt-4 space-y-2">
                  {campaign.optimization.ads.map((ad) => (
                    <li key={ad.ad_id || ad.name} className="flex items-center justify-between text-sm">
                      <span className="font-medium text-slate-800">{ad.name}</span>
                      <span className="text-slate-500">
                        {ad.status} · ${Number(ad.daily_budget || 0).toFixed(0)}/day · ROAS {Number(ad.roas || 0).toFixed(1)}x
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          )}

          <section className="mt-6">
            <h3 className="text-lg font-semibold text-slate-900">What the agents did</h3>
            <p className="mt-1 text-sm text-slate-500">Audit trail of pipeline steps, decisions, and auto-pause.</p>
            {timeline.length === 0 ? (
              <p className="mt-3 text-sm text-slate-500">No actions logged yet.</p>
            ) : (
              <ol className="mt-4 space-y-0 border-l-2 border-[var(--line)] pl-4">
                {timeline.slice(0, 12).map((ev) => (
                  <li key={ev.id} className="relative pb-4 last:pb-0">
                    <span
                      className={`absolute -left-[1.4rem] top-1.5 h-2.5 w-2.5 rounded-full ring-2 ring-white ${
                        ev.level === "error"
                          ? "bg-red-500"
                          : ev.level === "warning"
                            ? "bg-amber-500"
                            : "bg-moss"
                      }`}
                    />
                    <p className="text-sm font-medium text-slate-900">{ev.summary}</p>
                    <p className="mt-0.5 text-xs text-slate-500">
                      {ev.actor} · {ev.action} ·{" "}
                      {ev.created_at ? new Date(ev.created_at).toLocaleString() : ""}
                    </p>
                  </li>
                ))}
              </ol>
            )}
          </section>
        </>
      ) : (
        <>
          <div className="mb-4 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
            Technical view for demos and power users. Prefer{" "}
            <button type="button" className="font-semibold underline" onClick={() => setView("simple")}>
              Simple
            </button>{" "}
            for everyday publishing. Full agent diagrams also live on{" "}
            <Link href="/agents" className="font-semibold underline">
              Agents & workflows
            </Link>
            .
          </div>

          {campaign.warnings?.length > 0 && (
            <div className="mb-4">
              <Alert tone="warning">
                <strong>Degraded run:</strong> {campaign.warnings.join(" · ")}
              </Alert>
            </div>
          )}

          <section className="mb-4 card p-5">
            <h3 className="section-title">Product & targeting</h3>
            <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2 lg:grid-cols-3">
              <div>
                <dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">Product</dt>
                <dd className="mt-0.5 font-medium text-slate-900">{campaign.product_name}</dd>
              </div>
              <div>
                <dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">Objective</dt>
                <dd className="mt-0.5 font-medium capitalize text-slate-900">{campaign.objective || campaign.goal}</dd>
              </div>
              <div>
                <dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">Budget</dt>
                <dd className="mt-0.5 font-medium text-slate-900">
                  ${Number(campaign.daily_budget || 0).toFixed(0)}/day · {campaign.duration_days || "—"} days
                </dd>
              </div>
              <div className="sm:col-span-2">
                <dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">Description</dt>
                <dd className="mt-0.5 text-slate-700">{campaign.product_description || campaign.brief}</dd>
              </div>
              <div>
                <dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">Audience</dt>
                <dd className="mt-0.5 text-slate-700">
                  Ages {campaign.age_min ?? 18}–{campaign.age_max ?? 65} · {campaign.gender || "all"}
                </dd>
              </div>
            </dl>
          </section>

          <MetaAutomationPanels
            campaign={campaign}
            busy={busy}
            setBusy={setBusy}
            setError={setError}
            withAuth={withAuth}
            refresh={refresh}
            campaignId={id}
          />

          <section className="grid gap-4 lg:grid-cols-[1.35fr_1fr]">
            <div className="card p-5">
              <p className="text-[11px] font-semibold uppercase tracking-[0.1em] text-slate-500">Signal Aggregator</p>
              <h2 className="mt-2 text-2xl font-semibold tracking-tight text-slate-900">
                {campaign.decision || "Analyzing…"}
              </h2>
              <p className="mt-2 text-sm leading-relaxed text-slate-600">
                {campaign.decision_reason || "Waiting for parallel agents to finish."}
              </p>
              <div className="mt-5 flex flex-wrap gap-2">
                {pendingDecision && campaign.status === "awaiting_approval" && (
                  <button disabled={busy} onClick={approvePrimary} className="btn-primary">
                    {campaign.decision === "HALT" ? "Approve halt" : "Review & publish Meta"}
                  </button>
                )}
                <StatusBadge value={campaign.status} />
              </div>
            </div>
            <div className="card p-5">
              <h3 className="section-title">Performance signals</h3>
              {signals ? (
                <div className="mt-4 space-y-4">
                  <Gauge label="Creative ready" value={signals.creative_ready} />
                  <Gauge label="Brand sentiment" value={signals.brand_sentiment} />
                  <Gauge label="Spend burn" value={signals.spend_burn} />
                  <div className="grid grid-cols-2 gap-3 pt-1">
                    <div className="rounded-lg border border-[var(--line)] bg-slate-50 px-3 py-2.5">
                      <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">ROAS</p>
                      <p className="mt-0.5 text-lg font-semibold tabular-nums text-slate-900">{signals.roas.toFixed(2)}x</p>
                    </div>
                    <div className="rounded-lg border border-[var(--line)] bg-slate-50 px-3 py-2.5">
                      <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Spend</p>
                      <p className="mt-0.5 text-lg font-semibold tabular-nums text-slate-900">${signals.spend.toFixed(0)}</p>
                    </div>
                  </div>
                </div>
              ) : (
                <p className="mt-4 text-sm text-slate-500">Signals appear after aggregation.</p>
              )}
            </div>
          </section>

          <section className="mt-6">
            <h3 className="section-title mb-3">Specialist agents</h3>
            <div className="grid gap-3 md:grid-cols-3">
              {["creative", "sentiment", "strategy"].map((name) => {
                const run = agents.find((a) => a.agent === name);
                return (
                  <article key={name} className="card p-4">
                    <div className="flex items-center justify-between gap-2">
                      <h4 className="text-sm font-semibold capitalize text-slate-900">{name}</h4>
                      <StatusBadge value={run?.health || "pending"} kind="health" />
                    </div>
                    <p className="mt-3 text-sm leading-relaxed text-slate-600">{run?.message || "Waiting…"}</p>
                  </article>
                );
              })}
            </div>
          </section>

          {assets.length > 0 && (
            <section className="mt-6">
              <h3 className="section-title mb-3">Generated creatives</h3>
              <div className="grid gap-3 sm:grid-cols-3">
                {assets.map((a) => (
                  <figure key={a.format} className="card overflow-hidden">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={assetUrl(a.url)} alt={a.headline} className="aspect-video w-full object-cover" />
                    <figcaption className="space-y-1.5 px-3 py-2.5">
                      <p className="text-sm font-medium text-slate-900">{a.headline}</p>
                      {a.primary_text && <p className="text-xs text-slate-600">{a.primary_text}</p>}
                      <p className="text-[11px] uppercase text-slate-400">{a.format}</p>
                    </figcaption>
                  </figure>
                ))}
              </div>
            </section>
          )}

          {copyVariations.length > 0 && (
            <section className="mt-6">
              <h3 className="section-title mb-3">Ad copy variations</h3>
              <div className="grid gap-3 sm:grid-cols-2">
                {copyVariations.map((v, idx) => (
                  <article key={`${v.headline}-${idx}`} className="card p-4">
                    <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">{v.angle || `Variant ${idx + 1}`}</p>
                    <h4 className="mt-1 text-sm font-semibold text-slate-900">{v.headline}</h4>
                    {v.primary_text && <p className="mt-2 text-sm text-slate-600">{v.primary_text}</p>}
                  </article>
                ))}
              </div>
            </section>
          )}

          {audiences.length > 0 && (
            <section className="mt-6">
              <h3 className="section-title mb-3">AI audience suggestions (creative agent)</h3>
              <div className="grid gap-3 lg:grid-cols-3">
                {audiences.map((a) => (
                  <article key={a.name} className="card p-4">
                    <h4 className="text-sm font-semibold text-slate-900">{a.name}</h4>
                    {a.rationale && <p className="mt-2 text-xs text-slate-600">{a.rationale}</p>}
                  </article>
                ))}
              </div>
            </section>
          )}

          {campaign.landing_page_url && (
            <section className="mt-6">
              <h3 className="section-title mb-3">Landing preview</h3>
              <iframe title="Landing preview" src={campaign.landing_page_url} className="h-[420px] w-full rounded-xl border border-[var(--line)] bg-white" />
            </section>
          )}

          <section className="mt-6 card border-dashed p-5">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h3 className="section-title">Demo controls</h3>
                <p className="muted mt-1">
                  Trigger mid-flight events. Auto-pause is currently{" "}
                  <strong>{autoPauseOn ? "ON" : "OFF"}</strong>
                  {autoPauseOn ? " — spend spike / flood will halt ads." : " — only recommendations, no auto-halt."}
                </p>
              </div>
              <button
                type="button"
                disabled={busy}
                className="btn-secondary text-xs"
                onClick={async () => {
                  setBusy(true);
                  try {
                    const opts = await withAuth();
                    await setAutoPause(id, !autoPauseOn, opts);
                    await refresh();
                  } catch (e) {
                    setError(e instanceof Error ? e.message : "Failed to update auto-pause");
                  } finally {
                    setBusy(false);
                  }
                }}
              >
                {autoPauseOn ? "Disable auto-pause" : "Enable auto-pause"}
              </button>
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              <button disabled={busy} onClick={() => onDemo("negative_flood")} className="btn-secondary">Negative comment flood</button>
              <button disabled={busy} onClick={() => onDemo("spend_spike")} className="btn-secondary">Spend spike / ROAS drop</button>
              <button disabled={busy} onClick={() => onDemo("recover")} className="btn-secondary">Recover</button>
            </div>
          </section>

          <section className="mt-6">
            <h3 className="section-title mb-3">Action timeline</h3>
            {timeline.length === 0 ? (
              <div className="card px-4 py-8 text-center text-sm text-slate-500">No action events yet.</div>
            ) : (
              <ul className="space-y-2">
                {timeline.map((ev) => (
                  <li key={ev.id} className="card px-4 py-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <p className="text-sm font-semibold text-slate-900">{ev.summary}</p>
                      <span
                        className={`rounded-md px-2 py-0.5 text-[10px] font-semibold uppercase ${
                          ev.level === "error"
                            ? "bg-red-50 text-red-700"
                            : ev.level === "warning"
                              ? "bg-amber-50 text-amber-800"
                              : "bg-slate-100 text-slate-600"
                        }`}
                      >
                        {ev.level}
                      </span>
                    </div>
                    <p className="mt-1 text-xs text-slate-500">
                      {ev.actor} · {ev.action}
                      {ev.detail ? ` · ${ev.detail}` : ""} ·{" "}
                      {ev.created_at ? new Date(ev.created_at).toLocaleString() : ""}
                    </p>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section className="mt-6">
            <h3 className="section-title mb-3">Recommendations</h3>
            {recommendations.length === 0 ? (
              <div className="card px-4 py-8 text-center text-sm text-slate-500">No recommendations yet.</div>
            ) : (
              <ul className="space-y-2">
                {recommendations.map((r) => (
                  <li key={r.id} className="card flex flex-wrap items-center justify-between gap-3 px-4 py-3.5">
                    <div>
                      <p className="text-sm font-semibold text-slate-900">
                        {r.title} <span className="font-normal text-slate-400">· {r.status}</span>
                      </p>
                      <p className="mt-0.5 text-sm text-slate-500">{r.detail}</p>
                    </div>
                    {r.status === "pending" && (
                      <button
                        disabled={busy}
                        onClick={async () => {
                          setBusy(true);
                          try {
                            const opts = await withAuth();
                            await actOnRecommendation(r.id, "approve", opts);
                            await refresh();
                          } finally {
                            setBusy(false);
                          }
                        }}
                        className="btn-primary"
                      >
                        Approve
                      </button>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </section>
        </>
      )}
    </div>
  );
}

function MetaAutomationPanels({
  campaign,
  busy,
  setBusy,
  setError,
  withAuth,
  refresh,
  campaignId,
}: {
  campaign: CampaignDetail["campaign"];
  busy: boolean;
  setBusy: (v: boolean) => void;
  setError: (v: string | null) => void;
  withAuth: () => Promise<{ token?: string | null; workspaceId?: string | null }>;
  refresh: () => Promise<void>;
  campaignId: string;
}) {
  const structure = (campaign.meta_structure || {}) as {
    mode?: string;
    ads_manager_url?: string;
    ads_manager_account_url?: string;
    status?: string;
    steps?: Array<{ step: string; status: string; detail?: string }>;
    campaign?: { name?: string; objective?: string; status?: string; meta_id?: string };
    ad_set?: {
      name?: string;
      daily_budget?: number;
      placements?: string[];
      audience?: { name?: string };
      status?: string;
      meta_id?: string;
    };
    ads?: Array<{
      id?: string;
      name?: string;
      status?: string;
      budget_share?: number;
      creative?: { headline?: string; cta?: string };
      meta_id?: string;
    }>;
    notes?: string;
  };
  const audiences = campaign.audiences?.recommended || [];
  const opt = campaign.optimization || {};
  const publishStatus = campaign.publish_status || "none";
  const metaMode = structure.mode;
  const adsManagerUrl = structure.ads_manager_url;
  const isLiveInMeta = metaMode === "meta_live" && Boolean(structure.campaign?.meta_id);

  async function run(fn: (opts: { token?: string | null; workspaceId?: string | null }) => Promise<unknown>) {
    setBusy(true);
    setError(null);
    try {
      const opts = await withAuth();
      await fn(opts);
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Action failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mb-4 space-y-4">
      {(structure.campaign || publishStatus !== "none") && (
        <section className="card p-5">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h3 className="section-title">Automated Meta campaign</h3>
              <p className="muted mt-1">
                Draft → Review → Publish · status:{" "}
                <span className="font-medium text-slate-800">{publishStatus}</span>
                {metaMode && (
                  <>
                    {" "}
                    · mode: <span className="font-medium text-slate-800">{metaMode}</span>
                  </>
                )}
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              {isLiveInMeta && adsManagerUrl && (
                <a href={adsManagerUrl} target="_blank" rel="noreferrer" className="btn-primary">
                  Open in Ads Manager
                </a>
              )}
              {publishStatus === "published" && (
                <button
                  type="button"
                  disabled={busy}
                  className="btn-secondary"
                  onClick={() => run((opts) => syncMetaMetrics(campaignId, opts))}
                >
                  Sync Meta metrics
                </button>
              )}
              {publishStatus !== "published" && (
                <>
                  <button
                    type="button"
                    disabled={busy}
                    className="btn-secondary"
                    onClick={() => run((opts) => rebuildMetaDraft(campaignId, opts))}
                  >
                    Rebuild draft
                  </button>
                  <button
                    type="button"
                    disabled={busy || !structure.campaign}
                    className="btn-secondary"
                    onClick={() => run((opts) => submitMetaReview(campaignId, opts))}
                  >
                    Submit review
                  </button>
                  <button
                    type="button"
                    disabled={busy || !structure.campaign}
                    className="btn-primary"
                    onClick={() => run((opts) => publishMetaCampaign(campaignId, opts))}
                  >
                    Publish to Ads Manager
                  </button>
                </>
              )}
            </div>
          </div>

          {publishStatus === "published" && metaMode === "demo_mock" && (
            <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-950">
              Published in <strong>demo mode</strong> only — this campaign is not in Meta Ads Manager.
              Connect Meta under Account settings, select an Ad Account and Page, rebuild the draft,
              then publish again.
            </div>
          )}

          {isLiveInMeta && (
            <div className="mt-4 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-950">
              Campaign created in Meta Ads Manager as <strong>PAUSED</strong>. Open Ads Manager to
              review and activate when ready.
              {adsManagerUrl && (
                <>
                  {" "}
                  <a href={adsManagerUrl} target="_blank" rel="noreferrer" className="font-medium underline">
                    View campaign
                  </a>
                </>
              )}
            </div>
          )}

          {structure.steps && (
            <ol className="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
              {structure.steps.map((s) => (
                <li
                  key={s.step}
                  className={`rounded-lg border px-3 py-2 text-xs ${
                    s.status === "done"
                      ? "border-emerald-200 bg-emerald-50 text-emerald-800"
                      : "border-[var(--line)] bg-slate-50 text-slate-600"
                  }`}
                >
                  <span className="block font-semibold capitalize">{s.step.replace(/_/g, " ")}</span>
                  {s.detail && <span className="mt-0.5 block text-[11px] opacity-80">{s.detail}</span>}
                </li>
              ))}
            </ol>
          )}

          <div className="mt-4 grid gap-3 text-sm lg:grid-cols-3">
            <div className="rounded-lg border border-[var(--line)] p-3">
              <p className="text-[11px] font-semibold uppercase text-slate-500">Campaign</p>
              <p className="mt-1 font-medium text-slate-900">{structure.campaign?.name || "—"}</p>
              <p className="text-xs text-slate-500">
                {structure.campaign?.objective} · {structure.campaign?.status}
                {structure.campaign?.meta_id ? ` · ${structure.campaign.meta_id}` : ""}
              </p>
            </div>
            <div className="rounded-lg border border-[var(--line)] p-3">
              <p className="text-[11px] font-semibold uppercase text-slate-500">Ad set</p>
              <p className="mt-1 font-medium text-slate-900">{structure.ad_set?.name || "—"}</p>
              <p className="text-xs text-slate-500">
                ${Number(structure.ad_set?.daily_budget || 0).toFixed(0)}/day ·{" "}
                {structure.ad_set?.audience?.name || "audience"}
              </p>
              <p className="mt-1 text-[11px] text-slate-400">
                {(structure.ad_set?.placements || []).slice(0, 3).join(", ")}
                {(structure.ad_set?.placements || []).length > 3 ? "…" : ""}
              </p>
            </div>
            <div className="rounded-lg border border-[var(--line)] p-3">
              <p className="text-[11px] font-semibold uppercase text-slate-500">Ads</p>
              <ul className="mt-1 space-y-1">
                {(structure.ads || []).map((ad) => (
                  <li key={ad.id || ad.name} className="text-xs text-slate-700">
                    <span className="font-medium">{ad.name}</span>
                    <span className="text-slate-400">
                      {" "}
                      · ${Number(ad.budget_share || 0).toFixed(0)} · {ad.status}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
          {structure.notes && <p className="mt-3 text-xs text-slate-500">{structure.notes}</p>}
        </section>
      )}

      {audiences.length > 0 && (
        <section className="card p-5">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h3 className="section-title">Audience automation</h3>
              <p className="muted mt-1">
                Location, demographics, interests, behaviors, custom, lookalike, website visitors,
                retargeting, customer lists — AI recommends from your product description.
              </p>
            </div>
            <button
              type="button"
              disabled={busy}
              className="btn-secondary"
              onClick={() => run((opts) => recommendAudiences(campaignId, opts))}
            >
              Refresh AI audiences
            </button>
          </div>
          <div className="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {audiences.map((a) => {
              const selected = Boolean(a.selected);
              return (
                <button
                  key={a.id || a.name}
                  type="button"
                  disabled={busy || publishStatus === "published"}
                  onClick={() => {
                    const next = audiences
                      .map((x) => {
                        if ((x.id || x.name) === (a.id || a.name)) return { ...x, selected: !selected };
                        return x;
                      })
                      .filter((x) => x.selected)
                      .map((x) => x.id || x.name)
                      .filter(Boolean) as string[];
                    void run((opts) => selectAudiences(campaignId, next, opts));
                  }}
                  className={`rounded-lg border px-3 py-3 text-left transition ${
                    selected ? "border-moss/40 bg-blue-50" : "border-[var(--line)] hover:border-moss/30"
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <p className="text-sm font-semibold text-slate-900">{a.name}</p>
                    <span className="text-[10px] font-semibold uppercase text-slate-400">
                      {a.type || "audience"}
                    </span>
                  </div>
                  {a.rationale && <p className="mt-1 text-xs text-slate-600">{a.rationale}</p>}
                  <p className="mt-2 text-[11px] text-slate-500">
                    {[...(a.interests || []), ...(a.behaviors || []), ...(a.lookalikes || []), ...(a.retargeting || [])]
                      .slice(0, 4)
                      .join(" · ")}
                  </p>
                  {selected && (
                    <p className="mt-2 text-[11px] font-semibold uppercase text-moss">Selected</p>
                  )}
                </button>
              );
            })}
          </div>
        </section>
      )}

      {(publishStatus === "published" || (opt.ads && opt.ads.length > 0)) && (
        <section className="card p-5">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h3 className="section-title">Automated optimization</h3>
              <p className="muted mt-1">
                Rules pause losers, boost winners, and rotate creatives — e.g. start 3 ads at $
                {Number(campaign.daily_budget || 20).toFixed(0)}/day and reallocate budget.
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                disabled={busy}
                className="btn-secondary"
                onClick={() => run((opts) => runOptimizationTick(campaignId, { scenario: "mixed", days: 1 }, opts))}
              >
                Simulate 1 day
              </button>
              <button
                type="button"
                disabled={busy}
                className="btn-primary"
                onClick={() => run((opts) => runOptimizationTick(campaignId, { scenario: "mixed", days: 3 }, opts))}
              >
                Simulate 3 days
              </button>
            </div>
          </div>

          <p className="mt-3 text-xs text-slate-500">
            Day {opt.day || 0} · Ad set budget ${Number(opt.ad_set_daily_budget || campaign.daily_budget || 0).toFixed(0)}
            /day
            {opt.needs_new_creative ? " · New creative recommended" : ""}
          </p>

          {opt.rules && (
            <ul className="mt-3 grid gap-1 sm:grid-cols-2">
              {opt.rules.map((r) => (
                <li key={r.id} className="text-xs text-slate-600">
                  <span className={r.enabled === false ? "line-through opacity-50" : ""}>{r.name}</span>
                </li>
              ))}
            </ul>
          )}

          {opt.ads && opt.ads.length > 0 && (
            <div className="mt-4 overflow-x-auto">
              <table className="w-full min-w-[640px] text-left text-xs">
                <thead className="text-[11px] uppercase tracking-wide text-slate-400">
                  <tr>
                    <th className="pb-2 font-semibold">Ad</th>
                    <th className="pb-2 font-semibold">Status</th>
                    <th className="pb-2 font-semibold">Budget</th>
                    <th className="pb-2 font-semibold">Spend</th>
                    <th className="pb-2 font-semibold">ROAS</th>
                    <th className="pb-2 font-semibold">CPA</th>
                    <th className="pb-2 font-semibold">CTR</th>
                    <th className="pb-2 font-semibold">Freq</th>
                  </tr>
                </thead>
                <tbody>
                  {opt.ads.map((ad) => (
                    <tr key={ad.ad_id || ad.name} className="border-t border-[var(--line)]">
                      <td className="py-2 font-medium text-slate-800">{ad.name}</td>
                      <td className="py-2 capitalize">{ad.status}</td>
                      <td className="py-2">${Number(ad.daily_budget || 0).toFixed(2)}</td>
                      <td className="py-2">${Number(ad.spend || 0).toFixed(2)}</td>
                      <td className="py-2">{Number(ad.roas || 0).toFixed(2)}x</td>
                      <td className="py-2">
                        {ad.conversions ? `$${Number(ad.cpa || 0).toFixed(2)}` : "—"}
                      </td>
                      <td className="py-2">{((ad.ctr || 0) * 100).toFixed(2)}%</td>
                      <td className="py-2">{Number(ad.frequency || 0).toFixed(1)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {opt.actions_log && opt.actions_log.length > 0 && (
            <div className="mt-4">
              <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-500">Action log</h4>
              <ul className="mt-2 max-h-40 space-y-1 overflow-y-auto text-xs text-slate-600">
                {[...opt.actions_log].reverse().slice(0, 12).map((a) => (
                  <li key={a.id || `${a.at}-${a.detail}`}>
                    <span className="text-slate-400">{a.at ? new Date(a.at).toLocaleString() : ""}</span>{" "}
                    {a.detail}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>
      )}
    </div>
  );
}

function Gauge({ label, value }: { label: string; value: number }) {
  const pct = Math.max(0, Math.min(1, value));
  return (
    <div>
      <div className="mb-1.5 flex justify-between text-xs text-slate-500">
        <span>{label}</span>
        <span className="tabular-nums font-medium text-slate-700">{(pct * 100).toFixed(0)}%</span>
      </div>
      <div className="gauge" style={{ ["--value" as string]: pct }}>
        <span />
      </div>
    </div>
  );
}

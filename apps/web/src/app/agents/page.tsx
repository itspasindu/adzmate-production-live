"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Campaign, CampaignDetail, fetchHealth, getCampaign, listCampaigns, rerunCampaign } from "@/lib/api";
import { Alert, PageHeader, StatusBadge } from "@/components/ui";
import { useApiAuth } from "@/lib/useApiAuth";
import { useAuth } from "@/components/AuthProvider";
import { friendlyCampaignStatus } from "@/lib/friendly";

const WORKFLOW = [
  {
    title: "1. You describe the product",
    body: "Upload a photo, write a short description, set budget and who should see the ads.",
  },
  {
    title: "2. Creative Agent",
    body: "Writes headlines, primary text, CTAs, and builds ad images for Facebook, TikTok, and Google.",
  },
  {
    title: "3. Sentiment Agent",
    body: "Checks brand safety / comment tone so risky campaigns can be held or halted.",
  },
  {
    title: "4. Strategy Agent",
    body: "Looks at spend and return signals and suggests — or auto-applies — pause actions.",
  },
  {
    title: "5. Signal Aggregator",
    body: "Combines all agents into one decision: ready to publish, hold, or pause.",
  },
  {
    title: "6. You publish",
    body: "Draft → Review → Publish. Nothing goes live until you confirm (unless auto-pause mid-flight).",
  },
  {
    title: "7. Optimization",
    body: "After publish, rules boost winning ads and pause weak ones automatically.",
  },
];

const REALITY: Array<{ layer: string; status: "real" | "sim" | "optional"; note: string }> = [
  { layer: "Orchestrator + 3 parallel agents", status: "real", note: "FastAPI asyncio gather, SQLite state" },
  { layer: "Signal Aggregator LAUNCH/HALT/HOLD", status: "real", note: "Deterministic rule gates" },
  { layer: "Landing page deployer", status: "real", note: "Local HTML preview (CDN URL simulated)" },
  { layer: "Gemini / LLM enrichment", status: "optional", note: "Real when GEMINI_API_KEY is set" },
  { layer: "Ad spend / ROAS / pause", status: "sim", note: "Fixture metrics + mock platform ads" },
  { layer: "Meta campaign publish IDs", status: "sim", note: "Draft→Publish structure with demo IDs" },
  { layer: "Social comments", status: "sim", note: "Fixtures + demo flood events" },
  { layer: "Meta OAuth account link", status: "optional", note: "Real Graph when Meta App credentials set" },
];

export default function AgentsPage() {
  const { withAuth, workspaceId } = useApiAuth();
  const { loading: authLoading } = useAuth();
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [selectedId, setSelectedId] = useState<string>("");
  const [detail, setDetail] = useState<CampaignDetail | null>(null);
  const [health, setHealth] = useState<{
    llm_enabled?: boolean;
    llm_provider?: string | null;
    capabilities?: Record<string, string>;
    demo_script?: string[];
  } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (authLoading) return;
    let cancelled = false;
    (async () => {
      setLoading(true);
      try {
        const opts = await withAuth();
        const [list, h] = await Promise.all([listCampaigns(opts), fetchHealth()]);
        if (cancelled) return;
        setCampaigns(list);
        setHealth(h);
        const pick = selectedId && list.some((c) => c.id === selectedId) ? selectedId : list[0]?.id || "";
        setSelectedId(pick);
        if (pick) setDetail(await getCampaign(pick, opts));
        else setDetail(null);
        setError(null);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Failed to load");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [authLoading, workspaceId, withAuth]);

  useEffect(() => {
    if (!detail || !["received", "agents_running", "aggregating"].includes(detail.campaign.status)) return;
    const timer = window.setInterval(() => {
      void onPick(selectedId);
    }, 4000);
    return () => window.clearInterval(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [detail?.campaign.status, selectedId]);

  async function onStartAgents() {
    if (!selectedId) return;
    setBusy(true);
    setError(null);
    try {
      const opts = await withAuth();
      await rerunCampaign(selectedId, opts);
      setDetail(await getCampaign(selectedId, opts));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to start agents");
    } finally {
      setBusy(false);
    }
  }

  async function onPick(id: string) {
    setSelectedId(id);
    setLoading(true);
    try {
      const opts = await withAuth();
      setDetail(await getCampaign(id, opts));
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load campaign");
    } finally {
      setLoading(false);
    }
  }

  const agents = detail?.agents || [];
  const timeline = detail?.timeline || [];

  return (
    <div className="mx-auto max-w-5xl">
      <PageHeader
        title="Agents & workflows"
        description="Technical view: how agents reason and act. Day-to-day publishing stays on My ads."
        actions={
          <Link href="/campaigns/new" className="btn-primary">
            Publish ads
          </Link>
        }
      />

      {error && (
        <div className="mb-4">
          <Alert>{error}</Alert>
        </div>
      )}

      <section className="card p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="section-title">Real vs simulated</h2>
            <p className="muted mt-1">Be transparent with judges — agents are real; some platforms are demo.</p>
          </div>
          <div className="rounded-lg border border-[var(--line)] bg-slate-50 px-3 py-2 text-xs">
            LLM:{" "}
            <span className="font-semibold text-slate-900">
              {health?.llm_enabled ? `ON (${health.llm_provider})` : "OFF — templates / lexicon"}
            </span>
          </div>
        </div>
        <ul className="mt-4 divide-y divide-[var(--line)] rounded-xl border border-[var(--line)]">
          {REALITY.map((row) => (
            <li key={row.layer} className="flex flex-wrap items-start justify-between gap-2 px-4 py-3 text-sm">
              <div>
                <p className="font-medium text-slate-900">{row.layer}</p>
                <p className="text-xs text-slate-500">{row.note}</p>
              </div>
              <span
                className={`rounded-md px-2 py-0.5 text-[11px] font-semibold uppercase ${
                  row.status === "real"
                    ? "bg-emerald-50 text-emerald-700"
                    : row.status === "optional"
                      ? "bg-sky-50 text-sky-700"
                      : "bg-amber-50 text-amber-800"
                }`}
              >
                {row.status === "real" ? "Real" : row.status === "optional" ? "Optional / key" : "Simulated"}
              </span>
            </li>
          ))}
        </ul>
      </section>

      <section className="mt-5 card p-5">
        <h2 className="section-title">3-minute judging demo script</h2>
        <ol className="mt-4 list-decimal space-y-2 pl-5 text-sm text-slate-700">
          {(health?.demo_script || [
            "Show this page — real vs mock",
            "Healthy campaign → LAUNCH → Publish",
            "Poor ROAS → HALT",
            "Spend spike → auto-pause",
          ]).map((step) => (
            <li key={step}>{step}</li>
          ))}
        </ol>
        <p className="mt-3 text-xs text-slate-500">
          Reseed judging data:{" "}
          <code className="rounded bg-slate-100 px-1.5 py-0.5">cd apps/api && python -m app.seed --force</code>
        </p>
      </section>

      <section className="mt-5 card p-5">
        <h2 className="section-title">End-to-end workflow</h2>
        <ol className="mt-5 space-y-3">
          {WORKFLOW.map((step) => (
            <li key={step.title} className="flex gap-3 rounded-xl border border-[var(--line)] bg-slate-50/80 px-4 py-3">
              <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-moss text-[11px] font-bold text-white">
                {step.title.charAt(0)}
              </span>
              <div>
                <p className="text-sm font-semibold text-slate-900">{step.title}</p>
                <p className="mt-0.5 text-sm text-slate-600">{step.body}</p>
              </div>
            </li>
          ))}
        </ol>
      </section>

      <section className="mt-5 card p-5">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h2 className="section-title">Live agent status + timeline</h2>
            <p className="muted mt-1">Pick a campaign to inspect agents and the action audit trail.</p>
          </div>
          <select
            className="input mt-0 max-w-xs"
            value={selectedId}
            onChange={(e) => void onPick(e.target.value)}
            disabled={!campaigns.length}
          >
            {campaigns.length === 0 && <option value="">No campaigns yet</option>}
            {campaigns.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name} · {friendlyCampaignStatus(c.status)}
              </option>
            ))}
          </select>
        </div>

        {loading ? (
          <p className="mt-6 text-sm text-slate-500">Loading…</p>
        ) : !detail ? (
          <p className="mt-6 text-sm text-slate-500">
            Seed demos with{" "}
            <code className="rounded bg-slate-100 px-1">python -m app.seed --force</code> or{" "}
            <Link href="/campaigns/new" className="font-medium text-moss hover:underline">
              Publish ads
            </Link>
            .
          </p>
        ) : (
          <>
            <div className="mt-4 flex flex-wrap items-center gap-2 text-sm text-slate-600">
              <Link href={`/campaigns/${detail.campaign.id}`} className="font-medium text-moss hover:underline">
                {detail.campaign.name}
              </Link>
              <StatusBadge value={detail.campaign.status} />
              {detail.campaign.decision && (
                <span className="rounded-md bg-slate-100 px-2 py-0.5 text-xs font-semibold text-slate-700">
                  Decision: {detail.campaign.decision}
                </span>
              )}
              <span className="text-xs text-slate-500">
                Auto-pause: {detail.campaign.auto_pause_enabled === false ? "off" : "on"}
              </span>
              {detail.campaign.status === "received" && (
                <button
                  type="button"
                  disabled={busy}
                  className="btn-primary text-xs"
                  onClick={() => void onStartAgents()}
                >
                  {busy ? "Starting…" : "Start agents"}
                </button>
              )}
            </div>

            {detail.campaign.status === "received" && (
              <p className="mt-3 text-sm text-amber-800">
                Agents are queued but not running yet. Click <strong>Start agents</strong> or redeploy the API
                if this stays stuck.
              </p>
            )}

            <div className="mt-4 grid gap-3 md:grid-cols-3">
              {["creative", "sentiment", "strategy"].map((name) => {
                const run = agents.find((a) => a.agent === name);
                const engine = (run?.payload?.engine as string) || "";
                return (
                  <article key={name} className="rounded-xl border border-[var(--line)] p-4">
                    <div className="flex items-center justify-between gap-2">
                      <h3 className="text-sm font-semibold capitalize text-slate-900">{name} agent</h3>
                      <StatusBadge value={run?.health || "pending"} kind="health" />
                    </div>
                    <p className="mt-3 text-sm leading-relaxed text-slate-600">
                      {run?.message || "Waiting to start…"}
                    </p>
                    {engine && <p className="mt-2 text-[11px] text-slate-400">Engine: {engine}</p>}
                  </article>
                );
              })}
            </div>

            {timeline.length > 0 && (
              <div className="mt-5">
                <h3 className="text-sm font-semibold text-slate-900">Action timeline</h3>
                <ul className="mt-3 max-h-72 space-y-2 overflow-y-auto">
                  {timeline.slice(0, 24).map((e) => (
                    <li key={e.id} className="rounded-lg border border-[var(--line)] px-3 py-2 text-xs">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <span className="font-semibold capitalize text-slate-800">
                          {e.actor} · {e.action.replaceAll("_", " ")}
                        </span>
                        <span className="text-slate-400">{new Date(e.created_at).toLocaleString()}</span>
                      </div>
                      <p className="mt-1 text-slate-600">{e.summary}</p>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </>
        )}
      </section>
    </div>
  );
}

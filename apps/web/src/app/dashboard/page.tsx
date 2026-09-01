"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { Campaign, listCampaigns } from "@/lib/api";
import { Alert, EmptyState, Metric, PageHeader } from "@/components/ui";
import { useApiAuth } from "@/lib/useApiAuth";
import { useAuth } from "@/components/AuthProvider";
import { friendlyCampaignStatus } from "@/lib/friendly";

function formatDate(value: string) {
  try {
    return new Intl.DateTimeFormat("en", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }).format(new Date(value));
  } catch {
    return value;
  }
}

export default function DashboardPage() {
  const { withAuth, workspaceId } = useApiAuth();
  const { loading: authLoading } = useAuth();
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");

  useEffect(() => {
    if (authLoading) return;
    let cancelled = false;
    setLoading(true);
    (async () => {
      try {
        const opts = await withAuth();
        const data = await listCampaigns(opts);
        if (!cancelled) {
          setCampaigns(data);
          setError(null);
        }
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "API unreachable — start the FastAPI server on :8000");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [authLoading, workspaceId, withAuth]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return campaigns;
    return campaigns.filter((c) =>
      [c.name, c.client_name, c.brand_name, c.product_name, c.status, c.decision || ""]
        .join(" ")
        .toLowerCase()
        .includes(q),
    );
  }, [campaigns, query]);

  const stats = useMemo(() => {
    const live = campaigns.filter((c) => c.status === "live").length;
    const awaiting = campaigns.filter((c) => c.status === "awaiting_approval").length;
    const running = campaigns.filter((c) =>
      ["agents_running", "deploying", "received"].includes(c.status),
    ).length;
    const budget = campaigns.reduce((sum, c) => sum + (c.budget || 0), 0);
    return { live, awaiting, running, budget };
  }, [campaigns]);

  return (
    <div className="mx-auto max-w-7xl">
      <PageHeader
        title="My ads"
        description="Create ads from a product photo, review them, then publish — no ads expertise needed."
        actions={
          <Link href="/campaigns/new" className="btn-primary">
            Publish ads
          </Link>
        }
      />

      <div className="mb-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <Metric label="Total ads" value={String(campaigns.length)} hint="In this workspace" />
        <Metric label="Live now" value={String(stats.live)} hint="Showing to customers" />
        <Metric label="Ready to publish" value={String(stats.awaiting)} hint="Waiting for your OK" />
        <Metric
          label="Creating…"
          value={String(stats.running)}
          hint={`$${stats.budget.toLocaleString()} planned`}
        />
      </div>

      {error && (
        <div className="mb-4">
          <Alert>{error}</Alert>
        </div>
      )}

      <div className="card overflow-hidden">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--line)] px-4 py-3">
          <div>
            <h2 className="section-title">All your ads</h2>
            <p className="muted">{filtered.length} shown</p>
          </div>
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search by product or status…"
            className="input mt-0 max-w-xs"
          />
        </div>

        {loading || authLoading ? (
          <div className="px-4 py-12 text-center text-sm text-slate-500">Loading…</div>
        ) : filtered.length === 0 ? (
          <div className="p-4">
            <EmptyState
              title={campaigns.length === 0 ? "No ads yet" : "No matches"}
              description={
                campaigns.length === 0
                  ? "Upload a product photo and we'll create Facebook & Instagram ads for you."
                  : "Try a different search."
              }
              action={
                campaigns.length === 0 ? (
                  <Link href="/campaigns/new" className="btn-primary">
                    Publish your first ads
                  </Link>
                ) : undefined
              }
            />
          </div>
        ) : (
          <>
            <div className="hidden overflow-x-auto md:block">
              <table className="w-full min-w-[720px] text-left text-sm">
                <thead className="bg-slate-50 text-[11px] font-semibold uppercase tracking-[0.06em] text-slate-500">
                  <tr>
                    <th className="px-4 py-3">Product</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">What to do</th>
                    <th className="px-4 py-3">Budget</th>
                    <th className="px-4 py-3">Updated</th>
                    <th className="px-4 py-3" />
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--line)]">
                  {filtered.map((c) => (
                    <tr key={c.id} className="transition hover:bg-slate-50/80">
                      <td className="px-4 py-3.5">
                        <Link href={`/campaigns/${c.id}`} className="font-medium text-slate-900 hover:text-moss">
                          {c.product_name || c.name}
                        </Link>
                        <p className="mt-0.5 text-xs text-slate-500">{c.brand_name}</p>
                      </td>
                      <td className="px-4 py-3.5">
                        <span className="text-sm font-medium text-slate-800">{friendlyCampaignStatus(c.status)}</span>
                      </td>
                      <td className="max-w-[240px] px-4 py-3.5 text-sm text-slate-600">
                        {c.status === "awaiting_approval"
                          ? "Review & publish"
                          : c.status === "live"
                            ? "Running"
                            : c.decision || "Creating ads…"}
                      </td>
                      <td className="px-4 py-3.5 tabular-nums text-slate-600">
                        ${Number(c.daily_budget || c.budget).toLocaleString()}/day
                      </td>
                      <td className="px-4 py-3.5 text-slate-500">{formatDate(c.updated_at)}</td>
                      <td className="px-4 py-3.5 text-right">
                        <Link href={`/campaigns/${c.id}`} className="text-sm font-medium text-moss hover:underline">
                          Open
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="divide-y divide-[var(--line)] md:hidden">
              {filtered.map((c) => (
                <Link key={c.id} href={`/campaigns/${c.id}`} className="block px-4 py-4 hover:bg-slate-50">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="font-medium text-slate-900">{c.product_name || c.name}</p>
                      <p className="mt-0.5 text-xs text-slate-500">{c.brand_name}</p>
                    </div>
                    <span className="text-xs font-semibold text-slate-600">{friendlyCampaignStatus(c.status)}</span>
                  </div>
                  <p className="mt-2 text-sm text-slate-600">
                    ${Number(c.daily_budget || c.budget).toLocaleString()}/day
                  </p>
                </Link>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

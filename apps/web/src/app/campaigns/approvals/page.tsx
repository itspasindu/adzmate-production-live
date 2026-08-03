"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import {
  actOnRecommendation,
  listRecommendations,
  Recommendation,
} from "@/lib/api";
import { Alert, EmptyState, PageHeader } from "@/components/ui";
import { useApiAuth } from "@/lib/useApiAuth";
import { useAuth } from "@/components/AuthProvider";

export default function ApprovalsPage() {
  const { withAuth, workspaceId } = useApiAuth();
  const { loading: authLoading } = useAuth();
  const [recs, setRecs] = useState<Recommendation[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const opts = await withAuth();
      setRecs(await listRecommendations("pending", opts));
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }, [withAuth]);

  useEffect(() => {
    if (authLoading) return;
    refresh();
    const t = setInterval(refresh, 4000);
    return () => clearInterval(t);
  }, [authLoading, workspaceId, refresh]);

  async function act(id: string, action: "approve" | "reject") {
    setBusyId(id);
    try {
      const opts = await withAuth();
      await actOnRecommendation(id, action, opts);
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Action failed");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="mx-auto max-w-4xl">
      <PageHeader
        title="Approvals"
        description="Human-in-the-loop queue for launch, halt, pause, and resume recommendations."
        actions={
          <span className="rounded-full border border-[var(--line)] bg-white px-3 py-1 text-xs font-medium text-slate-600">
            {recs.length} pending
          </span>
        }
      />

      {error && (
        <div className="mb-4">
          <Alert>{error}</Alert>
        </div>
      )}

      {loading || authLoading ? (
        <div className="card px-4 py-12 text-center text-sm text-slate-500">Loading queue…</div>
      ) : recs.length === 0 ? (
        <EmptyState
          title="Queue is clear"
          description="No pending recommendations. Run a campaign pipeline to generate review items."
          action={
            <Link href="/campaigns/new" className="btn-primary">
              Create campaign
            </Link>
          }
        />
      ) : (
        <div className="space-y-3">
          {recs.map((r) => (
            <article key={r.id} className="card p-5">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="rounded-md bg-blue-50 px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wide text-moss ring-1 ring-inset ring-moss/15">
                      {r.type}
                    </span>
                    <span className="text-xs text-slate-400">Pending review</span>
                  </div>
                  <h2 className="mt-2 text-base font-semibold text-slate-900">{r.title}</h2>
                  <p className="mt-1.5 text-sm leading-relaxed text-slate-600">{r.detail}</p>
                  <Link
                    href={`/campaigns/${r.campaign_id}`}
                    className="mt-3 inline-flex text-sm font-medium text-moss hover:underline"
                  >
                    View campaign details
                  </Link>
                </div>
                <div className="flex shrink-0 gap-2">
                  <button
                    disabled={busyId === r.id}
                    onClick={() => act(r.id, "reject")}
                    className="btn-danger"
                  >
                    Reject
                  </button>
                  <button
                    disabled={busyId === r.id}
                    onClick={() => act(r.id, "approve")}
                    className="btn-primary"
                  >
                    Approve
                  </button>
                </div>
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}

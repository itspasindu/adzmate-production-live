"use client";

import { FormEvent, Suspense, useCallback, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import {
  Business,
  MetaConnection,
  createBusiness,
  demoConnectMeta,
  disconnectMeta,
  getMetaConnection,
  listBusinesses,
  metaOAuthStatus,
  startMetaOAuth,
  syncMeta,
  updateBusiness,
  updateMetaSelection,
} from "@/lib/api";
import { Alert, PageHeader } from "@/components/ui";
import { useApiAuth } from "@/lib/useApiAuth";
import { useAuth } from "@/components/AuthProvider";

function SettingsContent() {
  const { withAuth } = useApiAuth();
  const { user, me, authConfigured } = useAuth();
  const params = useSearchParams();
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [meta, setMeta] = useState<MetaConnection | null>(null);
  const [oauthConfigured, setOauthConfigured] = useState(false);
  const [metaConfigError, setMetaConfigError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);

  const selected = businesses.find((b) => b.id === selectedId) || null;

  const refresh = useCallback(
    async (preferId?: string | null) => {
      setLoading(true);
      try {
        const opts = await withAuth();
        const [list, status] = await Promise.all([listBusinesses(opts), metaOAuthStatus(opts)]);
        setBusinesses(list);
        setOauthConfigured(status.oauth_configured);
        setMetaConfigError(status.config_error ?? null);
        const preferred =
          preferId ||
          params.get("business_id") ||
          list[0]?.id ||
          null;
        setSelectedId(preferred);
        if (preferred && list.some((b) => b.id === preferred)) {
          try {
            setMeta(await getMetaConnection(preferred, opts));
          } catch {
            setMeta(null);
          }
        } else {
          setMeta(null);
        }
        setError(null);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load account settings");
      } finally {
        setLoading(false);
      }
    },
    [withAuth, params],
  );

  useEffect(() => {
    void refresh();
  }, [refresh]);

  useEffect(() => {
    const metaParam = params.get("meta");
    if (metaParam === "connected") setInfo("Meta account connected successfully.");
    if (metaParam === "error") setError(params.get("message") || "Meta OAuth failed");
  }, [params]);

  async function loadMetaFor(businessId: string) {
    setSelectedId(businessId);
    setBusy(true);
    try {
      const opts = await withAuth();
      setMeta(await getMetaConnection(businessId, opts));
      setError(null);
    } catch {
      setMeta(null);
    } finally {
      setBusy(false);
    }
  }

  async function onCreateBusiness(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = e.currentTarget;
    const fd = new FormData(form);
    setBusy(true);
    setError(null);
    try {
      const opts = await withAuth();
      const biz = await createBusiness(
        {
          name: String(fd.get("name") || ""),
          legal_name: String(fd.get("legal_name") || "") || null,
          website: String(fd.get("website") || "") || null,
          industry: String(fd.get("industry") || "") || null,
          country: String(fd.get("country") || "") || null,
          contact_email: String(fd.get("contact_email") || "") || null,
          timezone: String(fd.get("timezone") || "UTC"),
        },
        opts,
      );
      form.reset();
      setInfo(`Created business “${biz.name}”.`);
      await refresh(biz.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Create failed");
    } finally {
      setBusy(false);
    }
  }

  async function onSaveProfile(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!selected) return;
    setBusy(true);
    try {
      const fd = new FormData(e.currentTarget);
      const opts = await withAuth();
      const updated = await updateBusiness(
        selected.id,
        {
          name: String(fd.get("name") || ""),
          legal_name: String(fd.get("legal_name") || "") || null,
          website: String(fd.get("website") || "") || null,
          industry: String(fd.get("industry") || "") || null,
          country: String(fd.get("country") || "") || null,
          contact_email: String(fd.get("contact_email") || "") || null,
          timezone: String(fd.get("timezone") || "UTC"),
          notes: String(fd.get("notes") || "") || null,
        },
        opts,
      );
      setBusinesses((prev) => prev.map((b) => (b.id === updated.id ? { ...b, ...updated } : b)));
      setInfo("Business profile saved.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setBusy(false);
    }
  }

  async function onConnectMeta() {
    if (!selected) return;
    setBusy(true);
    setError(null);
    try {
      const opts = await withAuth();
      if (oauthConfigured) {
        const { authorize_url } = await startMetaOAuth(selected.id, opts);
        window.location.href = authorize_url;
        return;
      }
      const conn = await demoConnectMeta(selected.id, opts);
      setMeta(conn);
      setInfo("Demo Meta connection created (Pages, Instagram, Ad Accounts).");
      await refresh(selected.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Connect failed");
    } finally {
      setBusy(false);
    }
  }

  async function onSync() {
    if (!selected) return;
    setBusy(true);
    try {
      const opts = await withAuth();
      setMeta(await syncMeta(selected.id, opts));
      setInfo("Meta assets refreshed.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sync failed");
    } finally {
      setBusy(false);
    }
  }

  async function onDisconnect() {
    if (!selected) return;
    if (!window.confirm("Disconnect Meta account from this business?")) return;
    setBusy(true);
    try {
      const opts = await withAuth();
      await disconnectMeta(selected.id, opts);
      setMeta(null);
      setInfo("Meta disconnected.");
      await refresh(selected.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Disconnect failed");
    } finally {
      setBusy(false);
    }
  }

  async function onSelect(kind: "page" | "instagram" | "ad", id: string) {
    if (!selected) return;
    setBusy(true);
    try {
      const opts = await withAuth();
      const body =
        kind === "page"
          ? { page_id: id }
          : kind === "instagram"
            ? { instagram_id: id }
            : { ad_account_id: id };
      setMeta(await updateMetaSelection(selected.id, body, opts));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Selection failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-5xl">
      <PageHeader
        title="Account & Meta"
        description="Manage user profile, business companies, and Meta (Facebook / Instagram / Ads) connections."
      />

      {error && (
        <div className="mb-4">
          <Alert>{error}</Alert>
        </div>
      )}
      {info && (
        <div className="mb-4">
          <Alert tone="info">{info}</Alert>
        </div>
      )}

      <section className="card mb-5 p-5">
        <h2 className="section-title">User account</h2>
        <p className="muted mt-1">
          {authConfigured
            ? "Signed in with Supabase Auth."
            : "Local demo mode (Supabase not configured)."}
        </p>
        <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
          <div>
            <dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">Email</dt>
            <dd className="mt-0.5 font-medium text-slate-900">
              {user?.email || me?.email || "demo@local.dev"}
            </dd>
          </div>
          <div>
            <dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">User ID</dt>
            <dd className="mt-0.5 truncate font-mono text-xs text-slate-700">{me?.id || "—"}</dd>
          </div>
        </dl>
      </section>

      <div className="grid gap-5 lg:grid-cols-[240px_1fr]">
        <aside className="card p-4">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-900">Businesses</h3>
            <span className="text-xs text-slate-500">{businesses.length}</span>
          </div>
          {loading ? (
            <p className="text-sm text-slate-500">Loading…</p>
          ) : (
            <ul className="space-y-1">
              {businesses.map((b) => (
                <li key={b.id}>
                  <button
                    type="button"
                    onClick={() => void loadMetaFor(b.id)}
                    className={`w-full rounded-lg px-2.5 py-2 text-left text-sm transition ${
                      selectedId === b.id
                        ? "bg-blue-50 font-medium text-moss"
                        : "text-slate-700 hover:bg-slate-50"
                    }`}
                  >
                    <span className="block truncate">{b.name}</span>
                    <span className="block text-[11px] text-slate-400">
                      {b.meta_status ? `Meta · ${b.meta_status}` : "Meta not connected"}
                    </span>
                  </button>
                </li>
              ))}
              {businesses.length === 0 && (
                <li className="text-sm text-slate-500">No businesses yet.</li>
              )}
            </ul>
          )}
        </aside>

        <div className="space-y-5">
          <section className="card p-5">
            <h2 className="section-title">Add business / company</h2>
            <p className="muted mt-1">Create a company profile to attach Meta ad accounts.</p>
            <form onSubmit={onCreateBusiness} className="mt-4 grid gap-3 sm:grid-cols-2">
              <label className="label sm:col-span-2">
                Company name
                <input name="name" required className="input" placeholder="Aurora Labs" />
              </label>
              <label className="label">
                Legal name
                <input name="legal_name" className="input" />
              </label>
              <label className="label">
                Website
                <input name="website" className="input" placeholder="https://" />
              </label>
              <label className="label">
                Industry
                <input name="industry" className="input" placeholder="Consumer electronics" />
              </label>
              <label className="label">
                Country
                <input name="country" className="input" placeholder="United States" />
              </label>
              <label className="label">
                Contact email
                <input
                  name="contact_email"
                  type="email"
                  className="input"
                  defaultValue={user?.email || ""}
                />
              </label>
              <label className="label">
                Timezone
                <input name="timezone" className="input" defaultValue="UTC" />
              </label>
              <div className="sm:col-span-2">
                <button type="submit" disabled={busy} className="btn-primary">
                  Create business
                </button>
              </div>
            </form>
          </section>

          {selected && (
            <>
              <section className="card p-5">
                <h2 className="section-title">Business profile</h2>
                <form onSubmit={onSaveProfile} className="mt-4 grid gap-3 sm:grid-cols-2">
                  <label className="label sm:col-span-2">
                    Company name
                    <input name="name" required className="input" defaultValue={selected.name} key={selected.id + "-name"} />
                  </label>
                  <label className="label">
                    Legal name
                    <input name="legal_name" className="input" defaultValue={selected.legal_name || ""} key={selected.id + "-legal"} />
                  </label>
                  <label className="label">
                    Website
                    <input name="website" className="input" defaultValue={selected.website || ""} key={selected.id + "-web"} />
                  </label>
                  <label className="label">
                    Industry
                    <input name="industry" className="input" defaultValue={selected.industry || ""} key={selected.id + "-ind"} />
                  </label>
                  <label className="label">
                    Country
                    <input name="country" className="input" defaultValue={selected.country || ""} key={selected.id + "-co"} />
                  </label>
                  <label className="label">
                    Contact email
                    <input name="contact_email" className="input" defaultValue={selected.contact_email || ""} key={selected.id + "-em"} />
                  </label>
                  <label className="label">
                    Timezone
                    <input name="timezone" className="input" defaultValue={selected.timezone || "UTC"} key={selected.id + "-tz"} />
                  </label>
                  <label className="label sm:col-span-2">
                    Notes
                    <textarea name="notes" rows={2} className="input" defaultValue={selected.notes || ""} key={selected.id + "-notes"} />
                  </label>
                  <div className="sm:col-span-2">
                    <button type="submit" disabled={busy} className="btn-primary">
                      Save profile
                    </button>
                  </div>
                </form>
              </section>

              <section className="card p-5">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <h2 className="section-title">Meta connection</h2>
                    <p className="muted mt-1">
                      Connect Facebook Page, Instagram, and Ad Account via OAuth
                      {oauthConfigured ? "." : " (demo mode — Meta App credentials not set)."}
                    </p>
                    {metaConfigError && (
                      <p className="mt-2 text-sm text-amber-800">{metaConfigError}</p>
                    )}
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {!meta ? (
                      <button type="button" disabled={busy} onClick={onConnectMeta} className="btn-primary">
                        {oauthConfigured ? "Connect with Meta" : "Connect demo Meta"}
                      </button>
                    ) : (
                      <>
                        <button type="button" disabled={busy} onClick={onSync} className="btn-secondary">
                          Refresh assets
                        </button>
                        <button type="button" disabled={busy} onClick={onDisconnect} className="btn-danger">
                          Disconnect
                        </button>
                      </>
                    )}
                  </div>
                </div>

                {meta && (
                  <div className="mt-5 space-y-5">
                    <div className="rounded-lg border border-[var(--line)] bg-slate-50 px-4 py-3 text-sm">
                      <p className="font-medium text-slate-900">
                        {meta.meta_user_name || "Meta user"}{" "}
                        <span className="ml-2 rounded bg-white px-1.5 py-0.5 text-[11px] uppercase text-slate-600 ring-1 ring-slate-200">
                          {meta.status}
                        </span>
                      </p>
                      <p className="mt-1 text-xs text-slate-500">Scopes: {meta.scopes || "—"}</p>
                    </div>

                    <AssetPicker
                      title="Facebook Page"
                      empty="No pages returned."
                      items={meta.pages.map((p) => ({
                        id: p.page_id,
                        label: p.name,
                        hint: p.category || p.page_id,
                        selected: p.selected,
                      }))}
                      onSelect={(id) => onSelect("page", id)}
                    />
                    <AssetPicker
                      title="Instagram account"
                      empty="No Instagram Business accounts linked to pages."
                      items={meta.instagram_accounts.map((i) => ({
                        id: i.ig_user_id,
                        label: `@${i.username}`,
                        hint: i.name || i.ig_user_id,
                        selected: i.selected,
                      }))}
                      onSelect={(id) => onSelect("instagram", id)}
                    />
                    <AssetPicker
                      title="Meta Ad Account"
                      empty="No ad accounts found."
                      items={meta.ad_accounts.map((a) => ({
                        id: a.ad_account_id,
                        label: a.name,
                        hint: `${a.ad_account_id}${a.currency ? ` · ${a.currency}` : ""}`,
                        selected: a.selected,
                      }))}
                      onSelect={(id) => onSelect("ad", id)}
                    />
                  </div>
                )}
              </section>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function AssetPicker({
  title,
  empty,
  items,
  onSelect,
}: {
  title: string;
  empty: string;
  items: Array<{ id: string; label: string; hint: string; selected: boolean }>;
  onSelect: (id: string) => void;
}) {
  return (
    <div>
      <h3 className="text-sm font-semibold text-slate-900">{title}</h3>
      {items.length === 0 ? (
        <p className="mt-2 text-sm text-slate-500">{empty}</p>
      ) : (
        <ul className="mt-2 space-y-2">
          {items.map((item) => (
            <li key={item.id}>
              <button
                type="button"
                onClick={() => onSelect(item.id)}
                className={`flex w-full items-center justify-between rounded-lg border px-3 py-2.5 text-left text-sm transition ${
                  item.selected
                    ? "border-moss/40 bg-blue-50"
                    : "border-[var(--line)] bg-white hover:border-moss/30"
                }`}
              >
                <span>
                  <span className="block font-medium text-slate-900">{item.label}</span>
                  <span className="block text-xs text-slate-500">{item.hint}</span>
                </span>
                {item.selected && (
                  <span className="text-[11px] font-semibold uppercase text-moss">Selected</span>
                )}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default function SettingsPage() {
  return (
    <Suspense
      fallback={
        <div className="py-16 text-center text-sm text-slate-500">Loading account settings…</div>
      }
    >
      <SettingsContent />
    </Suspense>
  );
}

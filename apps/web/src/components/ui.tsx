const campaignStatus: Record<string, string> = {
  live: "bg-emerald-50 text-emerald-700 ring-emerald-600/15",
  halted: "bg-rose-50 text-rose-700 ring-rose-600/15",
  awaiting_approval: "bg-amber-50 text-amber-800 ring-amber-600/15",
  agents_running: "bg-sky-50 text-sky-700 ring-sky-600/15",
  deploying: "bg-sky-50 text-sky-700 ring-sky-600/15",
  failed: "bg-rose-50 text-rose-700 ring-rose-600/15",
  received: "bg-slate-100 text-slate-600 ring-slate-500/15",
};

const healthStatus: Record<string, string> = {
  ok: "bg-emerald-50 text-emerald-700 ring-emerald-600/15",
  running: "bg-sky-50 text-sky-700 ring-sky-600/15",
  pending: "bg-slate-100 text-slate-600 ring-slate-500/15",
  failed: "bg-rose-50 text-rose-700 ring-rose-600/15",
  degraded: "bg-amber-50 text-amber-800 ring-amber-600/15",
};

export function StatusBadge({
  value,
  kind = "campaign",
}: {
  value: string;
  kind?: "campaign" | "health";
}) {
  const map = kind === "health" ? healthStatus : campaignStatus;
  return (
    <span
      className={`inline-flex items-center rounded-md px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wide ring-1 ring-inset ${
        map[value] || "bg-slate-100 text-slate-600 ring-slate-500/15"
      }`}
    >
      {value.replaceAll("_", " ")}
    </span>
  );
}

export function PageHeader({
  title,
  description,
  actions,
  breadcrumb,
}: {
  title: string;
  description?: string;
  actions?: React.ReactNode;
  breadcrumb?: React.ReactNode;
}) {
  return (
    <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
      <div className="min-w-0">
        {breadcrumb && <div className="mb-2">{breadcrumb}</div>}
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900">{title}</h1>
        {description && <p className="mt-1 max-w-2xl text-sm text-slate-500">{description}</p>}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </div>
  );
}

export function Alert({
  tone = "error",
  children,
}: {
  tone?: "error" | "warning" | "info";
  children: React.ReactNode;
}) {
  const styles = {
    error: "border-rose-200 bg-rose-50 text-rose-900",
    warning: "border-amber-200 bg-amber-50 text-amber-950",
    info: "border-sky-200 bg-sky-50 text-sky-950",
  };
  return (
    <div className={`rounded-lg border px-4 py-3 text-sm ${styles[tone]}`}>{children}</div>
  );
}

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="card flex flex-col items-center px-6 py-14 text-center">
      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-slate-100 text-slate-400">
        <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.75">
          <path d="M4 7h16M4 12h10M4 17h7" strokeLinecap="round" />
        </svg>
      </div>
      <h3 className="mt-4 text-sm font-semibold text-slate-900">{title}</h3>
      <p className="mt-1 max-w-sm text-sm text-slate-500">{description}</p>
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}

export function Metric({
  label,
  value,
  hint,
}: {
  label: string;
  value: string;
  hint?: string;
}) {
  return (
    <div className="card px-4 py-3.5">
      <p className="text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold tracking-tight text-slate-900">{value}</p>
      {hint && <p className="mt-1 text-xs text-slate-500">{hint}</p>}
    </div>
  );
}

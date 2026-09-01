import { apiReachabilityHint, resolveApiUrl, resolveAssetUrl } from "@/lib/config";

export type Campaign = {
  id: string;
  workspace_id?: string | null;
  name: string;
  client_name: string;
  brand_name: string;
  product_name: string;
  brief: string;
  product_description?: string;
  product_url?: string | null;
  goal: string;
  objective?: string;
  budget: number;
  daily_budget?: number;
  duration_days?: number;
  target_country?: string;
  target_location?: string;
  age_min?: number;
  age_max?: number;
  gender?: string;
  language?: string;
  platforms: string[];
  brand_primary: string;
  brand_accent: string;
  scenario: string;
  status: string;
  product_image_url?: string | null;
  decision?: string | null;
  decision_reason?: string | null;
  decision_confidence?: number | null;
  landing_page_url?: string | null;
  cloudfront_url?: string | null;
  warnings: string[];
  publish_status?: string;
  auto_pause_enabled?: boolean;
  meta_structure?: Record<string, unknown>;
  audiences?: {
    supported_types?: string[];
    recommended?: AudienceSuggestion[];
    selected?: AudienceSuggestion[];
  };
  optimization?: OptimizationState;
  created_at: string;
  updated_at: string;
};

export type ActionEvent = {
  id: string;
  campaign_id: string;
  actor: string;
  action: string;
  summary: string;
  detail?: string | null;
  level: string;
  created_at: string;
};

export type AudienceSuggestion = {
  id?: string;
  type?: string;
  name: string;
  rationale?: string;
  age_min?: number;
  age_max?: number;
  gender?: string;
  locations?: string[];
  languages?: string[];
  interests?: string[];
  behaviors?: string[];
  custom_audiences?: string[];
  lookalikes?: string[];
  retargeting?: string[];
  estimated_reach?: string;
  selected?: boolean;
  source?: string;
};

export type OptimizationAd = {
  ad_id?: string;
  name?: string;
  status?: string;
  daily_budget?: number;
  spend?: number;
  impressions?: number;
  clicks?: number;
  conversions?: number;
  revenue?: number;
  ctr?: number;
  cpc?: number;
  cpa?: number;
  roas?: number;
  frequency?: number;
};

export type OptimizationState = {
  enabled?: boolean;
  day?: number;
  ad_set_daily_budget?: number;
  needs_new_creative?: boolean;
  targets?: Record<string, number>;
  rules?: Array<{
    id: string;
    name: string;
    enabled?: boolean;
    metric?: string;
    action?: string;
  }>;
  ads?: OptimizationAd[];
  actions_log?: Array<{ id?: string; at?: string; action?: string; detail?: string; rule_id?: string }>;
};

export type AgentRun = {
  id: string;
  campaign_id: string;
  agent: string;
  health: string;
  payload: Record<string, unknown>;
  message?: string | null;
  started_at?: string | null;
  finished_at?: string | null;
};

export type Signal = {
  campaign_id: string;
  creative_ready: number;
  brand_sentiment: number;
  roas: number;
  spend_burn: number;
  spend: number;
  updated_at: string;
};

export type Recommendation = {
  id: string;
  campaign_id: string;
  type: string;
  status: string;
  title: string;
  detail: string;
  created_at: string;
};

export type CampaignDetail = {
  campaign: Campaign;
  agents: AgentRun[];
  signals: Signal | null;
  recommendations: Recommendation[];
  timeline?: ActionEvent[];
};

export type WorkspaceSummary = {
  id: string;
  name: string;
  role: string;
  created_at: string;
};

export type MeResponse = {
  id: string;
  email?: string | null;
  auth_enabled: boolean;
  workspaces: WorkspaceSummary[];
};

type RequestOpts = {
  token?: string | null;
  workspaceId?: string | null;
};

async function request<T>(path: string, init?: RequestInit, opts?: RequestOpts): Promise<T> {
  const headers = new Headers(init?.headers || {});
  if (opts?.token) headers.set("Authorization", `Bearer ${opts.token}`);
  if (opts?.workspaceId) headers.set("X-Workspace-Id", opts.workspaceId);

  let res: Response;
  try {
    res = await fetch(resolveApiUrl(path), {
      ...init,
      headers,
      cache: "no-store",
    });
  } catch {
    throw new Error(
      `Cannot reach API at ${apiReachabilityHint()}. Confirm the API is running and refresh.`,
    );
  }
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  return res.json() as Promise<T>;
}

export function fetchMe(token?: string | null) {
  return request<MeResponse>("/api/me", undefined, { token });
}

export function listWorkspaces(token?: string | null) {
  return request<WorkspaceSummary[]>("/api/workspaces", undefined, { token });
}

export function createWorkspace(name: string, token?: string | null) {
  return request<WorkspaceSummary>(
    "/api/workspaces",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    },
    { token },
  );
}

export function listCampaigns(opts?: RequestOpts) {
  return request<Campaign[]>("/api/campaigns", undefined, opts);
}

export function getCampaign(id: string, opts?: RequestOpts) {
  return request<CampaignDetail>(`/api/campaigns/${id}`, undefined, opts);
}

export function listRecommendations(status = "pending", opts?: RequestOpts) {
  return request<Recommendation[]>(`/api/recommendations?status=${status}`, undefined, opts);
}

export async function createCampaignJson(body: Record<string, unknown>, opts?: RequestOpts) {
  return request<Campaign>(
    "/api/campaigns/json",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    },
    opts,
  );
}

export async function createCampaignForm(
  payload: Record<string, unknown>,
  file?: File | null,
  opts?: RequestOpts,
) {
  const form = new FormData();
  form.append("payload", JSON.stringify(payload));
  if (file) form.append("product_image", file);
  return request<Campaign>("/api/campaigns", { method: "POST", body: form }, opts);
}

export function actOnRecommendation(
  id: string,
  action: "approve" | "reject",
  opts?: RequestOpts,
) {
  return request<Recommendation>(
    `/api/recommendations/${id}/action`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action }),
    },
    opts,
  );
}

export function demoTick(campaignId: string, event: string, opts?: RequestOpts) {
  return request(
    `/api/campaigns/${campaignId}/demo-tick`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ event }),
    },
    opts,
  );
}

export function selectAudiences(campaignId: string, selectedIds: string[], opts?: RequestOpts) {
  return request<Campaign>(
    `/api/campaigns/${campaignId}/audiences/select`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ selected_ids: selectedIds }),
    },
    opts,
  );
}

export function recommendAudiences(campaignId: string, opts?: RequestOpts) {
  return request<Campaign>(`/api/campaigns/${campaignId}/audiences/recommend`, { method: "POST" }, opts);
}

export function rebuildMetaDraft(campaignId: string, opts?: RequestOpts) {
  return request<Campaign>(`/api/campaigns/${campaignId}/meta/rebuild-draft`, { method: "POST" }, opts);
}

export function submitMetaReview(campaignId: string, opts?: RequestOpts) {
  return request<Campaign>(`/api/campaigns/${campaignId}/meta/submit-review`, { method: "POST" }, opts);
}

export function rerunCampaign(campaignId: string, opts?: RequestOpts) {
  return request<Campaign>(`/api/campaigns/${campaignId}/rerun`, { method: "POST" }, opts);
}

export function publishMetaCampaign(campaignId: string, opts?: RequestOpts, live = true) {
  const q = live ? "?live=true" : "?live=false";
  return request<Campaign>(`/api/campaigns/${campaignId}/meta/publish${q}`, { method: "POST" }, opts);
}

export function syncMetaMetrics(campaignId: string, opts?: RequestOpts) {
  return request<Campaign>(`/api/campaigns/${campaignId}/meta/sync-metrics`, { method: "POST" }, opts);
}

export function runOptimizationTick(
  campaignId: string,
  body?: { scenario?: string; days?: number },
  opts?: RequestOpts,
) {
  return request<Campaign>(
    `/api/campaigns/${campaignId}/optimization/tick`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body || { scenario: "mixed", days: 1 }),
    },
    opts,
  );
}

export function setAutoPause(campaignId: string, enabled: boolean, opts?: RequestOpts) {
  return request<Campaign>(
    `/api/campaigns/${campaignId}/auto-pause`,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ enabled }),
    },
    opts,
  );
}

export function fetchHealth() {
  return request<{
    ok: boolean;
    llm_enabled?: boolean;
    llm_provider?: string | null;
    capabilities?: Record<string, string>;
    demo_script?: string[];
  }>("/api/health");
}

export function eventsUrl(campaignId: string, opts?: RequestOpts) {
  const params = new URLSearchParams();
  if (opts?.token) params.set("access_token", opts.token);
  if (opts?.workspaceId) params.set("workspace_id", opts.workspaceId);
  const qs = params.toString();
  return resolveApiUrl(`/api/campaigns/${campaignId}/events${qs ? `?${qs}` : ""}`);
}

export function assetUrl(url?: string | null) {
  if (!url) return "";
  return resolveAssetUrl(url);
}

export type Business = {
  id: string;
  workspace_id: string;
  name: string;
  legal_name?: string | null;
  website?: string | null;
  industry?: string | null;
  country?: string | null;
  timezone: string;
  contact_email?: string | null;
  logo_url?: string | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
  meta_status?: string | null;
  selected_page_id?: string | null;
  selected_instagram_id?: string | null;
  selected_ad_account_id?: string | null;
};

export type MetaConnection = {
  id: string;
  business_id: string;
  status: string;
  meta_user_id?: string | null;
  meta_user_name?: string | null;
  scopes: string;
  oauth_configured: boolean;
  selected_page_id?: string | null;
  selected_instagram_id?: string | null;
  selected_ad_account_id?: string | null;
  pages: Array<{
    page_id: string;
    name: string;
    category?: string | null;
    picture_url?: string | null;
    selected: boolean;
  }>;
  instagram_accounts: Array<{
    ig_user_id: string;
    username: string;
    name?: string | null;
    page_id?: string | null;
    profile_picture_url?: string | null;
    selected: boolean;
  }>;
  ad_accounts: Array<{
    ad_account_id: string;
    name: string;
    currency?: string | null;
    timezone_name?: string | null;
    account_status?: string | null;
    selected: boolean;
  }>;
  connected_at: string;
  updated_at: string;
};

export function listBusinesses(opts?: RequestOpts) {
  return request<Business[]>("/api/businesses", undefined, opts);
}

export function createBusiness(body: Record<string, unknown>, opts?: RequestOpts) {
  return request<Business>(
    "/api/businesses",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    },
    opts,
  );
}

export function updateBusiness(
  id: string,
  body: Record<string, unknown>,
  opts?: RequestOpts,
) {
  return request<Business>(
    `/api/businesses/${id}`,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    },
    opts,
  );
}

export function deleteBusiness(id: string, opts?: RequestOpts) {
  return request<{ ok: boolean }>(`/api/businesses/${id}`, { method: "DELETE" }, opts);
}

export function getMetaConnection(businessId: string, opts?: RequestOpts) {
  return request<MetaConnection>(`/api/businesses/${businessId}/meta`, undefined, opts);
}

export function startMetaOAuth(businessId: string, opts?: RequestOpts) {
  return request<{ authorize_url: string; redirect_uri: string }>(
    `/api/businesses/${businessId}/meta/oauth/start`,
    undefined,
    opts,
  );
}

export function demoConnectMeta(businessId: string, opts?: RequestOpts) {
  return request<MetaConnection>(
    `/api/businesses/${businessId}/meta/demo-connect`,
    { method: "POST" },
    opts,
  );
}

export function syncMeta(businessId: string, opts?: RequestOpts) {
  return request<MetaConnection>(
    `/api/businesses/${businessId}/meta/sync`,
    { method: "POST" },
    opts,
  );
}

export function updateMetaSelection(
  businessId: string,
  body: { page_id?: string | null; instagram_id?: string | null; ad_account_id?: string | null },
  opts?: RequestOpts,
) {
  return request<MetaConnection>(
    `/api/businesses/${businessId}/meta/selection`,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    },
    opts,
  );
}

export function disconnectMeta(businessId: string, opts?: RequestOpts) {
  return request<{ ok: boolean }>(
    `/api/businesses/${businessId}/meta`,
    { method: "DELETE" },
    opts,
  );
}

export function metaOAuthStatus(opts?: RequestOpts) {
  return request<{
    oauth_configured: boolean;
    app_id_set: boolean;
    demo_connect_available: boolean;
    config_error?: string | null;
  }>("/api/account/meta/status", undefined, opts);
}

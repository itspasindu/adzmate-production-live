/**
 * Server-side configuration — use private env names (no NEXT_PUBLIC_ prefix).
 * Values here are not bundled into the browser unless passed explicitly via layout props.
 */

export type PublicAuthConfig = {
  supabaseUrl: string;
  supabaseAnonKey: string;
};

function env(...keys: string[]): string {
  for (const key of keys) {
    const value = process.env[key]?.trim();
    if (value) return value;
  }
  return "";
}

export const Config = {
  supabaseUrl: env("SUPABASE_URL", "NEXT_PUBLIC_SUPABASE_URL"),
  supabaseAnonKey: env("SUPABASE_ANON_KEY", "NEXT_PUBLIC_SUPABASE_ANON_KEY"),
  apiInternalUrl: (env("API_INTERNAL_URL", "NEXT_PUBLIC_API_URL") || "http://127.0.0.1:8000").replace(
    /\/$/,
    "",
  ),
} as const;

export function isSupabaseConfigured(): boolean {
  return Boolean(Config.supabaseUrl && Config.supabaseAnonKey);
}

/** Passed from the server layout into client auth — avoids NEXT_PUBLIC_ env vars. */
export function getPublicAuthConfig(): PublicAuthConfig | null {
  if (!isSupabaseConfigured()) return null;
  return {
    supabaseUrl: Config.supabaseUrl,
    supabaseAnonKey: Config.supabaseAnonKey,
  };
}

function normalizeApiPath(path: string): string {
  const p = path.startsWith("/") ? path : `/${path}`;
  return p.startsWith("/api/") ? p : `/api${p}`;
}

/** Browser calls go through Next.js rewrites (/api-proxy → API). Server uses API_INTERNAL_URL. */
export function resolveApiUrl(path: string): string {
  const apiPath = normalizeApiPath(path);

  if (typeof window !== "undefined") {
    return apiPath.replace(/^\/api\//, "/api-proxy/");
  }

  return `${Config.apiInternalUrl}${apiPath}`;
}

export function resolveAssetUrl(url: string): string {
  if (!url) return "";

  const toSameOriginPath = (raw: string): string | null => {
    if (raw.startsWith("/generated/") || raw.startsWith("/uploads/") || raw.startsWith("/previews/")) {
      return raw;
    }
    if (raw.startsWith("/assets/")) {
      return raw;
    }
    if (raw.startsWith("http://") || raw.startsWith("https://")) {
      try {
        const pathname = new URL(raw).pathname;
        if (
          pathname.startsWith("/generated/") ||
          pathname.startsWith("/uploads/") ||
          pathname.startsWith("/previews/") ||
          pathname.startsWith("/assets/")
        ) {
          return pathname;
        }
      } catch {
        return null;
      }
    }
    return null;
  };

  if (typeof window !== "undefined") {
    const sameOrigin = toSameOriginPath(url);
    if (sameOrigin) return sameOrigin;
    if (url.startsWith("http://") || url.startsWith("https://")) return url;
    const path = url.startsWith("/") ? url : `/${url}`;
    return toSameOriginPath(path) || path;
  }

  const sameOrigin = toSameOriginPath(url);
  if (sameOrigin) {
    return `${Config.apiInternalUrl}${sameOrigin}`;
  }
  if (url.startsWith("http://") || url.startsWith("https://")) return url;

  const path = url.startsWith("/") ? url : `/${url}`;
  return `${Config.apiInternalUrl}${path}`;
}

export function apiReachabilityHint(): string {
  if (typeof window !== "undefined") {
    return "the API via /api-proxy (check API_INTERNAL_URL and that the API is running)";
  }
  return Config.apiInternalUrl;
}

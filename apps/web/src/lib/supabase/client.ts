import { createBrowserClient } from "@supabase/ssr";

import type { PublicAuthConfig } from "@/lib/config";

export function createClient(auth: PublicAuthConfig) {
  return createBrowserClient(auth.supabaseUrl, auth.supabaseAnonKey);
}

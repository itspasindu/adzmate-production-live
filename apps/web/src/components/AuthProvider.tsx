"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import type { Session, User } from "@supabase/supabase-js";
import { createClient, isSupabaseConfigured } from "@/lib/supabase/client";
import { fetchMe, MeResponse, WorkspaceSummary } from "@/lib/api";

type AuthContextValue = {
  loading: boolean;
  authConfigured: boolean;
  session: Session | null;
  user: User | null;
  me: MeResponse | null;
  workspaces: WorkspaceSummary[];
  workspaceId: string | null;
  workspace: WorkspaceSummary | null;
  setWorkspaceId: (id: string) => void;
  refreshMe: () => Promise<void>;
  signOut: () => Promise<void>;
  getAccessToken: () => Promise<string | null>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

const WORKSPACE_KEY = "adzmate_workspace_id";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const authConfigured = isSupabaseConfigured();
  const [loading, setLoading] = useState(true);
  const [session, setSession] = useState<Session | null>(null);
  const [me, setMe] = useState<MeResponse | null>(null);
  const [workspaceId, setWorkspaceIdState] = useState<string | null>(null);

  const getAccessToken = useCallback(async () => {
    if (!authConfigured) return null;
    const supabase = createClient();
    const { data } = await supabase.auth.getSession();
    return data.session?.access_token ?? null;
  }, [authConfigured]);

  const refreshMe = useCallback(async () => {
    try {
      const token = authConfigured ? await getAccessToken() : null;
      if (authConfigured && !token) {
        setMe(null);
        return;
      }
      const profile = await fetchMe(token);
      setMe(profile);
      const saved = typeof window !== "undefined" ? localStorage.getItem(WORKSPACE_KEY) : null;
      const ids = profile.workspaces.map((w) => w.id);
      const next =
        (saved && ids.includes(saved) && saved) ||
        profile.workspaces[0]?.id ||
        null;
      setWorkspaceIdState(next);
      if (next) localStorage.setItem(WORKSPACE_KEY, next);
    } catch (err) {
      // API may be restarting (uvicorn --reload) — don't crash the app shell
      console.warn(
        "AdzMate API unreachable. Is it running on",
        process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000",
        "?",
        err instanceof Error ? err.message : err,
      );
    }
  }, [authConfigured, getAccessToken]);

  useEffect(() => {
    let mounted = true;
    let unsubscribe: (() => void) | undefined;

    async function boot() {
      try {
        if (!authConfigured) {
          await refreshMe();
          return;
        }
        const supabase = createClient();
        const { data } = await supabase.auth.getSession();
        if (!mounted) return;
        setSession(data.session);
        if (data.session) {
          await refreshMe();
        }
        const { data: sub } = supabase.auth.onAuthStateChange(async (_event, nextSession) => {
          if (!mounted) return;
          setSession(nextSession);
          if (nextSession) {
            await refreshMe();
          } else {
            setMe(null);
            setWorkspaceIdState(null);
          }
        });
        unsubscribe = () => sub.subscription.unsubscribe();
      } catch (err) {
        console.warn("Auth boot failed:", err);
      } finally {
        if (mounted) setLoading(false);
      }
    }

    void boot();
    return () => {
      mounted = false;
      unsubscribe?.();
    };
  }, [authConfigured, refreshMe]);

  const setWorkspaceId = useCallback((id: string) => {
    setWorkspaceIdState(id);
    localStorage.setItem(WORKSPACE_KEY, id);
  }, []);

  const signOut = useCallback(async () => {
    if (!authConfigured) return;
    const supabase = createClient();
    await supabase.auth.signOut();
    setSession(null);
    setMe(null);
    setWorkspaceIdState(null);
    localStorage.removeItem(WORKSPACE_KEY);
  }, [authConfigured]);

  const workspace = useMemo(
    () => me?.workspaces.find((w) => w.id === workspaceId) || null,
    [me, workspaceId],
  );

  const value: AuthContextValue = {
    loading,
    authConfigured,
    session,
    user: session?.user ?? null,
    me,
    workspaces: me?.workspaces ?? [],
    workspaceId,
    workspace,
    setWorkspaceId,
    refreshMe,
    signOut,
    getAccessToken,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

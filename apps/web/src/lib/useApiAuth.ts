"use client";

import { useAuth } from "@/components/AuthProvider";
import { useCallback } from "react";

/** Auth + workspace headers for API calls. */
export function useApiAuth() {
  const { getAccessToken, workspaceId } = useAuth();

  const withAuth = useCallback(async () => {
    const token = await getAccessToken();
    return { token, workspaceId };
  }, [getAccessToken, workspaceId]);

  return { withAuth, workspaceId };
}

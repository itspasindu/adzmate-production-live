/** Plain-language status for non-technical users. */
export function friendlyCampaignStatus(status: string): string {
  const map: Record<string, string> = {
    draft: "Draft",
    received: "Starting…",
    agents_running: "Creating your ads…",
    aggregating: "Checking quality…",
    awaiting_approval: "Ready to publish",
    deploying: "Publishing…",
    live: "Live",
    halted: "Paused",
    failed: "Needs attention",
    degraded: "Running with warnings",
  };
  return map[status] || status.replaceAll("_", " ");
}

export function friendlyPublishStatus(status?: string | null): string {
  const map: Record<string, string> = {
    none: "Not started",
    draft: "Ads prepared — not live yet",
    in_review: "Waiting for your OK",
    published: "Published",
  };
  return map[status || "none"] || status || "Not started";
}

export function nextSimpleAction(campaign: {
  status: string;
  publish_status?: string | null;
  decision?: string | null;
}): { label: string; kind: "publish" | "wait" | "done" | "pause" | "fix" } {
  if (campaign.status === "halted") return { label: "Ads are paused", kind: "pause" };
  if (campaign.status === "failed") return { label: "Something went wrong — try again", kind: "fix" };
  if (campaign.publish_status === "published" || campaign.status === "live") {
    return { label: "Your ads are live", kind: "done" };
  }
  if (campaign.status === "awaiting_approval") {
    if (campaign.decision === "HALT") return { label: "Review pause recommendation", kind: "pause" };
    return { label: "Publish my ads", kind: "publish" };
  }
  if (["received", "agents_running", "aggregating", "deploying"].includes(campaign.status)) {
    return { label: "Working on your ads…", kind: "wait" };
  }
  return { label: "Continue", kind: "wait" };
}

/** Public marketing pages — no auth or app shell required. */
export const MARKETING_ROUTES = [
  "/",
  "/features",
  "/pricing",
  "/about",
  "/contact",
  "/faq",
  "/privacy",
  "/terms",
] as const;

export const AUTH_ROUTES = ["/login", "/signup"] as const;

export function isMarketingRoute(pathname: string): boolean {
  if (pathname === "/") return true;
  return MARKETING_ROUTES.some((route) => route !== "/" && pathname.startsWith(route));
}

export function isAuthRoute(pathname: string): boolean {
  return AUTH_ROUTES.some((route) => pathname === route || pathname.startsWith(`${route}/`));
}

export function isPublicRoute(pathname: string): boolean {
  return isMarketingRoute(pathname) || isAuthRoute(pathname);
}

export const APP_HOME = "/dashboard";

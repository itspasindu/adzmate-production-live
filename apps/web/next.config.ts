import type { NextConfig } from "next";
import path from "path";

/** Server-side proxy target (Docker service name or localhost). */
const apiInternal =
  process.env.API_INTERNAL_URL?.replace(/\/$/, "") || "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  output: "standalone",
  // Monorepo: include files from repo root in the standalone trace
  outputFileTracingRoot: path.join(__dirname, "../.."),
  async rewrites() {
    return [
      {
        source: "/api-proxy/:path*",
        destination: `${apiInternal}/api/:path*`,
      },
      {
        source: "/uploads/:path*",
        destination: `${apiInternal}/uploads/:path*`,
      },
      {
        source: "/generated/:path*",
        destination: `${apiInternal}/generated/:path*`,
      },
      {
        source: "/previews/:path*",
        destination: `${apiInternal}/previews/:path*`,
      },
    ];
  },
};

export default nextConfig;

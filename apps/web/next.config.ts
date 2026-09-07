import type { NextConfig } from "next";

const API = process.env.API_PROXY_TARGET || "http://127.0.0.1:8000";

if (process.env.MODAL_WEB_BUILD === "1" && !process.env.NEXT_PUBLIC_API_BASE) {
  console.error("NEXT_PUBLIC_API_BASE must be set when building the Modal web image.");
  process.exit(1);
}

const nextConfig: NextConfig = {
  output: "standalone",
  async rewrites() {
    if (process.env.NEXT_PUBLIC_API_BASE) return [];
    return [{ source: "/api/:path*", destination: `${API}/api/:path*` }];
  },
};

export default nextConfig;

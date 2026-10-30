import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  skipTrailingSlashRedirect: true,
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://127.0.0.1:8000/api/:path*",
      },
      {
        source: "/media/:path*",
        destination: "http://127.0.0.1:8000/media/:path*",
      },
    ]
  },
  cacheComponents: true,
  partialPrefetching: true,
  experimental: {
    // Composer/Anna LLM calls can take several minutes; the rewrite proxy
    // otherwise dies at 30s while Django is still writing the draft.
    proxyTimeout: 300000,
  },
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;

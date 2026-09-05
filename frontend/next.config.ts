import path from "path";
import type { NextConfig } from "next";

const onOneDriveWindows =
  process.platform === "win32" && !process.env.VERCEL && !process.env.RENDER;

const nextConfig: NextConfig = {
  // .next-local is a junction to %LOCALAPPDATA% (see scripts/prepare-next-cache.mjs).
  distDir: onOneDriveWindows ? ".next-local" : ".next",
  output: "standalone",
  reactStrictMode: true,
  webpack: (config) => {
    config.resolve.modules = [
      path.join(process.cwd(), "node_modules"),
      ...(config.resolve.modules || ["node_modules"]),
    ];
    return config;
  },
  async rewrites() {
    return [{ source: "/favicon.ico", destination: "/favicon.svg" }];
  },
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
        ],
      },
      {
        source: "/widget.js",
        headers: [
          { key: "Access-Control-Allow-Origin", value: "*" },
          { key: "Cache-Control", value: "public, max-age=300" },
        ],
      },
      {
        source: "/embed",
        headers: [
          {
            key: "Content-Security-Policy",
            value: "frame-ancestors *",
          },
        ],
      },
    ];
  },
};

export default nextConfig;

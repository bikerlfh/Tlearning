import type { NextConfig } from "next";
import { withSentryConfig } from "@sentry/nextjs";

// next-pwa@5 ships no .d.ts; cast through a minimal local type.
// eslint-disable-next-line @typescript-eslint/no-require-imports
const nextPWA = require("next-pwa") as (options: {
  dest: string;
  disable?: boolean;
  register?: boolean;
  skipWaiting?: boolean;
  customWorkerDir?: string;
}) => (config: NextConfig) => NextConfig;

const withPWA = nextPWA({
  dest: "public",
  disable: process.env.NODE_ENV === "development",
  register: true,
  skipWaiting: true,
  customWorkerDir: "worker",
});

const nextConfig: NextConfig = {
  reactStrictMode: true,
  async redirects() {
    // Marketing apex domain → PWA subdomain. No-op in local dev (host won't match).
    return [
      {
        source: "/:path*",
        has: [{ type: "host", value: "tlearning.app" }],
        destination: "https://app.tlearning.app/:path*",
        permanent: true,
      },
    ];
  },
};

// Compose: Sentry wraps PWA wraps the base config. Source map upload runs only
// when the org/project/auth-token env vars are set (Vercel/Fly secrets).
export default withSentryConfig(withPWA(nextConfig), {
  silent: true,
  org: process.env.SENTRY_ORG,
  project: process.env.SENTRY_PROJECT,
  authToken: process.env.SENTRY_AUTH_TOKEN,
  disableLogger: true,
  widenClientFileUpload: true,
  sourcemaps: { deleteSourcemapsAfterUpload: true },
});

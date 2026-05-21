import type { NextConfig } from "next";
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
};

export default withPWA(nextConfig);

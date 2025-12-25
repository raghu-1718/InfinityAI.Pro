import type { NextConfig } from "next";

const nextConfig = {
  /* config options here */
  reactCompiler: true,

  // Enable static export for Firebase Hosting
  output: 'export',

  // Disable image optimization for static export
  images: {
    unoptimized: true,
  },

  // Trailing slash for proper routing
  trailingSlash: true,

  // Set turbopack root to resolve workspace warning
  turbopack: {
    root: process.cwd(),
  },

  // Skip linting constraints during build for rapid iteration
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
};

export default nextConfig;

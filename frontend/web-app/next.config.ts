import type { NextConfig } from "next";

const nextConfig: NextConfig = {
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
};

export default nextConfig;

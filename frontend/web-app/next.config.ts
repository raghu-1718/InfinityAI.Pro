import path from "path";

/** @type {import('next').NextConfig} */
const nextConfig = {
  /* config options here */
  reactCompiler: true,

  // Enable static export for Firebase Hosting
  // API routes moved to Cloud Functions - see frontend/functions/
  // output: "export", // Removed for Vercel deployment

  // Images configuration for server-side rendering
  images: {
    unoptimized: true,
  },

  // Remove trailing slash for API route compatibility
  // trailingSlash: true,  // REMOVED - causes issues with API routes

  // Set turbopack root - use process.cwd() for better Docker compatibility
  turbopack:
    process.env.NODE_ENV === "production"
      ? {}
      : {
          root: path.resolve(__dirname, "../../"),
        },

  typescript: {
    ignoreBuildErrors: true,
  },

  // Webpack alias for @ -> ./src (ensures path resolution in Docker/Cloud Build)
  webpack: (config: any) => {
    config.resolve = config.resolve || {};
    config.resolve.alias = {
      ...(config.resolve.alias || {}),
      "@": path.resolve(__dirname, "src"),
    };
    return config;
  },

};

export default nextConfig;

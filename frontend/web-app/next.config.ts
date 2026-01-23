import path from "path";

/** @type {import('next').NextConfig} */
const nextConfig = {
  /* config options here */
  reactCompiler: true,

  // Enable static export for Firebase Hosting
  // API routes moved to Cloud Functions - see frontend/functions/
  output: "export",

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
  webpack: (config) => {
    config.resolve = config.resolve || {};
    config.resolve.alias = {
      ...(config.resolve.alias || {}),
      "@": path.resolve(__dirname, "src"),
    };
    return config;
  },

  // Turbopack experimental alias (Next.js 15+)
  experimental: {
    turbo: {
      resolveAlias: {
        "@": "./src",
      },
    },
  },

  // Firebase configuration - matches firebase/config.ts (UNIFIED)
  // Engine URLs removed - use Firebase Hosting rewrites instead (see firebase.json)
  env: {
    NEXT_PUBLIC_FIREBASE_API_KEY: "AIzaSyD_y3lIPm7bTEXy3Uy4deGTnZPpjr2A8B8",
    NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN:
      "galvanic-pulsar-482815-h0.firebaseapp.com",
    NEXT_PUBLIC_FIREBASE_PROJECT_ID: "galvanic-pulsar-482815-h0",
    NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET:
      "galvanic-pulsar-482815-h0.firebasestorage.app",
    NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID: "228557716858",
    NEXT_PUBLIC_FIREBASE_APP_ID: "1:228557716858:web:d3ae59af1254d4b893aac3",
    NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID: "G-17NHEMLXDV",
    // Ably Real-Time Configuration
    // Set via Secret Manager at deployment time
    NEXT_PUBLIC_ABLY_API_KEY: process.env.NEXT_PUBLIC_ABLY_API_KEY || "",
  },
};

export default nextConfig;

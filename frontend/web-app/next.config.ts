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

  // Set turbopack root to resolve workspace warning
  turbopack: {
    root: path.resolve(__dirname, "../../"),
  },

  typescript: {
    ignoreBuildErrors: true,
  },

  // Hardcoded environment variables to ensure they are available at build/runtime
  env: {
    NEXT_PUBLIC_ENGINE_A_URL:
      "https://engine-a-228557716858.us-central1.run.app",
    NEXT_PUBLIC_ENGINE_B_URL:
      "https://engine-b-228557716858.us-central1.run.app",
    NEXT_PUBLIC_ENGINE_C_URL:
      "https://engine-c-228557716858.us-central1.run.app",
    NEXT_PUBLIC_FIREBASE_API_KEY: "AIzaSyAnEUI1GqUnAL8h3GFQMmnpBXv7nh6tu3k",
    NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN:
      "galvanic-pulsar-482815-h0.firebaseapp.com",
    NEXT_PUBLIC_FIREBASE_PROJECT_ID: "galvanic-pulsar-482815-h0",
    NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET:
      "galvanic-pulsar-482815-h0.firebasestorage.app",
    NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID: "429140669077",
    NEXT_PUBLIC_FIREBASE_APP_ID: "1:429140669077:web:e071ad7a136c74a3ea219c",
    NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID: "G-NY37ZKLPBX",
  },
};

export default nextConfig;

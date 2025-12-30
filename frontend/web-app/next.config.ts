import path from "path";

/** @type {import('next').NextConfig} */
const nextConfig = {
  /* config options here */
  reactCompiler: true,

  // Enable static export for Firebase Hosting
  output: "export",

  // Disable image optimization for static export
  images: {
    unoptimized: true,
  },

  // Trailing slash for proper routing
  trailingSlash: true,

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
      "https://engine-a-429140669077.us-central1.run.app",
    NEXT_PUBLIC_ENGINE_B_URL:
      "https://engine-b-429140669077.us-central1.run.app",
    NEXT_PUBLIC_ENGINE_C_URL:
      "https://engine-c-429140669077.us-central1.run.app",
    NEXT_PUBLIC_FIREBASE_API_KEY: "AIzaSyAnEUI1GqUnAL8h3GFQMmnpBXv7nh6tu3k",
    NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN:
      "gen-lang-client-0779271931.firebaseapp.com",
    NEXT_PUBLIC_FIREBASE_PROJECT_ID: "gen-lang-client-0779271931",
    NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET:
      "gen-lang-client-0779271931.firebasestorage.app",
    NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID: "429140669077",
    NEXT_PUBLIC_FIREBASE_APP_ID: "1:429140669077:web:e071ad7a136c74a3ea219c",
    NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID: "G-NY37ZKLPBX",
  },
};

export default nextConfig;

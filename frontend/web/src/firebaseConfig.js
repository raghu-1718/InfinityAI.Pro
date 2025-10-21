// Lightweight Firebase initialization for frontend test helpers
// Reads config from Vite-style env vars when available; otherwise falls back to project defaults.

import { initializeApp, getApp, getApps } from "firebase/app";
import { getFunctions } from "firebase/functions";

const env = (typeof import !== 'undefined' && import.meta && import.meta.env) ? import.meta.env : {};

const firebaseConfig = {
  apiKey: env.VITE_FIREBASE_API_KEY,
  authDomain: env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: env.VITE_FIREBASE_PROJECT_ID || "infinity-ai-5ec7c",
  storageBucket: env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: env.VITE_FIREBASE_APP_ID,
};

// Initialize app (guarded for HMR)
export const app = getApps().length ? getApp() : initializeApp(firebaseConfig);

// Export Functions client pinned to deployed region
export const functions = getFunctions(app, "us-central1");
// Lightweight Firebase initialization for frontend test helpers
// Reads config from Vite-style env vars when available; otherwise fallback to placeholders.

import { initializeApp, getApp, getApps } from "firebase/app";
import { getFunctions } from "firebase/functions";

// Prefer Vite env variables if present; adjust as needed for your build tool
const firebaseConfig = {
  apiKey: (typeof import !== 'undefined' && import.meta && import.meta.env && import.meta.env.VITE_FIREBASE_API_KEY) || undefined,
  authDomain: (typeof import !== 'undefined' && import.meta && import.meta.env && import.meta.env.VITE_FIREBASE_AUTH_DOMAIN) || undefined,
  projectId: (typeof import !== 'undefined' && import.meta && import.meta.env && import.meta.env.VITE_FIREBASE_PROJECT_ID) || "infinity-ai-5ec7c",
  storageBucket: (typeof import !== 'undefined' && import.meta && import.meta.env && import.meta.env.VITE_FIREBASE_STORAGE_BUCKET) || undefined,
  messagingSenderId: (typeof import !== 'undefined' && import.meta && import.meta.env && import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID) || undefined,
  appId: (typeof import !== 'undefined' && import.meta && import.meta.env && import.meta.env.VITE_FIREBASE_APP_ID) || undefined,
};

// Initialize (guarded so it works in hot-reload)
export const app = getApps().length ? getApp() : initializeApp(firebaseConfig);

// Functions client (pin to deployed region)
export const functions = getFunctions(app, "us-central1");

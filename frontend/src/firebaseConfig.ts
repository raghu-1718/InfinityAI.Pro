/**
 * Firebase Configuration for InfinityAI.Pro
 * Project: infinity-ai-5ec7c
 * 
 * Initializes Firebase app with authentication, Firestore, and Cloud Functions
 * Uses environment variables for sensitive credentials
 * 
 * Updated: 2025-10-22 - Deployed with corrected API keys and workflow improvements
 */

import { initializeApp, getApp, getApps, FirebaseApp } from "firebase/app";
import { getAuth, Auth, connectAuthEmulator } from "firebase/auth";
import { getFirestore, Firestore, connectFirestoreEmulator } from "firebase/firestore";
import { getFunctions, Functions, connectFunctionsEmulator } from "firebase/functions";

// Firebase configuration - reads from Vite environment variables
const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || "AIzaSyDjD8D3UYwM_PvPkPoBNZ5soOpsN7hoNVU",
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || "infinity-ai-5ec7c.firebaseapp.com",
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || "infinity-ai-5ec7c",
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || "infinity-ai-5ec7c.firebasestorage.app",
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || "26140490557",
  appId: import.meta.env.VITE_FIREBASE_APP_ID || "1:26140490557:web:6d99cdd77d3f9408c26354",
  measurementId: import.meta.env.VITE_FIREBASE_MEASUREMENT_ID || "G-3GPS2VZQS9"
};

// Initialize Firebase (singleton pattern to avoid multiple instances)
let app: FirebaseApp;
if (getApps().length === 0) {
  app = initializeApp(firebaseConfig);
  console.log("Firebase initialized for project:", firebaseConfig.projectId);
} else {
  app = getApp();
}

// Initialize services
export const auth: Auth = getAuth(app);
export const db: Firestore = getFirestore(app);
export const functions: Functions = getFunctions(app, "us-central1");

// Enable emulators in development mode
if (import.meta.env.DEV && import.meta.env.VITE_USE_EMULATORS === "true") {
  connectAuthEmulator(auth, "http://localhost:9099");
  connectFirestoreEmulator(db, "localhost", 8080);
  connectFunctionsEmulator(functions, "localhost", 5001);
  console.log("🔧 Firebase emulators connected");
}

// Export the app instance
export { app };

// Export configuration for debugging
export const config = {
  projectId: firebaseConfig.projectId,
  region: "us-central1",
  authDomain: firebaseConfig.authDomain
};

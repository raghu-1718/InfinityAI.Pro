/**
 * InfinityAI.Pro - Cloud Functions Index
 *
 * Main entry point for all Firebase Cloud Functions
 * Exports: Authentication, Trading, Portfolio Analysis functions
 */

import * as admin from "firebase-admin";

// Initialize Firebase Admin SDK
admin.initializeApp();

// Export all functions
export { startTrading, stopTrading } from "./startTrading";
export {
  analyzePortfolio,
  getAiSignals,
  getVertexAiAnalysis,
  getGeminiAnalysis,
  getBatchAiSignals,
  getDhanOverview,
} from "./analyzePortfolio";

// Export new trading setup functions
export { verifyCoupon } from "./verifyCoupon";
export { submitDhanCredentialsV2 as storeUserCredentials, getDecryptedCredentials as getUserCredentials } from "./storeCredentials";
export { fetchAccountData } from "./accountData";

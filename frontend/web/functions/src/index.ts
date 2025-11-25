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
export { submitDhanCredentialsV2, saveDhanCredentials } from "./storeCredentials";
export { startTrading, stopTrading } from "./startTrading";
export {
  analyzePortfolio,
  syncHoldings,
  getAiSignals,
  getVertexAiAnalysis,
  getGeminiAnalysis,
  analyzeImageWithRoboticsER,
  getBatchAiSignals,
  getEngineBStatus,
  getDhanOverview,
} from "./analyzePortfolio";

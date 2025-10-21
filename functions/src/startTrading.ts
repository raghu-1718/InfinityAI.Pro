/**
 * Start Trading Function
 * 
 * Initiates a trading session by calling Engine C execution service
 * Creates session document in Firestore and triggers portfolio analysis
 */

import { onCall, HttpsError } from "firebase-functions/v2/https";
import * as admin from "firebase-admin";
import axios from "axios";
import { getDecryptedCredentials } from "./storeCredentials";

const db = admin.firestore();

// Cloud Run Engine URLs (configure via environment variables)
const ENGINE_C_URL = process.env.ENGINE_C_URL || "https://infinityai-engine-c-execution-26140490557.us-central1.run.app";

interface StartTradingData {
  userId: string;
  strategy: "equities" | "options" | "mcx";
  amount: string;
  risk: string;
}

/**
 * Start Trading Session
 * 
 * @param data - { userId, strategy, amount, risk }
 * @returns { message, sessionId, status }
 */
export const startTrading = onCall(
  {
    region: "us-central1",
    memory: "512MiB",
    timeoutSeconds: 120,
    secrets: ["ENCRYPTION_KEY"],
  },
  async (request) => {
    // Verify authentication
    if (!request.auth) {
      throw new HttpsError("unauthenticated", "User must be logged in to start trading.");
    }

  const uid = request.auth.uid;
  const { strategy, amount, risk } = request.data as StartTradingData;

    // Validate inputs
    if (!strategy || !amount || !risk) {
      throw new HttpsError("invalid-argument", "Missing required fields: strategy, amount, or risk");
    }

    const amountNum = parseFloat(amount);
    const riskNum = parseFloat(risk);

    if (isNaN(amountNum) || amountNum < 1000) {
      throw new HttpsError("invalid-argument", "Amount must be at least ₹1,000");
    }

    if (isNaN(riskNum) || riskNum < 1 || riskNum > 20) {
      throw new HttpsError("invalid-argument", "Risk must be between 1% and 20%");
    }

    if (!["equities", "options", "mcx"].includes(strategy)) {
      throw new HttpsError("invalid-argument", "Invalid strategy. Must be: equities, options, or mcx");
    }

    try {
      // Retrieve user's Dhan credentials
      const credentials = await getDecryptedCredentials(uid);

      if (!credentials.accessToken) {
        throw new HttpsError(
          "failed-precondition",
          "Access token not found. Please update your Dhan credentials with an access token."
        );
      }

      // Generate unique session ID
      const sessionId = `session_${Date.now()}_${uid.substring(0, 8)}`;

      // Create trading session document in Firestore
      const sessionData = {
        sessionId,
        userId: uid,
        strategy,
        amount: amountNum,
        risk: riskNum,
        status: "INITIATED",
        startTime: admin.firestore.FieldValue.serverTimestamp(),
        createdAt: admin.firestore.FieldValue.serverTimestamp(),
        engine: "engine-c",
      };

      await db.collection("trading_sessions").doc(sessionId).set(sessionData);

      console.log(`✅ Trading session created: ${sessionId}`);

      // Call Engine C to start trading execution
      try {
        const enginePayload = {
          sessionId,
          userId: uid,
          strategy,
          amount: amountNum,
          risk: riskNum,
          credentials: {
            clientId: credentials.clientId,
            accessToken: credentials.accessToken,
          },
        };

        const engineResponse = await axios.post(
          `${ENGINE_C_URL}/start`,
          enginePayload,
          {
            headers: {
              "Content-Type": "application/json",
            },
            timeout: 30000, // 30 seconds
          }
        );

        console.log(`✅ Engine C response:`, engineResponse.data);

        // Update session with engine response
        await db.collection("trading_sessions").doc(sessionId).update({
          status: "RUNNING",
          engineResponse: engineResponse.data,
          lastUpdatedAt: admin.firestore.FieldValue.serverTimestamp(),
        });

        // Trigger portfolio analysis after starting
        await triggerPortfolioAnalysis(uid, sessionId);

        return {
          message: `Trading session started successfully! Strategy: ${strategy}`,
          sessionId,
          status: "RUNNING",
          engineStatus: engineResponse.data,
        };
      } catch (engineError: any) {
        console.error("❌ Engine C execution error:", engineError.message);

        // Update session status to failed
        await db.collection("trading_sessions").doc(sessionId).update({
          status: "FAILED",
          error: engineError.message,
          lastUpdatedAt: admin.firestore.FieldValue.serverTimestamp(),
        });

        throw new HttpsError(
          "internal",
          `Failed to start trading on Engine C: ${engineError.message}`
        );
      }
    } catch (error: any) {
      console.error("❌ Error starting trading session:", error);
      
      if (error instanceof HttpsError) {
        throw error;
      }
      
      throw new HttpsError("internal", `Failed to start trading: ${error.message}`);
    }
  }
);

/**
 * Stop Trading Session
 * 
 * @param data - { sessionId }
 * @returns { message, status }
 */
export const stopTrading = onCall(
  {
    region: "us-central1",
    memory: "256MiB",
    timeoutSeconds: 60,
    secrets: ["ENCRYPTION_KEY"],
  },
  async (request) => {
    if (!request.auth) {
      throw new HttpsError("unauthenticated", "User must be logged in.");
    }

    const { sessionId } = request.data;

    if (!sessionId) {
      throw new HttpsError("invalid-argument", "Missing sessionId");
    }

    try {
      const sessionDoc = await db.collection("trading_sessions").doc(sessionId).get();

      if (!sessionDoc.exists) {
        throw new HttpsError("not-found", "Trading session not found");
      }

      const sessionData = sessionDoc.data()!;

      // Verify ownership
      if (sessionData.userId !== request.auth.uid) {
        throw new HttpsError("permission-denied", "You don't have permission to stop this session");
      }

      // Call Engine C to stop execution
      try {
        await axios.post(
          `${ENGINE_C_URL}/stop`,
          { sessionId },
          {
            headers: { "Content-Type": "application/json" },
            timeout: 10000,
          }
        );
      } catch (stopError) {
        console.warn("⚠️ Engine C stop request failed (continuing anyway):", stopError);
      }

      // Update session status
      await db.collection("trading_sessions").doc(sessionId).update({
        status: "STOPPED",
        endTime: admin.firestore.FieldValue.serverTimestamp(),
        lastUpdatedAt: admin.firestore.FieldValue.serverTimestamp(),
      });

      console.log(`✅ Trading session stopped: ${sessionId}`);

      return {
        message: "Trading session stopped successfully",
        status: "STOPPED",
      };
    } catch (error: any) {
      console.error("❌ Error stopping trading session:", error);
      throw new HttpsError("internal", `Failed to stop trading: ${error.message}`);
    }
  }
);

/**
 * Helper: Trigger portfolio analysis via Gemini
 */
async function triggerPortfolioAnalysis(userId: string, sessionId: string): Promise<void> {
  try {
    // Create a document in the 'generate' collection for Gemini extension
    await db.collection("generate").add({
      prompt: `Analyze the trading session for user ${userId}. Session ID: ${sessionId}. 
      
      Provide insights on:
      - Current market conditions for Indian markets (NIFTY, BANKNIFTY)
      - Risk assessment for the selected strategy
      - Recommended actions based on real-time data
      - Key support and resistance levels
      
      Be concise and actionable.`,
      model: "gemini-2.0-flash",
      userId,
      sessionId,
      createTime: admin.firestore.FieldValue.serverTimestamp(),
    });

    console.log(`✅ Gemini analysis triggered for session: ${sessionId}`);
  } catch (error) {
    console.warn("⚠️ Failed to trigger Gemini analysis:", error);
    // Don't fail the main request if analysis fails
  }
}

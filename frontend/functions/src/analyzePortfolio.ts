/**
 * Portfolio Analysis Functions
 *
 * Syncs holdings from Dhan API and triggers AI analysis
 * Firestore trigger: Automatically analyzes when holdings are updated
 */

import { onCall, HttpsError } from "firebase-functions/v2/https";
import { onDocumentWritten } from "firebase-functions/v2/firestore";
import * as admin from "firebase-admin";
import axios from "axios";
import { getDecryptedCredentials } from "./storeCredentials";
import { ENGINE_URLS } from "./config";

const db = admin.firestore();

interface DhanHolding {
  securityId: string;
  tradingSymbol: string;
  exchange: string;
  isin: string;
  totalQty: number;
  availableQty: number;
  avgCostPrice: number;
  currentMarketPrice: number;
  pnl: number;
  pnlPercentage: number;
}

/**
 * Sync Holdings from Dhan API
 *
 * Fetches current holdings and stores them in Firestore
 * @param data - { userId }
 * @returns { message, holdings, count }
 */
export const syncHoldings = onCall(
  {
    region: "us-central1",
    memory: "512MiB",
    timeoutSeconds: 120,
    // ENCRYPTION_KEY will be provided via environment variable instead
  },
  async (request) => {
    if (!request.auth) {
      throw new HttpsError("unauthenticated", "User must be logged in.");
    }

    const uid = request.auth.uid;

    try {
      // Get decrypted Dhan credentials
      const credentials = await getDecryptedCredentials(uid);

      if (!credentials.accessToken) {
        throw new HttpsError(
          "failed-precondition",
          "Access token required. Please update your credentials."
        );
      }

      console.log(`📊 Fetching holdings for user: ${uid}`);

      // ARCHITECTURE FIX: Point to Engine ANALYTICS, the data hub, not Engine C.
      // The Cloud Function securely provides the credentials to the trusted engine.
      // We will use the more efficient `overview` endpoint which includes holdings.
      const response = await axios.get(`${ENGINE_URLS.ANALYTICS}/api/dhan/overview`, {
        headers: {
          "x-client-id": credentials.clientId,
          "Authorization": `Bearer ${credentials.accessToken}`
        },
        timeout: 30000,
      });

      // The overview endpoint in Engine ANALYTICS returns holdings in a `holdings` field.
      const holdings: DhanHolding[] = response.data.holdings || [];

      console.log(`✅ Retrieved ${holdings.length} holdings from Dhan API`);

      const userHoldingsRef = db.collection("holdings").doc(uid);
      const itemsCollectionRef = userHoldingsRef.collection("items");

      // 1. Clear out old holdings to prevent stale data
      const oldHoldingsSnapshot = await itemsCollectionRef.get();
      if (!oldHoldingsSnapshot.empty) {
        console.log(`🗑️ Deleting ${oldHoldingsSnapshot.size} old holding items...`);
        // Handle batching for > 500 deletes
        const deletePromises: Promise<any>[] = [];
        let deleteBatch = db.batch();
        oldHoldingsSnapshot.docs.forEach((doc, index) => {
          deleteBatch.delete(doc.ref);
          if ((index + 1) % 500 === 0) {
            deletePromises.push(deleteBatch.commit());
            deleteBatch = db.batch();
          }
        });
        deletePromises.push(deleteBatch.commit());
        await Promise.all(deletePromises);
      }

      // Create a new batch for setting data
      const batch = db.batch();
      // 2. Update the main holdings document
      batch.set(userHoldingsRef, {
        userId: uid,
        totalHoldings: holdings.length,
        lastSyncedAt: admin.firestore.FieldValue.serverTimestamp(),
        updatedAt: admin.firestore.FieldValue.serverTimestamp(),
      }, { merge: true });

      // 3. Add the new individual holdings
      holdings.forEach((holding) => {
        // Use a consistent and safe document ID
        const holdingDocRef = itemsCollectionRef.doc(holding.securityId);
        batch.set(holdingDocRef, {
          ...holding,
          syncedAt: admin.firestore.FieldValue.serverTimestamp(),
        });
      });

      await batch.commit();

      console.log(`✅ Holdings synced to Firestore for user: ${uid}`);

      // Trigger AI analysis on the updated holdings
      await triggerHoldingsAnalysis(uid, holdings);

      return {
        message: "Holdings synced successfully",
        holdings,
        count: holdings.length,
      };
    } catch (error: any) {
      console.error("❌ Error syncing holdings:", error);

      if (error.response?.status === 401 || error.response?.data?.code === "UNAUTHENTICATED") {
        throw new HttpsError("unauthenticated", "Invalid or expired Dhan access token");
      }

      throw new HttpsError("internal", `Failed to sync holdings: ${error.message}`);
    }
  }
);

/**
 * Get AI Signals from Engine CORE
 *
 * Fetches AI/ML trading signals from the dedicated Engine CORE.
 * @param data - { symbol }
 * @returns { signals }
 */
export const getAiSignals = onCall(
  {
    region: "us-central1",
    memory: "256MiB",
    timeoutSeconds: 60,
    cpu: 0.25, // Reduced CPU to 0.25 to optimize quota usage
  },
  async (request) => {
    if (!request.auth) {
      throw new HttpsError("unauthenticated", "User must be logged in.");
    }

    const { symbol } = request.data;
    if (!symbol) {
      throw new HttpsError("invalid-argument", "Missing required field: symbol");
    }

    try {
      console.log(`🤖 Fetching AI signals for ${symbol} from Engine CORE`);

      // CORRECTED: Call the endpoint for a single symbol prediction.
      const response = await axios.post(`${ENGINE_URLS.CORE}/api/predict/${symbol}`);

      return {
        message: `Successfully fetched signals for ${symbol}`,
        signal: response.data.signal,
      };
    } catch (error: any) {
      console.error(`❌ Error fetching signals from Engine CORE:`, error);
      throw new HttpsError("internal", `Failed to get AI signals: ${error.message}`);
    }
  });

/**
 * Get Batch AI Signals from Engine CORE
 *
 * Fetches AI/ML trading signals for a list of symbols.
 * @param data - { symbols: string[] }
 * @returns { signals }
 */
export const getBatchAiSignals = onCall(
  {
    region: "us-central1",
    memory: "512MiB",
    timeoutSeconds: 180,
  },
  async (request) => {
    if (!request.auth) {
      throw new HttpsError("unauthenticated", "User must be logged in.");
    }

    const { symbols } = request.data;
    if (!symbols || !Array.isArray(symbols) || symbols.length === 0) {
      throw new HttpsError("invalid-argument", "Missing or invalid required field: symbols (must be a non-empty array)");
    }

    try {
      console.log(`🤖 Fetching batch AI signals for ${symbols.length} symbols from Engine CORE`);

      // GATEWAY PATTERN: Call Engine CORE's batch-predict endpoint
      const response = await axios.post(`${ENGINE_URLS.CORE}/api/batch-predict`, symbols);

      return {
        message: `Successfully fetched ${response.data.count} signals.`,
        signals: response.data.signals,
        count: response.data.count,
      };
    } catch (error: any) {
      console.error(`❌ Error fetching batch signals from Engine CORE:`, error);
      if (error.response) {
        console.error('Engine CORE Error Response:', error.response.data);
      }
      throw new HttpsError("internal", `Failed to get AI signals: ${error.message}`);
    }
  });

/**
 * Get Vertex AI Analysis from Engine ANALYTICS
 *
 * Relays a prompt to Engine ANALYTICS for processing with Google's Vertex AI.
 * @param data - { prompt: string, context?: any }
 * @returns { analysis }
 */
export const getVertexAiAnalysis = onCall(
  {
    region: "us-central1",
    memory: "256MiB",
    timeoutSeconds: 180, // Longer timeout for generative AI
  },
  async (request) => {
    if (!request.auth) {
      throw new HttpsError("unauthenticated", "User must be logged in.");
    }

    const { prompt, context } = request.data;
    if (!prompt) {
      throw new HttpsError("invalid-argument", "Missing required field: prompt");
    }

    try {
      console.log(`🧠 Relaying prompt to Engine ANALYTICS (Vertex AI)`);

      // GATEWAY PATTERN: Call Engine ANALYTICS's Vertex AI endpoint
      const response = await axios.post(`${ENGINE_URLS.ANALYTICS}/api/vertex/analyze`, {
        prompt,
        context: context || {},
        userId: request.auth.uid,
      }, {
        headers: { "Content-Type": "application/json" },
        timeout: 170000,
      });

      return {
        message: "Vertex AI analysis successful",
        analysis: response.data,
      };
    } catch (error: any) {
      console.error(`❌ Error fetching analysis from Engine ANALYTICS (Vertex AI):`, error);
      throw new HttpsError("internal", `Failed to get Vertex AI analysis: ${error.message}`);
    }
  }
);

/**
 * Get Gemini Analysis from Engine CORE
 *
 * Relays a prompt to Engine CORE for processing with its native Gemini models.
 * @param data - { prompt: string, context?: any }
 * @returns { analysis }
 */
export const getGeminiAnalysis = onCall(
  {
    region: "us-central1",
    memory: "256MiB",
    timeoutSeconds: 180,
    cpu: 0.25, // Reduced CPU to 0.25 to optimize quota usage
  },
  async (request) => {
    if (!request.auth) {
      throw new HttpsError("unauthenticated", "User must be logged in.");
    }

    const { prompt, context } = request.data;
    if (!prompt) {
      throw new HttpsError("invalid-argument", "Missing required field: prompt");
    }

    try {
      console.log(`🧠 Relaying prompt to Engine CORE (Gemini)`);

      // GATEWAY PATTERN: Call Engine CORE's Gemini endpoint
      const response = await axios.post(`${ENGINE_URLS.CORE}/api/gemini/analyze`, {
        prompt,
        context: context || {},
        userId: request.auth.uid,
      }, {
        headers: { "Content-Type": "application/json" },
        timeout: 170000,
      });

      return {
        message: "Gemini analysis successful",
        analysis: response.data,
      };
    } catch (error: any) {
      console.error(`❌ Error fetching analysis from Engine CORE (Gemini):`, error);
      throw new HttpsError("internal", `Failed to get Gemini analysis: ${error.message}`);
    }
  }
);

/**
 * Get Robotics ER Analysis from Engine CORE
 *
 * Relays an image and prompt to Engine CORE for processing with Gemini Robotics-ER.
 * @param data - { prompt: string, image: string (base64) }
 * @returns { analysis }
 */
export const analyzeImageWithRoboticsER = onCall(
  {
    region: "us-central1",
    memory: "512MiB", // Increased memory for image data
    timeoutSeconds: 180,
  },
  async (request) => {
    if (!request.auth) {
      throw new HttpsError("unauthenticated", "User must be logged in.");
    }

    const { prompt, image } = request.data;
    if (!prompt || !image) {
      throw new HttpsError("invalid-argument", "Missing required fields: prompt and image (base64)");
    }

    try {
      console.log(`🤖 Relaying image and prompt to Engine CORE (Robotics-ER)`);

      // GATEWAY PATTERN: Call Engine CORE's Robotics-ER endpoint
      // The image is passed as a base64 string in the JSON payload.
      const response = await axios.post(`${ENGINE_URLS.CORE}/api/robotics/analyze`, {
        prompt,
        image, // Your Python engine will decode this base64 string
        userId: request.auth.uid,
      }, {
        headers: { "Content-Type": "application/json" },
        timeout: 170000,
      });

      return {
        message: "Robotics-ER analysis successful",
        analysis: response.data,
      };
    } catch (error: any) {
      console.error(`❌ Error fetching analysis from Engine CORE (Robotics-ER):`, error);
      if (error.response) {
        console.error('Engine CORE Error Response:', error.response.data);
      }
      throw new HttpsError("internal", `Failed to get Robotics-ER analysis: ${error.message}`);
    }
  }
);

/**
 * Analyze Portfolio
 *
 * Manually trigger portfolio analysis with Gemini AI
 * @param data - { userId }
 * @returns { message, analysisId }
 */
export const analyzePortfolio = onCall(
  {
    region: "us-central1",
    memory: "256MiB",
    timeoutSeconds: 60,
    // Removed secrets configuration to avoid deployment validation issues
    // ENCRYPTION_KEY will be provided via environment variable instead
  },
  async (request) => {
    if (!request.auth) {
      throw new HttpsError("unauthenticated", "User must be logged in.");
    }

    const uid = request.auth.uid;

    try {
      // Fetch holdings from Firestore
      const holdingsSnapshot = await db
        .collection("holdings")
        .doc(uid)
        .collection("items")
        .get();

      if (holdingsSnapshot.empty) {
        throw new HttpsError(
          "failed-precondition",
          "No holdings found. Please sync your holdings first."
        );
      }

      const holdings = holdingsSnapshot.docs.map((doc) => doc.data());

      console.log(`📊 Analyzing ${holdings.length} holdings for user: ${uid}`);

      // Create analysis document in 'generate' collection
      const analysisRef = await db.collection("generate").add({
        prompt: `Analyze the following portfolio holdings for Indian markets:

${JSON.stringify(holdings, null, 2)}

Please provide:
1. Overall portfolio health assessment
2. Sector-wise exposure analysis
3. Risk assessment (concentration risk, sector risk)
4. Top performing and underperforming stocks
5. Recommended actions (hold/sell/rebalance)
6. Current market trends affecting these holdings

Be specific and actionable. Focus on Indian market context (NIFTY, BANKNIFTY, sectoral indices).`,
        model: "gemini-1.5-flash-latest", // Using a standard, current model name
        userId: uid,
        analysisType: "portfolio",
        holdingsCount: holdings.length,
        createTime: admin.firestore.FieldValue.serverTimestamp(),
      });

      console.log(`✅ Portfolio analysis triggered: ${analysisRef.id}`);

      return {
        message: "Portfolio analysis initiated. Check Gemini Insights for results.",
        analysisId: analysisRef.id,
      };
    } catch (error: any) {
      console.error("❌ Error analyzing portfolio:", error);

      if (error instanceof HttpsError) {
        throw error;
      }

      throw new HttpsError("internal", `Failed to analyze portfolio: ${error.message}`);
    }
  }
);

/**
 * Firestore Trigger: Auto-analyze when holdings are updated
 *
 * Listens to holdings/{userId} updates and triggers Gemini analysis
 */
export const onHoldingsUpdate = onDocumentWritten(
  {
    document: "holdings/{userId}",
    region: "us-central1",
    memory: "256MiB",
  },
  async (event) => {
    const userId = event.params.userId;
    const afterData = event.data?.after?.data();

    // Only trigger if document was updated (not deleted)
    if (!afterData) {
      console.log(`⏭️ Holdings deleted for user ${userId}, skipping analysis`);
      return;
    }

    console.log(`🔔 Holdings updated for user: ${userId}, triggering auto-analysis`);

    try {
      // Fetch individual holdings
      const holdingsSnapshot = await db
        .collection("holdings")
        .doc(userId)
        .collection("items")
        .get();

      if (holdingsSnapshot.empty) {
        console.log(`⚠️ No individual holdings found for user: ${userId}`);
        return;
      }

      const holdings = holdingsSnapshot.docs.map((doc) => doc.data());

      await triggerHoldingsAnalysis(userId, holdings);

      console.log(`✅ Auto-analysis triggered for user: ${userId}`);
    } catch (error) {
      console.error(`❌ Failed to trigger auto-analysis for user ${userId}:`, error);
      // Don't throw - this is a background trigger
    }
  }
);

/**
 * Helper: Trigger Gemini analysis for holdings
 */
async function triggerHoldingsAnalysis(userId: string, holdings: any[]): Promise<void> {
  try {
    const holdingsSummary = holdings.map((h) => ({
      symbol: h.tradingSymbol,
      qty: h.totalQty,
      avgPrice: h.avgCostPrice,
      currentPrice: h.currentMarketPrice,
      pnl: h.pnl,
      pnlPercent: h.pnlPercentage,
    }));

    await db.collection("generate").add({
      prompt: `Portfolio Update Analysis for ${holdings.length} holdings:

${JSON.stringify(holdingsSummary, null, 2)}

Provide:
1. Quick portfolio health check
2. Any immediate alerts (stocks down >5%, high volatility)
3. Market sentiment affecting these positions
4. Quick action items

Keep it concise (max 200 words).`,
      model: "gemini-1.5-flash-latest", // Using a standard, current model name
      userId,
      analysisType: "auto-holdings-update",
      holdingsCount: holdings.length,
      createTime: admin.firestore.FieldValue.serverTimestamp(),
    });

    console.log(`✅ Holdings analysis triggered for user: ${userId}`);
  } catch (error) {
    console.error("❌ Failed to trigger holdings analysis:", error);
    throw error;
  }
}

/**
 * Get Dhan Account Overview from Engine ANALYTICS
 *
 * Fetches a consolidated overview of the user's Dhan account, including
 * funds, holdings, positions, and profile information.
 * @returns { overview }
 */
export const getDhanOverview = onCall(
  {
    region: "us-central1",
    memory: "512MiB",
    timeoutSeconds: 120,
    // Removed secrets configuration to avoid deployment validation issues
    // ENCRYPTION_KEY will be provided via environment variable instead
  },
  async (request) => {
    if (!request.auth) {
      throw new HttpsError("unauthenticated", "User must be logged in.");
    }

    const uid = request.auth.uid;

    try {
      console.log(`📋 Fetching Dhan overview for user ${uid} from Engine ANALYTICS`);

      // This endpoint in Engine ANALYTICS will need the user's credentials.
      // We assume Engine ANALYTICS's /api/dhan/overview is a POST endpoint that accepts credentials.
      // If it's a GET, the credentials would need to be passed in headers.
      const { clientId, accessToken } = await getDecryptedCredentials(uid);

      if (!accessToken) {
        throw new HttpsError("failed-precondition", "Dhan access token is required for this operation.");
      }

      // Pass credentials securely in headers, which is a more standard practice.
      const response = await axios.get(`${ENGINE_URLS.ANALYTICS}/api/dhan/overview`, {
        headers: {
          "x-client-id": clientId,
          "Authorization": `Bearer ${accessToken}`
        }
      });

      return response.data;
    } catch (error: any) {
      console.error(`❌ Error fetching Dhan overview from Engine ANALYTICS:`, error);
      throw new HttpsError("internal", `Failed to get Dhan overview: ${error.message}`);
    }
  }
);

/**
 * Get Dhan Callback URLs from Engine ANALYTICS
 *
 * Fetches the configured Redirect and Postback URLs that users need
 * to set up their own Dhan developer applications.
 * @returns { redirect_url: string, postback_url: string }
 */
export const getDhanCallbackUrls = onCall(
  {
    region: "us-central1",
    memory: "256MiB",
    timeoutSeconds: 30,
  },
  async (request) => {
    // This is public information, but we can still require authentication
    // to prevent abuse.
    if (!request.auth) {
      throw new HttpsError("unauthenticated", "User must be logged in.");
    }

    try {
      console.log(`🔗 Fetching Dhan callback URLs from Engine ANALYTICS`);
      // Fetch URLs from Engine ANALYTICS, which is the authority for trading OAuth.
      const response = await axios.get(`${ENGINE_URLS.ANALYTICS}/api/dhan/callback-urls`);
      return response.data;
    } catch (error: any) {
      console.error(`❌ Error fetching Dhan callback URLs:`, error);
      throw new HttpsError("internal", `Failed to get Dhan callback URLs: ${error.message}`);
    }
  }
);

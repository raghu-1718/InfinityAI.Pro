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
    secrets: ["ENCRYPTION_KEY"],
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

      // Fetch holdings from Dhan API
      const response = await axios.get("https://api.dhan.co/v2/holdings", {
        headers: {
          "access-token": credentials.accessToken,
          "client-id": credentials.clientId,
        },
        timeout: 30000,
      });

      const holdings: DhanHolding[] = response.data.data || [];

      console.log(`✅ Retrieved ${holdings.length} holdings from Dhan API`);

      // Store holdings in Firestore
      const batch = db.batch();
      const holdingsRef = db.collection("holdings").doc(uid);

      // Update main holdings document
      batch.set(holdingsRef, {
        userId: uid,
        totalHoldings: holdings.length,
        lastSyncedAt: admin.firestore.FieldValue.serverTimestamp(),
        updatedAt: admin.firestore.FieldValue.serverTimestamp(),
      }, { merge: true });

      // Store individual holdings
      holdings.forEach((holding) => {
        const holdingDocRef = db
          .collection("holdings")
          .doc(uid)
          .collection("items")
          .doc(holding.securityId);

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

      if (error.response?.status === 401) {
        throw new HttpsError("unauthenticated", "Invalid or expired Dhan access token");
      }

      throw new HttpsError("internal", `Failed to sync holdings: ${error.message}`);
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
    secrets: ["ENCRYPTION_KEY"],
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
        model: "gemini-2.0-flash",
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
      model: "gemini-2.0-flash",
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

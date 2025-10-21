"use strict";
/**
 * Portfolio Analysis Functions
 *
 * Syncs holdings from Dhan API and triggers AI analysis
 * Firestore trigger: Automatically analyzes when holdings are updated
 */
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.onHoldingsUpdate = exports.analyzePortfolio = exports.syncHoldings = void 0;
const https_1 = require("firebase-functions/v2/https");
const firestore_1 = require("firebase-functions/v2/firestore");
const admin = __importStar(require("firebase-admin"));
const axios_1 = __importDefault(require("axios"));
const storeCredentials_1 = require("./storeCredentials");
const db = admin.firestore();
/**
 * Sync Holdings from Dhan API
 *
 * Fetches current holdings and stores them in Firestore
 * @param data - { userId }
 * @returns { message, holdings, count }
 */
exports.syncHoldings = (0, https_1.onCall)({
    region: "us-central1",
    memory: "512MiB",
    timeoutSeconds: 120,
    secrets: ["ENCRYPTION_KEY"],
}, async (request) => {
    var _a;
    if (!request.auth) {
        throw new https_1.HttpsError("unauthenticated", "User must be logged in.");
    }
    const uid = request.auth.uid;
    try {
        // Get decrypted Dhan credentials
        const credentials = await (0, storeCredentials_1.getDecryptedCredentials)(uid);
        if (!credentials.accessToken) {
            throw new https_1.HttpsError("failed-precondition", "Access token required. Please update your credentials.");
        }
        console.log(`📊 Fetching holdings for user: ${uid}`);
        // Fetch holdings from Dhan API
        const response = await axios_1.default.get("https://api.dhan.co/v2/holdings", {
            headers: {
                "access-token": credentials.accessToken,
                "client-id": credentials.clientId,
            },
            timeout: 30000,
        });
        const holdings = response.data.data || [];
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
            batch.set(holdingDocRef, Object.assign(Object.assign({}, holding), { syncedAt: admin.firestore.FieldValue.serverTimestamp() }));
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
    }
    catch (error) {
        console.error("❌ Error syncing holdings:", error);
        if (((_a = error.response) === null || _a === void 0 ? void 0 : _a.status) === 401) {
            throw new https_1.HttpsError("unauthenticated", "Invalid or expired Dhan access token");
        }
        throw new https_1.HttpsError("internal", `Failed to sync holdings: ${error.message}`);
    }
});
/**
 * Analyze Portfolio
 *
 * Manually trigger portfolio analysis with Gemini AI
 * @param data - { userId }
 * @returns { message, analysisId }
 */
exports.analyzePortfolio = (0, https_1.onCall)({
    region: "us-central1",
    memory: "256MiB",
    timeoutSeconds: 60,
    secrets: ["ENCRYPTION_KEY"],
}, async (request) => {
    if (!request.auth) {
        throw new https_1.HttpsError("unauthenticated", "User must be logged in.");
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
            throw new https_1.HttpsError("failed-precondition", "No holdings found. Please sync your holdings first.");
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
    }
    catch (error) {
        console.error("❌ Error analyzing portfolio:", error);
        if (error instanceof https_1.HttpsError) {
            throw error;
        }
        throw new https_1.HttpsError("internal", `Failed to analyze portfolio: ${error.message}`);
    }
});
/**
 * Firestore Trigger: Auto-analyze when holdings are updated
 *
 * Listens to holdings/{userId} updates and triggers Gemini analysis
 */
exports.onHoldingsUpdate = (0, firestore_1.onDocumentWritten)({
    document: "holdings/{userId}",
    region: "us-central1",
    memory: "256MiB",
}, async (event) => {
    var _a, _b;
    const userId = event.params.userId;
    const afterData = (_b = (_a = event.data) === null || _a === void 0 ? void 0 : _a.after) === null || _b === void 0 ? void 0 : _b.data();
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
    }
    catch (error) {
        console.error(`❌ Failed to trigger auto-analysis for user ${userId}:`, error);
        // Don't throw - this is a background trigger
    }
});
/**
 * Helper: Trigger Gemini analysis for holdings
 */
async function triggerHoldingsAnalysis(userId, holdings) {
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
    }
    catch (error) {
        console.error("❌ Failed to trigger holdings analysis:", error);
        throw error;
    }
}
//# sourceMappingURL=analyzePortfolio.js.map
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
exports.getDhanCallbackUrls = exports.getDhanOverview = exports.onHoldingsUpdate = exports.analyzePortfolio = exports.getEngineBStatus = exports.analyzeImageWithRoboticsER = exports.getGeminiAnalysis = exports.getVertexAiAnalysis = exports.getBatchAiSignals = exports.getAiSignals = exports.syncHoldings = void 0;
const https_1 = require("firebase-functions/v2/https");
const firestore_1 = require("firebase-functions/v2/firestore");
const admin = __importStar(require("firebase-admin"));
const axios_1 = __importDefault(require("axios"));
const storeCredentials_1 = require("./storeCredentials");
const config_1 = require("./config");
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
    // ENCRYPTION_KEY will be provided via environment variable instead
}, async (request) => {
    var _a, _b, _c;
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
        // ARCHITECTURE FIX: Point to Engine A, the data hub, not Engine C.
        // The Cloud Function securely provides the credentials to the trusted engine.
        // We will use the more efficient `overview` endpoint which includes holdings.
        const response = await axios_1.default.get(`${config_1.ENGINE_URLS.A}/api/dhan/overview`, {
            headers: {
                "x-client-id": credentials.clientId,
                "Authorization": `Bearer ${credentials.accessToken}`
            },
            timeout: 30000,
        });
        // The overview endpoint in Engine A returns holdings in a `holdings` field.
        const holdings = response.data.holdings || [];
        console.log(`✅ Retrieved ${holdings.length} holdings from Dhan API`);
        const userHoldingsRef = db.collection("holdings").doc(uid);
        const itemsCollectionRef = userHoldingsRef.collection("items");
        // 1. Clear out old holdings to prevent stale data
        const oldHoldingsSnapshot = await itemsCollectionRef.get();
        if (!oldHoldingsSnapshot.empty) {
            console.log(`🗑️ Deleting ${oldHoldingsSnapshot.size} old holding items...`);
            // Handle batching for > 500 deletes
            const deletePromises = [];
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
        if (((_a = error.response) === null || _a === void 0 ? void 0 : _a.status) === 401 || ((_c = (_b = error.response) === null || _b === void 0 ? void 0 : _b.data) === null || _c === void 0 ? void 0 : _c.code) === "UNAUTHENTICATED") {
            throw new https_1.HttpsError("unauthenticated", "Invalid or expired Dhan access token");
        }
        throw new https_1.HttpsError("internal", `Failed to sync holdings: ${error.message}`);
    }
});
/**
 * Get AI Signals from Engine B
 *
 * Fetches AI/ML trading signals from the dedicated Engine B.
 * @param data - { symbol }
 * @returns { signals }
 */
exports.getAiSignals = (0, https_1.onCall)({
    region: "us-central1",
    memory: "256MiB",
    timeoutSeconds: 60,
}, async (request) => {
    if (!request.auth) {
        throw new https_1.HttpsError("unauthenticated", "User must be logged in.");
    }
    const { symbol } = request.data;
    if (!symbol) {
        throw new https_1.HttpsError("invalid-argument", "Missing required field: symbol");
    }
    try {
        console.log(`🤖 Fetching AI signals for ${symbol} from Engine B`);
        // CORRECTED: Call the endpoint for a single symbol prediction.
        const response = await axios_1.default.post(`${config_1.ENGINE_URLS.B}/api/predict/${symbol}`);
        return {
            message: `Successfully fetched signals for ${symbol}`,
            signal: response.data.signal,
        };
    }
    catch (error) {
        console.error(`❌ Error fetching signals from Engine B:`, error);
        throw new https_1.HttpsError("internal", `Failed to get AI signals: ${error.message}`);
    }
});
/**
 * Get Batch AI Signals from Engine B
 *
 * Fetches AI/ML trading signals for a list of symbols.
 * @param data - { symbols: string[] }
 * @returns { signals }
 */
exports.getBatchAiSignals = (0, https_1.onCall)({
    region: "us-central1",
    memory: "512MiB",
    timeoutSeconds: 180,
}, async (request) => {
    if (!request.auth) {
        throw new https_1.HttpsError("unauthenticated", "User must be logged in.");
    }
    const { symbols } = request.data;
    if (!symbols || !Array.isArray(symbols) || symbols.length === 0) {
        throw new https_1.HttpsError("invalid-argument", "Missing or invalid required field: symbols (must be a non-empty array)");
    }
    try {
        console.log(`🤖 Fetching batch AI signals for ${symbols.length} symbols from Engine B`);
        // GATEWAY PATTERN: Call Engine B's batch-predict endpoint
        const response = await axios_1.default.post(`${config_1.ENGINE_URLS.B}/api/batch-predict`, symbols);
        return {
            message: `Successfully fetched ${response.data.count} signals.`,
            signals: response.data.signals,
            count: response.data.count,
        };
    }
    catch (error) {
        console.error(`❌ Error fetching batch signals from Engine B:`, error);
        if (error.response) {
            console.error('Engine B Error Response:', error.response.data);
        }
        throw new https_1.HttpsError("internal", `Failed to get AI signals: ${error.message}`);
    }
});
/**
 * Get Vertex AI Analysis from Engine A
 *
 * Relays a prompt to Engine A for processing with Google's Vertex AI.
 * @param data - { prompt: string, context?: any }
 * @returns { analysis }
 */
exports.getVertexAiAnalysis = (0, https_1.onCall)({
    region: "us-central1",
    memory: "256MiB",
    timeoutSeconds: 180, // Longer timeout for generative AI
}, async (request) => {
    if (!request.auth) {
        throw new https_1.HttpsError("unauthenticated", "User must be logged in.");
    }
    const { prompt, context } = request.data;
    if (!prompt) {
        throw new https_1.HttpsError("invalid-argument", "Missing required field: prompt");
    }
    try {
        console.log(`🧠 Relaying prompt to Engine A (Vertex AI)`);
        // GATEWAY PATTERN: Call Engine A's Vertex AI endpoint
        const response = await axios_1.default.post(`${config_1.ENGINE_URLS.A}/api/vertex/analyze`, {
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
    }
    catch (error) {
        console.error(`❌ Error fetching analysis from Engine A (Vertex AI):`, error);
        throw new https_1.HttpsError("internal", `Failed to get Vertex AI analysis: ${error.message}`);
    }
});
/**
 * Get Gemini Analysis from Engine B
 *
 * Relays a prompt to Engine B for processing with its native Gemini models.
 * @param data - { prompt: string, context?: any }
 * @returns { analysis }
 */
exports.getGeminiAnalysis = (0, https_1.onCall)({
    region: "us-central1",
    memory: "256MiB",
    timeoutSeconds: 180,
}, async (request) => {
    if (!request.auth) {
        throw new https_1.HttpsError("unauthenticated", "User must be logged in.");
    }
    const { prompt, context } = request.data;
    if (!prompt) {
        throw new https_1.HttpsError("invalid-argument", "Missing required field: prompt");
    }
    try {
        console.log(`🧠 Relaying prompt to Engine B (Gemini)`);
        // GATEWAY PATTERN: Call Engine B's Gemini endpoint
        const response = await axios_1.default.post(`${config_1.ENGINE_URLS.B}/api/gemini/analyze`, {
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
    }
    catch (error) {
        console.error(`❌ Error fetching analysis from Engine B (Gemini):`, error);
        throw new https_1.HttpsError("internal", `Failed to get Gemini analysis: ${error.message}`);
    }
});
/**
 * Get Robotics ER Analysis from Engine B
 *
 * Relays an image and prompt to Engine B for processing with Gemini Robotics-ER.
 * @param data - { prompt: string, image: string (base64) }
 * @returns { analysis }
 */
exports.analyzeImageWithRoboticsER = (0, https_1.onCall)({
    region: "us-central1",
    memory: "512MiB", // Increased memory for image data
    timeoutSeconds: 180,
}, async (request) => {
    if (!request.auth) {
        throw new https_1.HttpsError("unauthenticated", "User must be logged in.");
    }
    const { prompt, image } = request.data;
    if (!prompt || !image) {
        throw new https_1.HttpsError("invalid-argument", "Missing required fields: prompt and image (base64)");
    }
    try {
        console.log(`🤖 Relaying image and prompt to Engine B (Robotics-ER)`);
        // GATEWAY PATTERN: Call Engine B's Robotics-ER endpoint
        // The image is passed as a base64 string in the JSON payload.
        const response = await axios_1.default.post(`${config_1.ENGINE_URLS.B}/api/robotics/analyze`, {
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
    }
    catch (error) {
        console.error(`❌ Error fetching analysis from Engine B (Robotics-ER):`, error);
        if (error.response) {
            console.error('Engine B Error Response:', error.response.data);
        }
        throw new https_1.HttpsError("internal", `Failed to get Robotics-ER analysis: ${error.message}`);
    }
});
/**
 * Get Engine B Model Status
 *
 * Fetches the operational status of the AI models inside Engine B.
 * @returns { status }
 */
exports.getEngineBStatus = (0, https_1.onCall)({
    region: "us-central1",
    memory: "256MiB",
    timeoutSeconds: 30,
}, async (request) => {
    // Optional: Add admin-only authentication here
    if (!request.auth) {
        throw new https_1.HttpsError("unauthenticated", "User must be logged in.");
    }
    try {
        console.log(`🩺 Fetching model status from Engine B`);
        const response = await axios_1.default.get(`${config_1.ENGINE_URLS.B}/api/models/status`);
        return response.data;
    }
    catch (error) {
        console.error(`❌ Error fetching status from Engine B:`, error);
        throw new https_1.HttpsError("internal", `Failed to get Engine B status: ${error.message}`);
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
    // Removed secrets configuration to avoid deployment validation issues
    // ENCRYPTION_KEY will be provided via environment variable instead
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
            model: "gemini-1.5-flash-latest", // Using a standard, current model name
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
/**
 * Get Dhan Account Overview from Engine A
 *
 * Fetches a consolidated overview of the user's Dhan account, including
 * funds, holdings, positions, and profile information.
 * @returns { overview }
 */
exports.getDhanOverview = (0, https_1.onCall)({
    region: "us-central1",
    memory: "512MiB",
    timeoutSeconds: 120,
    // Removed secrets configuration to avoid deployment validation issues
    // ENCRYPTION_KEY will be provided via environment variable instead
}, async (request) => {
    if (!request.auth) {
        throw new https_1.HttpsError("unauthenticated", "User must be logged in.");
    }
    const uid = request.auth.uid;
    try {
        console.log(`📋 Fetching Dhan overview for user ${uid} from Engine A`);
        // This endpoint in Engine A will need the user's credentials.
        // We assume Engine A's /api/dhan/overview is a POST endpoint that accepts credentials.
        // If it's a GET, the credentials would need to be passed in headers.
        const { clientId, accessToken } = await (0, storeCredentials_1.getDecryptedCredentials)(uid);
        if (!accessToken) {
            throw new https_1.HttpsError("failed-precondition", "Dhan access token is required for this operation.");
        }
        // Pass credentials securely in headers, which is a more standard practice.
        const response = await axios_1.default.get(`${config_1.ENGINE_URLS.A}/api/dhan/overview`, {
            headers: {
                "x-client-id": clientId,
                "Authorization": `Bearer ${accessToken}`
            }
        });
        return response.data;
    }
    catch (error) {
        console.error(`❌ Error fetching Dhan overview from Engine A:`, error);
        throw new https_1.HttpsError("internal", `Failed to get Dhan overview: ${error.message}`);
    }
});
/**
 * Get Dhan Callback URLs from Engine A
 *
 * Fetches the configured Redirect and Postback URLs that users need
 * to set up their own Dhan developer applications.
 * @returns { redirect_url: string, postback_url: string }
 */
exports.getDhanCallbackUrls = (0, https_1.onCall)({
    region: "us-central1",
    memory: "256MiB",
    timeoutSeconds: 30,
}, async (request) => {
    // This is public information, but we can still require authentication
    // to prevent abuse.
    if (!request.auth) {
        throw new https_1.HttpsError("unauthenticated", "User must be logged in.");
    }
    try {
        console.log(`🔗 Fetching Dhan callback URLs from Engine C`);
        // Fetch URLs from Engine C, which is the authority for trading OAuth.
        const response = await axios_1.default.get(`${config_1.ENGINE_URLS.C}/api/dhan/callback-urls`);
        return response.data;
    }
    catch (error) {
        console.error(`❌ Error fetching Dhan callback URLs:`, error);
        throw new https_1.HttpsError("internal", `Failed to get Dhan callback URLs: ${error.message}`);
    }
});
//# sourceMappingURL=analyzePortfolio.js.map
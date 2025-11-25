"use strict";
/**
 * Start Trading Function
 *
 * Initiates a trading session by calling Engine C execution service
 * Creates session document in Firestore and triggers portfolio analysis
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
exports.stopTrading = exports.startTrading = void 0;
const https_1 = require("firebase-functions/v2/https");
const admin = __importStar(require("firebase-admin"));
const axios_1 = __importDefault(require("axios"));
const storeCredentials_1 = require("./storeCredentials");
const config_1 = require("./config");
const db = admin.firestore();
/**
 * Start Trading Session
 *
 * @param data - { userId, strategy, amount, risk }
 * @returns { message, sessionId, status }
 */
exports.startTrading = (0, https_1.onCall)({
    region: "us-central1",
    memory: "512MiB",
    timeoutSeconds: 120,
    // Removed secrets configuration to avoid deployment validation issues
    // ENCRYPTION_KEY will be provided via environment variable instead
}, async (request) => {
    // Verify authentication
    if (!request.auth) {
        throw new https_1.HttpsError("unauthenticated", "User must be logged in to start trading.");
    }
    const uid = request.auth.uid;
    const { strategy, amount, risk } = request.data;
    // Validate inputs
    if (!strategy || !amount || !risk) {
        throw new https_1.HttpsError("invalid-argument", "Missing required fields: strategy, amount, or risk");
    }
    const amountNum = parseFloat(amount);
    const riskNum = parseFloat(risk);
    if (isNaN(amountNum) || amountNum < 1000) {
        throw new https_1.HttpsError("invalid-argument", "Amount must be at least ₹1,000");
    }
    if (isNaN(riskNum) || riskNum < 1 || riskNum > 20) {
        throw new https_1.HttpsError("invalid-argument", "Risk must be between 1% and 20%");
    }
    if (!["equities", "options", "mcx"].includes(strategy)) {
        throw new https_1.HttpsError("invalid-argument", "Invalid strategy. Must be: equities, options, or mcx");
    }
    try {
        // Retrieve user's Dhan credentials
        const credentials = await (0, storeCredentials_1.getDecryptedCredentials)(uid);
        if (!credentials.accessToken) {
            throw new https_1.HttpsError("failed-precondition", "Access token not found. Please update your Dhan credentials with an access token.");
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
            // 1. Get a real-time signal from Engine B first
            console.log(`🤖 Requesting initial signal from Engine B for strategy: ${strategy}`);
            // We need a representative symbol for the strategy to get a signal
            const representativeSymbol = strategy === "mcx" ? "CRUDEOIL" : "NIFTY";
            const signalResponse = await axios_1.default.post(`${config_1.ENGINE_URLS.CORE}/api/predict/${representativeSymbol}`);
            const aiSignal = signalResponse.data.signal;
            if (!aiSignal || !aiSignal.signal_type || aiSignal.signal_type === "HOLD") {
                throw new https_1.HttpsError("aborted", "AI signal is HOLD or unavailable. No trade initiated.");
            }
            console.log(`👍 Received initial signal: ${aiSignal.signal_type} ${aiSignal.symbol}`);
            // This payload should match the `/api/orders/place` endpoint in Engine C
            const enginePayload = {
                // 2. Use the AI signal to construct the trade order
                symbol: aiSignal.symbol,
                quantity: 1, // Simplified quantity, should be based on risk/amount
                strategy,
                order_type: "MARKET",
                transaction_type: aiSignal.signal_type, // Use the signal from Engine B
                price: 0, // Market order
                demo: false, // For live trading
            };
            const engineResponse = await axios_1.default.post(`${config_1.ENGINE_URLS.EXECUTION}/api/orders/place`, enginePayload, {
                headers: {
                    "Content-Type": "application/json",
                },
                timeout: 30000, // 30 seconds
            });
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
        }
        catch (engineError) {
            console.error("❌ Engine C execution error:", engineError.message);
            // Update session status to failed
            await db.collection("trading_sessions").doc(sessionId).update({
                status: "FAILED",
                error: engineError.message,
                lastUpdatedAt: admin.firestore.FieldValue.serverTimestamp(),
            });
            throw new https_1.HttpsError("internal", `Failed to start trading on Engine C: ${engineError.message}`);
        }
    }
    catch (error) {
        console.error("❌ Error starting trading session:", error);
        if (error instanceof https_1.HttpsError) {
            throw error;
        }
        throw new https_1.HttpsError("internal", `Failed to start trading: ${error.message}`);
    }
});
/**
 * Stop Trading Session
 *
 * @param data - { sessionId }
 * @returns { message, status }
 */
exports.stopTrading = (0, https_1.onCall)({
    region: "us-central1",
    memory: "256MiB",
    timeoutSeconds: 60,
    cpu: 0.25, // Reduced CPU to 0.25 to optimize quota usage
    // Removed secrets configuration to avoid deployment validation issues
    // ENCRYPTION_KEY will be provided via environment variable instead
}, async (request) => {
    if (!request.auth) {
        throw new https_1.HttpsError("unauthenticated", "User must be logged in.");
    }
    const { sessionId } = request.data;
    if (!sessionId) {
        throw new https_1.HttpsError("invalid-argument", "Missing sessionId");
    }
    try {
        const sessionDoc = await db.collection("trading_sessions").doc(sessionId).get();
        if (!sessionDoc.exists) {
            throw new https_1.HttpsError("not-found", "Trading session not found");
        }
        const sessionData = sessionDoc.data();
        // Verify ownership
        if (sessionData.userId !== request.auth.uid) {
            throw new https_1.HttpsError("permission-denied", "You don't have permission to stop this session");
        }
        // Call Engine C to stop execution
        try {
            await axios_1.default.post(`${config_1.ENGINE_URLS.EXECUTION}/stop`, { sessionId }, {
                headers: { "Content-Type": "application/json" },
                timeout: 10000,
            });
        }
        catch (stopError) {
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
    }
    catch (error) {
        console.error("❌ Error stopping trading session:", error);
        throw new https_1.HttpsError("internal", `Failed to stop trading: ${error.message}`);
    }
});
/**
 * Helper: Trigger portfolio analysis via Gemini
 */
async function triggerPortfolioAnalysis(userId, sessionId) {
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
            model: "gemini-1.5-flash-latest", // Using a standard, current model name
            userId,
            sessionId,
            createTime: admin.firestore.FieldValue.serverTimestamp(),
        });
        console.log(`✅ Gemini analysis triggered for session: ${sessionId}`);
    }
    catch (error) {
        console.warn("⚠️ Failed to trigger Gemini analysis:", error);
        // Don't fail the main request if analysis fails
    }
}
//# sourceMappingURL=startTrading.js.map
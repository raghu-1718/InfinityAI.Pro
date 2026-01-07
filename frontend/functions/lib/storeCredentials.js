"use strict";
/**
 * Store Credentials Functions
 *
 * Securely stores Dhan API credentials with AES-256-GCM encryption
 * Credentials are encrypted before being written to Firestore
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
exports.saveDhanCredentials = exports.submitDhanCredentialsV2 = exports.ENCRYPTION_KEY = void 0;
exports.getDecryptedCredentials = getDecryptedCredentials;
const https_1 = require("firebase-functions/v2/https");
const admin = __importStar(require("firebase-admin"));
const crypto = __importStar(require("crypto"));
const axios_1 = __importDefault(require("axios"));
const db = admin.firestore();
const params_1 = require("firebase-functions/params");
// Encryption configuration - Using environment variable for better compatibility
exports.ENCRYPTION_KEY = (0, params_1.defineSecret)("ENCRYPTION_KEY");
const PROJECT_ID = process.env.GCP_PROJECT ||
    process.env.GCLOUD_PROJECT ||
    process.env.GOOGLE_CLOUD_PROJECT;
const ALGORITHM = "aes-256-gcm";
const USE_SECRET_MANAGER = false;
/**
 * Encrypts sensitive data using AES-256-GCM
 */
function encrypt(text) {
    const keyHex = exports.ENCRYPTION_KEY.value();
    if (!keyHex) {
        throw new Error("ENCRYPTION_KEY not configured via params API");
    }
    const iv = crypto.randomBytes(12);
    const key = Buffer.from(keyHex, "hex");
    const cipher = crypto.createCipheriv(ALGORITHM, key, iv);
    let encrypted = cipher.update(text, "utf8", "hex");
    encrypted += cipher.final("hex");
    const authTag = cipher.getAuthTag().toString("hex");
    return `${iv.toString("hex")}:${authTag}:${encrypted}`;
}
/**
 * Decrypts encrypted data
 */
function decrypt(encryptedData) {
    const keyHex = exports.ENCRYPTION_KEY.value();
    if (!keyHex) {
        throw new Error("ENCRYPTION_KEY not configured via params API");
    }
    const parts = encryptedData.split(":");
    if (parts.length !== 3) {
        throw new Error("Invalid encrypted data format");
    }
    const [ivHex, authTagHex, encryptedText] = parts;
    const iv = Buffer.from(ivHex, "hex");
    const authTag = Buffer.from(authTagHex, "hex");
    const key = Buffer.from(keyHex, "hex");
    const decipher = crypto.createDecipheriv(ALGORITHM, key, iv);
    decipher.setAuthTag(authTag);
    let decrypted = decipher.update(encryptedText, "hex", "utf8");
    decrypted += decipher.final("utf8");
    return decrypted;
}
/**
 * V2 Cloud Function: Save Dhan API Credentials
 *
 * @param data - { userId, clientId, apiKey, apiSecret, accessToken? }
 * @returns { message, status }
 */
exports.submitDhanCredentialsV2 = (0, https_1.onCall)({
    region: "us-central1",
    memory: "256MiB",
    timeoutSeconds: 60,
    // Removed secrets configuration to avoid deployment validation issues
    // ENCRYPTION_KEY will be provided via params API
}, async (request) => {
    // Verify authentication
    if (!request.auth) {
        throw new https_1.HttpsError("unauthenticated", "User must be logged in to save credentials.");
    }
    const uid = request.auth.uid;
    const { clientId, apiKey, apiSecret, accessToken } = request.data;
    // Validate required fields
    if (!clientId || !apiKey || !apiSecret) {
        throw new https_1.HttpsError("invalid-argument", "Missing required fields: clientId, apiKey, or apiSecret");
    }
    try {
        // Encrypt sensitive credentials
        const encryptedData = {
            clientId: encrypt(clientId),
            apiKey: encrypt(apiKey),
            apiSecret: encrypt(apiSecret),
            accessToken: accessToken ? encrypt(accessToken) : null,
            userId: uid,
            lastUpdatedAt: admin.firestore.FieldValue.serverTimestamp(),
            createdAt: admin.firestore.FieldValue.serverTimestamp(),
        };
        // Store in Firestore
        await db
            .collection("dhan_credentials")
            .doc(uid)
            .set(encryptedData, { merge: true });
        // Update User Profile to reflect connection status
        await db.collection("users").doc(uid).set({
            dhanConnected: true,
            dhanClientId: clientId,
            lastUpdatedAt: admin.firestore.FieldValue.serverTimestamp(),
        }, { merge: true });
        // Optionally store secrets in Secret Manager for system-level access
        if (USE_SECRET_MANAGER && PROJECT_ID) {
            let secretClient = null;
            try {
                const sm = await Promise.resolve().then(() => __importStar(require("@google-cloud/secret-manager")));
                secretClient = new sm.SecretManagerServiceClient();
            }
            catch (e) {
                console.warn("⚠️ Secret Manager client not available at runtime:", (e === null || e === void 0 ? void 0 : e.message) || e);
            }
            if (secretClient) {
                const makeSecret = async (id, value) => {
                    if (!value)
                        return;
                    const secretId = `dhan_${uid}_${id}`;
                    const parent = `projects/${PROJECT_ID}`;
                    try {
                        // Create secret if not exists (idempotent)
                        try {
                            await secretClient.createSecret({
                                parent,
                                secretId,
                                secret: { replication: { automatic: {} } },
                            });
                            console.log(`🔐 Created secret ${secretId}`);
                        }
                        catch (e) {
                            // If already exists, ignore
                            if (!/already exists/.test(String(e.message))) {
                                console.warn(`Could not create secret ${secretId}: ${e.message}`);
                            }
                        }
                        // Add a new secret version
                        const secretName = `projects/${PROJECT_ID}/secrets/${secretId}`;
                        await secretClient.addSecretVersion({
                            parent: secretName,
                            payload: { data: Buffer.from(value, "utf8") },
                        });
                        console.log(`🔐 Added secret version for ${secretId}`);
                    }
                    catch (err) {
                        console.warn(`⚠️ Failed to write secret ${secretId}: ${err.message}`);
                    }
                };
                // write each secret value
                await makeSecret("client_id", clientId);
                await makeSecret("api_key", apiKey);
                await makeSecret("api_secret", apiSecret);
                if (accessToken)
                    await makeSecret("access_token", accessToken);
            }
        }
        console.log(`✅ Credentials saved for user: ${uid}`);
        // Optionally verify credentials with Dhan API
        if (accessToken) {
            try {
                const verifyResponse = await axios_1.default.get("https://api.dhan.co/v2/holdings", {
                    headers: {
                        "access-token": accessToken,
                        "client-id": clientId,
                    },
                    timeout: 5000,
                });
                if (verifyResponse.status === 200) {
                    console.log(`✅ Dhan API credentials verified for user: ${uid}`);
                }
            }
            catch (verifyError) {
                console.warn(`⚠️ Failed to verify Dhan credentials: ${verifyError.message}`);
                // Don't fail the entire request if verification fails
            }
        }
        return {
            message: "Credentials saved successfully and encrypted securely.",
            status: "success",
        };
    }
    catch (error) {
        console.error("❌ Error saving credentials:", error);
        throw new https_1.HttpsError("internal", `Failed to save credentials: ${error.message}`);
    }
});
/**
 * Alternative function name for backward compatibility
 */
exports.saveDhanCredentials = exports.submitDhanCredentialsV2;
/**
 * Helper function to retrieve and decrypt credentials
 * Used by other functions that need Dhan API access
 */
async function getDecryptedCredentials(userId) {
    // If using Secret Manager, prefer reading per-user secrets there
    if (USE_SECRET_MANAGER && PROJECT_ID) {
        try {
            let secretClient = null;
            try {
                const sm = await Promise.resolve().then(() => __importStar(require("@google-cloud/secret-manager")));
                secretClient = new sm.SecretManagerServiceClient();
            }
            catch (e) {
                console.warn("⚠️ Secret Manager client not available at runtime:", (e === null || e === void 0 ? void 0 : e.message) || e);
            }
            const access = async (secretSuffix) => {
                var _a, _b;
                if (!secretClient)
                    return null;
                const name = `projects/${PROJECT_ID}/secrets/dhan_${userId}_${secretSuffix}/versions/latest`;
                const [version] = await secretClient.accessSecretVersion({ name });
                return ((_b = (_a = version.payload) === null || _a === void 0 ? void 0 : _a.data) === null || _b === void 0 ? void 0 : _b.toString("utf8")) || null;
            };
            const clientId = await access("client_id");
            const apiKey = await access("api_key");
            const apiSecret = await access("api_secret");
            const accessToken = await access("access_token");
            if (!clientId || !apiKey || !apiSecret) {
                // Fallback to Firestore if Secret Manager doesn't contain all values
                console.warn("🔎 Secret Manager missing some Dhan values, falling back to Firestore");
            }
            else {
                return {
                    clientId,
                    apiKey,
                    apiSecret,
                    accessToken: accessToken || undefined,
                };
            }
        }
        catch (err) {
            console.warn(`⚠️ Secret Manager access failed: ${err.message}. Falling back to Firestore`);
            // Continue to Firestore fallback below
        }
    }
    const credDoc = await db.collection("dhan_credentials").doc(userId).get();
    if (!credDoc.exists) {
        throw new https_1.HttpsError("not-found", "Credentials not found. Please configure your Dhan API credentials.");
    }
    const data = credDoc.data();
    return {
        clientId: decrypt(data.clientId),
        apiKey: decrypt(data.apiKey),
        apiSecret: decrypt(data.apiSecret),
        accessToken: data.accessToken ? decrypt(data.accessToken) : undefined,
    };
}
//# sourceMappingURL=storeCredentials.js.map
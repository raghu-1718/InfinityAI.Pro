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
var _a;
Object.defineProperty(exports, "__esModule", { value: true });
exports.saveDhanCredentials = exports.submitDhanCredentialsV2 = void 0;
exports.getDecryptedCredentials = getDecryptedCredentials;
const functions = __importStar(require("firebase-functions"));
const https_1 = require("firebase-functions/v2/https");
const admin = __importStar(require("firebase-admin"));
const crypto = __importStar(require("crypto"));
const axios_1 = __importDefault(require("axios"));
const db = admin.firestore();
// Encryption configuration
const ENCRYPTION_KEY = process.env.ENCRYPTION_KEY || ((_a = functions.config().secrets) === null || _a === void 0 ? void 0 : _a.encryption_key);
const ALGORITHM = "aes-256-gcm";
if (!ENCRYPTION_KEY) {
    console.warn("⚠️ ENCRYPTION_KEY not set. Please configure: firebase functions:config:set secrets.encryption_key=YOUR_KEY");
}
/**
 * Encrypts sensitive data using AES-256-GCM
 */
function encrypt(text) {
    if (!ENCRYPTION_KEY) {
        throw new Error("ENCRYPTION_KEY not configured");
    }
    const iv = crypto.randomBytes(16);
    const key = Buffer.from(ENCRYPTION_KEY, "hex");
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
    if (!ENCRYPTION_KEY) {
        throw new Error("ENCRYPTION_KEY not configured");
    }
    const parts = encryptedData.split(":");
    if (parts.length !== 3) {
        throw new Error("Invalid encrypted data format");
    }
    const [ivHex, authTagHex, encryptedText] = parts;
    const iv = Buffer.from(ivHex, "hex");
    const authTag = Buffer.from(authTagHex, "hex");
    const key = Buffer.from(ENCRYPTION_KEY, "hex");
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
    secrets: ["ENCRYPTION_KEY"],
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
        await db.collection("dhan_credentials").doc(uid).set(encryptedData, { merge: true });
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
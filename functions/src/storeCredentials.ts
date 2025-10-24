/**
 * Store Credentials Functions
 * 
 * Securely stores Dhan API credentials with AES-256-GCM encryption
 * Credentials are encrypted before being written to Firestore
 */

import { onCall, HttpsError } from "firebase-functions/v2/https";
import * as admin from "firebase-admin";
import * as crypto from "crypto";
import axios from "axios";

const db = admin.firestore();

// Encryption configuration - Using environment variable for better compatibility
const ENCRYPTION_KEY = process.env.ENCRYPTION_KEY;
const ALGORITHM = "aes-256-gcm";

if (!ENCRYPTION_KEY) {
  console.warn("⚠️ ENCRYPTION_KEY not set. Please configure: firebase functions:config:set secrets.encryption_key=YOUR_KEY");
}

/**
 * Encrypts sensitive data using AES-256-GCM
 */
function encrypt(text: string): string {
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
function decrypt(encryptedData: string): string {
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
export const submitDhanCredentialsV2 = onCall(
  {
    region: "us-central1",
    memory: "256MiB",
    timeoutSeconds: 60,
    // Removed secrets configuration to avoid deployment validation issues
    // ENCRYPTION_KEY will be provided via environment variable instead
  },
  async (request) => {
    // Verify authentication
    if (!request.auth) {
      throw new HttpsError("unauthenticated", "User must be logged in to save credentials.");
    }

  const uid = request.auth.uid;
  const { clientId, apiKey, apiSecret, accessToken } = request.data;

    // Validate required fields
    if (!clientId || !apiKey || !apiSecret) {
      throw new HttpsError(
        "invalid-argument",
        "Missing required fields: clientId, apiKey, or apiSecret"
      );
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
          const verifyResponse = await axios.get("https://api.dhan.co/v2/holdings", {
            headers: {
              "access-token": accessToken,
              "client-id": clientId,
            },
            timeout: 5000,
          });

          if (verifyResponse.status === 200) {
            console.log(`✅ Dhan API credentials verified for user: ${uid}`);
          }
        } catch (verifyError: any) {
          console.warn(`⚠️ Failed to verify Dhan credentials: ${verifyError.message}`);
          // Don't fail the entire request if verification fails
        }
      }

      return {
        message: "Credentials saved successfully and encrypted securely.",
        status: "success",
      };
    } catch (error: any) {
      console.error("❌ Error saving credentials:", error);
      throw new HttpsError("internal", `Failed to save credentials: ${error.message}`);
    }
  }
);

/**
 * Alternative function name for backward compatibility
 */
export const saveDhanCredentials = submitDhanCredentialsV2;

/**
 * Helper function to retrieve and decrypt credentials
 * Used by other functions that need Dhan API access
 */
export async function getDecryptedCredentials(userId: string): Promise<{
  clientId: string;
  apiKey: string;
  apiSecret: string;
  accessToken?: string;
}> {
  const credDoc = await db.collection("dhan_credentials").doc(userId).get();

  if (!credDoc.exists) {
    throw new HttpsError("not-found", "Credentials not found. Please configure your Dhan API credentials.");
  }

  const data = credDoc.data()!;

  return {
    clientId: decrypt(data.clientId),
    apiKey: decrypt(data.apiKey),
    apiSecret: decrypt(data.apiSecret),
    accessToken: data.accessToken ? decrypt(data.accessToken) : undefined,
  };
}

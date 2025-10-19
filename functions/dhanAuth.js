const functions = require("firebase-functions/v1");
const admin = require("firebase-admin");
const crypto = require("crypto");
const axios = require("axios");

admin.initializeApp();

// Make sure to set ENCRYPTION_KEY in your Firebase functions config
// firebase functions:config:set secrets.encryption_key="your-secret-key"
const secretKey = process.env.ENCRYPTION_KEY;
const algorithm = "aes-256-gcm";

function encrypt(text) {
  const iv = crypto.randomBytes(16);
  const cipher = crypto.createCipheriv(algorithm, Buffer.from(secretKey, "hex"), iv);
  let encrypted = cipher.update(text, "utf8", "hex");
  encrypted += cipher.final("hex");
  const authTag = cipher.getAuthTag().toString("hex");
  return `${iv.toString("hex")}:${authTag}:${encrypted}`;
}

exports.submitDhanCredentials = functions.https.onCall(async (data, context) => {
  if (!secretKey) {
    throw new functions.https.HttpsError("internal", "ENCRYPTION_KEY not set.");
  }
  const uid = context.auth?.uid;
  if (!uid) throw new functions.https.HttpsError("unauthenticated", "User not signed in");

  const { accessToken, apiKey, apiSecret } = data;
  if (!accessToken || !apiKey || !apiSecret)
    throw new functions.https.HttpsError("invalid-argument", "Missing credentials");

  const encrypted = {
    accessToken: encrypt(accessToken),
    apiKey: encrypt(apiKey),
    apiSecret: encrypt(apiSecret),
    lastUpdatedAt: admin.firestore.FieldValue.serverTimestamp(),
  };

  await admin.firestore().collection("dhan_credentials").doc(uid).set(encrypted);
  return { message: "Credentials securely stored" };
});

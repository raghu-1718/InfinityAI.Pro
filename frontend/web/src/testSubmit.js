/**
 * Frontend test helper for Firebase Cloud Functions callable
 * 
 * Usage:
 *   import { testSubmit } from './testSubmit';
 *   testSubmit(); // Call from a button click or console
 */

import { httpsCallable } from "firebase/functions";
import { functions } from "./firebaseConfig";

/**
 * Tests the submitDhanCredentialsV2 callable function
 * @returns {Promise<void>}
 */
export async function testSubmit() {
  try {
    const submit = httpsCallable(functions, "submitDhanCredentialsV2");
    const res = await submit({ userId: "test", apiKey: "demo" });
    console.log("✅ Backend Response:", res.data);
    return res.data;
  } catch (error) {
    console.error("❌ Error calling submitDhanCredentialsV2:", error);
    throw error;
  }
}

/**
 * Tests the Gemini extension via generateOnCall callable
 * @param {string} engineData - The engine data to send to Gemini
 * @returns {Promise<void>}
 */
export async function testGeminiCall(engineData = "Test prompt for Gemini API") {
  try {
    const gemini = httpsCallable(functions, "ext-firestore-multimodal-genai-generateOnCall");
    const res = await gemini({ engine_data: engineData });
    console.log("✅ Gemini Response:", res.data);
    return res.data;
  } catch (error) {
    console.error("❌ Error calling Gemini extension:", error);
    throw error;
  }
}

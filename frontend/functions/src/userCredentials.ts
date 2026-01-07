/**
 * User Credentials Cloud Function
 *
 * Manages secure storage and retrieval of DhanHQ credentials
 * POST: Save credentials
 * GET: Retrieve credentials
 */

import { onCall, HttpsError } from "firebase-functions/v2/https";
import * as admin from "firebase-admin";

const db = admin.firestore();

// @ts-ignore-next-line
interface StoreCredentialsRequest {
  user_id: string;
  dhan_client_id: string;
  dhan_access_token: string;
}

// @ts-ignore-next-line
interface GetCredentialsRequest {
  user_id: string;
}

interface CredentialsResponse {
  success: boolean;
  dhan_client_id?: string;
  dhan_access_token?: string;
  updated_at?: string;
  message?: string;
}

/**
 * Store user DhanHQ credentials
 */
export const storeUserCredentials = onCall(
  { cors: true },
  async (request): Promise<CredentialsResponse> => {
  const { user_id, dhan_client_id, dhan_access_token } = request.data;

  // Validate input
  if (!user_id || !dhan_client_id || !dhan_access_token) {
    throw new HttpsError(
      "invalid-argument",
      "Missing required fields: user_id, dhan_client_id, dhan_access_token"
    );
  }

  try {
    const timestamp = admin.firestore.Timestamp.now();

    // Store in user_credentials collection
    await db
      .collection("user_credentials")
      .doc(user_id)
      .set({
        user_id,
        dhan_client_id,
        dhan_access_token,
        updated_at: timestamp,
      });

    // Update user_profiles with has_credentials flag
    await db
      .collection("user_profiles")
      .doc(user_id)
      .set(
        {
          user_id,
          has_credentials: true,
          credentials_updated_at: timestamp,
          clientId: dhan_client_id, // For compatibility with existing code
        },
        { merge: true }
      );

    return {
      success: true,
      message: "Credentials stored successfully",
      updated_at: timestamp.toDate().toISOString(),
    };
  } catch (error) {
    console.error("Error storing credentials:", error);
    throw new HttpsError(
      "internal",
      "Error storing credentials. Please try again."
    );
  }
});

/**
 * Retrieve user DhanHQ credentials
 */
export const getUserCredentials = onCall(
  { cors: true },
  async (request): Promise<CredentialsResponse> => {
    const { user_id } = request.data;

    // Validate input
    if (!user_id) {
      throw new HttpsError(
        "invalid-argument",
        "Missing required field: user_id"
      );
    }

    try {
      const credentialsDoc = await db
        .collection("user_credentials")
        .doc(user_id)
        .get();

      if (!credentialsDoc.exists) {
        throw new HttpsError(
          "not-found",
          "No credentials found for this user"
        );
      }

      const data = credentialsDoc.data();

      return {
        success: true,
        dhan_client_id: data?.dhan_client_id,
        dhan_access_token: data?.dhan_access_token,
        updated_at: data?.updated_at?.toDate?.().toISOString?.() || "",
      };
    } catch (error) {
      if (error instanceof HttpsError) {
        throw error;
      }
      console.error("Error retrieving credentials:", error);
      throw new HttpsError(
        "internal",
        "Error retrieving credentials. Please try again."
      );
    }
  }
);

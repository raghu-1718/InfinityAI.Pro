/**
 * Account Data Cloud Function
 *
 * Fetches complete account data from Engine-C
 * Includes balance, holdings, positions, orders, trades, and P&L
 */

import { onCall, HttpsError } from "firebase-functions/v2/https";
import axios from "axios";

// @ts-ignore-next-line
interface FetchAccountDataRequest {
  user_id: string;
  dhan_client_id: string;
  dhan_access_token: string;
}

interface AccountDataResponse {
  success?: boolean;
  data?: any;
  error?: string;
  status?: number;
}

const ENGINE_C_URL =
  process.env.ENGINE_C_URL ||
  "https://engine-c-3acobgd3qa-uc.a.run.app";

/**
 * Fetch account data from Engine-C
 */
export const fetchAccountData = onCall(
  { cors: true },
  async (request): Promise<AccountDataResponse> => {
    const { user_id, dhan_client_id, dhan_access_token } = request.data;

    // Validate input
    if (!user_id || !dhan_client_id || !dhan_access_token) {
      throw new HttpsError(
        "invalid-argument",
        "Missing required fields: user_id, dhan_client_id, dhan_access_token"
      );
    }

    try {
      // Call Engine-C account endpoint
      const response = await axios.get(
        `${ENGINE_C_URL}/api/v1/user/${dhan_client_id}/account`,
        {
          headers: {
            "X-Dhan-Token": dhan_access_token,
            "Content-Type": "application/json",
          },
          timeout: 10000, // 10 second timeout
        }
      );

      return {
        success: true,
        data: response.data,
      };
    } catch (error: any) {
      console.error("Error fetching account data from Engine-C:", error);

      // Pass through Engine-C errors
      if (error.response) {
        const status = error.response.status;
        const message = error.response.data?.message || error.message;

        throw new HttpsError(
          status === 401
            ? "unauthenticated"
            : status === 403
              ? "permission-denied"
              : status === 404
                ? "not-found"
                : "internal",
          `Engine-C error: ${message}`
        );
      }

      // Network or timeout errors
      throw new HttpsError(
        "unavailable",
        "Unable to connect to Engine-C. Please try again."
      );
    }
  }
);

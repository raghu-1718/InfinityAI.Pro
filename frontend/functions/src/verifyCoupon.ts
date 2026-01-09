/**
 * Verify Coupon Cloud Function
 *
 * Validates coupon codes and creates user sessions with feature access
 * Prevents duplicate redemptions and enforces expiry/usage limits
 */

import { onCall, HttpsError } from "firebase-functions/v2/https";
import * as admin from "firebase-admin";

const db = admin.firestore();

// @ts-ignore-next-line
interface VerifyCouponRequest {
  coupon_code: string;
  google_user_id: string;
  google_email: string;
}

interface VerifyCouponResponse {
  success: boolean;
  session_id?: string;
  features?: string[];
  expires_at?: string;
  message?: string;
}

// Valid coupon configurations
const VALID_COUPONS: Record<
  string,
  {
    features: string[];
    expires_at: string;
    max_uses: number;
  }
> = {
  INFINITY1718: {
    features: [
      "live_trading",
      "portfolio_analysis",
      "ai_signals",
      "vertex_ai",
      "engine_c_access",
    ],
    // Extended 6 months from current date (2026-01-08 → 2026-07-08)
    expires_at: "2026-07-08",
    max_uses: 100,
  },
  INFINITY0506: {
    features: ["portfolio_analysis", "ai_signals"],
    // Extended 6 months from current date (2026-01-08 → 2026-07-08)
    expires_at: "2026-07-08",
    max_uses: 50,
  },
  INFINITYRAJ: {
    features: ["portfolio_analysis"],
    // Extended 6 months from current date (2026-01-08 → 2026-07-08)
    expires_at: "2026-07-08",
    max_uses: 1,
  },
  TESTCOUPON: {
    features: ["portfolio_analysis"],
    // Long-lived test coupon kept far-future
    expires_at: "2099-12-31",
    max_uses: 999,
  },
};

export const verifyCoupon = onCall(
  { cors: true },
  async (request): Promise<VerifyCouponResponse> => {
    const { coupon_code, google_user_id, google_email } = request.data;

    // Validate input
    if (!coupon_code || !google_user_id || !google_email) {
      throw new HttpsError(
        "invalid-argument",
        "Missing required fields: coupon_code, google_user_id, google_email"
      );
    }

    const normalizedCode = coupon_code.trim().toUpperCase();

    // Check if coupon exists
    if (!VALID_COUPONS[normalizedCode]) {
      throw new HttpsError("not-found", "Invalid coupon code");
    }

    const couponConfig = VALID_COUPONS[normalizedCode];
    const today = new Date().toISOString().split("T")[0];

    // Check if coupon has expired
    if (today > couponConfig.expires_at) {
      throw new HttpsError("failed-precondition", "Coupon has expired");
    }

    // Check if user has already used this coupon
    const userCouponRef = db
      .collection("user_coupons")
      .doc(`${google_user_id}_${normalizedCode}`);
    const userCouponSnap = await userCouponRef.get();

    if (userCouponSnap.exists) {
      // Allow re-verification: Return existing session instead of blocking
      const userSessionRef = db.collection("user_sessions").doc(google_user_id);
      const sessionSnap = await userSessionRef.get();

      if (sessionSnap.exists) {
        const sessionData = sessionSnap.data();
        return {
          success: true,
          session_id: sessionData?.session_id || `session_${google_user_id}_${Date.now()}`,
          features: couponConfig.features,
          expires_at: sessionData?.expires_at?.toDate().toISOString() || new Date(Date.now() + 90 * 24 * 60 * 60 * 1000).toISOString(),
        };
      }
      // If session doesn't exist but redemption does, continue to create new session below
    }

    // Check coupon usage limit
    const couponUsageRef = db.collection("coupon_usage").doc(normalizedCode);
    const couponUsageSnap = await couponUsageRef.get();
    const currentUsage = couponUsageSnap.exists
      ? couponUsageSnap.data()?.total_uses || 0
      : 0;

    if (currentUsage >= couponConfig.max_uses) {
      throw new HttpsError(
        "resource-exhausted",
        "Coupon usage limit reached"
      );
    }

    // Generate session ID
    const sessionId = `session_${google_user_id}_${Date.now()}`;
    const expiresAt = new Date();
    expiresAt.setDate(expiresAt.getDate() + 90);

    try {
      // Atomically update Firestore collections
      const batch = db.batch();

      // 1. Increment coupon usage counter
      batch.set(
        couponUsageRef,
        {
          total_uses: currentUsage + 1,
          last_used_by: google_email,
          last_used_at: admin.firestore.Timestamp.now(),
        },
        { merge: true }
      );

      // 2. Record user coupon redemption
      batch.set(userCouponRef, {
        user_id: google_user_id,
        coupon_code: normalizedCode,
        email: google_email,
        redeemed_at: admin.firestore.Timestamp.now(),
      });

      // 3. Create/update user session
      const userSessionRef = db
        .collection("user_sessions")
        .doc(google_user_id);
      batch.set(
        userSessionRef,
        {
          session_id: sessionId,
          features: couponConfig.features,
          created_at: admin.firestore.Timestamp.now(),
          expires_at: admin.firestore.Timestamp.fromDate(expiresAt),
          coupon_code: normalizedCode,
        },
        { merge: true }
      );

      // 4. Update user profile with features
      const userProfileRef = db.collection("user_profiles").doc(google_user_id);
      batch.set(
        userProfileRef,
        {
          google_user_id,
          email: google_email,
          features: couponConfig.features,
          coupon_code: normalizedCode,
          coupon_redeemed_at: admin.firestore.Timestamp.now(),
          coupon_expires_at: admin.firestore.Timestamp.fromDate(expiresAt),
          last_login: admin.firestore.Timestamp.now(),
        },
        { merge: true }
      );

      await batch.commit();

      return {
        success: true,
        session_id: sessionId,
        features: couponConfig.features,
        expires_at: expiresAt.toISOString(),
      };
    } catch (error) {
      console.error("Error verifying coupon:", error);
      throw new HttpsError(
        "internal",
        "Error verifying coupon. Please try again."
      );
    }
  }
);

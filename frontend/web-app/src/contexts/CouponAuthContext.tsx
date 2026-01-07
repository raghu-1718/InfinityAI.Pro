"use client";

import React, {
  createContext,
  useContext,
  useEffect,
  useState,
  ReactNode,
  useCallback,
} from "react";
import { User } from "firebase/auth";
import {
  auth,
  createOrUpdateUserProfile,
  getUserProfile,
  UserProfile,
  signInWithGoogle as firebaseSignInWithGoogle,
  logOut as firebaseLogOut,
  onAuthChange,
} from "@/lib/firebase";

// Storage keys
const COUPON_SESSION_KEY = "infinityai_coupon_session";
const AUTH_TYPE_KEY = "infinityai_auth_type";
const STORAGE_VERSION_KEY = "infinityai_version";
const CURRENT_VERSION = "3.8";

// Clear old storage on version mismatch
function clearOldStorage() {
  if (typeof window === "undefined") return;
  const storedVersion = localStorage.getItem(STORAGE_VERSION_KEY);
  if (storedVersion !== CURRENT_VERSION) {
    console.log(
      "Clearing old storage data for version upgrade to",
      CURRENT_VERSION
    );
    localStorage.removeItem(COUPON_SESSION_KEY);
    localStorage.removeItem(AUTH_TYPE_KEY);
    localStorage.removeItem("infinityai_session");
    localStorage.removeItem("infinityai_user");
    localStorage.removeItem("infinityai-storage");
    localStorage.setItem(STORAGE_VERSION_KEY, CURRENT_VERSION);
  }
}

export type AuthType = "firebase" | "coupon" | null;

export interface CouponSession {
  sessionId: string;
  userId: string;
  features: string[];
  expiresAt: string;
  dhanConfigured: boolean;
}

export interface CouponUser {
  userId: string;
  name?: string;
  email?: string;
  dhanConnected: boolean;
  dhanClientId?: string;
  photoURL?: string | null;
}

interface CouponAuthContextType {
  // State
  session: CouponSession | null;
  user: CouponUser | null;
  loading: boolean;
  isAuthenticated: boolean;
  authType: AuthType;
  firebaseUser: User | null;
  userProfile: UserProfile | null;

  // Firebase Auth methods
  signInWithGoogle: () => Promise<{ success: boolean; error?: string }>;

  // Coupon Auth methods
  verifyCoupon: (
    couponCode: string
  ) => Promise<{ success: boolean; error?: string }>;

  // Common methods
  logout: () => Promise<void>;
  refreshSession: () => Promise<void>;

  // Dhan connection methods (for coupon auth)
  connectDhan: (
    clientId: string,
    accessToken: string
  ) => Promise<{ success: boolean; error?: string }>;
  disconnectDhan: () => Promise<{ success: boolean; error?: string }>;
}

const CouponAuthContext = createContext<CouponAuthContextType | undefined>(
  undefined
);

import { getEngineCUrl } from "@/lib/api";

// Engine C URL for coupon verification
const ENGINE_C_URL = getEngineCUrl();

export function CouponAuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<CouponSession | null>(null);
  const [user, setUser] = useState<CouponUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [authType, setAuthType] = useState<AuthType>(null);
  const [firebaseUser, setFirebaseUser] = useState<User | null>(null);
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);

  // Clear old storage on mount (version upgrade)
  useEffect(() => {
    clearOldStorage();
  }, []);

  // Initialize auth state - check both Firebase and coupon
  useEffect(() => {
    let isMounted = true;

    // Safety timeout
    const safetyTimeout = setTimeout(() => {
      if (isMounted && loading) {
        console.warn("Auth loading safety timeout triggered");
        setLoading(false);
      }
    }, 5000);

    // Check for existing coupon session
    const storedAuthType =
      typeof window !== "undefined"
        ? localStorage.getItem(AUTH_TYPE_KEY)
        : null;
    const storedCouponSession =
      typeof window !== "undefined"
        ? localStorage.getItem(COUPON_SESSION_KEY)
        : null;

    // Listen for Firebase auth state changes (safe wrapper handles SSR case)
    const unsubscribe = onAuthChange(async (fbUser) => {
      if (!isMounted) return;

      if (fbUser) {
        // User is signed in with Firebase
        clearTimeout(safetyTimeout);
        try {
          const profile = await getUserProfile(fbUser.uid);

          if (isMounted) {
            setFirebaseUser(fbUser);
            setUserProfile(profile);
            setAuthType("firebase");

            // Create session from Firebase user
            setSession({
              sessionId: fbUser.uid,
              userId: fbUser.uid,
              features: ["premium", "ai_signals", "auto_trading"],
              expiresAt: new Date(
                Date.now() + 30 * 24 * 60 * 60 * 1000
              ).toISOString(),
              dhanConfigured: profile?.dhanConnected || false,
            });

            setUser({
              userId: fbUser.uid,
              name: fbUser.displayName || profile?.displayName || "User",
              email: fbUser.email || undefined,
              dhanConnected: profile?.dhanConnected || false,
              dhanClientId: profile?.dhanClientId,
              photoURL: fbUser.photoURL,
            });

            localStorage.setItem(AUTH_TYPE_KEY, "firebase");
            localStorage.removeItem(COUPON_SESSION_KEY);
            setLoading(false);
          }
        } catch (error) {
          console.error("Error loading Firebase user profile:", error);
          if (isMounted) {
            setFirebaseUser(fbUser);
            setAuthType("firebase");
            setSession({
              sessionId: fbUser.uid,
              userId: fbUser.uid,
              features: ["basic"],
              expiresAt: new Date(
                Date.now() + 30 * 24 * 60 * 60 * 1000
              ).toISOString(),
              dhanConfigured: false,
            });
            setUser({
              userId: fbUser.uid,
              name: fbUser.displayName || "User",
              email: fbUser.email || undefined,
              dhanConnected: false,
              photoURL: fbUser.photoURL,
            });
            setLoading(false);
          }
        }
      } else {
        // No Firebase user - check for coupon session
        setFirebaseUser(null);
        setUserProfile(null);

        if (storedAuthType === "coupon" && storedCouponSession) {
          try {
            const couponData = JSON.parse(storedCouponSession);
            if (isMounted) {
              setAuthType("coupon");
              setSession({
                sessionId: couponData.sessionId || couponData.userId,
                userId: couponData.userId,
                features: couponData.features || [],
                expiresAt: couponData.expiresAt || "",
                dhanConfigured: false,
              });
              setUser({
                userId: couponData.userId,
                name:
                  couponData.displayName ||
                  `User ${(couponData.userId || "").slice(0, 8)}`,
                dhanConnected: false,
              });
              clearTimeout(safetyTimeout);
              setLoading(false);
            }
          } catch (e) {
            console.error("Failed to parse coupon session:", e);
            localStorage.removeItem(COUPON_SESSION_KEY);
            localStorage.removeItem(AUTH_TYPE_KEY);
            if (isMounted) {
              setSession(null);
              setUser(null);
              setAuthType(null);
              clearTimeout(safetyTimeout);
              setLoading(false);
            }
          }
        } else {
          // No auth at all
          if (isMounted) {
            setSession(null);
            setUser(null);
            setAuthType(null);
            clearTimeout(safetyTimeout);
            setLoading(false);
          }
        }
      }
    });

    return () => {
      isMounted = false;
      clearTimeout(safetyTimeout);
      unsubscribe();
    };
  }, []);

  // Sign in with Google
  const signInWithGoogle = useCallback(async () => {
    setLoading(true);
    try {
      const res = await firebaseSignInWithGoogle();
      if (!res.success) {
        setLoading(false);
        return { success: false, error: res.error || "Google sign-in failed" };
      }

      const fbUser = res.user!;
      const profile = res.profile ?? (await getUserProfile(fbUser.uid));

      setFirebaseUser(fbUser);
      setUserProfile(profile || null);
      setAuthType("firebase");

      setSession({
        sessionId: fbUser.uid,
        userId: fbUser.uid,
        features: ["premium", "ai_signals", "auto_trading"],
        expiresAt: new Date(
          Date.now() + 30 * 24 * 60 * 60 * 1000
        ).toISOString(),
        dhanConfigured: profile?.dhanConnected || false,
      });

      setUser({
        userId: fbUser.uid,
        name: fbUser.displayName || profile?.displayName || "User",
        email: fbUser.email || undefined,
        dhanConnected: profile?.dhanConnected || false,
        dhanClientId: profile?.dhanClientId,
        photoURL: fbUser.photoURL,
      });

      localStorage.setItem(AUTH_TYPE_KEY, "firebase");
      localStorage.removeItem(COUPON_SESSION_KEY);

      setLoading(false);
      return { success: true };
    } catch (error) {
      console.error("Google sign-in error:", error);
      setLoading(false);
      return {
        success: false,
        error:
          error instanceof Error
            ? error.message
            : "Failed to sign in with Google",
      };
    }
  }, []);

  // Verify coupon code
  const verifyCoupon = useCallback(async (couponCode: string) => {
    setLoading(true);
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 15000);

      console.log("CouponAuth: Verifying coupon:", couponCode);

      const response = await fetch(`${ENGINE_C_URL}/api/auth/coupon/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ coupon_code: couponCode }),
        signal: controller.signal,
      });
      clearTimeout(timeoutId);

      console.log("CouponAuth: Response status:", response.status);

      // Handle non-OK responses
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        console.error(
          "CouponAuth: Verification failed:",
          response.status,
          errorData
        );
        setLoading(false);
        return {
          success: false,
          error:
            errorData.detail ||
            errorData.message ||
            `Server error: ${response.status}`,
        };
      }

      const data = await response.json();
      console.log("CouponAuth: Response data:", data);

      if (data.success) {
        const couponSession = {
          sessionId: data.session_id,
          userId: data.user_id,
          displayName: `User ${(data.user_id || "").slice(0, 8)}`,
          features: data.features || [],
          expiresAt: data.expires_at,
        };

        localStorage.setItem(COUPON_SESSION_KEY, JSON.stringify(couponSession));
        localStorage.setItem(AUTH_TYPE_KEY, "coupon");

        setAuthType("coupon");
        setSession({
          sessionId: data.session_id,
          userId: data.user_id,
          features: data.features || [],
          expiresAt: data.expires_at,
          dhanConfigured: false,
        });
        setUser({
          userId: data.user_id,
          name: couponSession.displayName,
          dhanConnected: false,
        });

        setLoading(false);
        return { success: true };
      } else {
        setLoading(false);
        return {
          success: false,
          error: data.detail || data.message || "Invalid coupon code",
        };
      }
    } catch (error) {
      console.error("Coupon verification error:", error);
      setLoading(false);
      return {
        success: false,
        error:
          error instanceof Error && error.name === "AbortError"
            ? "Request timeout. Please try again."
            : "Failed to verify coupon. Please try again.",
      };
    }
  }, []);

  // Logout
  const logout = useCallback(async () => {
    setLoading(true);
    try {
      // Sign out using firebase helper (safe for SSR)
      await firebaseLogOut();

      // Try to notify backend for coupon logout
      try {
        await fetch(`${ENGINE_C_URL}/api/auth/logout`, { method: "POST" });
      } catch (e) {
        // Ignore errors
      }

      // Clear all auth storage
      localStorage.removeItem(COUPON_SESSION_KEY);
      localStorage.removeItem(AUTH_TYPE_KEY);
      localStorage.removeItem("infinityai_session");
      localStorage.removeItem("infinityai_user");

      setSession(null);
      setUser(null);
      setAuthType(null);
      setFirebaseUser(null);
      setUserProfile(null);
    } catch (error) {
      console.error("Logout error:", error);
    }
    setLoading(false);
  }, []);

  // Refresh session
  const refreshSession = useCallback(async () => {
    if (firebaseUser) {
      try {
        const profile = await getUserProfile(firebaseUser.uid);
        setUserProfile(profile);
      } catch (error) {
        console.error("Failed to refresh session:", error);
      }
    }
  }, [firebaseUser]);

  // Connect Dhan (placeholder - needs backend integration)
  const connectDhan = useCallback(
    async (clientId: string, accessToken: string) => {
      return {
        success: false,
        error: "Dhan connection requires settings page",
      };
    },
    []
  );

  // Disconnect Dhan (placeholder)
  const disconnectDhan = useCallback(async () => {
    return {
      success: false,
      error: "Dhan disconnection requires settings page",
    };
  }, []);

  const value: CouponAuthContextType = {
    session,
    user,
    loading,
    isAuthenticated: !!session,
    authType,
    firebaseUser,
    userProfile,
    signInWithGoogle,
    verifyCoupon,
    logout,
    refreshSession,
    connectDhan,
    disconnectDhan,
  };

  return (
    <CouponAuthContext.Provider value={value}>
      {children}
    </CouponAuthContext.Provider>
  );
}

export function useCouponAuth() {
  const context = useContext(CouponAuthContext);
  if (context === undefined) {
    throw new Error("useCouponAuth must be used within a CouponAuthProvider");
  }
  return context;
}

// Hook for requiring authentication
export function useRequireCouponAuth() {
  const { isAuthenticated, loading } = useCouponAuth();

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      console.log("User not authenticated");
    }
  }, [isAuthenticated, loading]);

  return { isAuthenticated, loading };
}

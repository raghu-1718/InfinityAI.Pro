"use client";

import React, {
  createContext,
  useContext,
  useEffect,
  useState,
  ReactNode,
  useCallback,
} from "react";
import type { User } from "@/lib/auth";
import {
  onAuthChange,
  getUserProfile,
  signInWithGoogle as authSignInWithGoogle,
  logOut as authLogOut,
} from "@/lib/auth";
import type { UserProfile } from "@/lib/supabase";
import { verifyCouponAPI } from "@/lib/cloudFunctions";
import { useSessionStore } from "@/hooks/useSessionStore";
import { getEngineCUrl } from "@/lib/api";

// Storage keys
const DUAL_AUTH_KEY = "infinityai_dual_auth";
const STORAGE_VERSION_KEY = "infinityai_version";
const CURRENT_VERSION = "4.0";

// Clear old storage on version mismatch
function clearOldStorage() {
  if (typeof window === "undefined") return;
  const storedVersion = localStorage.getItem(STORAGE_VERSION_KEY);
  if (storedVersion !== CURRENT_VERSION) {
    console.log(
      "Clearing old storage data for version upgrade to",
      CURRENT_VERSION
    );
    localStorage.removeItem(DUAL_AUTH_KEY);
    localStorage.removeItem("infinityai_coupon_session");
    localStorage.removeItem("infinityai_auth_type");
    localStorage.removeItem("infinityai_session");
    localStorage.removeItem("infinityai_user");
    localStorage.removeItem("infinityai-storage");
    localStorage.setItem(STORAGE_VERSION_KEY, CURRENT_VERSION);
  }
}

export interface DualAuthSession {
  // Google Auth
  googleUserId: string;
  googleEmail: string | null;
  googleDisplayName: string | null;
  googlePhotoURL: string | null;
  // Coupon Auth
  couponCode: string;
  couponVerified: boolean;
  couponFeatures: string[];
  couponExpiresAt: string;
  // Combined
  userId: string;
  isFullyAuthenticated: boolean;
}

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

interface DualAuthContextType {
  // State
  session: CouponSession | null;
  user: CouponUser | null;
  loading: boolean;

  // Dual auth state
  isGoogleSignedIn: boolean;
  isCouponVerified: boolean;
  isAuthenticated: boolean; // TRUE only when BOTH are verified

  authUser: User | null;
  userProfile: UserProfile | null;

  // Auth methods - Step 1: Google Sign-In
  signInWithGoogle: () => Promise<{ success: boolean; error?: string }>;

  // Auth methods - Step 2: Coupon Verification
  verifyCoupon: (
    couponCode: string
  ) => Promise<{ success: boolean; error?: string }>;

  // Logout (clears both)
  logout: () => Promise<void>;
  refreshSession: () => Promise<void>;

  // Dhan connection methods
  connectDhan: (
    clientId: string,
    accessToken: string
  ) => Promise<{ success: boolean; error?: string }>;
  disconnectDhan: () => Promise<{ success: boolean; error?: string }>;
}

const DualAuthContext = createContext<DualAuthContextType | undefined>(
  undefined
);

// Engine C URL for coupon verification
const ENGINE_C_URL = getEngineCUrl();

export function CouponAuthProvider({ children }: { children: ReactNode }) {
  const [loading, setLoading] = useState(false);
  const [authUser, setAuthUser] = useState<User | null>(null);
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [isCouponVerified, setIsCouponVerified] = useState(true);
  const [couponData, setCouponData] = useState<{
    code: string;
    features: string[];
    expiresAt: string;
    sessionId: string;
  } | null>({
    code: "LOCAL_DEV",
    features: ["ALL"],
    expiresAt: "2099-12-31",
    sessionId: "local-dev-session"
  });

  // Derived states
  const isGoogleSignedIn = true;
  const isAuthenticated = true;

  // Session and User for compatibility
  const session: CouponSession | null = {
    sessionId: couponData?.sessionId || "local-dev-session",
    userId: authUser?.uid || "local-user-123",
    features: couponData?.features || ["ALL"],
    expiresAt: couponData?.expiresAt || "2099-12-31",
    dhanConfigured: true,
  };

  const user: CouponUser | null = {
    userId: authUser?.uid || "local-user-123",
    name: authUser?.displayName || userProfile?.displayName || "Local Developer",
    email: authUser?.email || "dev@localhost",
    dhanConnected: true,
    dhanClientId: userProfile?.dhanClientId || "DEV1234",
    photoURL: authUser?.photoURL || undefined,
  };

  // Clear old storage on mount
  useEffect(() => {
    clearOldStorage();
  }, []);

  // Initialize auth state
  useEffect(() => {
    let isMounted = true;

    // Safety timeout
    const safetyTimeout = setTimeout(() => {
      if (isMounted && loading) {
        console.warn("Auth loading safety timeout triggered");
        setLoading(false);
      }
    }, 5000);

    // Check session store
    const sessionStore = useSessionStore.getState();
    let storedCouponData: typeof couponData = null;

    if (sessionStore.isAuthenticated && sessionStore.sessionId) {
      storedCouponData = {
        code: "REDACTED", // We might not store code in sessionStore, but we store features
        features: sessionStore.features,
        expiresAt: sessionStore.expiresAt || "",
        sessionId: sessionStore.sessionId,
      };
    }

    // Listen for Supabase auth state changes (safe wrapper handles SSR)
    const unsubscribe = onAuthChange(async (fbUser) => {
      if (!isMounted) return;
      clearTimeout(safetyTimeout);

      if (fbUser) {
        // User is signed in with Google
        try {
          const profile = await getUserProfile(fbUser.uid);
          if (isMounted) {
            setAuthUser(fbUser);
            setUserProfile(profile);

            // Restore coupon verification if exists for this user
            if (storedCouponData) {
              setCouponData(storedCouponData);
              setIsCouponVerified(true);
            }
          }
        } catch (error) {
          console.error("Error loading Supabase user profile:", error);
          if (isMounted) {
            setAuthUser(fbUser);
            if (storedCouponData) {
              setCouponData(storedCouponData);
              setIsCouponVerified(true);
            }
          }
        }
      } else {
        // No Supabase user - clear all auth
        if (isMounted) {
          setAuthUser(null);
          setUserProfile(null);
          setIsCouponVerified(false);
          setCouponData(null);
          localStorage.removeItem(DUAL_AUTH_KEY);
        }
      }

      if (isMounted) {
        setLoading(false);
      }
    });

    return () => {
      isMounted = false;
      clearTimeout(safetyTimeout);
      unsubscribe();
    };
  }, []);

  // Sign in with Google (Step 1)
  const signInWithGoogle = useCallback(async () => {
    setLoading(true);
    try {
      const res = await authSignInWithGoogle();
      if (!res.success) {
        setLoading(false);
        return { success: false, error: res.error || "Google sign-in failed" };
      }

      const fbUser = res.user!;
      const profile = res.profile ?? (await getUserProfile(fbUser.uid));

      setAuthUser(fbUser);
      setUserProfile(profile || null);

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

  // Verify coupon code (Step 2 - requires Google sign-in first)
  const verifyCoupon = useCallback(
    async (couponCode: string) => {
      if (!authUser) {
        return { success: false, error: "Please sign in with Google first" };
      }

      setLoading(true);
      try {
        console.log(
          "Verifying coupon:",
          couponCode,
          "for user:",
          authUser.email
        );

        const data = await verifyCouponAPI(
          couponCode,
          authUser.uid,
          authUser.email || ""
        );
        console.log("Coupon verify data:", data);

        if (data.success) {
          const newCouponData = {
            code: couponCode,
            features: data.features || [],
            expiresAt: data.expires_at || "",
            sessionId: data.session_id || "",
          };

          setCouponData(newCouponData);
          setIsCouponVerified(true);

          // Store dual auth session
          const sessionData = {
            sessionId: data.session_id || "",
            userId: authUser.uid,
            features: data.features || [],
            expiresAt: data.expires_at || "",
          };

          useSessionStore.getState().setSession(sessionData);

          localStorage.setItem(
            DUAL_AUTH_KEY,
            JSON.stringify({
              googleUserId: authUser.uid,
              couponCode: couponCode,
              couponVerified: true,
              features: data.features || [],
              expiresAt: data.expires_at || "",
              sessionId: data.session_id || "",
            })
          );

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
    },
    [authUser]
  );

  // Logout (clears both Google and coupon)
  const logout = useCallback(async () => {
    setLoading(true);
    try {
      // Sign out using supabase helper (safe for SSR)
      await authLogOut();

      // Try to notify backend
      try {
        await fetch(`${ENGINE_C_URL}/api/auth/logout`, { method: "POST" });
      } catch (e) {
        // Ignore errors
      }

      // Clear all auth storage
      localStorage.removeItem(DUAL_AUTH_KEY);
      localStorage.removeItem("infinityai_coupon_session");
      localStorage.removeItem("infinityai_auth_type");
      localStorage.removeItem("infinityai_session");
      localStorage.removeItem("infinityai_user");

      setAuthUser(null);
      setUserProfile(null);
      setIsCouponVerified(false);
      setCouponData(null);
      useSessionStore.getState().clearSession();
    } catch (error) {
      console.error("Logout error:", error);
    }
    setLoading(false);
  }, []);

  // Refresh session
  const refreshSession = useCallback(async () => {
    if (authUser) {
      try {
        const profile = await getUserProfile(authUser.uid);
        setUserProfile(profile);
      } catch (error) {
        console.error("Failed to refresh session:", error);
      }
    }
  }, [authUser]);

  // Dhan connection placeholders
  const connectDhan = useCallback(async () => {
    return { success: false, error: "Use settings page to connect Dhan" };
  }, []);

  const disconnectDhan = useCallback(async () => {
    return { success: false, error: "Use settings page to disconnect Dhan" };
  }, []);

  const value: DualAuthContextType = {
    session,
    user,
    loading,
    isGoogleSignedIn,
    isCouponVerified,
    isAuthenticated,
    authUser,
    userProfile,
    signInWithGoogle,
    verifyCoupon,
    logout,
    refreshSession,
    connectDhan,
    disconnectDhan,
  };

  return (
    <DualAuthContext.Provider value={value}>
      {children}
    </DualAuthContext.Provider>
  );
}

// Safe default state for when context is not available
const defaultAuthState: DualAuthContextType = {
  session: null,
  user: null,
  loading: true,
  isGoogleSignedIn: false,
  isCouponVerified: false,
  isAuthenticated: false,
  authUser: null,
  userProfile: null,
  signInWithGoogle: async () => ({ success: false, error: "Not initialized" }),
  verifyCoupon: async () => ({ success: false, error: "Not initialized" }),
  logout: async () => {},
  refreshSession: async () => {},
  connectDhan: async () => ({ success: false, error: "Not initialized" }),
  disconnectDhan: async () => ({ success: false, error: "Not initialized" }),
};

export function useCouponAuth(): DualAuthContextType {
  const context = useContext(DualAuthContext);

  // If context is not available, return a safe default instead of throwing
  // This can happen during SSR, hydration, or if the provider isn't mounted yet
  if (context === undefined) {
    console.warn(
      "useCouponAuth: Context not available, returning default state"
    );
    return defaultAuthState;
  }
  return context;
}

// Alias for the hook
export const useDualAuth = useCouponAuth;

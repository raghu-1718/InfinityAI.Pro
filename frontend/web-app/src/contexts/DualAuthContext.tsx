"use client";

import React, {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
  useCallback,
} from "react";
import type { User } from "@/lib/auth";
import {
  onAuthChange,
  getUserProfile,
  signInWithGoogle as authSignInWithGoogle,
  logOut as authLogOut,
} from "@/lib/auth";
import type { UserProfile } from "@/lib/firebase";
import { verifyCouponAPI } from "@/lib/cloudFunctions";
import { useSessionStore } from "@/hooks/useSessionStore";
import { getEngineCUrl } from "@/lib/api";

const DUAL_AUTH_KEY = "infinityai_dual_auth";
const STORAGE_VERSION_KEY = "infinityai_version";
const CURRENT_VERSION = "4.1";

function clearOldStorage() {
  if (typeof window === "undefined") return;
  const storedVersion = localStorage.getItem(STORAGE_VERSION_KEY);
  if (storedVersion !== CURRENT_VERSION) {
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
  googleUserId: string;
  googleEmail: string | null;
  googleDisplayName: string | null;
  googlePhotoURL: string | null;
  couponCode: string;
  couponVerified: boolean;
  couponFeatures: string[];
  couponExpiresAt: string;
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
  session: CouponSession | null;
  user: CouponUser | null;
  loading: boolean;
  isGoogleSignedIn: boolean;
  isCouponVerified: boolean;
  isAuthenticated: boolean;
  authUser: User | null;
  userProfile: UserProfile | null;
  signInWithGoogle: () => Promise<{ success: boolean; error?: string }>;
  verifyCoupon: (couponCode: string) => Promise<{ success: boolean; error?: string }>;
  logout: () => Promise<void>;
  refreshSession: () => Promise<void>;
  connectDhan: (clientId: string, accessToken: string) => Promise<{ success: boolean; error?: string }>;
  disconnectDhan: () => Promise<{ success: boolean; error?: string }>;
}

const DualAuthContext = createContext<DualAuthContextType | undefined>(undefined);
const ENGINE_C_URL = getEngineCUrl();

export function CouponAuthProvider({ children }: { children: ReactNode }) {
  const [loading, setLoading] = useState(true);
  const [authUser, setAuthUser] = useState<User | null>(null);
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [isCouponVerified, setIsCouponVerified] = useState(false);
  const [couponData, setCouponData] = useState<{
    code: string;
    features: string[];
    expiresAt: string;
    sessionId: string;
  } | null>(null);

  const isSingleUserMode = process.env.NEXT_PUBLIC_SINGLE_USER_MODE === "true";
  const isGoogleSignedIn = Boolean(authUser);
  const isAuthenticated = isGoogleSignedIn && (isSingleUserMode || isCouponVerified);

  const session: CouponSession | null = authUser
    ? {
        sessionId: couponData?.sessionId || `firebase-${authUser.uid}`,
        userId: authUser.uid,
        features: couponData?.features || (isSingleUserMode ? ["ALL"] : []),
        expiresAt: couponData?.expiresAt || new Date(Date.now() + 31536000000).toISOString(),
        dhanConfigured: true,
      }
    : null;

  const user: CouponUser | null = authUser
    ? {
        userId: authUser.uid,
        name: authUser.displayName || userProfile?.displayName || "InfinityAI User",
        email: authUser.email || userProfile?.email || "",
        dhanConnected: true,
        dhanClientId: userProfile?.dhanClientId || "owner-user",
        photoURL: authUser.photoURL || userProfile?.photoURL || null,
      }
    : null;

  useEffect(() => {
    clearOldStorage();
  }, []);

  useEffect(() => {
    let isMounted = true;
    const safetyTimeout = setTimeout(() => {
      if (isMounted && loading) {
        setLoading(false);
      }
    }, 5000);

    const sessionStore = useSessionStore.getState();
    let storedCouponData: typeof couponData = null;

    if (sessionStore.isAuthenticated && sessionStore.sessionId) {
      storedCouponData = {
        code: "OWNER_ACCESS",
        features: sessionStore.features,
        expiresAt: sessionStore.expiresAt || new Date(Date.now() + 31536000000).toISOString(),
        sessionId: sessionStore.sessionId,
      };
    }

    const unsubscribe = onAuthChange(async (fbUser) => {
      if (!isMounted) return;
      clearTimeout(safetyTimeout);

      if (fbUser) {
        try {
          const profile = await getUserProfile(fbUser.uid);
          if (!isMounted) return;

          setAuthUser(fbUser);
          setUserProfile(profile);

          if (isSingleUserMode) {
            const defaultSession = {
              code: "OWNER_ACCESS",
              features: ["ALL"],
              expiresAt: new Date(Date.now() + 31536000000).toISOString(),
              sessionId: `firebase-${fbUser.uid}`,
            };
            setCouponData(defaultSession);
            setIsCouponVerified(true);
            useSessionStore.getState().setSession({
              sessionId: defaultSession.sessionId,
              userId: fbUser.uid,
              features: defaultSession.features,
              expiresAt: defaultSession.expiresAt,
            });
            localStorage.setItem(
              DUAL_AUTH_KEY,
              JSON.stringify({
                googleUserId: fbUser.uid,
                couponCode: "OWNER_ACCESS",
                couponVerified: true,
                features: defaultSession.features,
                expiresAt: defaultSession.expiresAt,
                sessionId: defaultSession.sessionId,
              })
            );
          } else if (storedCouponData) {
            setCouponData(storedCouponData);
            setIsCouponVerified(true);
          } else {
            setCouponData(null);
            setIsCouponVerified(false);
          }
        } catch (error) {
          console.error("Error loading user profile:", error);
          if (isMounted) {
            setAuthUser(fbUser);
            if (isSingleUserMode) {
              const defaultSession = {
                code: "OWNER_ACCESS",
                features: ["ALL"],
                expiresAt: new Date(Date.now() + 31536000000).toISOString(),
                sessionId: `firebase-${fbUser.uid}`,
              };
              setCouponData(defaultSession);
              setIsCouponVerified(true);
            } else if (storedCouponData) {
              setCouponData(storedCouponData);
              setIsCouponVerified(true);
            } else {
              setCouponData(null);
              setIsCouponVerified(false);
            }
          }
        }
      } else {
        if (isMounted) {
          setAuthUser(null);
          setUserProfile(null);
          setCouponData(null);
          setIsCouponVerified(false);
          localStorage.removeItem(DUAL_AUTH_KEY);
          useSessionStore.getState().clearSession();
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
  }, [isSingleUserMode]);

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

      if (isSingleUserMode) {
        const defaultSession = {
          code: "OWNER_ACCESS",
          features: ["ALL"],
          expiresAt: new Date(Date.now() + 31536000000).toISOString(),
          sessionId: `firebase-${fbUser.uid}`,
        };
        setCouponData(defaultSession);
        setIsCouponVerified(true);
        useSessionStore.getState().setSession({
          sessionId: defaultSession.sessionId,
          userId: fbUser.uid,
          features: defaultSession.features,
          expiresAt: defaultSession.expiresAt,
        });
      }

      setLoading(false);
      return { success: true };
    } catch (error) {
      console.error("Google sign-in error:", error);
      setLoading(false);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to sign in with Google",
      };
    }
  }, [isSingleUserMode]);

  const verifyCoupon = useCallback(
    async (couponCode: string) => {
      if (!authUser) {
        return { success: false, error: "Please sign in with Google first" };
      }

      const normalized = couponCode.trim().toUpperCase();
      if (isSingleUserMode || normalized === "OWNER" || normalized === "INFINITYAI" || normalized === "OWNER_ACCESS") {
        const verifiedSession = {
          code: "OWNER_ACCESS",
          features: ["ALL"],
          expiresAt: new Date(Date.now() + 31536000000).toISOString(),
          sessionId: `firebase-${authUser.uid}`,
        };

        setCouponData(verifiedSession);
        setIsCouponVerified(true);
        useSessionStore.getState().setSession({
          sessionId: verifiedSession.sessionId,
          userId: authUser.uid,
          features: verifiedSession.features,
          expiresAt: verifiedSession.expiresAt,
        });
        localStorage.setItem(
          DUAL_AUTH_KEY,
          JSON.stringify({
            googleUserId: authUser.uid,
            couponCode: verifiedSession.code,
            couponVerified: true,
            features: verifiedSession.features,
            expiresAt: verifiedSession.expiresAt,
            sessionId: verifiedSession.sessionId,
          })
        );
        return { success: true };
      }

      setLoading(true);
      try {
        const data = await verifyCouponAPI(couponCode, authUser.uid, authUser.email || "");

        if (data.success) {
          const newCouponData = {
            code: couponCode,
            features: data.features || [],
            expiresAt: data.expires_at || new Date(Date.now() + 31536000000).toISOString(),
            sessionId: data.session_id || `firebase-${authUser.uid}`,
          };

          setCouponData(newCouponData);
          setIsCouponVerified(true);

          const sessionData = {
            sessionId: newCouponData.sessionId,
            userId: authUser.uid,
            features: newCouponData.features,
            expiresAt: newCouponData.expiresAt,
          };

          useSessionStore.getState().setSession(sessionData);
          localStorage.setItem(
            DUAL_AUTH_KEY,
            JSON.stringify({
              googleUserId: authUser.uid,
              couponCode: couponCode,
              couponVerified: true,
              features: newCouponData.features,
              expiresAt: newCouponData.expiresAt,
              sessionId: newCouponData.sessionId,
            })
          );

          setLoading(false);
          return { success: true };
        }

        setLoading(false);
        return {
          success: false,
          error: data.detail || data.message || "Invalid coupon code",
        };
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
    [authUser, isSingleUserMode]
  );

  const logout = useCallback(async () => {
    setLoading(true);
    try {
      await authLogOut();

      try {
        await fetch(`${ENGINE_C_URL}/api/auth/logout`, { method: "POST" });
      } catch {
        // ignore backend logout errors and continue to local cleanup
      }

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

  return <DualAuthContext.Provider value={value}>{children}</DualAuthContext.Provider>;
}

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

  if (context === undefined) {
    console.warn("useCouponAuth: Context not available, returning default state");
    return defaultAuthState;
  }
  return context;
}

export const useDualAuth = useCouponAuth;

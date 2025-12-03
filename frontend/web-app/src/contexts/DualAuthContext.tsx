'use client';

import React, { createContext, useContext, useEffect, useState, ReactNode, useCallback } from 'react';
import { User, onAuthStateChanged, signInWithPopup, signOut, GoogleAuthProvider } from 'firebase/auth';
import { auth, createOrUpdateUserProfile, getUserProfile, UserProfile } from '@/lib/firebase';

// Storage keys
const DUAL_AUTH_KEY = 'infinityai_dual_auth';
const STORAGE_VERSION_KEY = 'infinityai_version';
const CURRENT_VERSION = '4.0';

// Clear old storage on version mismatch
function clearOldStorage() {
  if (typeof window === 'undefined') return;
  const storedVersion = localStorage.getItem(STORAGE_VERSION_KEY);
  if (storedVersion !== CURRENT_VERSION) {
    console.log('Clearing old storage data for version upgrade to', CURRENT_VERSION);
    localStorage.removeItem(DUAL_AUTH_KEY);
    localStorage.removeItem('infinityai_coupon_session');
    localStorage.removeItem('infinityai_auth_type');
    localStorage.removeItem('infinityai_session');
    localStorage.removeItem('infinityai_user');
    localStorage.removeItem('infinityai-storage');
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

  firebaseUser: User | null;
  userProfile: UserProfile | null;

  // Auth methods - Step 1: Google Sign-In
  signInWithGoogle: () => Promise<{ success: boolean; error?: string }>;

  // Auth methods - Step 2: Coupon Verification
  verifyCoupon: (couponCode: string) => Promise<{ success: boolean; error?: string }>;

  // Logout (clears both)
  logout: () => Promise<void>;
  refreshSession: () => Promise<void>;

  // Dhan connection methods
  connectDhan: (clientId: string, accessToken: string) => Promise<{ success: boolean; error?: string }>;
  disconnectDhan: () => Promise<{ success: boolean; error?: string }>;
}

const DualAuthContext = createContext<DualAuthContextType | undefined>(undefined);

// Engine C URL for coupon verification
const ENGINE_C_URL = process.env.NEXT_PUBLIC_ENGINE_C_URL || 'https://engine-c-573866363639.us-central1.run.app';

export function CouponAuthProvider({ children }: { children: ReactNode }) {
  const [loading, setLoading] = useState(true);
  const [firebaseUser, setFirebaseUser] = useState<User | null>(null);
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [isCouponVerified, setIsCouponVerified] = useState(false);
  const [couponData, setCouponData] = useState<{
    code: string;
    features: string[];
    expiresAt: string;
    sessionId: string;
  } | null>(null);

  // Derived states
  const isGoogleSignedIn = !!firebaseUser;
  const isAuthenticated = isGoogleSignedIn && isCouponVerified;

  // Session and User for compatibility
  const session: CouponSession | null = isAuthenticated && firebaseUser ? {
    sessionId: couponData?.sessionId || firebaseUser.uid,
    userId: firebaseUser.uid,
    features: couponData?.features || [],
    expiresAt: couponData?.expiresAt || '',
    dhanConfigured: userProfile?.dhanConnected || false,
  } : null;

  const user: CouponUser | null = isAuthenticated && firebaseUser ? {
    userId: firebaseUser.uid,
    name: firebaseUser.displayName || userProfile?.displayName || 'User',
    email: firebaseUser.email || undefined,
    dhanConnected: userProfile?.dhanConnected || false,
    dhanClientId: userProfile?.dhanClientId,
    photoURL: firebaseUser.photoURL,
  } : null;

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
        console.warn('Auth loading safety timeout triggered');
        setLoading(false);
      }
    }, 5000);

    // Check for existing dual auth session
    const storedDualAuth = typeof window !== 'undefined' ? localStorage.getItem(DUAL_AUTH_KEY) : null;
    let storedCouponData: typeof couponData = null;

    if (storedDualAuth) {
      try {
        const parsed = JSON.parse(storedDualAuth);
        if (parsed.couponVerified && parsed.couponCode) {
          storedCouponData = {
            code: parsed.couponCode,
            features: parsed.features || [],
            expiresAt: parsed.expiresAt || '',
            sessionId: parsed.sessionId || '',
          };
        }
      } catch (e) {
        console.error('Failed to parse dual auth session:', e);
        localStorage.removeItem(DUAL_AUTH_KEY);
      }
    }

    // Listen for Firebase auth state changes
    const unsubscribe = onAuthStateChanged(auth, async (fbUser) => {
      if (!isMounted) return;
      clearTimeout(safetyTimeout);

      if (fbUser) {
        // User is signed in with Google
        try {
          const profile = await getUserProfile(fbUser.uid);
          if (isMounted) {
            setFirebaseUser(fbUser);
            setUserProfile(profile);

            // Restore coupon verification if exists for this user
            if (storedCouponData) {
              setCouponData(storedCouponData);
              setIsCouponVerified(true);
            }
          }
        } catch (error) {
          console.error('Error loading Firebase user profile:', error);
          if (isMounted) {
            setFirebaseUser(fbUser);
            if (storedCouponData) {
              setCouponData(storedCouponData);
              setIsCouponVerified(true);
            }
          }
        }
      } else {
        // No Firebase user - clear all auth
        if (isMounted) {
          setFirebaseUser(null);
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
      const provider = new GoogleAuthProvider();
      provider.setCustomParameters({ prompt: 'select_account' });

      const result = await signInWithPopup(auth, provider);
      const fbUser = result.user;

      // Create or update user profile in Firestore
      const profile = await createOrUpdateUserProfile(fbUser);

      setFirebaseUser(fbUser);
      setUserProfile(profile);

      setLoading(false);
      return { success: true };
    } catch (error) {
      console.error('Google sign-in error:', error);
      setLoading(false);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to sign in with Google'
      };
    }
  }, []);

  // Verify coupon code (Step 2 - requires Google sign-in first)
  const verifyCoupon = useCallback(async (couponCode: string) => {
    if (!firebaseUser) {
      return { success: false, error: 'Please sign in with Google first' };
    }

    setLoading(true);
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000);

      const response = await fetch(`${ENGINE_C_URL}/api/auth/coupon/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          coupon_code: couponCode,
          google_user_id: firebaseUser.uid,
          google_email: firebaseUser.email,
        }),
        signal: controller.signal,
      });
      clearTimeout(timeoutId);

      const data = await response.json();

      if (data.success) {
        const newCouponData = {
          code: couponCode,
          features: data.features || [],
          expiresAt: data.expires_at || '',
          sessionId: data.session_id || '',
        };

        setCouponData(newCouponData);
        setIsCouponVerified(true);

        // Store dual auth session
        localStorage.setItem(DUAL_AUTH_KEY, JSON.stringify({
          googleUserId: firebaseUser.uid,
          couponCode: couponCode,
          couponVerified: true,
          features: data.features || [],
          expiresAt: data.expires_at || '',
          sessionId: data.session_id || '',
        }));

        setLoading(false);
        return { success: true };
      } else {
        setLoading(false);
        return {
          success: false,
          error: data.detail || data.message || 'Invalid coupon code'
        };
      }
    } catch (error) {
      console.error('Coupon verification error:', error);
      setLoading(false);
      return {
        success: false,
        error: error instanceof Error && error.name === 'AbortError'
          ? 'Request timeout. Please try again.'
          : 'Failed to verify coupon. Please try again.'
      };
    }
  }, [firebaseUser]);

  // Logout (clears both Google and coupon)
  const logout = useCallback(async () => {
    setLoading(true);
    try {
      // Sign out from Firebase
      if (auth.currentUser) {
        await signOut(auth);
      }

      // Try to notify backend
      try {
        await fetch(`${ENGINE_C_URL}/api/auth/logout`, { method: 'POST' });
      } catch (e) {
        // Ignore errors
      }

      // Clear all auth storage
      localStorage.removeItem(DUAL_AUTH_KEY);
      localStorage.removeItem('infinityai_coupon_session');
      localStorage.removeItem('infinityai_auth_type');
      localStorage.removeItem('infinityai_session');
      localStorage.removeItem('infinityai_user');

      setFirebaseUser(null);
      setUserProfile(null);
      setIsCouponVerified(false);
      setCouponData(null);
    } catch (error) {
      console.error('Logout error:', error);
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
        console.error('Failed to refresh session:', error);
      }
    }
  }, [firebaseUser]);

  // Dhan connection placeholders
  const connectDhan = useCallback(async () => {
    return { success: false, error: 'Use settings page to connect Dhan' };
  }, []);

  const disconnectDhan = useCallback(async () => {
    return { success: false, error: 'Use settings page to disconnect Dhan' };
  }, []);

  const value: DualAuthContextType = {
    session,
    user,
    loading,
    isGoogleSignedIn,
    isCouponVerified,
    isAuthenticated,
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
  firebaseUser: null,
  userProfile: null,
  signInWithGoogle: async () => ({ success: false, error: 'Not initialized' }),
  verifyCoupon: async () => ({ success: false, error: 'Not initialized' }),
  logout: async () => {},
  refreshSession: async () => {},
  connectDhan: async () => ({ success: false, error: 'Not initialized' }),
  disconnectDhan: async () => ({ success: false, error: 'Not initialized' }),
};

export function useCouponAuth(): DualAuthContextType {
  const context = useContext(DualAuthContext);

  // If context is not available, return a safe default instead of throwing
  // This can happen during SSR, hydration, or if the provider isn't mounted yet
  if (context === undefined) {
    console.warn('useCouponAuth: Context not available, returning default state');
    return defaultAuthState;
  }
  return context;
}

// Alias for the hook
export const useDualAuth = useCouponAuth;

'use client';

import React, { createContext, useContext, useEffect, useState, ReactNode, useCallback } from 'react';
import { useAppStore } from '@/lib/store';
import { engineC } from '@/lib/api';

// Session stored in localStorage
const SESSION_KEY = 'infinityai_session';
const USER_KEY = 'infinityai_user';

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
}

interface CouponAuthContextType {
  session: CouponSession | null;
  user: CouponUser | null;
  loading: boolean;
  isAuthenticated: boolean;

  // Auth methods
  verifyCoupon: (couponCode: string) => Promise<{ success: boolean; error?: string }>;
  logout: () => Promise<void>;
  refreshSession: () => Promise<void>;

  // Dhan connection methods
  connectDhan: (clientId: string, accessToken: string) => Promise<{ success: boolean; error?: string }>;
  disconnectDhan: () => Promise<{ success: boolean; error?: string }>;
}

const CouponAuthContext = createContext<CouponAuthContextType | undefined>(undefined);

// API helper for coupon auth
const ENGINE_C_URL = process.env.NEXT_PUBLIC_ENGINE_C_URL || 'https://engine-c-573866363639.us-central1.run.app';

async function couponApi(endpoint: string, options: RequestInit = {}) {
  const sessionId = typeof window !== 'undefined' ? localStorage.getItem(SESSION_KEY) : null;

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  if (sessionId) {
    (headers as Record<string, string>)['X-Session-ID'] = sessionId;
  }

  // Add timeout to prevent hanging
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout

  try {
    const response = await fetch(`${ENGINE_C_URL}${endpoint}`, {
      ...options,
      headers,
      signal: controller.signal,
    });
    clearTimeout(timeoutId);
    return response.json();
  } catch (error) {
    clearTimeout(timeoutId);
    if (error instanceof Error && error.name === 'AbortError') {
      throw new Error('Request timeout');
    }
    throw error;
  }
}

export function CouponAuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<CouponSession | null>(null);
  const [user, setUser] = useState<CouponUser | null>(null);
  const [loading, setLoading] = useState(true);

  const { setUserProfile, clearUserData } = useAppStore();

  // Load session from localStorage on mount
  useEffect(() => {
    let isMounted = true;

    const loadSession = async () => {
      // Only run on client side
      if (typeof window === 'undefined') {
        if (isMounted) setLoading(false);
        return;
      }

      try {
        const storedSessionId = localStorage.getItem(SESSION_KEY);
        const storedUser = localStorage.getItem(USER_KEY);

        if (!storedSessionId) {
          // No session stored, nothing to validate
          if (isMounted) setLoading(false);
          return;
        }

        try {
          // Verify session with backend
          const response = await couponApi('/api/auth/session');

          if (!isMounted) return;

          if (response.success && response.is_valid) {
            const sessionData: CouponSession = {
              sessionId: response.session_id,
              userId: response.user_id,
              features: response.features || [],
              expiresAt: response.expires_at,
              dhanConfigured: response.dhan_configured || false,
            };

            setSession(sessionData);

            // Load user data if Dhan is connected
            if (response.dhan_configured) {
              try {
                const dematData = await engineC.getUserDemat(response.user_id);
                if (!isMounted) return;
                const userData: CouponUser = {
                  userId: response.user_id,
                  dhanConnected: true,
                  name: `User ${response.user_id.slice(0, 8)}`,
                };
                setUser(userData);

                // Sync with Zustand store
                setUserProfile({
                  userId: response.user_id,
                  clientId: '',
                  name: userData.name || 'User',
                  email: '',
                  isConnected: true,
                  isVerified: true,
                });
              } catch (e) {
                console.error('Failed to load Dhan data:', e);
              }
            } else if (storedUser) {
              try {
                const userData = JSON.parse(storedUser);
                if (isMounted) setUser(userData);
              } catch (e) {
                console.error('Failed to parse stored user:', e);
              }
            }
          } else {
            // Invalid session, clear storage
            localStorage.removeItem(SESSION_KEY);
            localStorage.removeItem(USER_KEY);
          }
        } catch (error) {
          console.error('Failed to verify session:', error);
          localStorage.removeItem(SESSION_KEY);
          localStorage.removeItem(USER_KEY);
        }
      } finally {
        // ALWAYS set loading to false
        if (isMounted) setLoading(false);
      }
    };

    loadSession();

    return () => {
      isMounted = false;
    };
  }, []); // Remove setUserProfile from dependencies to prevent re-runs

  const verifyCoupon = useCallback(async (couponCode: string) => {
    setLoading(true);

    try {
      const response = await couponApi('/api/auth/coupon/verify', {
        method: 'POST',
        body: JSON.stringify({ coupon_code: couponCode }),
      });

      if (response.success) {
        const sessionData: CouponSession = {
          sessionId: response.session_id,
          userId: response.user_id,
          features: response.features || [],
          expiresAt: response.expires_at,
          dhanConfigured: false,
        };

        // Store session
        localStorage.setItem(SESSION_KEY, response.session_id);
        setSession(sessionData);

        const userData: CouponUser = {
          userId: response.user_id,
          dhanConnected: false,
          name: `User ${response.user_id.slice(0, 8)}`,
        };
        localStorage.setItem(USER_KEY, JSON.stringify(userData));
        setUser(userData);

        setLoading(false);
        return { success: true };
      } else {
        setLoading(false);
        return { success: false, error: response.detail || response.message || 'Invalid coupon code' };
      }
    } catch (error) {
      setLoading(false);
      return { success: false, error: 'Failed to verify coupon. Please try again.' };
    }
  }, []);

  const logout = useCallback(async () => {
    setLoading(true);

    try {
      // Notify backend
      await couponApi('/api/auth/logout', { method: 'POST' });
    } catch (e) {
      console.error('Logout error:', e);
    }

    // Clear local storage
    localStorage.removeItem(SESSION_KEY);
    localStorage.removeItem(USER_KEY);

    // Clear state
    setSession(null);
    setUser(null);
    clearUserData();

    setLoading(false);
  }, [clearUserData]);

  const refreshSession = useCallback(async () => {
    const storedSessionId = localStorage.getItem(SESSION_KEY);
    if (!storedSessionId) return;

    try {
      const response = await couponApi('/api/auth/session');

      if (response.success && response.is_valid) {
        setSession({
          sessionId: response.session_id,
          userId: response.user_id,
          features: response.features || [],
          expiresAt: response.expires_at,
          dhanConfigured: response.dhan_configured || false,
        });
      }
    } catch (error) {
      console.error('Failed to refresh session:', error);
    }
  }, []);

  const connectDhan = useCallback(async (clientId: string, accessToken: string) => {
    if (!session?.userId) {
      return { success: false, error: 'No active session' };
    }

    try {
      const response = await engineC.saveUserCredentials({
        user_id: session.userId,
        client_id: clientId,
        access_token: accessToken,
      });

      if (response.is_verified) {
        // Update session
        setSession(prev => prev ? { ...prev, dhanConfigured: true } : null);

        // Update user
        const updatedUser: CouponUser = {
          ...user!,
          dhanConnected: true,
          dhanClientId: clientId,
        };
        setUser(updatedUser);
        localStorage.setItem(USER_KEY, JSON.stringify(updatedUser));

        // Sync with Zustand store
        setUserProfile({
          userId: session.userId,
          clientId: clientId,
          name: user?.name || 'User',
          email: user?.email || '',
          isConnected: true,
          isVerified: true,
        });

        return { success: true };
      } else {
        return { success: false, error: 'Failed to verify Dhan credentials. Please check your access token.' };
      }
    } catch (error) {
      console.error('Connect Dhan error:', error);
      return { success: false, error: 'Failed to connect Dhan account. Please try again.' };
    }
  }, [session, user, setUserProfile]);

  const disconnectDhan = useCallback(async () => {
    if (!session?.userId) {
      return { success: false, error: 'No active session' };
    }

    try {
      await engineC.deleteUserCredentials(session.userId);

      // Update session
      setSession(prev => prev ? { ...prev, dhanConfigured: false } : null);

      // Update user
      const updatedUser: CouponUser = {
        ...user!,
        dhanConnected: false,
        dhanClientId: undefined,
      };
      setUser(updatedUser);
      localStorage.setItem(USER_KEY, JSON.stringify(updatedUser));

      clearUserData();

      return { success: true };
    } catch (error) {
      console.error('Disconnect Dhan error:', error);
      return { success: false, error: 'Failed to disconnect Dhan account.' };
    }
  }, [session, user, clearUserData]);

  const value: CouponAuthContextType = {
    session,
    user,
    loading,
    isAuthenticated: !!session,
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
    throw new Error('useCouponAuth must be used within a CouponAuthProvider');
  }
  return context;
}

// Hook for requiring authentication
export function useRequireCouponAuth() {
  const { isAuthenticated, loading } = useCouponAuth();

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      // Could redirect to login page
      console.log('User not authenticated');
    }
  }, [isAuthenticated, loading]);

  return { isAuthenticated, loading };
}

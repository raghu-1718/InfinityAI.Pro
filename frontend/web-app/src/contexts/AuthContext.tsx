"use client";

import React, {
  createContext,
  useContext,
  useEffect,
  useState,
  ReactNode,
} from "react";
import type { User } from "@/lib/firebase";
import {
  onAuthChange,
  signInWithGoogle,
  logOut,
  getUserProfile,
} from "@/lib/firebase";
import type { UserProfile } from "@/lib/supabase";
import { supabase } from "@/lib/supabase";
import { useAppStore } from "@/lib/store";
import { engineC } from "@/lib/api";

interface AuthContextType {
  user: User | null;
  userProfile: UserProfile | null;
  loading: boolean;
  signIn: () => Promise<{ success: boolean; error?: string }>;
  signOut: () => Promise<{ success: boolean; error?: string }>;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);

  const {
    setUserProfile: setStoreUserProfile,
    setDhanConnected,
    clearUserData,
  } = useAppStore();

  // Listen to auth state changes
  useEffect(() => {
    const unsubscribe = onAuthChange(async (supabaseUser) => {
      setUser(supabaseUser);

      if (supabaseUser) {
        // Fetch user profile from Supabase
        const profile = await getUserProfile(supabaseUser.uid);
        setUserProfile(profile);

        // Sync with Zustand store
        if (profile) {
          setStoreUserProfile({
            userId: profile.uid,
            clientId: profile.dhanClientId || "",
            name: profile.displayName || "User",
            email: profile.email || "",
            isConnected: profile.dhanConnected,
            isVerified: profile.dhanConnected,
          });
        }

        // Poll for credential changes via Supabase instead of Firestore onSnapshot
        const checkCredentials = async () => {
          try {
            const { data } = await supabase
              .from("user_credentials")
              .select("broker_client_id")
              .eq("user_uid", supabaseUser.uid)
              .maybeSingle();

            const isConnected = !!data?.broker_client_id;
            setDhanConnected(isConnected);
            setStoreUserProfile((prev) =>
              prev
                ? {
                    ...prev,
                    isConnected,
                    isVerified: isConnected,
                  }
                : null,
            );
          } catch (error) {
            console.warn("Error checking credentials:", error);
          }
        };

        // Check immediately and set up polling
        checkCredentials();
        const credentialInterval = setInterval(checkCredentials, 30000); // Poll every 30s

        // Cleanup interval on unmount or user change
        const cleanup = () => clearInterval(credentialInterval);
        // Store cleanup for return
        (window as any).__authCredentialCleanup = cleanup;
      } else {
        setUserProfile(null);
        setDhanConnected(false);
        clearUserData();
      }

      setLoading(false);
    });

    return () => {
      unsubscribe();
      // Clean up credential polling
      if ((window as any).__authCredentialCleanup) {
        (window as any).__authCredentialCleanup();
      }
    };
  }, [setStoreUserProfile, setDhanConnected, clearUserData]);

  const signIn = async () => {
    setLoading(true);
    const result = await signInWithGoogle();

    if (result.success && result.user) {
      const profile = await getUserProfile(result.user.uid);
      setUserProfile(profile);

      // Sync with Zustand store
      if (profile) {
        setStoreUserProfile({
          userId: profile.uid,
          clientId: profile.dhanClientId || "",
          name: profile.displayName || "User",
          email: profile.email || "",
          isConnected: profile.dhanConnected,
          isVerified: profile.dhanConnected,
        });
      }
    }

    setLoading(false);
    return result;
  };

  const signOut = async () => {
    setLoading(true);

    // Delete Dhan credentials from backend if connected
    if (userProfile?.dhanConnected && user?.uid) {
      try {
        await engineC.deleteUserCredentials(user.uid);
      } catch (e) {
        console.error("Failed to delete Dhan credentials:", e);
      }
    }

    const result = await logOut();

    if (result.success) {
      setUser(null);
      setUserProfile(null);
      clearUserData();
    }

    setLoading(false);
    return result;
  };

  const refreshProfile = async () => {
    if (user) {
      const profile = await getUserProfile(user.uid);
      setUserProfile(profile);

      if (profile) {
        setStoreUserProfile({
          userId: profile.uid,
          clientId: profile.dhanClientId || "",
          name: profile.displayName || "User",
          email: profile.email || "",
          isConnected: profile.dhanConnected,
          isVerified: profile.dhanConnected,
        });
      }
    }
  };

  const value = {
    user,
    userProfile,
    loading,
    signIn,
    signOut,
    refreshProfile,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}

// Hook for checking if user is authenticated
export function useRequireAuth() {
  const { user, loading } = useAuth();

  useEffect(() => {
    if (!loading && !user) {
      // Could redirect to login page if needed
      console.log("User not authenticated");
    }
  }, [user, loading]);

  return { user, loading };
}

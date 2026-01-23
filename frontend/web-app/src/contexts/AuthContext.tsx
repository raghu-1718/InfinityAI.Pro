"use client";

import React, {
  createContext,
  useContext,
  useEffect,
  useState,
  ReactNode,
} from "react";
import { User } from "firebase/auth";
import {
  onAuthChange,
  signInWithGoogle,
  logOut,
  getUserProfile,
  UserProfile,
} from "@/lib/firebase";
import { useAppStore } from "@/lib/store";
import { engineC } from "@/lib/api";
import { db } from "@/lib/firebase/config";
import { doc, onSnapshot } from "firebase/firestore";

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
    const unsubscribe = onAuthChange(async (firebaseUser) => {
      setUser(firebaseUser);

      if (firebaseUser) {
        // Fetch user profile from Firestore
        const profile = await getUserProfile(firebaseUser.uid);
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

        // Listen to Dhan Credentials changes in real-time
        const credentialsRef = doc(db, "dhan_credentials", firebaseUser.uid);
        const unsubscribeCreds = onSnapshot(
          credentialsRef,
          (credSnapshot) => {
            if (credSnapshot.exists()) {
              const credData = credSnapshot.data();
              const isConnected = !!(
                credData.client_id && credData.access_token
              );

              // Update global state when credentials change
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
            } else {
              // No credentials document means disconnected
              setDhanConnected(false);
              setStoreUserProfile((prev) =>
                prev
                  ? {
                      ...prev,
                      isConnected: false,
                      isVerified: false,
                    }
                  : null,
              );
            }
          },
          (error) => {
            console.warn("Error listening to credentials:", error);
            // Silently continue - not a fatal error
          },
        );

        return () => {
          unsubscribeCreds();
        };
      } else {
        setUserProfile(null);
        setDhanConnected(false);
        clearUserData();
      }

      setLoading(false);
    });

    return () => unsubscribe();
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

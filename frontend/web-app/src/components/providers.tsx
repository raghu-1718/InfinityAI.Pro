"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { useState, useEffect, type ReactNode } from "react";
import { Toaster } from "@/components/ui/sonner";
import { CouponAuthProvider } from "@/contexts/DualAuthContext";
import { AuthProvider } from "@/contexts/AuthContext";
import { AblyProvider } from "@/contexts/AblyContext";
import { useAppStore } from "@/lib/store";
import { auth } from "@/lib/firebase/config";
import { onAuthStateChanged } from "firebase/auth";

// Hydrate Zustand store and listen for auth state changes
function StoreHydration() {
  const clearUserData = useAppStore((state) => state.clearUserData);

  useEffect(() => {
    useAppStore.persist.rehydrate();

    // Listen for Firebase Auth state changes
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      if (!user) {
        // User logged out, clear all user data from Zustand
        console.log("User logged out, clearing local state");
        clearUserData();
      }
    });

    return () => unsubscribe();
  }, [clearUserData]);

  return null;
}

export function Providers({ children }: { children: ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 30 * 1000,
            retry: 2,
            refetchOnWindowFocus: false,
          },
        },
      }),
  );

  return (
    <QueryClientProvider client={queryClient}>
      <StoreHydration />
      <AuthProvider>
        <AblyProvider>
          <CouponAuthProvider>{children}</CouponAuthProvider>
        </AblyProvider>
      </AuthProvider>
      <Toaster position="top-right" richColors />
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}

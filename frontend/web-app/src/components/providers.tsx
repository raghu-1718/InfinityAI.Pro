"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { useState, useEffect, type ReactNode } from "react";
import { Toaster } from "@/components/ui/sonner";
import { CouponAuthProvider } from "@/contexts/DualAuthContext";
import { AuthProvider } from "@/contexts/AuthContext";
import { useAppStore } from "@/lib/store";

// Hydrate Zustand store
function StoreHydration() {
  useEffect(() => {
    useAppStore.persist.rehydrate();
  }, []);

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
        <CouponAuthProvider>{children}</CouponAuthProvider>
      </AuthProvider>
      <Toaster position="top-right" richColors />
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}

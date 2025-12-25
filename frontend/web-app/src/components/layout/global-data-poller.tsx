'use client';

import { useEngineHealth, useUserAccount, useFunds, usePositions, useOrders, useUserProfile, useSignals } from '@/hooks/useApi';

/**
 * This component has no UI. Its sole purpose is to keep the global Zustand store
 * synchronized with the backend by calling the React Query hooks.
 * It should only be mounted within the authenticated Dashboard layout.
 */
export function GlobalDataPoller() {
  // 1. Engine Health (Critical for System Status)
  useEngineHealth();

  // 2. User Profile & Credentials (Dhan Connection Status)
  useUserProfile();

  // 3. Financial Data (Funds, Positions, Orders)
  // These internal hooks handle avoiding calls if user is not connected
  useFunds();
  usePositions(); // Real-time positions (10s)
  useOrders();    // Real-time orders (5s)
  
  // 4. Signals (For Auto-trading context)
  useSignals();

  return null; // Render nothing
}

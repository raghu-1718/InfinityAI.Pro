'use client';

import { useState, useEffect } from 'react';

/**
 * Hook to track hydration state for components that need to wait
 * for client-side data (like Zustand persisted state) to be available.
 *
 * This prevents hydration mismatch between SSR and client rendering.
 */
export function useHydration() {
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    // This runs after the first client render
    setHydrated(true);
  }, []);

  return hydrated;
}

/**
 * Hook that returns the value only after hydration is complete.
 * Before hydration, returns the fallback value.
 */
export function useHydratedValue<T>(value: T, fallback: T): T {
  const hydrated = useHydration();
  return hydrated ? value : fallback;
}

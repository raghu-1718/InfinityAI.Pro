/**
 * Ably Provider Context
 * Manages global Ably client initialization and connection state
 */

"use client";

import React, {
  createContext,
  useContext,
  useEffect,
  useState,
  ReactNode,
} from "react";
import * as Ably from "ably";
import {
  initializeAblyClient,
  getConnectionState,
  closeAblyConnection,
} from "@/lib/ably";

interface AblyContextType {
  connectionState: Ably.Types.ConnectionState | "disconnected";
  isConnected: boolean;
  error: Ably.Types.ErrorInfo | null;
}

const AblyContext = createContext<AblyContextType | undefined>(undefined);

export function AblyProvider({ children }: { children: ReactNode }) {
  const [connectionState, setConnectionState] = useState<
    Ably.Types.ConnectionState | "disconnected"
  >("connecting");
  const [error, setError] = useState<Ably.Types.ErrorInfo | null>(null);

  useEffect(() => {
    try {
      // Initialize Ably client
      const client = initializeAblyClient();

      // If Ably is not configured, set disconnected state and return
      if (!client) {
        setConnectionState("disconnected");
        return;
      }

      // Monitor connection state
      const handleStateChange = (
        stateChange: Ably.Types.ConnectionStateChange,
      ) => {
        setConnectionState(stateChange.current);

        if (stateChange.current === "failed") {
          setError(stateChange.reason || null);
          console.error("Ably connection failed:", stateChange.reason);
        } else if (
          stateChange.current === "connected" ||
          stateChange.current === "open"
        ) {
          setError(null);
          console.log("Ably connected successfully");
        }
      };

      client.connection.on(handleStateChange);

      // Cleanup on unmount
      return () => {
        client.connection.off(handleStateChange);
        closeAblyConnection();
      };
    } catch (err) {
      console.error("Failed to initialize Ably:", err);
      setError(
        err instanceof Ably.Types.ErrorInfo
          ? err
          : new Ably.Types.ErrorInfo({
              message: `Failed to initialize Ably: ${String(err)}`,
              code: 50000,
            }),
      );
    }
  }, []);

  const isConnected =
    connectionState === "connected" || connectionState === "open";

  return (
    <AblyContext.Provider value={{ connectionState, isConnected, error }}>
      {children}
    </AblyContext.Provider>
  );
}

/**
 * Hook to access Ably context
 */
export function useAblyContext() {
  const context = useContext(AblyContext);
  if (!context) {
    throw new Error("useAblyContext must be used within AblyProvider");
  }
  return context;
}

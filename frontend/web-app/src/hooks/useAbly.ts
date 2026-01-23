/**
 * React Hooks for Ably Real-Time Integration
 * Provides easy-to-use hooks for subscribing to real-time data
 */

"use client";

import { useEffect, useCallback, useRef, useState } from "react";
import * as Ably from "ably";
import {
  getAblyClient,
  subscribeToChannel,
  subscribeToChannelState,
  ABLY_CHANNELS,
} from "@/lib/ably";

/**
 * Hook to subscribe to Ably channel messages
 */
export function useAblyChannel<T = any>(
  channelName: string,
  onMessage?: (data: T) => void,
) {
  const [connectionState, setConnectionState] =
    useState<Ably.Types.ConnectionState>("connecting");
  const [error, setError] = useState<Ably.Types.ErrorInfo | null>(null);
  const unsubscribeRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    try {
      // Subscribe to channel messages
      unsubscribeRef.current = subscribeToChannel(
        channelName,
        (message) => {
          if (onMessage) {
            onMessage(message.data as T);
          }
        },
        (err) => {
          setError(err);
        },
      );

      // Subscribe to connection state changes
      const client = getAblyClient();
      const unsubscribeState = subscribeToChannelState(
        channelName,
        (stateChange) => {
          setConnectionState(stateChange.current);
          if (stateChange.current === "failed") {
            setError(stateChange.reason || undefined);
          }
        },
      );

      // Also watch main connection state
      const connectionStateHandler = (
        stateChange: Ably.Types.ConnectionStateChange,
      ) => {
        setConnectionState(stateChange.current);
      };
      client.connection.on(connectionStateHandler);

      return () => {
        if (unsubscribeRef.current) {
          unsubscribeRef.current();
        }
        unsubscribeState();
        client.connection.off(connectionStateHandler);
      };
    } catch (err) {
      console.error(`Failed to subscribe to channel ${channelName}:`, err);
      setError(
        err instanceof Ably.Types.ErrorInfo
          ? err
          : new Ably.Types.ErrorInfo({ message: String(err) }),
      );
    }
  }, [channelName, onMessage]);

  return { connectionState, error };
}

/**
 * Hook for market data real-time updates
 */
export function useMarketData(
  onUpdate?: (data: {
    symbol: string;
    price: number;
    bid: number;
    ask: number;
    timestamp: number;
  }) => void,
) {
  return useAblyChannel(ABLY_CHANNELS.LIVE_QUOTES, onUpdate);
}

/**
 * Hook for trading signals
 */
export function useTradingSignals(
  engineId?: string,
  onSignal?: (signal: {
    engineId: string;
    symbol: string;
    action: "BUY" | "SELL" | "HOLD";
    confidence: number;
    reason: string;
    timestamp: number;
  }) => void,
) {
  const channelName = engineId
    ? ABLY_CHANNELS.ENGINE_STATUS(engineId)
    : ABLY_CHANNELS.TRADING_SIGNALS;

  return useAblyChannel(channelName, onSignal);
}

/**
 * Hook for trade execution updates
 */
export function useTradeExecution(
  onExecution?: (trade: {
    tradeId: string;
    symbol: string;
    quantity: number;
    price: number;
    type: "BUY" | "SELL";
    status: "PENDING" | "EXECUTED" | "FAILED";
    timestamp: number;
  }) => void,
) {
  return useAblyChannel(ABLY_CHANNELS.TRADE_EXECUTION, onExecution);
}

/**
 * Hook for portfolio updates
 */
export function usePortfolioUpdates(
  userId?: string,
  onUpdate?: (portfolio: {
    totalValue: number;
    buyingPower: number;
    positions: Array<{
      symbol: string;
      quantity: number;
      avgPrice: number;
      currentPrice: number;
    }>;
    timestamp: number;
  }) => void,
) {
  const channelName = userId
    ? ABLY_CHANNELS.USER_PORTFOLIO(userId)
    : ABLY_CHANNELS.PORTFOLIO_UPDATE;

  return useAblyChannel(channelName, onUpdate);
}

/**
 * Hook for user notifications
 */
export function useNotifications(
  userId?: string,
  onNotification?: (notification: {
    id: string;
    type: "info" | "warning" | "error" | "success";
    title: string;
    message: string;
    timestamp: number;
  }) => void,
) {
  const channelName = userId
    ? ABLY_CHANNELS.USER_NOTIFICATIONS
    : ABLY_CHANNELS.USER_NOTIFICATIONS;

  return useAblyChannel(channelName, onNotification);
}

/**
 * Hook for system status
 */
export function useSystemStatus(
  onStatusChange?: (status: {
    isOnline: boolean;
    engines: {
      [key: string]: {
        status: "operational" | "degraded" | "down";
        lastHeartbeat: number;
      };
    };
    latency: number;
  }) => void,
) {
  return useAblyChannel(ABLY_CHANNELS.SYSTEM_STATUS, onStatusChange);
}

/**
 * Hook to monitor Ably connection
 */
export function useAblyConnection() {
  const [connectionState, setConnectionState] =
    useState<Ably.Types.ConnectionState>("connecting");
  const [error, setError] = useState<Ably.Types.ErrorInfo | null>(null);

  useEffect(() => {
    try {
      const client = getAblyClient();

      const handleStateChange = (
        stateChange: Ably.Types.ConnectionStateChange,
      ) => {
        setConnectionState(stateChange.current);
        if (stateChange.current === "failed") {
          setError(stateChange.reason || undefined);
        } else if (
          stateChange.current === "connected" ||
          stateChange.current === "open"
        ) {
          setError(null);
        }
      };

      client.connection.on(handleStateChange);

      return () => {
        client.connection.off(handleStateChange);
      };
    } catch (err) {
      console.error("Failed to monitor Ably connection:", err);
      setError(
        err instanceof Ably.Types.ErrorInfo
          ? err
          : new Ably.Types.ErrorInfo({ message: String(err) }),
      );
    }
  }, []);

  const isConnected =
    connectionState === "connected" || connectionState === "open";

  return { connectionState, error, isConnected };
}

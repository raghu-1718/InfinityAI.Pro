/**
 * useRealtimeTrading Hook
 *
 * Real-time Server-Sent Events (SSE) hook for live trading updates
 * Connects to Engine-C SSE endpoint for real-time order, trade, and position updates
 *
 * Features:
 * - Auto-reconnect on connection loss
 * - Heartbeat monitoring
 * - Event type filtering
 * - Connection status tracking
 * - Error handling
 *
 * Usage:
 * ```tsx
 * const { connected, latestUpdate, events } = useRealtimeTrading(userId);
 * ```
 */

import { useState, useEffect, useCallback, useRef } from "react";

// Engine-C Service URL
const ENGINE_C_URL =
  process.env.NEXT_PUBLIC_ENGINE_C_URL ||
  "https://engine-c-r2f5flt77q-uc.a.run.app";

export interface TradeEvent {
  event:
    | "order_update"
    | "position_update"
    | "trade_update"
    | "heartbeat"
    | "connected";
  data: {
    order_id?: string;
    symbol?: string;
    status?: string;
    side?: string;
    price?: number;
    quantity?: number;
    filled_qty?: number;
    client_id?: string;
    timestamp: string;
    [key: string]: any;
  };
  timestamp: string;
}

export interface UseRealtimeTradingResult {
  connected: boolean;
  connecting: boolean;
  error: string | null;
  latestUpdate: TradeEvent | null;
  events: TradeEvent[];
  eventCount: number;
  lastHeartbeat: Date | null;
  reconnect: () => void;
  clearEvents: () => void;
}

export function useRealtimeTrading(
  userId: string,
  options?: {
    maxEvents?: number;
    autoReconnect?: boolean;
    reconnectDelay?: number;
  },
): UseRealtimeTradingResult {
  const {
    maxEvents = 100,
    autoReconnect = true,
    reconnectDelay = 3000,
  } = options || {};

  const [connected, setConnected] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [latestUpdate, setLatestUpdate] = useState<TradeEvent | null>(null);
  const [events, setEvents] = useState<TradeEvent[]>([]);
  const [lastHeartbeat, setLastHeartbeat] = useState<Date | null>(null);

  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);

  const clearEvents = useCallback(() => {
    setEvents([]);
    setLatestUpdate(null);
  }, []);

  const connectToSSE = useCallback(() => {
    if (!userId) {
      setError("User ID is required");
      return;
    }

    // Close existing connection if any
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }

    setConnecting(true);
    setError(null);

    try {
      const url = `${ENGINE_C_URL}/api/realtime/stream/${userId}`;
      console.log(`🔌 Connecting to real-time stream: ${url}`);

      const eventSource = new EventSource(url);
      eventSourceRef.current = eventSource;

      // Connection opened
      eventSource.addEventListener("open", () => {
        console.log("✅ Real-time connection established");
        setConnected(true);
        setConnecting(false);
        setError(null);
        reconnectAttemptsRef.current = 0;
      });

      // Connected event
      eventSource.addEventListener("connected", (event) => {
        console.log("📡 Server confirmed connection");
        const data = JSON.parse(event.data);
        const tradeEvent: TradeEvent = {
          event: "connected",
          data,
          timestamp: new Date().toISOString(),
        };
        setLatestUpdate(tradeEvent);
      });

      // Heartbeat event
      eventSource.addEventListener("heartbeat", (event) => {
        setLastHeartbeat(new Date());
        console.log("💓 Heartbeat received");
      });

      // Order update event
      eventSource.addEventListener("order_update", (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log("📊 Order Update:", data);

          const tradeEvent: TradeEvent = {
            event: "order_update",
            data,
            timestamp: data.timestamp || new Date().toISOString(),
          };

          setLatestUpdate(tradeEvent);
          setEvents((prev) => [tradeEvent, ...prev.slice(0, maxEvents - 1)]);
        } catch (err) {
          console.error("Failed to parse order_update:", err);
        }
      });

      // Position update event
      eventSource.addEventListener("position_update", (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log("📈 Position Update:", data);

          const tradeEvent: TradeEvent = {
            event: "position_update",
            data,
            timestamp: data.timestamp || new Date().toISOString(),
          };

          setLatestUpdate(tradeEvent);
          setEvents((prev) => [tradeEvent, ...prev.slice(0, maxEvents - 1)]);
        } catch (err) {
          console.error("Failed to parse position_update:", err);
        }
      });

      // Trade update event
      eventSource.addEventListener("trade_update", (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log("💹 Trade Update:", data);

          const tradeEvent: TradeEvent = {
            event: "trade_update",
            data,
            timestamp: data.timestamp || new Date().toISOString(),
          };

          setLatestUpdate(tradeEvent);
          setEvents((prev) => [tradeEvent, ...prev.slice(0, maxEvents - 1)]);
        } catch (err) {
          console.error("Failed to parse trade_update:", err);
        }
      });

      // Connection error
      eventSource.addEventListener("error", (event) => {
        console.error("❌ Real-time connection error:", event);
        setConnected(false);
        setConnecting(false);

        // Auto-reconnect logic
        if (autoReconnect && reconnectAttemptsRef.current < 10) {
          const delay = Math.min(
            reconnectDelay * Math.pow(2, reconnectAttemptsRef.current),
            30000,
          );
          console.log(
            `🔄 Reconnecting in ${delay}ms (attempt ${reconnectAttemptsRef.current + 1}/10)...`,
          );

          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttemptsRef.current += 1;
            connectToSSE();
          }, delay);
        } else {
          setError("Connection lost. Please refresh the page.");
        }
      });
    } catch (err) {
      console.error("Failed to create SSE connection:", err);
      setError(err instanceof Error ? err.message : "Failed to connect");
      setConnecting(false);
    }
  }, [userId, autoReconnect, reconnectDelay, maxEvents]);

  const reconnect = useCallback(() => {
    reconnectAttemptsRef.current = 0;
    connectToSSE();
  }, [connectToSSE]);

  // Initialize connection on mount
  useEffect(() => {
    if (userId) {
      connectToSSE();
    }

    // Cleanup on unmount
    return () => {
      if (eventSourceRef.current) {
        console.log("🔌 Closing real-time connection");
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
    };
  }, [userId, connectToSSE]);

  return {
    connected,
    connecting,
    error,
    latestUpdate,
    events,
    eventCount: events.length,
    lastHeartbeat,
    reconnect,
    clearEvents,
  };
}

/**
 * Lightweight hook for monitoring connection status only
 */
export function useRealtimeConnectionStatus(userId: string) {
  const { connected, connecting, error, lastHeartbeat } = useRealtimeTrading(
    userId,
    {
      maxEvents: 1, // Don't store events
    },
  );

  return { connected, connecting, error, lastHeartbeat };
}

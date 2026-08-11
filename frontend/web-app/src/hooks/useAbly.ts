import { useEffect, useState, useRef } from "react";
import { API_CONFIG } from "@/lib/api";

// Assuming we have user_id stored somewhere or passed in
// For now, defaulting to 'default_user' if not provided
const DEFAULT_USER_ID = "default_user";

export function useTradingSignals(engineId?: string, callback?: (signal: any) => void) {
  const [connectionState, setConnectionState] = useState("disconnected");
  const [error, setError] = useState<Error | null>(null);

  // Use REST/SSE polling since signals aren't in WS yet
  return { connectionState, error };
}

export function usePortfolioUpdates(userId: string, callback?: (update: any) => void) {
  const [connectionState, setConnectionState] = useState("disconnected");
  const [error, setError] = useState<Error | null>(null);
  const ws = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!userId) return;

    try {
      // API_CONFIG.EXECUTION_URL is https://engine-c-...
      // Convert to wss://
      const wsUrl = API_CONFIG.EXECUTION_URL.replace(/^http/, "ws") + `/api/ws/order-updates?user_id=${userId}`;
      ws.current = new WebSocket(wsUrl);

      ws.current.onopen = () => setConnectionState("connected");
      ws.current.onclose = () => setConnectionState("disconnected");
      ws.current.onerror = (e) => {
        console.error("WebSocket Error (Portfolio):", e);
        setError(new Error("WebSocket Error"));
      };

      ws.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'order_update' && callback) {
          callback(data.data);
        }
      };
    } catch (err) {
      console.error(err);
      setError(err as Error);
    }

    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [userId, callback]);

  return { connectionState, error };
}

export function useMarketData(symbols: string[], callback?: (data: any) => void) {
  const [connectionState, setConnectionState] = useState("disconnected");
  const [error, setError] = useState<Error | null>(null);
  const ws = useRef<WebSocket | null>(null);

  useEffect(() => {
    try {
      const wsUrl = API_CONFIG.EXECUTION_URL.replace(/^http/, "ws") + `/api/ws/market-feed?user_id=${DEFAULT_USER_ID}`;
      ws.current = new WebSocket(wsUrl);

      ws.current.onopen = () => {
        setConnectionState("connected");
        // Subscribe to symbols
        if (symbols.length > 0 && ws.current) {
          ws.current.send(JSON.stringify({
            type: "subscribe",
            instruments: symbols
          }));
        }
      };

      ws.current.onclose = () => setConnectionState("disconnected");
      ws.current.onerror = (e) => {
        console.error("WebSocket Error (Market):", e);
        setError(new Error("WebSocket Error"));
      };

      ws.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'market_tick' && callback) {
          callback(data.data);
        }
      };
    } catch (err) {
      console.error(err);
      setError(err as Error);
    }

    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [symbols.join(','), callback]);

  return { connectionState, error };
}

export function useTradeExecution(callback?: (execution: any) => void) {
  // Similar to portfolio updates, reusing the same logic or could be a different topic
  return { connectionState: "disconnected", error: null };
}

/**
 * Real-Time Trading Signals Component
 * Displays AI trading signals with live updates
 */

"use client";

import React, { useState, useCallback } from "react";
import { useTradingSignals } from "@/hooks/useAbly";
import { AlertCircle, TrendingUp, AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";

interface Signal {
  engineId: string;
  symbol: string;
  action: "BUY" | "SELL" | "HOLD";
  confidence: number;
  reason: string;
  timestamp: number;
  id?: string;
}

interface TradingSignalsProps {
  engineId?: string;
}

export function TradingSignals({ engineId }: TradingSignalsProps) {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [maxSignals] = useState(10);

  const { connectionState, error } = useTradingSignals(engineId, (signal) => {
    setSignals((prev) => [
      {
        ...signal,
        id: `${signal.engineId}-${signal.timestamp}`,
      },
      ...prev.slice(0, maxSignals - 1),
    ]);
  });

  const isConnected =
    connectionState === "connected" || connectionState === "open";

  const getActionColor = (action: string) => {
    switch (action) {
      case "BUY":
        return "text-green-600 bg-green-50";
      case "SELL":
        return "text-red-600 bg-red-50";
      case "HOLD":
        return "text-yellow-600 bg-yellow-50";
      default:
        return "text-gray-600 bg-gray-50";
    }
  };

  const getActionIcon = (action: string) => {
    switch (action) {
      case "BUY":
        return <TrendingUp className="w-5 h-5 text-green-600" />;
      case "SELL":
        return <AlertTriangle className="w-5 h-5 text-red-600" />;
      case "HOLD":
        return <AlertCircle className="w-5 h-5 text-yellow-600" />;
      default:
        return null;
    }
  };

  return (
    <div className="w-full">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold">Trading Signals</h2>
        {!isConnected && (
          <span className="text-sm text-yellow-600">
            Connecting to signals...
          </span>
        )}
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-600">
            Connection Error: {error.message}
          </p>
        </div>
      )}

      <div className="space-y-3">
        {signals.map((signal) => (
          <div
            key={signal.id}
            className={cn(
              "p-4 border rounded-lg transition-all hover:shadow-lg",
              getActionColor(signal.action),
            )}
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex items-start gap-3 flex-1">
                {getActionIcon(signal.action)}
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold text-lg">{signal.symbol}</h3>
                    <span className="font-bold uppercase text-sm">
                      {signal.action}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600">{signal.reason}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    Engine: {signal.engineId}
                  </p>
                </div>
              </div>

              <div className="text-right">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-sm font-semibold">Confidence</span>
                  <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className={cn(
                        "h-full transition-all",
                        signal.confidence >= 0.7
                          ? "bg-green-600"
                          : signal.confidence >= 0.5
                            ? "bg-yellow-600"
                            : "bg-red-600",
                      )}
                      style={{ width: `${signal.confidence * 100}%` }}
                    />
                  </div>
                </div>
                <p className="text-sm font-bold">
                  {(signal.confidence * 100).toFixed(0)}%
                </p>
                <p className="text-xs text-gray-500 mt-2">
                  {new Date(signal.timestamp).toLocaleTimeString()}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {signals.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          <p>No trading signals yet</p>
          <p className="text-sm">
            Waiting for AI signals from trading engines...
          </p>
        </div>
      )}
    </div>
  );
}

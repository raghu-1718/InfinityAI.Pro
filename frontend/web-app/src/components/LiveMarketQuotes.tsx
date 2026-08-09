/**
 * Real-Time Market Data Component
 * Displays live market quotes with Ably streaming
 */

"use client";

import React, { useState, useCallback } from "react";
import { useMarketData } from "@/hooks/useAbly";
import { TrendingUp, TrendingDown, Wifi, WifiOff } from "lucide-react";
import { cn } from "@/lib/utils";

interface Quote {
  symbol: string;
  price: number;
  bid: number;
  ask: number;
  timestamp: number;
  change?: number;
  changePercent?: number;
}

export function LiveMarketQuotes() {
  const [quotes, setQuotes] = useState<Map<string, Quote>>(new Map());
  const { connectionState, error } = useMarketData(['NIFTY', 'BANKNIFTY'], (data: any) => {
    setQuotes((prev) => {
      const updated = new Map(prev);
      updated.set(data.symbol, {
        ...data,
        change: updated.get(data.symbol)
          ? data.price - (updated.get(data.symbol)?.price || 0)
          : 0,
        changePercent: updated.get(data.symbol)
          ? ((data.price - (updated.get(data.symbol)?.price || 0)) /
              (updated.get(data.symbol)?.price || 1)) *
            100
          : 0,
      });
      return updated;
    });
  });

  const isConnected =
    connectionState === "connected" || connectionState === "open";

  return (
    <div className="w-full">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold">Live Market Data</h2>
        <div className="flex items-center gap-2">
          {isConnected ? (
            <div className="flex items-center gap-1 text-green-600">
              <Wifi className="w-4 h-4" />
              <span className="text-sm">Connected</span>
            </div>
          ) : (
            <div className="flex items-center gap-1 text-red-600">
              <WifiOff className="w-4 h-4" />
              <span className="text-sm">Connecting...</span>
            </div>
          )}
        </div>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-600">
            Connection Error: {(error as any)?.message || String(error)}
          </p>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {Array.from(quotes.values()).map((quote) => (
          <div
            key={quote.symbol}
            className="p-4 border rounded-lg hover:shadow-lg transition-shadow"
          >
            <div className="flex justify-between items-start mb-2">
              <h3 className="font-semibold text-lg">{quote.symbol}</h3>
              {(quote.change || 0) >= 0 ? (
                <TrendingUp className="w-5 h-5 text-green-600" />
              ) : (
                <TrendingDown className="w-5 h-5 text-red-600" />
              )}
            </div>

            <div className="mb-3">
              <p className="text-2xl font-bold">₹{quote.price.toFixed(2)}</p>
              <p
                className={cn(
                  "text-sm",
                  (quote.change || 0) >= 0 ? "text-green-600" : "text-red-600",
                )}
              >
                {(quote.change || 0) >= 0 ? "+" : ""}
                {quote.change?.toFixed(2)} ({quote.changePercent?.toFixed(2)}%)
              </p>
            </div>

            <div className="flex gap-4 text-sm">
              <div>
                <p className="text-gray-600">Bid</p>
                <p className="font-semibold">₹{quote.bid.toFixed(2)}</p>
              </div>
              <div>
                <p className="text-gray-600">Ask</p>
                <p className="font-semibold">₹{quote.ask.toFixed(2)}</p>
              </div>
            </div>

            <p className="text-xs text-gray-500 mt-2">
              {new Date(quote.timestamp).toLocaleTimeString()}
            </p>
          </div>
        ))}
      </div>

      {quotes.size === 0 && (
        <div className="text-center py-12 text-gray-500">
          <p>Waiting for market data...</p>
        </div>
      )}
    </div>
  );
}

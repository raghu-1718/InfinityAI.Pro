/**
 * Real-Time Portfolio Updates Component
 * Displays live portfolio changes with Ably streaming
 */

"use client";

import React, { useState } from "react";
import { usePortfolioUpdates } from "@/hooks/useAbly";
import { TrendingUp, TrendingDown } from "lucide-react";
import { cn } from "@/lib/utils";

interface Position {
  symbol: string;
  quantity: number;
  avgPrice: number;
  currentPrice: number;
}

interface PortfolioData {
  totalValue: number;
  buyingPower: number;
  positions: Position[];
  timestamp: number;
}

interface PortfolioUpdatesProps {
  userId?: string;
}

export function PortfolioUpdates({ userId }: PortfolioUpdatesProps) {
  const [portfolio, setPortfolio] = useState<PortfolioData | null>(null);
  const [previousValue, setPreviousValue] = useState<number | null>(null);

  const { connectionState, error } = usePortfolioUpdates(userId || "", (data) => {
    setPreviousValue(portfolio?.totalValue || null);
    setPortfolio(data);
  });

  const isConnected =
    connectionState === "connected" || connectionState === "open";
  const change = previousValue ? portfolio?.totalValue || 0 - previousValue : 0;
  const changePercent = previousValue ? (change / previousValue) * 100 : 0;

  return (
    <div className="w-full space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Portfolio</h2>
        {!isConnected && (
          <span className="text-sm text-yellow-600">Updating...</span>
        )}
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-600">
            Connection Error: {(error as any)?.message || String(error)}
          </p>
        </div>
      )}

      {portfolio ? (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Total Value */}
            <div className="p-4 border rounded-lg bg-gradient-to-br from-blue-50 to-blue-100">
              <p className="text-sm text-gray-600 mb-1">
                Total Portfolio Value
              </p>
              <div className="flex items-end justify-between">
                <div>
                  <p className="text-3xl font-bold">
                    ₹{(portfolio.totalValue || 0).toLocaleString()}
                  </p>
                  <p
                    className={cn(
                      "text-sm mt-1",
                      change >= 0 ? "text-green-600" : "text-red-600",
                    )}
                  >
                    {change >= 0 ? "+" : ""}
                    {change.toLocaleString()} ({changePercent.toFixed(2)}%)
                  </p>
                </div>
                {change >= 0 ? (
                  <TrendingUp className="w-6 h-6 text-green-600" />
                ) : (
                  <TrendingDown className="w-6 h-6 text-red-600" />
                )}
              </div>
            </div>

            {/* Buying Power */}
            <div className="p-4 border rounded-lg bg-gradient-to-br from-green-50 to-green-100">
              <p className="text-sm text-gray-600 mb-1">
                Available Buying Power
              </p>
              <p className="text-3xl font-bold">
                ₹{(portfolio.buyingPower || 0).toLocaleString()}
              </p>
              <p className="text-xs text-gray-500 mt-2">
                {(
                  ((portfolio.buyingPower || 0) / (portfolio.totalValue || 1)) *
                  100
                ).toFixed(1)}
                % of portfolio
              </p>
            </div>
          </div>

          {/* Positions */}
          <div>
            <h3 className="text-lg font-semibold mb-3">Current Positions</h3>
            <div className="space-y-2">
              {portfolio.positions && portfolio.positions.length > 0 ? (
                portfolio.positions.map((position) => {
                  const positionValue =
                    position.quantity * position.currentPrice;
                  const gainLoss =
                    (position.currentPrice - position.avgPrice) *
                    position.quantity;
                  const gainLossPercent =
                    ((position.currentPrice - position.avgPrice) /
                      position.avgPrice) *
                    100;

                  return (
                    <div
                      key={position.symbol}
                      className="p-3 border rounded-lg hover:shadow-md transition-shadow"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <h4 className="font-semibold">{position.symbol}</h4>
                          <p className="text-sm text-gray-600">
                            {position.quantity} shares @ ₹
                            {position.avgPrice.toFixed(2)} avg
                          </p>
                        </div>

                        <div className="text-right">
                          <p className="font-semibold">
                            ₹{positionValue.toLocaleString()}
                          </p>
                          <p
                            className={cn(
                              "text-sm",
                              gainLoss >= 0 ? "text-green-600" : "text-red-600",
                            )}
                          >
                            {gainLoss >= 0 ? "+" : ""}
                            {gainLoss.toLocaleString()} (
                            {gainLossPercent.toFixed(2)}%)
                          </p>
                        </div>
                      </div>

                      {/* Position details */}
                      <div className="flex gap-4 text-xs text-gray-500 mt-2">
                        <span>
                          Current: ₹{position.currentPrice.toFixed(2)}
                        </span>
                      </div>
                    </div>
                  );
                })
              ) : (
                <p className="text-center py-8 text-gray-500">
                  No positions held
                </p>
              )}
            </div>
          </div>

          <p className="text-xs text-gray-500 text-right">
            Updated: {new Date(portfolio.timestamp).toLocaleTimeString()}
          </p>
        </>
      ) : (
        <div className="text-center py-12 text-gray-500">
          <p>Loading portfolio data...</p>
        </div>
      )}
    </div>
  );
}

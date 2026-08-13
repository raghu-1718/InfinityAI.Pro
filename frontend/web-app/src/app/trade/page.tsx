"use client";

import { useState } from "react";
import { useAuth } from "@/contexts/AuthContext";

export default function AutomatedTradingPage() {
  const { user } = useAuth();
  const [assetClass, setAssetClass] = useState("options");
  const [strategy, setStrategy] = useState("iron_condor");
  const [symbol, setSymbol] = useState("NIFTY");
  const [capital, setCapital] = useState(100000);
  const [riskPercent, setRiskPercent] = useState(2);
  const [profitTarget, setProfitTarget] = useState(5);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const executeStrategy = async () => {
    if (!user) {
      setError("Please sign in to execute strategies");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        "https://engine-c-313407263327.asia-south1.run.app/api/strategies/execute",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-User-ID": user.uid,
          },
          body: JSON.stringify({
            asset_class: assetClass,
            strategy,
            symbol,
            capital,
            risk_percent: riskPercent,
            profit_target: profitTarget,
          }),
        },
      );

      if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`);
      }

      const data = await response.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message || "Strategy execution failed");
      console.error("Strategy execution error:", err);
    } finally {
      setLoading(false);
    }
  };

  const strategyOptions = {
    options: [
      {
        value: "iron_condor",
        label: "Iron Condor",
        description: "4-leg neutral strategy",
      },
      {
        value: "bull_call_spread",
        label: "Bull Call Spread",
        description: "Bullish spread",
      },
      {
        value: "bear_put_spread",
        label: "Bear Put Spread",
        description: "Bearish spread",
      },
      {
        value: "covered_call",
        label: "Covered Call",
        description: "Income generation",
      },
      { value: "straddle", label: "Straddle", description: "Volatility play" },
      {
        value: "strangle",
        label: "Strangle",
        description: "Wide volatility play",
      },
    ],
    equities: [
      { value: "rsi", label: "RSI Strategy", description: "Mean reversion" },
      {
        value: "ma_crossover",
        label: "MA Crossover",
        description: "Trend following",
      },
      {
        value: "hybrid",
        label: "Hybrid Selector",
        description: "Multi-strategy",
      },
    ],
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-6">
      <div className="container mx-auto max-w-6xl">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Automated Trading
          </h1>
          <p className="text-gray-600">
            Configure and execute trading strategies with automated position
            sizing
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Configuration Panel */}
          <div className="lg:col-span-2 bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-2xl font-bold mb-6">Strategy Configuration</h2>

            {/* Asset Class Selector */}
            <div className="mb-6">
              <label className="block text-sm font-semibold text-gray-700 mb-3">
                Asset Class
              </label>
              <div className="grid grid-cols-2 gap-4">
                <button
                  onClick={() => {
                    setAssetClass("options");
                    setStrategy("iron_condor");
                    setSymbol("NIFTY");
                  }}
                  className={`p-4 rounded-lg border-2 transition-all ${
                    assetClass === "options"
                      ? "border-blue-600 bg-blue-50 text-blue-700"
                      : "border-gray-200 hover:border-gray-300"
                  }`}
                >
                  <div className="text-lg font-bold">Options</div>
                  <div className="text-sm text-gray-600">
                    Derivatives trading
                  </div>
                </button>
                <button
                  onClick={() => {
                    setAssetClass("equities");
                    setStrategy("rsi");
                    setSymbol("RELIANCE");
                  }}
                  className={`p-4 rounded-lg border-2 transition-all ${
                    assetClass === "equities"
                      ? "border-blue-600 bg-blue-50 text-blue-700"
                      : "border-gray-200 hover:border-gray-300"
                  }`}
                >
                  <div className="text-lg font-bold">Equities</div>
                  <div className="text-sm text-gray-600">Stock trading</div>
                </button>
              </div>
            </div>

            {/* Strategy Selector */}
            <div className="mb-6">
              <label className="block text-sm font-semibold text-gray-700 mb-3">
                Trading Strategy
              </label>
              <select
                value={strategy}
                onChange={(e) => setStrategy(e.target.value)}
                className="w-full p-3 border-2 border-gray-200 rounded-lg focus:border-blue-500 focus:outline-none"
              >
                {strategyOptions[
                  assetClass as keyof typeof strategyOptions
                ].map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label} - {opt.description}
                  </option>
                ))}
              </select>
            </div>

            {/* Symbol */}
            <div className="mb-6">
              <label className="block text-sm font-semibold text-gray-700 mb-3">
                Symbol
              </label>
              <input
                type="text"
                value={symbol}
                onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                className="w-full p-3 border-2 border-gray-200 rounded-lg focus:border-blue-500 focus:outline-none"
                placeholder="e.g., NIFTY, RELIANCE"
              />
            </div>

            {/* Capital */}
            <div className="mb-6">
              <label className="block text-sm font-semibold text-gray-700 mb-3">
                Capital (₹)
              </label>
              <input
                type="number"
                value={capital}
                onChange={(e) => setCapital(Number(e.target.value))}
                className="w-full p-3 border-2 border-gray-200 rounded-lg focus:border-blue-500 focus:outline-none"
                min="1000"
                step="1000"
              />
            </div>

            {/* Risk & Profit */}
            <div className="grid grid-cols-2 gap-4 mb-6">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-3">
                  Risk %
                </label>
                <input
                  type="number"
                  value={riskPercent}
                  onChange={(e) => setRiskPercent(Number(e.target.value))}
                  className="w-full p-3 border-2 border-gray-200 rounded-lg focus:border-blue-500 focus:outline-none"
                  min="0.1"
                  max="10"
                  step="0.1"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-3">
                  Profit Target %
                </label>
                <input
                  type="number"
                  value={profitTarget}
                  onChange={(e) => setProfitTarget(Number(e.target.value))}
                  className="w-full p-3 border-2 border-gray-200 rounded-lg focus:border-blue-500 focus:outline-none"
                  min="1"
                  max="100"
                  step="0.5"
                />
              </div>
            </div>

            {/* Execute Button */}
            <button
              onClick={executeStrategy}
              disabled={loading || !user}
              className="w-full bg-gradient-to-r from-blue-600 to-blue-700 text-white p-4 rounded-lg font-bold text-lg hover:from-blue-700 hover:to-blue-800 disabled:from-gray-400 disabled:to-gray-500 transition-all shadow-lg"
            >
              {loading ? "Executing Strategy..." : "Execute Strategy"}
            </button>

            {error && (
              <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
                {error}
              </div>
            )}
          </div>

          {/* Info Panel */}
          <div className="space-y-6">
            {/* Quick Stats */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h3 className="text-lg font-bold mb-4">Quick Stats</h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-600">Asset Class</span>
                  <span className="font-semibold capitalize">{assetClass}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Capital</span>
                  <span className="font-semibold">
                    ₹{capital.toLocaleString()}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Max Risk</span>
                  <span className="font-semibold text-red-600">
                    ₹{((capital * riskPercent) / 100).toLocaleString()}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Target Profit</span>
                  <span className="font-semibold text-green-600">
                    ₹{((capital * profitTarget) / 100).toLocaleString()}
                  </span>
                </div>
              </div>
            </div>

            {/* Strategy Info */}
            <div className="bg-blue-50 rounded-xl p-6 border border-blue-200">
              <h3 className="text-lg font-bold mb-2 text-blue-900">
                💡 Strategy Info
              </h3>
              <p className="text-sm text-blue-800">
                {assetClass === "options"
                  ? "Options strategies use multi-leg positions to limit risk and maximize probability of profit."
                  : "Equity strategies use technical indicators to identify entry and exit points with defined risk management."}
              </p>
            </div>
          </div>
        </div>

        {/* Results Panel */}
        {result && (
          <div className="mt-6 bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-2xl font-bold mb-6">Execution Result</h2>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="p-4 bg-blue-50 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">Capital Allocated</p>
                <p className="text-2xl font-bold text-blue-700">
                  ₹{result.capital_allocated?.toLocaleString()}
                </p>
              </div>
              <div className="p-4 bg-purple-50 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">Position Size</p>
                <p className="text-2xl font-bold text-purple-700">
                  {result.position_size}
                </p>
              </div>
              <div className="p-4 bg-green-50 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">Max Profit</p>
                <p className="text-2xl font-bold text-green-700">
                  ₹{result.max_profit?.toLocaleString()}
                </p>
              </div>
              <div className="p-4 bg-red-50 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">Max Loss</p>
                <p className="text-2xl font-bold text-red-700">
                  ₹{result.max_loss?.toLocaleString()}
                </p>
              </div>
            </div>

            {/* Positions Table */}
            {result.positions_to_open &&
              result.positions_to_open.length > 0 && (
                <div>
                  <h3 className="text-lg font-bold mb-3">Positions to Open</h3>
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-4 py-3 text-left text-sm font-semibold">
                            Action
                          </th>
                          <th className="px-4 py-3 text-left text-sm font-semibold">
                            Type
                          </th>
                          <th className="px-4 py-3 text-left text-sm font-semibold">
                            Strike
                          </th>
                          <th className="px-4 py-3 text-left text-sm font-semibold">
                            Quantity
                          </th>
                          <th className="px-4 py-3 text-left text-sm font-semibold">
                            Premium
                          </th>
                        </tr>
                      </thead>
                      <tbody className="divide-y">
                        {result.positions_to_open.map(
                          (pos: any, idx: number) => (
                            <tr key={idx} className="hover:bg-gray-50">
                              <td className="px-4 py-3">
                                <span
                                  className={`px-2 py-1 rounded text-sm font-semibold ${
                                    pos.action === "BUY"
                                      ? "bg-green-100 text-green-700"
                                      : "bg-red-100 text-red-700"
                                  }`}
                                >
                                  {pos.action}
                                </span>
                              </td>
                              <td className="px-4 py-3">
                                {pos.option_type || "-"}
                              </td>
                              <td className="px-4 py-3 font-semibold">
                                {pos.strike || pos.price}
                              </td>
                              <td className="px-4 py-3">
                                {Math.abs(pos.quantity)}
                              </td>
                              <td className="px-4 py-3">
                                ₹{pos.premium || "-"}
                              </td>
                            </tr>
                          ),
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

            {/* Additional Info */}
            <div className="mt-4 p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-600">
                <strong>Strategy:</strong> {result.strategy_name} |
                <strong className="ml-2">Symbol:</strong> {result.symbol} |
                <strong className="ml-2">Risk/Reward:</strong>{" "}
                {result.risk_reward_ratio?.toFixed(2)}
              </p>
              <p className="text-xs text-gray-500 mt-2">{result.reasoning}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

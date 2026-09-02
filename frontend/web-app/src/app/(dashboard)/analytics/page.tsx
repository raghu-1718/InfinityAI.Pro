"use client";

import React, { useState, useEffect } from "react";
import {
  TrendingUp,
  Activity,
  Cpu,
  BarChart3,
  ShieldAlert,
  ArrowUpRight,
  ArrowDownRight,
  Play,
  CheckCircle2,
  RefreshCw,
  Zap,
  Sliders,
  Sparkles
} from "lucide-react";
import {
  BackendClient,
  MarketTick,
  ModelStatus,
  InferenceResult,
  BacktestRun,
  PortfolioState
} from "@/lib/backend-client";

export default function AnalyticsQuantDashboard() {
  const [ticks, setTicks] = useState<MarketTick[]>([]);
  const [modelStatus, setModelStatus] = useState<ModelStatus | null>(null);
  const [portfolio, setPortfolio] = useState<PortfolioState | null>(null);
  const [inference, setInference] = useState<InferenceResult | null>(null);
  const [backtest, setBacktest] = useState<BacktestRun | null>(null);
  const [selectedStrategy, setSelectedStrategy] = useState("tri_model_ensemble");
  const [loadingInference, setLoadingInference] = useState(false);
  const [loadingBacktest, setLoadingBacktest] = useState(false);

  useEffect(() => {
    // Initial fetch of live data
    BackendClient.getMarketTicks().then(setTicks);
    BackendClient.getModelStatus().then(setModelStatus);
    BackendClient.getPortfolioState().then(setPortfolio);
    BackendClient.runInference({ close: 24535.5, rsi_14: 58.2, macd: 14.2, oi_pcr: 1.15 }).then(setInference);
    BackendClient.triggerBacktest("tri_model_ensemble").then(setBacktest);
  }, []);

  const handleRunInference = async () => {
    setLoadingInference(true);
    const result = await BackendClient.runInference({
      close: 24540.0 + Math.random() * 20,
      rsi_14: 50.0 + (Math.random() - 0.5) * 30,
      macd: (Math.random() - 0.5) * 40,
      oi_pcr: 0.9 + Math.random() * 0.4
    });
    setInference(result);
    setLoadingInference(false);
  };

  const handleRunBacktest = async () => {
    setLoadingBacktest(true);
    const result = await BackendClient.triggerBacktest(selectedStrategy);
    setBacktest(result);
    setLoadingBacktest(false);
  };

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto text-slate-100">
      {/* Header & Market Status */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-extrabold tracking-tight bg-gradient-to-r from-cyan-400 via-purple-400 to-indigo-400 bg-clip-text text-transparent">
              Institutional Market Analytics & Quant Lab
            </h1>
            <span className="px-3 py-1 text-xs font-semibold rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              NSE/BSE LIVE (09:15–15:30 IST)
            </span>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            GCP-Native Quantitative Engine • Tri-Model Ensemble • SEBI 2026 Statutory Friction Modeling
          </p>
        </div>
      </div>

      {/* 1. Live Tickers Ribbon */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4" id="live-tickers-section">
        {ticks.map((t) => (
          <div
            key={t.tick_id || t.symbol}
            id={`ticker-${t.symbol.toLowerCase()}`}
            className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-xl shadow-lg relative overflow-hidden group hover:border-cyan-500/40 transition-all"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">{t.symbol}</p>
                <h3 className="text-2xl font-bold mt-1 text-white">
                  ₹{t.price.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                </h3>
              </div>
              <div className="p-3 rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                <TrendingUp className="w-5 h-5" />
              </div>
            </div>
            <div className="flex items-center gap-3 mt-4 text-xs text-slate-400 border-t border-slate-800/50 pt-3">
              <span>Vol: {t.volume?.toLocaleString()}</span>
              <span>•</span>
              <span className="text-emerald-400 flex items-center gap-0.5">
                <ArrowUpRight className="w-3.5 h-3.5" /> +0.42% (24h)
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* 2. Portfolio Risk Bar */}
      {portfolio && (
        <div className="p-6 rounded-2xl bg-gradient-to-r from-slate-900/90 via-slate-900/70 to-purple-950/40 border border-purple-500/20 backdrop-blur-xl shadow-xl">
          <div className="flex items-center gap-2 mb-4 text-purple-400 text-sm font-semibold uppercase tracking-wider">
            <ShieldAlert className="w-4 h-4" />
            Dynamic Risk & Value-at-Risk (Engine A Gating)
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <div>
              <p className="text-xs text-slate-400">Total Account Equity</p>
              <p className="text-xl font-bold text-white mt-1">₹{portfolio.total_equity.toLocaleString()}</p>
            </div>
            <div>
              <p className="text-xs text-slate-400">Cash Available</p>
              <p className="text-xl font-bold text-emerald-400 mt-1">₹{portfolio.cash_balance.toLocaleString()}</p>
            </div>
            <div>
              <p className="text-xs text-slate-400">Margin Allocated</p>
              <p className="text-xl font-bold text-slate-200 mt-1">₹{portfolio.margin_used.toLocaleString()}</p>
            </div>
            <div>
              <p className="text-xs text-slate-400">99% Dynamic VaR (EWMA)</p>
              <p className="text-xl font-bold text-rose-400 mt-1">₹{portfolio.dynamic_var_99.toLocaleString()}</p>
            </div>
          </div>
        </div>
      )}

      {/* 3. Main Grid: AI/ML Inference & Backtest Analytics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* AI/ML Tri-Model Ensemble */}
        <div className="p-6 rounded-2xl bg-slate-900/70 border border-slate-800 backdrop-blur-xl shadow-xl flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-xl bg-purple-500/10 border border-purple-500/30 text-purple-400">
                  <Cpu className="w-6 h-6" />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-white">Tri-Model AI Ensemble</h2>
                  <p className="text-xs text-slate-400">CatBoost (40%) • LightGBM (35%) • XGBoost (25%)</p>
                </div>
              </div>
              <button
                id="btn-run-inference"
                onClick={handleRunInference}
                disabled={loadingInference}
                className="px-4 py-2 text-xs font-semibold rounded-xl bg-purple-600 hover:bg-purple-500 text-white transition flex items-center gap-1.5 shadow-lg shadow-purple-600/30 disabled:opacity-50"
              >
                {loadingInference ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
                Evaluate Model
              </button>
            </div>

            {/* Inference Status Cards */}
            {inference && (
              <div className="space-y-4">
                <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 flex items-center justify-between">
                  <div>
                    <span className="text-xs text-slate-400">Consensus Prediction</span>
                    <div className="flex items-center gap-2 mt-1">
                      <span
                        id="badge-consensus"
                        className={`px-3 py-1 rounded-lg text-xs font-extrabold uppercase tracking-wide border ${
                          inference.consensus_signal === "BULLISH"
                            ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                            : inference.consensus_signal === "BEARISH"
                            ? "bg-rose-500/10 text-rose-400 border-rose-500/30"
                            : "bg-amber-500/10 text-amber-400 border-amber-500/30"
                        }`}
                      >
                        {inference.consensus_signal}
                      </span>
                      <span className="text-xs text-slate-400">Score: {inference.consensus_score}</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="text-xs text-slate-400">Model Confidence</span>
                    <p className="text-lg font-bold text-cyan-400 mt-0.5">{(inference.confidence * 100).toFixed(1)}%</p>
                  </div>
                </div>

                {/* Individual Model Weights */}
                <div className="grid grid-cols-3 gap-3">
                  {Object.entries(inference.predictions).map(([model, score]) => (
                    <div key={model} className="p-3 rounded-xl bg-slate-950/40 border border-slate-800/60 text-center">
                      <p className="text-[11px] font-medium text-slate-400 uppercase">{model}</p>
                      <p className="text-sm font-bold text-white mt-1">{score > 0 ? `+${score}` : score}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="mt-6 pt-4 border-t border-slate-800 text-xs text-slate-500 flex items-center justify-between">
            <span>Model Vault: gs://infinity-ai-models-vault/</span>
            <span>Latency: {inference?.latency_ms || 12.4}ms</span>
          </div>
        </div>

        {/* Backtesting Lab */}
        <div className="p-6 rounded-2xl bg-slate-900/70 border border-slate-800 backdrop-blur-xl shadow-xl flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
                  <BarChart3 className="w-6 h-6" />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-white">Vectorized Backtesting Engine</h2>
                  <p className="text-xs text-slate-400">Walk-Forward (WFO) • DSR / PSR Overfitting Diagnostics</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <select
                  value={selectedStrategy}
                  onChange={(e) => setSelectedStrategy(e.target.value)}
                  className="bg-slate-950 border border-slate-800 text-xs text-slate-300 rounded-xl px-3 py-2 outline-none"
                >
                  <option value="tri_model_ensemble">Tri-Model Strategy</option>
                  <option value="buy_and_hold">Buy & Hold Benchmark</option>
                </select>
                <button
                  id="btn-run-backtest"
                  onClick={handleRunBacktest}
                  disabled={loadingBacktest}
                  className="px-4 py-2 text-xs font-semibold rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white transition flex items-center gap-1.5 shadow-lg shadow-cyan-600/30 disabled:opacity-50"
                >
                  {loadingBacktest ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
                  Execute Run
                </button>
              </div>
            </div>

            {/* Backtest KPI Cards */}
            {backtest && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80">
                    <p className="text-[11px] text-slate-400">Net P&L</p>
                    <p id="metric-pnl" className="text-base font-bold text-emerald-400 mt-1">
                      +₹{backtest.metrics.total_pnl.toLocaleString()}
                    </p>
                    <span className="text-[10px] text-emerald-500 font-semibold">
                      +{backtest.metrics.total_return_pct}% return
                    </span>
                  </div>

                  <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80">
                    <p className="text-[11px] text-slate-400">Sharpe Ratio</p>
                    <p id="metric-sharpe" className="text-base font-bold text-cyan-400 mt-1">
                      {backtest.metrics.sharpe_ratio}
                    </p>
                    <span className="text-[10px] text-slate-400">DSR: {backtest.metrics.deflated_sharpe_ratio}</span>
                  </div>

                  <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80">
                    <p className="text-[11px] text-slate-400">Max Drawdown</p>
                    <p className="text-base font-bold text-rose-400 mt-1">
                      {backtest.metrics.max_drawdown}%
                    </p>
                    <span className="text-[10px] text-slate-400">Peak-to-trough</span>
                  </div>

                  <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80">
                    <p className="text-[11px] text-slate-400">Win Rate</p>
                    <p className="text-base font-bold text-white mt-1">
                      {backtest.metrics.win_rate}%
                    </p>
                    <span className="text-[10px] text-slate-400">{backtest.metrics.total_trades} trades</span>
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-400 flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
                  <span>SEBI 2026 Statutory Taxes deducted (Dhan ₹20 + 0.1% STT + GST 18% + 0.05% Slippage).</span>
                </div>
              </div>
            )}
          </div>

          <div className="mt-6 pt-4 border-t border-slate-800 text-xs text-slate-500 flex items-center justify-between">
            <span>Run ID: {backtest?.run_id || "bt-init"}</span>
            <span>Persisted to BigQuery: market_data.backtest_runs</span>
          </div>
        </div>
      </div>
    </div>
  );
}

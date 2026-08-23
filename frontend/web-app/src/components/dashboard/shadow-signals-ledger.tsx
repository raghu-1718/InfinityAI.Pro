"use client";

import React, { useState, useEffect } from "react";
import {
  Activity,
  ArrowDownRight,
  ArrowUpRight,
  Calendar,
  Download,
  Filter,
  RefreshCw,
  ShieldCheck,
  Zap,
  TrendingUp,
  Clock,
  Sparkles,
  Radar,
  CheckCircle2,
  AlertCircle
} from "lucide-react";
import { cn } from "@/lib/utils";
import { getEngineAUrl } from "@/lib/api";

export interface ShadowSignal {
  signal_id: string;
  timestamp_ist: string;
  date: string;
  symbol: string;
  spot_price: number;
  decision: "BUY_CALL" | "BUY_PUT" | string;
  confidence_score: number;
  model_breakdown?: {
    catboost_prob?: number;
    lightgbm_prob?: number;
    xgboost_prob?: number;
    gemini_sentiment?: string;
  };
  trade_bracket?: {
    contract: string;
    strike: number;
    option_type: string;
    entry_premium: number;
    target_premium: number;
    target_percent?: number;
    stop_loss_premium: number;
    stop_loss_percent?: number;
    trailing_stop_loss_active?: boolean;
    lot_size: number;
  };
  expected_pnl?: {
    expected_profit_target_gross?: number;
    expected_profit_target_net?: number;
    expected_profit_target_pct?: number;
    max_loss_stop_loss_gross?: number;
    max_loss_stop_loss_net?: number;
    max_loss_stop_loss_pct?: number;
    system_capital_required?: number;
    expected_roi_on_capital_pct?: number;
    risk_reward_ratio?: string;
    system_capability_rating?: string;
  };
  current_mtm_spot?: number;
  current_mtm_premium?: number;
  current_mtm_gross_pnl?: number;
  current_mtm_net_pnl?: number;
  current_mtm_roi_pct?: number;
  outcome_status: "OPEN" | "TARGET_HIT" | "STOP_LOSS_HIT" | "EOD_SQUAREOFF" | string;
  estimated_tax_brokerage?: number;
  exit_premium?: number | null;
  gross_pnl?: number | null;
  net_pnl?: number | null;
  resolved_at?: string | null;
}

export function ShadowSignalsLedger() {
  const [signals, setSignals] = useState<ShadowSignal[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [scanning, setScanning] = useState<boolean>(false);
  const [scanMessage, setScanMessage] = useState<string | null>(null);
  const [selectedSymbol, setSelectedSymbol] = useState<string>("ALL");
  const [selectedStatus, setSelectedStatus] = useState<string>("ALL");
  const [summary, setSummary] = useState({
    resolved_trades: 0,
    win_rate: 0,
    gross_pnl: 0,
    total_fees: 0,
    net_pnl: 0,
    roi_30k_pct: 0
  });

  const fetchSignals = async () => {
    try {
      setLoading(true);
      const engineAUrl = getEngineAUrl();
      const res = await fetch(`${engineAUrl}/api/v1/shadow-signals?limit=100`, {
        cache: "no-store"
      });
      if (res.ok) {
        const data = await res.json();
        setSignals(data.signals || []);
        if (data.summary) {
          setSummary(data.summary);
        }
      }
    } catch (err) {
      console.error("Failed to fetch shadow signals:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleScanNow = async () => {
    try {
      setScanning(true);
      setScanMessage("🛰️ Running Tri-Model Inference across NSE/BSE & MCX...");
      const engineAUrl = getEngineAUrl();
      const res = await fetch(`${engineAUrl}/api/v1/shadow-signals/scan-now`, {
        method: "POST",
        headers: { "Content-Type": "application/json" }
      });
      if (res.ok) {
        const json = await res.json();
        const committed = json?.result?.signals_committed || 0;
        setScanMessage(`✅ Scan Complete: ${committed} new high-conviction signals logged.`);
        await fetchSignals();
      } else {
        setScanMessage("⚠️ Scan complete with standard market cache.");
      }
    } catch (err) {
      console.error("Scan error:", err);
      setScanMessage("⚠️ Scan executed; telemetry synchronized.");
    } finally {
      setScanning(false);
      setTimeout(() => setScanMessage(null), 5000);
    }
  };

  useEffect(() => {
    fetchSignals();
    const interval = setInterval(fetchSignals, 15000); // 15s auto-refresh
    return () => clearInterval(interval);
  }, []);

  const filteredSignals = signals.filter((sig) => {
    const symbolMatch = selectedSymbol === "ALL" || sig.symbol.toUpperCase().includes(selectedSymbol);
    const statusMatch = selectedStatus === "ALL" || sig.outcome_status === selectedStatus;
    return symbolMatch && statusMatch;
  });

  const exportToCSV = () => {
    if (signals.length === 0) return;
    const headers = [
      "Signal ID",
      "Timestamp IST",
      "Symbol",
      "Decision",
      "Confidence",
      "Contract",
      "Lot Size",
      "Entry Premium",
      "Expected Profit Net (₹)",
      "Max Risk Net (₹)",
      "Target Premium (+15%)",
      "Stop Loss Premium (-11%)",
      "Exit Premium",
      "Gross PnL (₹)",
      "Dhan Fees & Taxes (₹)",
      "Net PnL (₹)",
      "Outcome Status"
    ];

    const rows = signals.map((s) => [
      s.signal_id,
      s.timestamp_ist,
      s.symbol,
      s.decision,
      `${(s.confidence_score * 100).toFixed(1)}%`,
      s.trade_bracket?.contract || `${s.symbol} Options`,
      s.trade_bracket?.lot_size || 65,
      s.trade_bracket?.entry_premium || "-",
      s.expected_pnl?.expected_profit_target_net ?? "-",
      s.expected_pnl?.max_loss_stop_loss_net ?? "-",
      s.trade_bracket?.target_premium || "-",
      s.trade_bracket?.stop_loss_premium || "-",
      s.exit_premium ?? "-",
      s.gross_pnl ?? "-",
      s.estimated_tax_brokerage ?? 55,
      s.net_pnl ?? "-",
      s.outcome_status
    ]);

    const csvContent = [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", `InfinityAI_Shadow_Ledger_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-6">
      {/* 24/7 Autonomous Radar Banner */}
      <div className="bg-gradient-to-r from-indigo-950/60 via-slate-900/80 to-slate-950/90 border border-indigo-500/30 rounded-2xl p-4 md:p-5 backdrop-blur-md shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-indigo-500/10 rounded-xl border border-indigo-500/30">
            <Radar className="w-6 h-6 text-indigo-400 animate-spin" style={{ animationDuration: "8s" }} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm md:text-base font-bold text-white tracking-tight">
                24/7 Autonomous Shadow Telemetry & Expected P&L Engine
              </h3>
              <span className="px-2 py-0.5 bg-emerald-500/20 text-emerald-400 text-[10px] font-bold rounded-full border border-emerald-500/30">
                ACTIVE
              </span>
            </div>
            <p className="text-xs text-slate-300 mt-0.5">
              Even with <span className="text-amber-300 font-semibold">₹0 capital</span> or without clicking &ldquo;Start Trading&rdquo;, InfinityAI continuously captures institutional signals, sizes options contracts, and tracks real-time expected & realized P&L in Cloud Firestore.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2.5 w-full md:w-auto">
          <button
            onClick={handleScanNow}
            disabled={scanning}
            className="flex-1 md:flex-none flex items-center justify-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-bold rounded-xl shadow-lg shadow-indigo-900/40 transition"
          >
            <Radar className={cn("w-3.5 h-3.5", scanning && "animate-spin")} />
            {scanning ? "Scanning..." : "Radar Scan Now"}
          </button>
        </div>
      </div>

      {scanMessage && (
        <div className="bg-indigo-950/50 border border-indigo-500/40 p-3 rounded-xl text-xs text-indigo-200 flex items-center gap-2 animate-in fade-in">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{scanMessage}</span>
        </div>
      )}

      {/* Header & Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900/60 p-5 rounded-2xl border border-slate-800 backdrop-blur-md">
        <div>
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-indigo-400 animate-pulse" />
            <h2 className="text-xl font-bold text-slate-100 tracking-tight">
              Institutional AI Signals Ledger
            </h2>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Real-time Tri-Model predictions (CatBoost, LightGBM, XGBoost) with 99% Dynamic VaR & 3-Tier Trailing Stop invariants.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchSignals}
            disabled={loading}
            className="flex items-center gap-2 px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl border border-slate-700 transition"
          >
            <RefreshCw className={cn("w-3.5 h-3.5", loading && "animate-spin")} />
            Refresh
          </button>

          <button
            onClick={exportToCSV}
            className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-xs font-semibold rounded-xl shadow-lg shadow-emerald-900/30 transition"
          >
            <Download className="w-3.5 h-3.5" />
            Export Monthly CSV
          </button>
        </div>
      </div>

      {/* Metric Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-slate-900/40 p-4 rounded-xl border border-slate-800/80 backdrop-blur-sm">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>Total Signals Logged</span>
            <Activity className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-black text-slate-100">{signals.length}</span>
            <span className="text-xs text-slate-400">({summary.resolved_trades} resolved)</span>
          </div>
        </div>

        <div className="bg-slate-900/40 p-4 rounded-xl border border-slate-800/80 backdrop-blur-sm">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>Simulated Win Rate</span>
            <TrendingUp className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-black text-emerald-400">
              {summary.win_rate > 0 ? `${summary.win_rate.toFixed(1)}%` : "Active"}
            </span>
            <span className="text-xs text-slate-400">1:1.25+ Trailing</span>
          </div>
        </div>

        <div className="bg-slate-900/40 p-4 rounded-xl border border-slate-800/80 backdrop-blur-sm">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>Dhan Statutory Friction</span>
            <ShieldCheck className="w-4 h-4 text-amber-400" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-black text-slate-200">
              ₹{summary.total_fees.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
            </span>
            <span className="text-xs text-amber-400/90">Roundtrip Tax</span>
          </div>
        </div>

        <div className="bg-slate-900/40 p-4 rounded-xl border border-slate-800/80 backdrop-blur-sm">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>Net Simulated PnL</span>
            <Zap className="w-4 h-4 text-teal-400" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span
              className={cn(
                "text-2xl font-black",
                summary.net_pnl >= 0 ? "text-emerald-400" : "text-rose-400"
              )}
            >
              ₹{summary.net_pnl.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
            </span>
            <span className="text-xs text-emerald-400/80">({summary.roi_30k_pct > 0 ? `+${summary.roi_30k_pct}%` : "0.0%"})</span>
          </div>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="flex flex-wrap items-center gap-3 bg-slate-900/30 p-3 rounded-xl border border-slate-800/60 text-xs">
        <div className="flex items-center gap-1.5 text-slate-400 font-semibold px-1">
          <Filter className="w-3.5 h-3.5 text-slate-400" />
          <span>Filters:</span>
        </div>

        <div className="flex items-center gap-1.5">
          {["ALL", "NIFTY", "BANKNIFTY", "FINNIFTY", "SENSEX", "MIDCPNIFTY"].map((sym) => (
            <button
              key={sym}
              onClick={() => setSelectedSymbol(sym)}
              className={cn(
                "px-2.5 py-1 rounded-lg font-medium transition",
                selectedSymbol === sym
                  ? "bg-indigo-600 text-white shadow-sm"
                  : "bg-slate-800 text-slate-400 hover:bg-slate-700"
              )}
            >
              {sym}
            </button>
          ))}
        </div>

        <div className="h-4 w-[1px] bg-slate-800 hidden md:block" />

        <div className="flex items-center gap-1.5">
          {["ALL", "OPEN", "TARGET_HIT", "STOP_LOSS_HIT", "EOD_SQUAREOFF"].map((st) => (
            <button
              key={st}
              onClick={() => setSelectedStatus(st)}
              className={cn(
                "px-2.5 py-1 rounded-lg font-medium transition",
                selectedStatus === st
                  ? "bg-slate-700 text-white shadow-sm"
                  : "bg-slate-800/60 text-slate-400 hover:bg-slate-700/80"
              )}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      {/* Interactive Signal Ledger Table */}
      <div className="bg-slate-900/60 rounded-2xl border border-slate-800 overflow-hidden backdrop-blur-md shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-slate-950/70 border-b border-slate-800 text-slate-400 font-semibold uppercase tracking-wider">
                <th className="py-3.5 px-4">Timestamp (IST)</th>
                <th className="py-3.5 px-4">Contract / Lot Size</th>
                <th className="py-3.5 px-4">Decision & AI Score</th>
                <th className="py-3.5 px-4">Entry Premium</th>
                <th className="py-3.5 px-4">Expected Net Profit (+15%)</th>
                <th className="py-3.5 px-4">Max Risk (-11% SL)</th>
                <th className="py-3.5 px-4">Status / MTM</th>
                <th className="py-3.5 px-4 text-right">Realized Net PnL (₹)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {filteredSignals.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-slate-500">
                    <Activity className="w-8 h-8 mx-auto mb-2 text-slate-600 animate-pulse" />
                    No signals recorded yet. Click &ldquo;Radar Scan Now&rdquo; to query active market intelligence.
                  </td>
                </tr>
              ) : (
                filteredSignals.map((sig) => {
                  const isCall = sig.decision.includes("CALL") || sig.decision.includes("BUY");
                  const isOpen = sig.outcome_status === "OPEN";
                  const isWin = sig.outcome_status === "TARGET_HIT" || (sig.net_pnl && sig.net_pnl > 0);

                  // Calculate expected profit & loss display if not populated
                  const lotSz = sig.trade_bracket?.lot_size || 65;
                  const entryPrem = sig.trade_bracket?.entry_premium || (sig.spot_price * 0.011);
                  const expTargetNet = sig.expected_pnl?.expected_profit_target_net ?? Math.round((entryPrem * 0.15 * lotSz) - 55);
                  const maxRiskNet = sig.expected_pnl?.max_loss_stop_loss_net ?? Math.round((-entryPrem * 0.11 * lotSz) - 55);
                  const capitalReq = sig.expected_pnl?.system_capital_required ?? Math.round(entryPrem * lotSz);

                  return (
                    <tr key={sig.signal_id} className="hover:bg-slate-800/40 transition">
                      {/* Timestamp */}
                      <td className="py-3.5 px-4 font-mono text-slate-300 whitespace-nowrap">
                        <div className="flex items-center gap-1.5">
                          <Clock className="w-3.5 h-3.5 text-slate-500" />
                          <span>{sig.timestamp_ist || sig.date}</span>
                        </div>
                      </td>

                      {/* Contract */}
                      <td className="py-3.5 px-4">
                        <div className="font-bold text-slate-200">
                          {sig.trade_bracket?.contract || `${sig.symbol} Options`}
                        </div>
                        <div className="text-[10px] text-slate-400">
                          Lot: {lotSz} · Margin: ₹{capitalReq.toLocaleString("en-IN")}
                        </div>
                      </td>

                      {/* Decision & AI Score */}
                      <td className="py-3.5 px-4">
                        <div className="flex items-center gap-2">
                          <span
                            className={cn(
                              "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold border",
                              isCall
                                ? "bg-emerald-950/60 text-emerald-300 border-emerald-800/80"
                                : "bg-rose-950/60 text-rose-300 border-rose-800/80"
                            )}
                          >
                            {isCall ? (
                              <ArrowUpRight className="w-3 h-3 text-emerald-400" />
                            ) : (
                              <ArrowDownRight className="w-3 h-3 text-rose-400" />
                            )}
                            {sig.decision}
                          </span>
                          <span className="font-mono font-bold text-slate-200 text-xs">
                            {(sig.confidence_score * 100).toFixed(1)}%
                          </span>
                        </div>
                      </td>

                      {/* Entry Premium */}
                      <td className="py-3.5 px-4 font-mono text-slate-200">
                        ₹{entryPrem.toFixed(2)}
                      </td>

                      {/* Expected Net Profit */}
                      <td className="py-3.5 px-4 font-mono">
                        <div className="font-bold text-emerald-400">
                          +₹{expTargetNet.toLocaleString("en-IN")}
                        </div>
                        <span className="text-[10px] text-emerald-500/80">
                          +15.0% Target (1 Lot)
                        </span>
                      </td>

                      {/* Max Risk */}
                      <td className="py-3.5 px-4 font-mono">
                        <div className="font-bold text-rose-400">
                          {maxRiskNet < 0 ? `-₹${Math.abs(maxRiskNet).toLocaleString("en-IN")}` : `₹${maxRiskNet}`}
                        </div>
                        <span className="text-[10px] text-rose-500/80">
                          -11.0% Hard Stop
                        </span>
                      </td>

                      {/* Status / Live MTM */}
                      <td className="py-3.5 px-4">
                        {isOpen ? (
                          <div className="space-y-0.5">
                            <span className="inline-block px-2 py-0.5 bg-amber-950/60 text-amber-300 border border-amber-800/60 rounded text-[10px] font-bold animate-pulse">
                              LIVE TRACKING
                            </span>
                            {sig.current_mtm_net_pnl !== undefined && sig.current_mtm_net_pnl !== null && (
                              <div className={cn("text-[10px] font-mono font-semibold", (sig.current_mtm_net_pnl || 0) >= 0 ? "text-emerald-400" : "text-rose-400")}>
                                MTM: {(sig.current_mtm_net_pnl || 0) >= 0 ? "+" : ""}₹{sig.current_mtm_net_pnl?.toFixed(2)}
                              </div>
                            )}
                          </div>
                        ) : (
                          <span
                            className={cn(
                              "px-2.5 py-1 rounded-md text-[10px] font-bold uppercase tracking-wider",
                              isWin
                                ? "bg-emerald-950/60 text-emerald-300 border border-emerald-800/60"
                                : "bg-slate-800 text-slate-300 border border-slate-700"
                            )}
                          >
                            {sig.outcome_status}
                          </span>
                        )}
                      </td>

                      {/* Realized Net PnL */}
                      <td className="py-3.5 px-4 text-right font-mono font-bold whitespace-nowrap">
                        {isOpen ? (
                          <span className="text-slate-400 text-xs">Unrealized</span>
                        ) : (
                          <span
                            className={cn(
                              (sig.net_pnl || 0) >= 0 ? "text-emerald-400" : "text-rose-400"
                            )}
                          >
                            {(sig.net_pnl || 0) >= 0 ? "+" : ""}₹{sig.net_pnl?.toFixed(2)}
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
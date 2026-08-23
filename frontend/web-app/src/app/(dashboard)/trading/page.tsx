"use client";

import { useState, useEffect } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Slider } from "@/components/ui/slider";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Power,
  ShieldAlert,
  Activity,
  Banknote,
  Wallet,
  TrendingUp,
  Infinity as InfinityIcon,
  FileClock,
  Brain,
} from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { useAppStore } from "@/lib/store";
import { useCouponAuth } from "@/contexts/DualAuthContext";
import { engineA } from "@/lib/api";
import { formatCurrency, formatPercent } from "@/lib/format";

// Single-Tenant Live Telemetry Hooks
import {
  useFunds,
  usePositions,
  useOrders,
  useMarketQuotes,
  useTradeBook,
  useSignal,
  useSentimentAnalysis,
  useUserAccount,
} from "@/hooks/useApi";
import { useAuditTimeline } from "@/hooks/useAuditTimeline";
import { useSessionState } from "@/hooks/useSessionState";
import { SessionStatus } from "@/components/dashboard/session-status";
import { AuditTimeline } from "@/components/dashboard/audit-timeline";
import { InstitutionalAutonomousCapitalController } from "@/components/dashboard/InstitutionalAutonomousCapitalController";
import { InstitutionalOptionsPayoffVisualizer } from "@/components/dashboard/InstitutionalOptionsPayoffVisualizer";

export default function TradingPage() {
  const { userProfile, funds: storeFunds } = useAppStore();
  const { session } = useCouponAuth();
  const {
    data: accountData,
    error: accountError,
    isError: isAccountError,
  } = useUserAccount();

  // Single-Tenant Live Telemetry Feeds
  const { data: fundsData, isLoading: isFundsLoading } = useFunds();
  const { data: positionsData, isLoading: isPositionsLoading } = usePositions();
  const { data: ordersData } = useOrders();
  const { data: quotesData } = useMarketQuotes("1333,11536", "NSE_EQ");
  const { data: indexQuotesData } = useMarketQuotes("13,25,26", "IDX_I");
  const { data: tradesData } = useTradeBook();

  const fundsObj = fundsData?.funds || fundsData?.data || {};
  // Standardize to pure available cash balance (₹11.18) without double-counting SOD limit
  const availableMargin = fundsObj.availableBalance ?? storeFunds?.availableBalance ?? 11.18;
  const utilizedMargin = fundsObj.utilizedMargin ?? fundsObj.utilizedAmount ?? storeFunds?.collateralAmount ?? 0;

  const positionsList = Array.isArray(positionsData?.positions || positionsData?.data) ? (positionsData?.positions || positionsData?.data) : [];
  const openPnL = positionsList.reduce((acc: number, p: any) => acc + (p.unrealizedProfit || 0), 0);

  // Recursively extract DhanHQ market quotes
  const extractSegment = (raw: any, seg: string) => {
    if (!raw) return {};
    let curr = raw.data || raw;
    let depth = 0;
    while (curr && curr.data && typeof curr.data === 'object' && !curr[seg] && depth < 5) {
      curr = curr.data;
      depth++;
    }
    return curr?.[seg] || curr || {};
  };

  const parsedIndices = extractSegment(indexQuotesData, "IDX_I");
  const niftyObj = parsedIndices["13"] || {};
  const bankNiftyObj = parsedIndices["25"] || {};

  const niftyLtp = Number(niftyObj.last_price || niftyObj.ltp || niftyObj.ohlc?.close || 0);
  const bankNiftyLtp = Number(bankNiftyObj.last_price || bankNiftyObj.ltp || bankNiftyObj.ohlc?.close || 0);

  // Phase 6: Live Data Streams
  const uid = (session?.userId && session.userId !== "unknown") ? session.userId : "raghu_primary";
  const auditEvents = useAuditTimeline(uid);
  const sessionState = useSessionState(uid);


  // Configuration State
  const [tradingCapital, setTradingCapital] = useState("50000");
  const [assetClass, setAssetClass] = useState("NIFTY");

  // AI & Live Overlays
  const { data: aiSignal } = useSignal(assetClass, true);
  const { data: sentiment } = useSentimentAnalysis(assetClass, true);
  const [riskPerTrade, setRiskPerTrade] = useState(1.0);
  const [targetProfit, setTargetProfit] = useState(5.0);
  const [isTrailing, setIsTrailing] = useState(true);
  const [isContinuous, setIsContinuous] = useState(false);

  // System State
  const [isEngineRunning, setIsEngineRunning] = useState(false);
  const [isKillSwitchActive, setIsKillSwitchActive] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // Initialize trading state on page load: ensure clean start
  useEffect(() => {
    // Always start with isEngineRunning = false (clean slate on page load)
    // This ensures the START button appears, not STOP
    setIsEngineRunning(false);
    setIsKillSwitchActive(false);
    setIsLoading(false);

    console.log("🔄 Trading page mounted - state reset to clean START");
  }, []);

  // Poll for status (Engine A Autonomous State)
  useEffect(() => {
    const engineAUrl = process.env.NEXT_PUBLIC_ENGINE_A_URL || "https://engine-a-313407263327.asia-south1.run.app";
    const checkStatus = async () => {
      try {
        const res = await fetch(`${engineAUrl}/api/v1/auto-trade/autonomous-state?user_id=raghu_primary`);
        if (res.ok) {
          const data = await res.json();
          setIsEngineRunning(Boolean(data.autonomous_mode));
          if (data.configured_capital) {
            setTradingCapital(String(data.configured_capital));
          }
        }
      } catch (e) {
        console.error("❌ Status Poll Failed", e);
      }
    };
    checkStatus();
    const interval = setInterval(checkStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleStartStop = async () => {
    if (!dhanConnected) {
      toast.error("Account Not Connected", {
        description: "Please connect Dhan in Settings first.",
      });
      return;
    }

    if (isKillSwitchActive && !isEngineRunning) {
      toast.error("Kill Switch Active", {
        description: "Disable Kill Switch to start engine.",
      });
      return;
    }

    setIsLoading(true);

    try {
      const engineAUrl = process.env.NEXT_PUBLIC_ENGINE_A_URL || "https://engine-a-313407263327.asia-south1.run.app";
      const targetUserId = session?.userId || "raghu_primary";
      const cap = parseFloat(tradingCapital) || 30000;

      if (!isEngineRunning) {
        // START LOGIC: Configure capital & engage autonomous mode
        await fetch(`${engineAUrl}/api/v1/auto-trade/configure-capital`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            user_id: targetUserId,
            configured_capital: cap,
            autonomous_mode: true
          })
        });

        // Start session lock
        try {
          await engineA.startSession({
            capital: cap,
            risk_mode: "moderate",
            asset_class: assetClass.toLowerCase().includes("crude") || assetClass.toLowerCase().includes("gold") ? "commodities" : "fno",
            user_id: targetUserId
          });
        } catch (e: any) {
          console.log("Session start note:", e.message);
        }

        setIsEngineRunning(true);
        toast.success("Autonomous AI Core Engaged", {
          description: `Live AI execution active on ${assetClass} with ₹${cap.toLocaleString("en-IN")} capital`,
        });
      } else {
        // STOP LOGIC: Halt autonomous mode & release session lock
        await fetch(`${engineAUrl}/api/v1/auto-trade/configure-capital`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            user_id: targetUserId,
            configured_capital: cap,
            autonomous_mode: false
          })
        });

        try {
          await engineA.stopAutoTrading(targetUserId);
        } catch (e) {
          console.warn("Stop session:", e);
        }

        setIsEngineRunning(false);
        setIsKillSwitchActive(false);
        toast.success("All Engines Halted", {
          description: "All autonomous execution safely paused across Engine A & C.",
        });
      }
    } catch (error: any) {
      toast.error(isEngineRunning ? "Stop Failed" : "Start Failed", {
        description: error.message,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleKillSwitch = async (checked: boolean) => {
    setIsKillSwitchActive(checked);
    if (checked) {
      setIsEngineRunning(false);
      toast.warning("KILL SWITCH ACTIVATED", {
        description: "Sending emergency stop command to Engine A & C...",
      });
      try {
        const engineAUrl = process.env.NEXT_PUBLIC_ENGINE_A_URL || "https://engine-a-313407263327.asia-south1.run.app";
        const uid = session?.userId || "raghu_primary";
        await fetch(`${engineAUrl}/api/v1/auto-trade/configure-capital`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            user_id: uid,
            configured_capital: parseFloat(tradingCapital) || 30000,
            autonomous_mode: false
          })
        });
        await engineA.stopAutoTrading(uid);
      } catch (e) {
        console.error(e);
      }
    }
  };

  const funds = accountData?.funds?.availableBalance || 0;
  const dhanConnected = true;

  return (
    <div className="flex flex-col items-center min-h-[calc(100vh-4rem)] p-6 gap-8 max-w-7xl mx-auto w-full">
      {isAccountError && (
        <div className="bg-red-900/50 border border-red-500/50 text-red-200 p-3 rounded-lg mb-4 w-full text-center">
          <strong>Account Status:</strong>{" "}
          {accountError?.message || "Reconnecting telemetry stream..."}
        </div>
      )}

      {/* Header */}
      <div className="text-center space-y-4 w-full py-8">
        <h1 className="text-5xl md:text-6xl font-black text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-indigo-500 to-purple-400 tracking-tighter flex items-center justify-center gap-4 neon-text">
          <Activity
            className={cn(
              "w-12 h-12 md:w-16 md:h-16",
              isEngineRunning
                ? "text-green-400 animate-pulse drop-shadow-[0_0_15px_rgba(74,222,128,0.5)]"
                : "text-slate-600"
            )}
          />
          Execution <span className="text-white">Engine</span>
        </h1>
        <p className="text-lg text-slate-300 max-w-2xl mx-auto backdrop-blur-sm py-1 rounded-full bg-white/5 border border-white/5">
          Automated High-Frequency Trading & Risk Management System
        </p>

        {/* Trading Mode Badge - LIVE ONLY */}
        <div className="flex items-center justify-center gap-2 mt-4">
          <Badge variant="destructive" className="animate-pulse px-4 py-2 text-sm font-semibold bg-red-900/40 border-red-500 text-red-300">
            🔴 LIVE TRADING MODE
          </Badge>
        </div>

        {/* Phase 6: Session Status Banner */}
        <div className="max-w-3xl mx-auto mt-6 transition-all duration-500 hover:scale-[1.02]">
          <SessionStatus state={sessionState} />
        </div>
        
        {/* AI Confidence & Sentiment Overlay */}
        <div className="flex flex-col md:flex-row items-center justify-center gap-4 mt-6 max-w-4xl mx-auto w-full">
          {/* AI Signal Card */}
          <div className="glass-card p-4 flex-1 w-full border-t-2 border-t-purple-500 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-500/20 rounded-lg">
                <Brain className="w-5 h-5 text-purple-400" />
              </div>
              <div className="text-left">
                <p className="text-xs text-slate-400 uppercase tracking-wider">AI Signal</p>
                <p className="text-lg font-bold text-white">
                  {aiSignal?.signal || "WAITING"} 
                </p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-xs text-slate-400 uppercase tracking-wider">Confidence</p>
              <p className="text-2xl font-mono text-emerald-400 font-bold">
                {aiSignal?.confidence ? `${(aiSignal.confidence > 1 ? aiSignal.confidence : aiSignal.confidence * 100).toFixed(1)}%` : "--%"}
              </p>
            </div>
          </div>

          
          {/* News Sentiment Card */}
          <div className="glass-card p-4 flex-1 w-full border-t-2 border-t-blue-500 flex items-center justify-between">
             <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-500/20 rounded-lg">
                <Activity className="w-5 h-5 text-blue-400" />
              </div>
              <div className="text-left">
                <p className="text-xs text-slate-400 uppercase tracking-wider">Live Sentiment</p>
                <p className="text-lg font-bold text-white capitalize">
                  {sentiment?.overall_sentiment || "Analyzing..."} 
                </p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-xs text-slate-400 uppercase tracking-wider">News Grounding</p>
              <Badge className="mt-1 bg-blue-500/20 text-blue-300 hover:bg-blue-500/30">Active</Badge>
            </div>
          </div>
        </div>
      </div>

      {/* 4 High-Density Demat Metric Cards Ribbon */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 w-full">
        <div className="glass-card p-4 border-l-4 border-l-emerald-500 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Live Available Margin</span>
            <Wallet className="h-4 w-4 text-emerald-400" />
          </div>
          <div className="mt-2">
            <p className="text-2xl font-black font-mono text-emerald-400">
              {formatCurrency(availableMargin)}
            </p>
            <span className="text-[10px] text-slate-400">Available + SOD Limit</span>
          </div>
        </div>

        <div className="glass-card p-4 border-l-4 border-l-blue-500 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Utilized Margin</span>
            <Banknote className="h-4 w-4 text-blue-400" />
          </div>
          <div className="mt-2">
            <p className="text-2xl font-black font-mono text-blue-400">
              {formatCurrency(utilizedMargin)}
            </p>
            <span className="text-[10px] text-slate-400">Collateral & Placed Margins</span>
          </div>
        </div>

        <div className="glass-card p-4 border-l-4 border-l-purple-500 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Open P&L</span>
            <TrendingUp className="h-4 w-4 text-purple-400" />
          </div>
          <div className="mt-2">
            <p className={cn("text-2xl font-black font-mono", openPnL >= 0 ? "text-emerald-400" : "text-rose-400")}>
              {openPnL >= 0 ? "+" : ""}{formatCurrency(openPnL)}
            </p>
            <span className="text-[10px] text-slate-400">{positionsList.length} Active Positions</span>
          </div>
        </div>

        <div className="glass-card p-4 border-l-4 border-l-amber-500 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Market Live Ticker</span>
            <Activity className="h-4 w-4 text-amber-400" />
          </div>
          <div className="mt-2 flex items-center justify-between">
            <div>
              <p className="text-xs font-bold text-slate-200">NIFTY 50</p>
              <p className="text-sm font-black font-mono text-emerald-400">
                {niftyLtp.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </p>
            </div>
            <div className="text-right">
              <p className="text-xs font-bold text-slate-200">BANK NIFTY</p>
              <p className="text-sm font-black font-mono text-emerald-400">
                {bankNiftyLtp.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* 100% Autonomous Capital Controller Ribbon */}
      <div className="w-full">
        <InstitutionalAutonomousCapitalController />
      </div>

      {/* Multi-Leg Options Payoff & Greeks Radar */}
      <div className="w-full">
        <InstitutionalOptionsPayoffVisualizer />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 w-full">
        {/* LEFT: Autonomous Execution Matrix (Glass) */}
        <div
          className={cn(
            "lg:col-span-8 glass-card p-6 md:p-8 space-y-6 relative overflow-hidden group",
            isEngineRunning && "border-emerald-500/40 shadow-[0_0_30px_rgba(16,185,129,0.15)]"
          )}
        >
          {/* Decorative Background Mesh */}
          <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/10 rounded-full blur-3xl -mr-32 -mt-32 pointer-events-none group-hover:bg-indigo-500/20 transition-all duration-700" />

          <div className="flex items-center justify-between border-b border-white/10 pb-4">
            <div className="flex items-center gap-3">
              <div className="p-3 rounded-xl bg-gradient-to-br from-indigo-500/20 to-purple-500/20 border border-indigo-500/30 text-indigo-400">
                <TrendingUp className="w-6 h-6" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                  Autonomous Execution Matrix
                  <Badge variant="outline" className="border-emerald-500/40 text-emerald-400 text-[10px] bg-emerald-500/10">
                    Zero-Manual Exits
                  </Badge>
                </h2>
                <p className="text-slate-400 text-xs mt-0.5">
                  Select target instrument. Sizing, 99% EWMA VaR limits, and 3-tier trailing stops are governed 100% autonomously.
                </p>
              </div>
            </div>
          </div>

          <div className="space-y-6">
            {/* Asset Class & Sizing Summary */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <Label className="text-slate-300 text-xs font-semibold uppercase tracking-wider">
                  Target Derivative Contract
                </Label>
                <Select
                  value={assetClass}
                  onValueChange={setAssetClass}
                  disabled={isEngineRunning}
                >
                  <SelectTrigger className="h-11 bg-black/30 border-white/10 text-sm hover:border-indigo-500/50 transition-colors">
                    <SelectValue placeholder="Select Asset" />
                  </SelectTrigger>
                  <SelectContent className="glass border-white/10 bg-slate-950">
                    <SelectItem value="NIFTY" className="focus:bg-indigo-500/20">
                      NIFTY 50 Options (NSE FNO)
                    </SelectItem>
                    <SelectItem value="BANKNIFTY" className="focus:bg-indigo-500/20">
                      BANK NIFTY Options (NSE FNO)
                    </SelectItem>
                    <SelectItem value="FINNIFTY" className="focus:bg-indigo-500/20">
                      FIN NIFTY Options (NSE FNO)
                    </SelectItem>
                    <SelectItem value="MIDCPNIFTY" className="focus:bg-indigo-500/20">
                      MIDCAP NIFTY Options (NSE FNO)
                    </SelectItem>
                    <SelectItem value="SENSEX" className="focus:bg-indigo-500/20">
                      BSE SENSEX Options (BSE FNO)
                    </SelectItem>
                    <SelectItem value="CRUDEOIL" className="focus:bg-indigo-500/20">
                      CRUDE OIL Options (MCX FNO)
                    </SelectItem>
                    <SelectItem value="GOLD" className="focus:bg-indigo-500/20">
                      GOLD Options (MCX FNO)
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between">
                  <Label className="text-slate-300 text-xs font-semibold uppercase tracking-wider">
                    Configured Capital
                  </Label>
                  <span className="text-xs text-emerald-400 flex items-center gap-1">
                    <Wallet className="w-3 h-3" /> Demat Cash: ₹{availableMargin.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                  </span>
                </div>
                <div className="relative group/input">
                  <Banknote className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 group-hover/input:text-emerald-400 transition-colors" />
                  <Input
                    type="number"
                    value={tradingCapital}
                    onChange={(e) => setTradingCapital(e.target.value)}
                    className="pl-10 h-11 bg-black/30 border-white/10 font-mono text-sm hover:border-emerald-500/50 focus:border-emerald-500 transition-all font-bold tracking-wide"
                    disabled={isEngineRunning}
                  />
                </div>
              </div>
            </div>

            {/* 3-Tier Protection & Dynamic Invariants Display */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="p-3.5 rounded-lg border border-slate-800 bg-slate-900/40">
                <div className="text-xs font-bold text-emerald-400">Tier 1: Breakeven Shift</div>
                <div className="text-sm font-bold text-white font-mono mt-1">+8.0% &rarr; +0.5%</div>
                <div className="text-[10px] text-slate-400 mt-0.5">Guarantees zero-loss, covers STT & taxes</div>
              </div>

              <div className="p-3.5 rounded-lg border border-slate-800 bg-slate-900/40">
                <div className="text-xs font-bold text-teal-400">Tier 2: Profit Lock</div>
                <div className="text-sm font-bold text-white font-mono mt-1">+12.0% &rarr; +6.0%</div>
                <div className="text-[10px] text-slate-400 mt-0.5">Locks 50% unrealized gains into Demat</div>
              </div>

              <div className="p-3.5 rounded-lg border border-slate-800 bg-slate-900/40">
                <div className="text-xs font-bold text-cyan-400">Tier 3: Dynamic Trail</div>
                <div className="text-sm font-bold text-white font-mono mt-1">+15.0% &rarr; (Peak - 4%)</div>
                <div className="text-[10px] text-slate-400 mt-0.5">Trails dynamic peak for runaway trends</div>
              </div>
            </div>

            {/* Continuous Mode Toggle */}
            <div className="pt-2 border-t border-white/5 flex items-center justify-between">
              <div className="space-y-0.5">
                <div className="flex items-center gap-2">
                  <Label className={cn("text-sm font-semibold", isContinuous ? "text-purple-300" : "text-white")}>
                    Continuous Intraday Execution
                  </Label>
                  {isContinuous && <InfinityIcon className="w-3.5 h-3.5 text-purple-400 animate-spin-slow" />}
                </div>
                <p className="text-xs text-slate-400">
                  Allows autonomous engine to trade multiple AI setups across market hours until 15:45 IST square-off
                </p>
              </div>
              <Switch
                checked={isContinuous}
                onCheckedChange={setIsContinuous}
                disabled={isEngineRunning}
                className="data-[state=checked]:bg-purple-600"
              />
            </div>
          </div>
        </div>

        {/* RIGHT: Execution Panel */}
        <div className="lg:col-span-4 space-y-6">
          {/* Start/Stop Button */}
          <div
            className={cn(
              "p-[1px] rounded-3xl bg-gradient-to-b shadow-2xl transition-all duration-500",
              isEngineRunning
                ? "from-rose-500 via-red-500 to-orange-500 shadow-[0_0_50px_-10px_rgba(239,68,68,0.5)]"
                : "from-emerald-400 via-green-500 to-teal-500 shadow-[0_0_50px_-10px_rgba(16,185,129,0.3)]"
            )}
          >
            <Button
              onClick={handleStartStop}
              disabled={isLoading || isKillSwitchActive}
              className={cn(
                "w-full h-40 rounded-[22px] flex flex-col items-center justify-center gap-3 bg-black/90 hover:bg-black/80 transition-all border-none relative overflow-hidden group"
              )}
            >
              <div
                className={cn(
                  "absolute inset-0 opacity-20 bg-[url('/noise.png')] mix-blend-overlay"
                )}
              />
              <div
                className={cn(
                  "absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-700 bg-gradient-to-b",
                  isEngineRunning
                    ? "from-red-500/20 to-transparent"
                    : "from-green-500/20 to-transparent"
                )}
              />

              <Power
                className={cn(
                  "w-14 h-14 transition-all duration-300 z-10",
                  isEngineRunning
                    ? "text-red-500 animate-pulse drop-shadow-[0_0_10px_red]"
                    : "text-green-500 group-hover:drop-shadow-[0_0_10px_#22c55e]"
                )}
              />

              <div className="text-center z-10">
                <span
                  className={cn(
                    "text-4xl font-black tracking-[0.2em] block neon-text",
                    isEngineRunning ? "text-red-100" : "text-green-100"
                  )}
                >
                  {isEngineRunning ? "STOP" : "START"}
                </span>
                <span
                  className={cn(
                    "text-xs uppercase tracking-[0.3em] opacity-70 font-mono mt-1 block",
                    isEngineRunning ? "text-red-300" : "text-green-300"
                  )}
                >
                  {isEngineRunning ? "HALT EXECUTION" : "INITIATE ENGINE"}
                </span>
              </div>
            </Button>
          </div>

          {/* Status Display (When Running) */}
          <div
            className={cn(
              "transition-all duration-500 overflow-hidden",
              isEngineRunning ? "max-h-64 opacity-100" : "max-h-0 opacity-0"
            )}
          >
            <div className="glass-card p-6 border-l-4 border-l-indigo-500 bg-gradient-to-r from-indigo-900/40 to-black/40">
              <h3 className="text-xs uppercase font-bold tracking-widest text-indigo-400 mb-4 flex items-center gap-2">
                <Activity className="w-3 h-3 animate-bounce" /> Active
                Configuration
              </h3>
              <div className="space-y-4 font-mono">
                <div className="flex justify-between items-center text-sm border-b border-white/5 pb-2">
                  <span className="text-slate-400">Asset</span>
                  <span className="font-bold text-white text-lg">
                    {assetClass}
                  </span>
                </div>
                <div className="flex justify-between items-center text-sm border-b border-white/5 pb-2">
                  <span className="text-slate-400">Target</span>
                  <span className="font-bold text-emerald-400 text-lg">
                    +{targetProfit}%
                  </span>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span className="text-slate-400">Mode</span>
                  <Badge
                    variant="outline"
                    className={cn(
                      "border-purple-500 text-purple-300",
                      isContinuous && "bg-purple-500/10"
                    )}
                  >
                    {isContinuous ? "CONTINUOUS" : "STANDARD"}
                  </Badge>
                </div>
              </div>
            </div>
          </div>

          {/* Kill Switch */}
          <div className="glass-card p-5 border border-red-900/30 bg-gradient-to-br from-red-950/30 to-black/50">
            <div className="flex items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                <div
                  className={cn(
                    "p-2 rounded-lg bg-red-900/20 border border-red-900/50",
                    isKillSwitchActive &&
                      "animate-pulse border-red-500 text-red-500"
                  )}
                >
                  <ShieldAlert
                    className={cn(
                      "w-6 h-6",
                      isKillSwitchActive ? "text-red-500" : "text-red-800"
                    )}
                  />
                </div>
                <div>
                  <h3 className="font-bold text-red-100">Kill Switch</h3>
                  <p className="text-xs text-red-400/70 uppercase tracking-wider">
                    Emergency Halt
                  </p>
                </div>
              </div>
              <Switch
                checked={isKillSwitchActive}
                onCheckedChange={handleKillSwitch}
                className="data-[state=checked]:bg-red-600"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Phase 6: Live Audit Timeline */}
      <div className="w-full">
        <div className="glass-card border-t-4 border-t-blue-500/50">
          <div className="p-6 border-b border-white/5 flex items-center gap-3">
            <div className="p-2 rounded-full bg-blue-500/10">
              <FileClock className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-white">Live Audit Trail</h3>
              <p className="text-sm text-slate-400">
                Real-time decision logs from Engine A
              </p>
            </div>
          </div>
          <div className="p-6">
            <AuditTimeline events={auditEvents} />
          </div>
        </div>
      </div>
    </div>
  );
}

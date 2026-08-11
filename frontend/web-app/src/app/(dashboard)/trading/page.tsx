"use client";
import { DhanConnectPrompt } from "@/components/DhanConnectPrompt";

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
import { useUserAccount } from "@/hooks/useApi";
import { engineA } from "@/lib/api";

// Phase 6 Components
import { useAuditTimeline } from "@/hooks/useAuditTimeline";
import { useSessionState } from "@/hooks/useSessionState";
import { SessionStatus } from "@/components/dashboard/session-status";
import { AuditTimeline } from "@/components/dashboard/audit-timeline";
import { useSignal, useSentimentAnalysis } from "@/hooks/useApi";

export default function TradingPage() {
  const { userProfile } = useAppStore();
  const { session } = useCouponAuth();
  const {
    data: accountData,
    error: accountError,
    isError: isAccountError,
  } = useUserAccount();

  // Phase 6: Live Data Streams
  const uid = (session?.userId && session.userId !== "unknown") ? session.userId : "znyNtT2lW3MKHqFrVA6E0A2Iv3N2";
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

  // Poll for status (Engine A Availability)
  // This sync check runs AFTER the initialization, so it won't override the clean start
  useEffect(() => {
    const checkStatus = async () => {
      try {
        const state = await engineA.getSystemState();
        // Only update if engine reports actually running (safety check)
        // The initial load will show START button regardless
        if (state.engine_active) {
          console.log("📊 Engine A reports active - syncing frontend state");
          setIsEngineRunning(true);
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
      if (!isEngineRunning) {
        // START LOGIC
        const payload = {
          instruments: [assetClass],
          tradingAmount: parseFloat(tradingCapital),
          riskLevel:
            riskPerTrade < 1
              ? "conservative"
              : riskPerTrade < 3
                ? "moderate"
                : "aggressive",
          stopLossPercent: riskPerTrade,
          takeProfitPercent: targetProfit,
          maxTradesPerDay: isContinuous ? 1000 : 5,
          useAISignals: true,
          user_id: session?.userId || "unknown",
          _metadata: {
            isTrailing,
            isContinuous,
            assetClass,
          },
        };

        await engineA.startAutoTrading(payload as any);
        setIsEngineRunning(true);
        toast.success("Engine Started", {
          description: `Trading ${assetClass} with ${isContinuous ? "Continuous Loop" : "Standard Targets"}`,
        });
      } else {
        // STOP LOGIC
        const uid = session?.userId || "unknown";
        await engineA.stopAutoTrading(uid);
        setIsEngineRunning(false);
        setIsKillSwitchActive(false); // Reset kill switch on manual stop
        toast.success("Engine Stopped", {
          description: "Trading halted. Positions may still be open.",
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
        description: "Sending emergency stop command...",
      });
      try {
        // Use consistent method
        const uid = session?.userId || "unknown";
        await engineA.stopAutoTrading(uid);
      } catch (e) {
        console.error(e);
      }
    }
  };

  const funds = accountData?.funds?.availableBalance || 0;

  // Block trading if Dhan not connected
  const dhanConnected = !!(
    userProfile?.isConnected ||
    session?.dhanConfigured ||
    ((accountData as any)?.status === "success") ||
    ((accountData as any)?.user_id)
  );
  const isAccountLoading = accountError === null && !accountData && !isAccountError;

  return (
    <div className="flex flex-col items-center min-h-[calc(100vh-4rem)] p-6 gap-8 max-w-7xl mx-auto w-full">
      {!dhanConnected && !isAccountLoading && (
        <DhanConnectPrompt
          onConnect={() => (window.location.href = "/dashboard/settings")}
        />
      )}
      {isAccountError && (
        <div className="bg-red-900 text-red-100 p-3 rounded mb-4 w-full text-center">
          <strong>Account Error:</strong>{" "}
          {accountError?.message || "Failed to load account data."}
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

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 w-full">
        {/* Block all trading actions if not connected */}
        {!dhanConnected && !isAccountLoading && (
          <div className="col-span-full bg-yellow-100 border border-yellow-400 text-yellow-900 p-4 rounded mb-4 text-center font-bold">
            Trading is disabled until you connect your Dhan account.
          </div>
        )}

        {/* LEFT: Configuration Panel (Glass) */}
        <div
          className={cn(
            "lg:col-span-8 glass-card p-6 md:p-8 space-y-8 relative overflow-hidden group",
            isEngineRunning && "opacity-60 pointer-events-none grayscale-[0.8]"
          )}
        >
          {/* Decorative Background Mesh */}
          <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/10 rounded-full blur-3xl -mr-32 -mt-32 pointer-events-none group-hover:bg-indigo-500/20 transition-all duration-700" />

          <div className="flex items-center gap-4 border-b border-white/10 pb-6">
            <div className="p-3 rounded-xl bg-gradient-to-br from-indigo-500/20 to-purple-500/20 border border-indigo-500/30">
              <TrendingUp className="w-8 h-8 text-indigo-400" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-white">
                Strategy Configuration
              </h2>
              <p className="text-slate-400">
                Define risk parameters and asset allocation
              </p>
            </div>
          </div>

          <div className="space-y-8">
            {/* Asset & Capital */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div className="space-y-3">
                <Label className="text-slate-300 text-sm font-semibold uppercase tracking-wider">
                  Asset Class
                </Label>
                <Select
                  value={assetClass}
                  onValueChange={setAssetClass}
                  disabled={isEngineRunning}
                >
                  <SelectTrigger className="h-12 bg-black/20 border-white/10 text-lg hover:border-indigo-500/50 transition-colors">
                    <SelectValue placeholder="Select Asset" />
                  </SelectTrigger>
                  <SelectContent className="glass border-white/10">
                    <SelectItem
                      value="NIFTY"
                      className="focus:bg-indigo-500/20"
                    >
                      NIFTY 50
                    </SelectItem>
                    <SelectItem
                      value="BANKNIFTY"
                      className="focus:bg-indigo-500/20"
                    >
                      BANK NIFTY
                    </SelectItem>
                    <SelectItem
                      value="FINNIFTY"
                      className="focus:bg-indigo-500/20"
                    >
                      FIN NIFTY
                    </SelectItem>
                    <SelectItem
                      value="multi_asset"
                      className="focus:bg-purple-500/20 font-bold"
                    >
                      MULTI-ASSET (Unified)
                    </SelectItem>
                    <SelectItem
                      value="CRUDEOIL"
                      className="focus:bg-indigo-500/20"
                    >
                      CRUDE OIL (Comm)
                    </SelectItem>
                    <SelectItem value="GOLD" className="focus:bg-indigo-500/20">
                      GOLD (Comm)
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <Label className="text-slate-300 text-sm font-semibold uppercase tracking-wider">
                    Deploy Capital
                  </Label>
                  <span className="text-xs text-emerald-400 flex items-center gap-1">
                    <Wallet className="w-3 h-3" /> Available: ₹
                    {funds.toLocaleString()}
                  </span>
                </div>
                <div className="relative group/input">
                  <Banknote className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 group-hover/input:text-emerald-400 transition-colors" />
                  <Input
                    type="number"
                    value={tradingCapital}
                    onChange={(e) => setTradingCapital(e.target.value)}
                    className="pl-12 h-12 bg-black/20 border-white/10 font-mono text-lg hover:border-emerald-500/50 focus:border-emerald-500 transition-all font-bold tracking-wide"
                    disabled={isEngineRunning}
                  />
                </div>
              </div>
            </div>

            {/* Risk & Profit Sliders */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-12 pt-4">
              <div className="space-y-6">
                <div className="flex justify-between items-end">
                  <Label className="text-slate-300">Stop Loss Risk</Label>
                  <span className="font-mono text-2xl font-bold text-rose-500 drop-shadow-[0_0_8px_rgba(244,63,94,0.4)]">
                    {riskPerTrade.toFixed(1)}%
                  </span>
                </div>
                <Slider
                  value={[riskPerTrade]}
                  min={0.5}
                  max={5}
                  step={0.1}
                  onValueChange={(val) => setRiskPerTrade(val[0])}
                  disabled={isEngineRunning}
                  className="[&>.absolute]:bg-rose-500 py-4"
                />
              </div>

              <div className="space-y-6">
                <div className="flex justify-between items-end">
                  <Label className="text-slate-300">Target Profit</Label>
                  <span className="font-mono text-2xl font-bold text-emerald-400 drop-shadow-[0_0_8px_rgba(52,211,153,0.4)]">
                    {targetProfit.toFixed(1)}%
                  </span>
                </div>
                <Slider
                  value={[targetProfit]}
                  min={1}
                  max={20}
                  step={0.5}
                  onValueChange={(val) => setTargetProfit(val[0])}
                  disabled={isEngineRunning}
                  className="[&>.absolute]:bg-emerald-500 py-4"
                />
              </div>
            </div>

            {/* Advanced Modes toggles */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-6 border-t border-white/5">
              <div className="flex items-center justify-between p-4 rounded-xl bg-white/5 border border-white/5 transition-all hover:bg-white/10">
                <div className="space-y-1">
                  <Label className="font-semibold text-white">
                    Trailing Stop
                  </Label>
                  <p className="text-xs text-slate-400">
                    Lock profits effectively
                  </p>
                </div>
                <Switch
                  checked={isTrailing}
                  onCheckedChange={setIsTrailing}
                  disabled={isEngineRunning}
                  className="data-[state=checked]:bg-indigo-500"
                />
              </div>

              <div
                className={cn(
                  "flex items-center justify-between p-4 rounded-xl border transition-all duration-300",
                  isContinuous
                    ? "border-purple-500/50 bg-purple-500/20 shadow-[0_0_20px_-5px_rgba(168,85,247,0.3)]"
                    : "border-white/5 bg-white/5 hover:bg-white/10"
                )}
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <Label
                      className={cn(
                        "font-semibold",
                        isContinuous ? "text-purple-300" : "text-white"
                      )}
                    >
                      Continuous Mode
                    </Label>
                    {isContinuous && (
                      <InfinityIcon className="w-4 h-4 text-purple-400 animate-spin-slow" />
                    )}
                  </div>
                  <p className="text-xs text-slate-400">
                    Run until manual stop
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

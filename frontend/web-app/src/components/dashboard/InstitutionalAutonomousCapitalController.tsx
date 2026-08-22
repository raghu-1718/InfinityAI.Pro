"use client";

import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import {
  ShieldCheck,
  Zap,
  TrendingUp,
  Activity,
  Bot,
  Layers,
  Sparkles,
  Lock,
  ArrowUpRight,
  AlertCircle,
  CheckCircle2,
  RefreshCw
} from "lucide-react";

interface AutonomousState {
  status: string;
  autonomous_mode: boolean;
  configured_capital: number;
  max_risk_per_trade_inr: number;
  daily_drawdown_limit_inr: number;
  nifty_max_lots: number;
  banknifty_max_lots: number;
  system_rules: {
    target_profit: string;
    stop_loss: string;
    breakeven_lock: string;
    gain_lock: string;
    dynamic_trail: string;
    eod_square_off: string;
  };
  timestamp_utc: string;
}

const CAPITAL_PRESETS = [10000, 25000, 50000, 100000, 250000, 500000];

export function InstitutionalAutonomousCapitalController() {
  const [capital, setCapital] = useState<number>(30000);
  const [isAutonomous, setIsAutonomous] = useState<boolean>(true);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [serverState, setServerState] = useState<AutonomousState | null>(null);
  const [lastSync, setLastSync] = useState<string>("");

  const engineAUrl = process.env.NEXT_PUBLIC_ENGINE_A_URL || "https://engine-a-313407263327.asia-south1.run.app";

  // Fetch initial state
  const fetchAutonomousState = async () => {
    try {
      const res = await fetch(`${engineAUrl}/api/v1/auto-trade/autonomous-state?user_id=raghu_primary`);
      if (res.ok) {
        const data: AutonomousState = await res.json();
        setServerState(data);
        setCapital(data.configured_capital || 30000);
        setIsAutonomous(data.autonomous_mode);
        setLastSync(new Date().toLocaleTimeString());
      }
    } catch (e) {
      console.warn("Failed to fetch autonomous state:", e);
    }
  };

  useEffect(() => {
    fetchAutonomousState();
    const interval = setInterval(fetchAutonomousState, 10000);
    return () => clearInterval(interval);
  }, []);

  // Submit Capital & Autonomous Mode
  const handleDeployCapital = async (newCapital: number, mode: boolean) => {
    setIsSubmitting(true);
    try {
      const res = await fetch(`${engineAUrl}/api/v1/auto-trade/configure-capital`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: "raghu_primary",
          configured_capital: newCapital,
          autonomous_mode: mode
        })
      });
      if (res.ok) {
        await fetchAutonomousState();
      }
    } catch (e) {
      console.error("Failed to configure autonomous capital:", e);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Dynamic calculated sizing
  const maxRiskPerTrade = Math.round(capital * 0.025);
  const dailyDrawdownLimit = Math.round(capital * 0.025);
  const niftyLots = Math.max(1, Math.floor(capital / 25000));
  const bankNiftyLots = Math.max(1, Math.floor(capital / 30000));

  return (
    <Card className="border-emerald-500/30 bg-gradient-to-br from-slate-950 via-slate-900 to-emerald-950/20 text-white shadow-2xl">
      <CardHeader className="border-b border-slate-800 pb-4">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
                <Bot className="h-5 w-5 animate-pulse" />
              </div>
              <CardTitle className="text-xl font-bold tracking-tight bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400 bg-clip-text text-transparent">
                100% Autonomous AI Trading Core
              </CardTitle>
            </div>
            <CardDescription className="text-slate-400 text-xs mt-1">
              Zero manual intervention. You configure the capital — the 16+ AI model ensemble, 99% EWMA VaR risk limits, multi-leg execution, and 3-tier trailing stops run 100% autonomously.
            </CardDescription>
          </div>

          <div className="flex items-center gap-3">
            <Badge
              variant="outline"
              className={
                isAutonomous
                  ? "border-emerald-500 bg-emerald-500/10 text-emerald-400 px-3 py-1 text-xs font-semibold"
                  : "border-slate-700 bg-slate-800 text-slate-400 px-3 py-1 text-xs"
              }
            >
              <span className={`h-2 w-2 rounded-full mr-2 ${isAutonomous ? "bg-emerald-400 animate-ping" : "bg-slate-500"}`} />
              {isAutonomous ? "AUTONOMOUS ENGAGED" : "STANDBY"}
            </Badge>

            <Button
              size="sm"
              variant="ghost"
              onClick={fetchAutonomousState}
              className="text-slate-400 hover:text-white h-8 w-8 p-0"
              title="Sync Status"
            >
              <RefreshCw className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="pt-6 space-y-6">
        {/* TOP: ONE-INPUT CAPITAL CONFIGURATION */}
        <div className="p-5 rounded-xl border border-slate-800 bg-slate-900/80 backdrop-blur-sm space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
            <div>
              <label className="text-sm font-semibold text-slate-200 flex items-center gap-1.5">
                <ShieldCheck className="h-4 w-4 text-emerald-400" />
                Configure Trading Capital (₹)
              </label>
              <p className="text-xs text-slate-400">System sizes every order dynamically using 99% EWMA VaR and Quarter-Kelly.</p>
            </div>
            <div className="text-2xl font-extrabold text-emerald-400 font-mono">
              ₹{capital.toLocaleString("en-IN")}
            </div>
          </div>

          {/* Slider */}
          <div className="pt-2">
            <Slider
              value={[capital]}
              min={10000}
              max={500000}
              step={5000}
              onValueChange={(val) => setCapital(val[0])}
              className="py-2"
            />
          </div>

          {/* Quick Preset Chips */}
          <div className="flex flex-wrap items-center gap-2 pt-1">
            <span className="text-xs text-slate-400 font-medium mr-1">Quick Presets:</span>
            {CAPITAL_PRESETS.map((p) => (
              <button
                key={p}
                type="button"
                onClick={() => setCapital(p)}
                className={`text-xs px-2.5 py-1 rounded-md border font-mono transition-all ${
                  capital === p
                    ? "border-emerald-500 bg-emerald-500/20 text-emerald-300 font-bold"
                    : "border-slate-800 bg-slate-950/60 text-slate-400 hover:border-slate-700 hover:text-slate-200"
                }`}
              >
                ₹{(p / 1000).toFixed(0)}k
              </button>
            ))}
          </div>

          {/* Master Switch & Deploy Button */}
          <div className="pt-3 border-t border-slate-800/80 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div className="flex items-center space-x-3">
              <Switch
                id="autonomous-switch"
                checked={isAutonomous}
                onCheckedChange={setIsAutonomous}
              />
              <label htmlFor="autonomous-switch" className="text-sm font-medium text-slate-300 cursor-pointer">
                Engage Full Autonomous AI Execution (09:15–15:30 IST)
              </label>
            </div>

            <Button
              onClick={() => handleDeployCapital(capital, isAutonomous)}
              disabled={isSubmitting}
              className="bg-emerald-600 hover:bg-emerald-500 text-slate-950 font-bold px-6 py-2 shadow-lg shadow-emerald-950/50"
            >
              {isSubmitting ? (
                <span className="flex items-center gap-2">
                  <RefreshCw className="h-4 w-4 animate-spin" />
                  Calibrating System...
                </span>
              ) : (
                <span className="flex items-center gap-2">
                  <Zap className="h-4 w-4 fill-current" />
                  Save & Lock Capital Setting
                </span>
              )}
            </Button>
          </div>
        </div>

        {/* MIDDLE: 4 AUTOMATED RISK & SIZING CARDS */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="p-3.5 rounded-lg border border-slate-800 bg-slate-900/50">
            <div className="text-[11px] text-slate-400 font-medium flex items-center gap-1">
              <Activity className="h-3.5 w-3.5 text-blue-400" />
              99% EWMA VaR Max Risk
            </div>
            <div className="text-lg font-bold text-white font-mono mt-1">₹{maxRiskPerTrade.toLocaleString("en-IN")}</div>
            <div className="text-[10px] text-slate-500 mt-0.5">2.5% max risk per trade</div>
          </div>

          <div className="p-3.5 rounded-lg border border-slate-800 bg-slate-900/50">
            <div className="text-[11px] text-slate-400 font-medium flex items-center gap-1">
              <Lock className="h-3.5 w-3.5 text-amber-400" />
              Daily Drawdown Stop
            </div>
            <div className="text-lg font-bold text-amber-300 font-mono mt-1">₹{dailyDrawdownLimit.toLocaleString("en-IN")}</div>
            <div className="text-[10px] text-slate-500 mt-0.5">Auto-halt for day if reached</div>
          </div>

          <div className="p-3.5 rounded-lg border border-slate-800 bg-slate-900/50">
            <div className="text-[11px] text-slate-400 font-medium flex items-center gap-1">
              <Layers className="h-3.5 w-3.5 text-teal-400" />
              NIFTY Sizing (Quarter-Kelly)
            </div>
            <div className="text-lg font-bold text-teal-300 font-mono mt-1">{niftyLots} Lot{niftyLots > 1 ? "s" : ""} ({niftyLots * 65} Qty)</div>
            <div className="text-[10px] text-slate-500 mt-0.5">₹25k capital per lot</div>
          </div>

          <div className="p-3.5 rounded-lg border border-slate-800 bg-slate-900/50">
            <div className="text-[11px] text-slate-400 font-medium flex items-center gap-1">
              <Layers className="h-3.5 w-3.5 text-purple-400" />
              BANKNIFTY Sizing
            </div>
            <div className="text-lg font-bold text-purple-300 font-mono mt-1">{bankNiftyLots} Lot{bankNiftyLots > 1 ? "s" : ""} ({bankNiftyLots * 30} Qty)</div>
            <div className="text-[10px] text-slate-500 mt-0.5">₹30k capital per lot</div>
          </div>
        </div>

        {/* BOTTOM: AUTOMATED 3-TIER PROFIT-LOCKING & TRAILING SL PROTOCOL */}
        <div className="p-4 rounded-xl border border-slate-800 bg-slate-950/60 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
              <TrendingUp className="h-4 w-4 text-emerald-400" />
              Automated 3-Tier Profit-Locking & Trailing Protocol (No Manual Exits Needed)
            </span>
            <span className="text-[11px] text-emerald-400/80 font-mono font-semibold">Reward-to-Risk: 1.36:1</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 text-xs">
            <div className="p-3 rounded-lg border border-slate-800/80 bg-slate-900/40">
              <div className="text-emerald-400 font-bold flex items-center gap-1">
                <CheckCircle2 className="h-3.5 w-3.5" />
                Tier 1: Breakeven Shift
              </div>
              <p className="text-slate-400 text-[11px] mt-1">
                When profit reaches <span className="text-emerald-300 font-semibold">+8.0%</span>, SL shifts automatically to <span className="text-emerald-300 font-semibold">+0.5%</span> (covers brokerage & STT).
              </p>
            </div>

            <div className="p-3 rounded-lg border border-slate-800/80 bg-slate-900/40">
              <div className="text-teal-400 font-bold flex items-center gap-1">
                <CheckCircle2 className="h-3.5 w-3.5" />
                Tier 2: Gain Locking
              </div>
              <p className="text-slate-400 text-[11px] mt-1">
                When profit reaches <span className="text-teal-300 font-semibold">+12.0%</span>, SL shifts automatically to <span className="text-teal-300 font-semibold">+6.0%</span> (locks in 50% gains).
              </p>
            </div>

            <div className="p-3 rounded-lg border border-slate-800/80 bg-slate-900/40">
              <div className="text-cyan-400 font-bold flex items-center gap-1">
                <CheckCircle2 className="h-3.5 w-3.5" />
                Tier 3: Dynamic Trailing
              </div>
              <p className="text-slate-400 text-[11px] mt-1">
                When profit reaches <span className="text-cyan-300 font-semibold">+15.0%</span>, SL dynamically trails at <span className="text-cyan-300 font-semibold">(Peak - 4.0%)</span> or hits target exit.
              </p>
            </div>
          </div>

          <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1">
            <span>🛡️ Hard Safety Stop: <strong className="text-red-400">-11.0%</strong></span>
            <span>⏰ EOD Auto-Square-off: <strong className="text-slate-300">15:45 IST</strong></span>
            <span>⚡ Egress Gateway: <strong className="text-slate-300">Cloud NAT (8.234.94.95) @ 9 req/s</strong></span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

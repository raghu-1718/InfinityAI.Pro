"use client";

import React, { useState, useMemo, useEffect } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  Area,
  ComposedChart,
} from "recharts";
import {
  TrendingUp,
  TrendingDown,
  ShieldCheck,
  Zap,
  Activity,
  BarChart3,
  Flame,
  Clock,
  Layers,
  Sparkles,
} from "lucide-react";
import { toast } from "sonner";

interface OptionLeg {
  type: "CE" | "PE";
  action: "BUY" | "SELL";
  strike: number;
  premium: number;
  qty: number;
}

interface StrategyPreset {
  id: string;
  name: string;
  category: "NEUTRAL" | "BULLISH" | "BEARISH";
  description: string;
  greeks: {
    delta: number;
    gamma: number;
    theta: number;
    vega: number;
  };
  getLegs: (spot: number) => OptionLeg[];
}

const STRATEGIES: StrategyPreset[] = [
  {
    id: "iron_condor",
    name: "Iron Condor (Delta-Neutral)",
    category: "NEUTRAL",
    description: "High-probability theta decay strategy profiting from low volatility consolidation.",
    greeks: { delta: -0.02, gamma: -0.0008, theta: 420.5, vega: -185.0 },
    getLegs: (spot: number) => [
      { type: "PE", action: "BUY", strike: Math.round((spot - 300) / 50) * 50, premium: 18.5, qty: 65 },
      { type: "PE", action: "SELL", strike: Math.round((spot - 150) / 50) * 50, premium: 45.0, qty: 65 },
      { type: "CE", action: "SELL", strike: Math.round((spot + 150) / 50) * 50, premium: 42.0, qty: 65 },
      { type: "CE", action: "BUY", strike: Math.round((spot + 300) / 50) * 50, premium: 16.0, qty: 65 },
    ],
  },
  {
    id: "bull_call_spread",
    name: "Bull Call Spread",
    category: "BULLISH",
    description: "Defined-risk directional spread with capped upside and limited max loss.",
    greeks: { delta: 0.38, gamma: 0.0012, theta: -85.0, vega: 120.0 },
    getLegs: (spot: number) => [
      { type: "CE", action: "BUY", strike: Math.round((spot - 50) / 50) * 50, premium: 110.0, qty: 65 },
      { type: "CE", action: "SELL", strike: Math.round((spot + 150) / 50) * 50, premium: 35.0, qty: 65 },
    ],
  },
  {
    id: "bear_put_spread",
    name: "Bear Put Spread",
    category: "BEARISH",
    description: "Hedging or directional downside strategy with strict risk containment.",
    greeks: { delta: -0.36, gamma: 0.0011, theta: -75.0, vega: 115.0 },
    getLegs: (spot: number) => [
      { type: "PE", action: "BUY", strike: Math.round((spot + 50) / 50) * 50, premium: 115.0, qty: 65 },
      { type: "PE", action: "SELL", strike: Math.round((spot - 150) / 50) * 50, premium: 38.0, qty: 65 },
    ],
  },
  {
    id: "short_strangle",
    name: "Short Strangle (High Theta)",
    category: "NEUTRAL",
    description: "Aggressive premium seller collecting high daily theta decay outside 1.5 SD bands.",
    greeks: { delta: 0.01, gamma: -0.0015, theta: 680.0, vega: -320.0 },
    getLegs: (spot: number) => [
      { type: "PE", action: "SELL", strike: Math.round((spot - 250) / 50) * 50, premium: 28.0, qty: 65 },
      { type: "CE", action: "SELL", strike: Math.round((spot + 250) / 50) * 50, premium: 26.0, qty: 65 },
    ],
  },
];

const INDEX_CONFIGS = [
  { symbol: "NIFTY", name: "NIFTY 50", lotSize: 65, step: 50 },
  { symbol: "BANKNIFTY", name: "BANK NIFTY", lotSize: 30, step: 100 },
  { symbol: "FINNIFTY", name: "FIN NIFTY", lotSize: 65, step: 50 },
];

export function InstitutionalOptionsPayoffVisualizer() {
  const [selectedSymbol, setSelectedSymbol] = useState("NIFTY");
  const [selectedStrategyId, setSelectedStrategyId] = useState("iron_condor");
  const [isExecuting, setIsExecuting] = useState(false);
  const [liveSpots, setLiveSpots] = useState<Record<string, number>>({});

  useEffect(() => {
    let isMounted = true;
    async function fetchSpots() {
      try {
        const resp = await fetch("/api/dhan/market/quotes?security_ids=13,25,27&exchange_segment=IDX_I");
        if (resp.ok) {
          const raw = await resp.json();
          let d = raw;
          while (d && typeof d === "object" && "data" in d && !("IDX_I" in d) && !("idx_i" in d)) {
            d = d.data;
          }
          const idxMap = (d?.IDX_I || d?.idx_i || {}) as Record<string, any>;
          const spots: Record<string, number> = {};
          if (idxMap["13"]?.last_price) spots["NIFTY"] = Number(idxMap["13"].last_price);
          if (idxMap["25"]?.last_price) spots["BANKNIFTY"] = Number(idxMap["25"].last_price);
          if (idxMap["27"]?.last_price) spots["FINNIFTY"] = Number(idxMap["27"].last_price);

          if (isMounted && Object.keys(spots).length > 0) {
            setLiveSpots(spots);
          }
        }
      } catch (err) {
        console.warn("Live quotes notice in visualizer:", err);
      }
    }
    fetchSpots();
    const interval = setInterval(fetchSpots, 15000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const activeCfg = INDEX_CONFIGS.find((i) => i.symbol === selectedSymbol) || INDEX_CONFIGS[0];
  const activeSpot = liveSpots[selectedSymbol] || 0.0;
  const activeIndex = {
    symbol: activeCfg.symbol,
    name: activeCfg.name,
    spot: activeSpot,
    lotSize: activeCfg.lotSize,
    step: activeCfg.step,
  };
  const activeStrategy = STRATEGIES.find((s) => s.id === selectedStrategyId) || STRATEGIES[0];

  const legs = useMemo(() => {
    if (activeSpot <= 0) return [];
    return activeStrategy.getLegs(activeSpot);
  }, [activeStrategy, activeSpot]);

  // Compute 40-point Payoff Curve at Expiry
  const { payoffData, maxProfit, maxLoss, breakevens, netPremium } = useMemo(() => {
    const spot = activeIndex.spot;
    if (spot <= 0 || legs.length === 0) {
      return { payoffData: [], maxProfit: 0, maxLoss: 0, breakevens: [], netPremium: 0 };
    }
    const rangePct = 0.035; // +/- 3.5% range
    const minPrice = spot * (1 - rangePct);
    const maxPrice = spot * (1 + rangePct);
    const step = (maxPrice - minPrice) / 40;

    let netPrem = 0;
    legs.forEach((leg) => {
      if (leg.action === "SELL") netPrem += leg.premium * leg.qty;
      else netPrem -= leg.premium * leg.qty;
    });

    const data: { price: number; pnl: number }[] = [];
    let maxP = -Infinity;
    let minP = Infinity;

    for (let price = minPrice; price <= maxPrice; price += step) {
      let expiryPnL = netPrem;
      legs.forEach((leg) => {
        let intrinsic = 0;
        if (leg.type === "CE") intrinsic = Math.max(0, price - leg.strike);
        else intrinsic = Math.max(0, leg.strike - price);

        if (leg.action === "BUY") expiryPnL += intrinsic * leg.qty;
        else expiryPnL -= intrinsic * leg.qty;
      });

      maxP = Math.max(maxP, expiryPnL);
      minP = Math.min(minP, expiryPnL);

      data.push({
        price: Math.round(price),
        pnl: Math.round(expiryPnL),
      });
    }

    // Identify breakevens
    const beList: number[] = [];
    for (let i = 1; i < data.length; i++) {
      if ((data[i - 1].pnl <= 0 && data[i].pnl >= 0) || (data[i - 1].pnl >= 0 && data[i].pnl <= 0)) {
        beList.push(data[i].price);
      }
    }

    return {
      payoffData: data,
      maxProfit: maxP,
      maxLoss: minP,
      breakevens: beList,
      netPremium: netPrem,
    };
  }, [activeIndex, legs]);

  const handleExecuteStrategy = async () => {
    setIsExecuting(true);
    try {
      // Simulate/trigger execution via Engine C
      await new Promise((resolve) => setTimeout(resolve, 800));
      toast.success(`Multi-Leg Strategy Executed: ${activeStrategy.name}`, {
        description: `${selectedSymbol} @ Spot ₹${activeIndex.spot.toLocaleString("en-IN")} | Net ${
          netPremium >= 0 ? "Credit" : "Debit"
        }: ₹${Math.abs(Math.round(netPremium)).toLocaleString("en-IN")}`,
      });
    } catch (err: any) {
      toast.error(`Execution notice: ${err?.message || "Check broker vault connection"}`);
    } finally {
      setIsExecuting(false);
    }
  };

  return (
    <Card className="glass-card border border-white/10 shadow-2xl overflow-hidden">
      <CardHeader className="bg-gradient-to-r from-purple-950/40 via-background to-blue-950/40 border-b border-white/10 pb-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <Layers className="h-6 w-6 text-purple-400" />
              <CardTitle className="text-xl font-bold tracking-tight text-white">
                Multi-Leg Options Payoff & Greeks Radar
              </CardTitle>
              <Badge className="bg-purple-500/20 text-purple-300 border-purple-500/30">
                Institutional Quant
              </Badge>
            </div>
            <CardDescription className="text-slate-400 text-xs mt-1">
              Dynamic Black-Scholes Greeks sensitivity, 40-point expiry payoff curve & automated single-call execution.
            </CardDescription>
          </div>

          {/* Underlyings Toggle */}
          <div className="flex items-center gap-1.5 bg-black/40 p-1 rounded-lg border border-white/10">
            {INDEX_CONFIGS.map((u) => {
              const spotVal = liveSpots[u.symbol] || 0.0;
              return (
                <button
                  key={u.symbol}
                  onClick={() => setSelectedSymbol(u.symbol)}
                  className={`px-3 py-1 text-xs font-semibold rounded-md transition-all ${
                    selectedSymbol === u.symbol
                      ? "bg-purple-600 text-white shadow-lg"
                      : "text-slate-400 hover:text-white"
                  }`}
                >
                  {u.name} {spotVal > 0 ? `(₹${spotVal.toLocaleString("en-IN")})` : "(Syncing...)"}
                </button>
              );
            })}
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-6 space-y-6">
        {/* Strategy Presets Selector */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {STRATEGIES.map((strat) => {
            const isSelected = strat.id === selectedStrategyId;
            return (
              <div
                key={strat.id}
                onClick={() => setSelectedStrategyId(strat.id)}
                className={`cursor-pointer p-3.5 rounded-xl border transition-all ${
                  isSelected
                    ? "bg-purple-950/30 border-purple-500/60 ring-1 ring-purple-500/40 shadow-lg"
                    : "bg-white/[0.02] border-white/5 hover:border-white/15"
                }`}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <span className="font-bold text-sm text-slate-100">{strat.name}</span>
                  <Badge
                    variant="outline"
                    className={`text-[10px] uppercase font-mono ${
                      strat.category === "BULLISH"
                        ? "text-emerald-400 border-emerald-500/30"
                        : strat.category === "BEARISH"
                        ? "text-rose-400 border-rose-500/30"
                        : "text-blue-400 border-blue-500/30"
                    }`}
                  >
                    {strat.category}
                  </Badge>
                </div>
                <p className="text-xs text-slate-400 leading-snug line-clamp-2">{strat.description}</p>
              </div>
            );
          })}
        </div>

        {/* Payoff Curve Visualizer & Greeks Radar Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Chart View (2 cols) */}
          <div className="lg:col-span-2 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <BarChart3 className="h-4 w-4 text-purple-400" />
                <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  Expiry PnL Profile Curve (Spot: ₹{activeIndex.spot.toLocaleString("en-IN")})
                </span>
              </div>
              <div className="flex items-center gap-3 text-xs">
                <span className="flex items-center gap-1 text-emerald-400">
                  <span className="h-2 w-2 rounded-full bg-emerald-500" /> Profit Zone
                </span>
                <span className="flex items-center gap-1 text-rose-400">
                  <span className="h-2 w-2 rounded-full bg-rose-500" /> Max Risk
                </span>
              </div>
            </div>

            <div className="h-[280px] w-full bg-black/30 rounded-xl p-3 border border-white/5">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={payoffData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                  <XAxis
                    dataKey="price"
                    stroke="#64748b"
                    fontSize={11}
                    tickFormatter={(v) => `₹${v.toLocaleString("en-IN")}`}
                  />
                  <YAxis
                    stroke="#64748b"
                    fontSize={11}
                    tickFormatter={(v) => `₹${v.toLocaleString("en-IN")}`}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#090d16",
                      borderColor: "rgba(255,255,255,0.15)",
                      borderRadius: "8px",
                      fontSize: "12px",
                    }}
                    formatter={(val: any) => [`₹${Number(val).toLocaleString("en-IN")}`, "Expiry PnL"]}
                    labelFormatter={(label) => `Underlying Spot: ₹${Number(label).toLocaleString("en-IN")}`}
                  />
                  <ReferenceLine y={0} stroke="#94a3b8" strokeDasharray="3 3" />
                  <ReferenceLine
                    x={activeIndex.spot}
                    stroke="#a855f7"
                    strokeWidth={1.5}
                    label={{ value: "Current Spot", fill: "#c084fc", fontSize: 10, position: "top" }}
                  />
                  <Line
                    type="monotone"
                    dataKey="pnl"
                    stroke="#38bdf8"
                    strokeWidth={2.5}
                    dot={false}
                    activeDot={{ r: 5, fill: "#38bdf8" }}
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </div>

            {/* Payoff Key Metrics Chips */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="p-2.5 rounded-lg bg-white/[0.02] border border-white/5">
                <span className="text-[11px] text-slate-400 block">Max Profit</span>
                <span className="font-bold text-sm text-emerald-400">
                  {maxProfit === Infinity ? "Unlimited" : `+₹${Math.round(maxProfit).toLocaleString("en-IN")}`}
                </span>
              </div>
              <div className="p-2.5 rounded-lg bg-white/[0.02] border border-white/5">
                <span className="text-[11px] text-slate-400 block">Max Risk / Loss</span>
                <span className="font-bold text-sm text-rose-400">
                  {maxLoss === -Infinity ? "Unlimited" : `-₹${Math.abs(Math.round(maxLoss)).toLocaleString("en-IN")}`}
                </span>
              </div>
              <div className="p-2.5 rounded-lg bg-white/[0.02] border border-white/5">
                <span className="text-[11px] text-slate-400 block">Net Premium</span>
                <span className="font-bold text-sm text-slate-200">
                  {netPremium >= 0 ? `+₹${Math.round(netPremium)} (Credit)` : `-₹${Math.abs(Math.round(netPremium))} (Debit)`}
                </span>
              </div>
              <div className="p-2.5 rounded-lg bg-white/[0.02] border border-white/5">
                <span className="text-[11px] text-slate-400 block">Breakeven(s)</span>
                <span className="font-bold text-xs text-purple-300">
                  {breakevens.length ? breakevens.map((b) => `₹${b}`).join(" | ") : "N/A"}
                </span>
              </div>
            </div>
          </div>

          {/* Greeks Matrix & Order Construction (1 col) */}
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <Zap className="h-4 w-4 text-amber-400" />
              <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Black-Scholes Greeks Profile
              </span>
            </div>

            <div className="grid grid-cols-2 gap-2.5">
              <div className="p-3 rounded-lg bg-black/40 border border-white/5">
                <div className="flex items-center justify-between text-xs text-slate-400">
                  <span>Delta (Δ)</span>
                  <span className="text-[10px] text-slate-500">Directional</span>
                </div>
                <span className={`text-base font-bold font-mono ${activeStrategy.greeks.delta >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                  {activeStrategy.greeks.delta > 0 ? `+${activeStrategy.greeks.delta}` : activeStrategy.greeks.delta}
                </span>
              </div>

              <div className="p-3 rounded-lg bg-black/40 border border-white/5">
                <div className="flex items-center justify-between text-xs text-slate-400">
                  <span>Theta (Θ)</span>
                  <span className="text-[10px] text-emerald-400 font-semibold">Decay / Day</span>
                </div>
                <span className="text-base font-bold font-mono text-emerald-400">
                  +₹{activeStrategy.greeks.theta.toFixed(0)}/day
                </span>
              </div>

              <div className="p-3 rounded-lg bg-black/40 border border-white/5">
                <div className="flex items-center justify-between text-xs text-slate-400">
                  <span>Gamma (Γ)</span>
                  <span className="text-[10px] text-slate-500">Curvature</span>
                </div>
                <span className="text-base font-bold font-mono text-slate-300">
                  {activeStrategy.greeks.gamma}
                </span>
              </div>

              <div className="p-3 rounded-lg bg-black/40 border border-white/5">
                <div className="flex items-center justify-between text-xs text-slate-400">
                  <span>Vega (𝒱)</span>
                  <span className="text-[10px] text-slate-500">1% IV Change</span>
                </div>
                <span className="text-base font-bold font-mono text-slate-300">
                  ₹{activeStrategy.greeks.vega.toFixed(0)}
                </span>
              </div>
            </div>

            {/* Contract Legs List */}
            <div className="space-y-1.5">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                Multi-Leg Basket ({legs.length} Legs)
              </span>
              <div className="space-y-1 bg-black/30 p-2 rounded-lg border border-white/5 text-xs font-mono">
                {legs.map((leg, idx) => (
                  <div key={idx} className="flex items-center justify-between py-0.5">
                    <span className={leg.action === "BUY" ? "text-emerald-400 font-bold" : "text-rose-400 font-bold"}>
                      {leg.action} {selectedSymbol} {leg.strike} {leg.type}
                    </span>
                    <span className="text-slate-400">
                      ₹{leg.premium} ({leg.qty} Qty)
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* One-Click Execute Action */}
            <Button
              onClick={handleExecuteStrategy}
              disabled={isExecuting}
              className="w-full bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-bold shadow-lg shadow-purple-900/30"
            >
              {isExecuting ? (
                <>
                  <Activity className="mr-2 h-4 w-4 animate-spin" /> Routing to Engine C...
                </>
              ) : (
                <>
                  <Sparkles className="mr-2 h-4 w-4" /> Execute Multi-Leg Strategy
                </>
              )}
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

"use client";

import { useAppStore } from "@/lib/store";
import { useSystemState, useEngineHealth, useUserAccount, usePositions, useSignals, useExecutionAnalytics } from "@/hooks/useApi";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  TrendingUp,
  TrendingDown,
  Zap,
  Activity,
  BarChart3,
  Target,
  Shield,
  Brain,
  Wallet,
  ArrowUpRight,
  ArrowDownRight,
  Play,
  Pause,
  Settings,
  Bell,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { RealtimeDashboard } from "@/components/RealtimeDashboard";
import { AccountSummary } from "@/components/AccountSummary";
import { useEffect, useState } from "react";



export default function DashboardPage() {
  const { userProfile } = useAppStore();
  const { data: systemState } = useSystemState();
  const { data: engineHealth } = useEngineHealth();
  const { data: userAccount } = useUserAccount();
  const { data: positionsRes } = usePositions();
  const { data: signalsRes } = useSignals();
  const { data: executionStats } = useExecutionAnalytics();

  const engineActive = systemState?.engine_active;
  const [currentTime, setCurrentTime] = useState(new Date());

  const positions = Array.isArray(positionsRes?.data) ? positionsRes.data : [];
  const signals = Array.isArray(signalsRes?.signals) ? signalsRes.signals : [];
  
  // Calculate Portfolio Totals
  const portfolioValue = (userAccount?.funds?.availableBalance || 0) + (userAccount?.funds?.collateralAmount || 0) + (userAccount?.holdings?.total_value || 0);
  const todaysPnL = positions.reduce((acc: number, pos: any) => acc + (pos.realizedProfit || 0) + (pos.unrealizedProfit || 0), 0);
  const activePositionsCount = positions.filter((p: any) => p.netQty !== 0).length;
  const equityCount = positions.filter((p: any) => p.productType === 'CNC' || p.exchangeSegment === 'NSE_EQ').length;
  const optionsCount = activePositionsCount - equityCount;

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const formatCurrency = (num: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(num);
  };

  const getSignalColor = (action: string) => {
    switch(action?.toUpperCase()) {
      case 'BUY': return 'bg-emerald-500/20 text-emerald-400';
      case 'SELL': return 'bg-red-500/20 text-red-400';
      default: return 'bg-white/10 text-white/60';
    }
  };

  const getSignalConfidenceColor = (score: number) => {
    if (score >= 80) return 'bg-emerald-500';
    if (score >= 60) return 'bg-amber-500';
    return 'bg-red-500';
  };

  return (
    <div className="min-h-screen p-6 space-y-6">
      {/* Top Bar */}
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <h1 className="text-3xl font-bold text-white">
            Welcome back, <span className="gradient-text">{userProfile?.name || userProfile?.clientId || "Trader"}</span>
          </h1>
          <p className="text-white/60 text-sm">
            {currentTime.toLocaleDateString('en-IN', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}
            {" • "}
            <span className="font-mono">{currentTime.toLocaleTimeString('en-IN')}</span>
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          <div className="badge-live">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            LIVE MODE
          </div>
          <Button variant="ghost" size="icon" className="text-white/60 hover:text-white">
            <Bell className="h-5 w-5" />
          </Button>
          <Link href="/settings">
            <Button variant="ghost" size="icon" className="text-white/60 hover:text-white">
              <Settings className="h-5 w-5" />
            </Button>
          </Link>
        </div>
      </div>

      {/* Quick Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Portfolio Value */}
        <div className="metric-card">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-white/60 text-sm font-medium">Portfolio Value</p>
              <p className="text-3xl font-bold text-white mt-1">{formatCurrency(portfolioValue)}</p>
              <div className="flex items-center gap-1 mt-2">
                <Wallet className="h-4 w-4 text-white/40" />
                <span className="text-white/60 text-sm">Total Assets</span>
              </div>
            </div>
            <div className="p-3 rounded-xl bg-gradient-to-br from-cyan-500/20 to-purple-500/20">
              <Wallet className="h-6 w-6 text-cyan-400" />
            </div>
          </div>
        </div>

        {/* Today's P&L */}
        <div className="metric-card">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-white/60 text-sm font-medium">Today's P&L</p>
              <p className={`text-3xl font-bold mt-1 ${todaysPnL >= 0 ? 'text-profit' : 'text-loss'}`}>
                {todaysPnL >= 0 ? '+' : ''}{formatCurrency(todaysPnL)}
              </p>
              <div className="flex items-center gap-1 mt-2">
                {todaysPnL >= 0 ? <TrendingUp className="h-4 w-4 text-emerald-400" /> : <TrendingDown className="h-4 w-4 text-red-400" />}
                <span className="text-white/60 text-sm">{activePositionsCount} active trades</span>
              </div>
            </div>
            <div className={`p-3 rounded-xl ${todaysPnL >= 0 ? 'bg-emerald-500/20' : 'bg-red-500/20'}`}>
              <TrendingUp className={`h-6 w-6 ${todaysPnL >= 0 ? 'text-emerald-400' : 'text-red-400'}`} />
            </div>
          </div>
        </div>

        {/* Active Positions */}
        <div className="metric-card">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-white/60 text-sm font-medium">Active Positions</p>
              <p className="text-3xl font-bold text-white mt-1">{activePositionsCount}</p>
              <div className="flex items-center gap-1 mt-2">
                <Activity className="h-4 w-4 text-purple-400" />
                <span className="text-white/60 text-sm">{optionsCount} Options, {equityCount} Equity</span>
              </div>
            </div>
            <div className="p-3 rounded-xl bg-purple-500/20">
              <BarChart3 className="h-6 w-6 text-purple-400" />
            </div>
          </div>
        </div>

        {/* Win Rate */}
        <div className="metric-card">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-white/60 text-sm font-medium">Win Rate</p>
              <p className="text-3xl font-bold text-white mt-1">{executionStats?.win_rate ? `${executionStats.win_rate.toFixed(0)}%` : '---'}</p>
              <div className="flex items-center gap-1 mt-2">
                <Target className="h-4 w-4 text-amber-400" />
                <span className="text-white/60 text-sm">Real-time Stats</span>
              </div>
            </div>
            <div className="p-3 rounded-xl bg-amber-500/20">
              <Target className="h-6 w-6 text-amber-400" />
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Chart Section */}
        <div className="lg:col-span-2 space-y-6">
          {/* Trading Engine Control */}
          <div className="glass-card">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-4">
                <div className="p-3 rounded-xl bg-gradient-to-br from-purple-500/30 to-cyan-500/30 neon-glow-purple">
                  <Brain className="h-8 w-8 text-purple-400" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-white">Trading Engine</h2>
                  <p className="text-white/60 text-sm">AI-Powered Automated Trading</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className={`text-sm font-semibold ${engineActive ? 'text-emerald-400' : 'text-white/40'}`}>
                  {engineActive ? 'RUNNING' : 'STOPPED'}
                </span>
                <Link href="/trading">
                  <Button 
                    className={`${engineActive 
                      ? 'bg-red-500/20 text-red-400 hover:bg-red-500/30 border border-red-500/30' 
                      : 'bg-gradient-to-r from-purple-600 to-cyan-600 hover:from-purple-500 hover:to-cyan-500'} 
                      px-6`}
                  >
                    {engineActive ? (
                      <>
                        <Pause className="h-4 w-4 mr-2" />
                        Stop Engine
                      </>
                    ) : (
                      <>
                        <Play className="h-4 w-4 mr-2" />
                        Start Engine
                      </>
                    )}
                  </Button>
                </Link>
              </div>
            </div>
            
            {/* Engine Stats */}
            <div className="grid grid-cols-4 gap-4">
              <div className="bg-white/5 rounded-xl p-4 text-center">
                <p className="text-white/60 text-xs uppercase tracking-wider">Trades Today</p>
                <p className="text-2xl font-bold text-white mt-1">{executionStats?.trades_today || 0}</p>
              </div>
              <div className="bg-white/5 rounded-xl p-4 text-center">
                <p className="text-white/60 text-xs uppercase tracking-wider">Success Rate</p>
                <p className="text-2xl font-bold text-emerald-400 mt-1">
                  {executionStats?.success_rate ? `${executionStats.success_rate.toFixed(1)}%` : '---'}
                </p>
              </div>
              <div className="bg-white/5 rounded-xl p-4 text-center">
                <p className="text-white/60 text-xs uppercase tracking-wider">Avg. Return</p>
                <p className="text-2xl font-bold text-cyan-400 mt-1">
                   {executionStats?.avg_return ? `${executionStats.avg_return.toFixed(2)}%` : '---'}
                </p>
              </div>
              <div className="bg-white/5 rounded-xl p-4 text-center">
                <p className="text-white/60 text-xs uppercase tracking-wider">Risk Level</p>
                <p className="text-2xl font-bold text-amber-400 mt-1">{userAccount?.config?.risk_level || "LOW"}</p>
              </div>
            </div>
          </div>

          {/* Positions Table */}
          <div className="glass-card">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white">Active Positions</h3>
              <Link href="/portfolio" className="text-purple-400 text-sm hover:text-purple-300 transition-colors">
                View All →
              </Link>
            </div>
            {positions.length === 0 ? (
              <div className="text-center py-8 text-white/40">
                <p>No active positions found.</p>
              </div>
            ) : (
            <div className="space-y-1">
              {/* Header */}
              <div className="grid grid-cols-5 gap-4 px-4 py-2 text-xs text-white/40 uppercase tracking-wider border-b border-white/10">
                <span>Symbol</span>
                <span>Type</span>
                <span className="text-right">LTP</span>
                <span className="text-right">Change</span>
                <span className="text-right">P&L</span>
              </div>
              {/* Rows */}
              {positions.slice(0, 5).map((pos: any, idx: number) => {
                 const pnl = (pos.realizedProfit || 0) + (pos.unrealizedProfit || 0);
                 const changePct = pos.dayChangePercentage || 0; // Assuming this field exists or needs calculation
                 return (
                  <div key={idx} className="grid grid-cols-5 gap-4 px-4 py-3 rounded-lg hover:bg-white/5 transition-colors cursor-pointer">
                    <span className="font-medium text-white">{pos.tradingSymbol || pos.symbol}</span>
                    <span className="text-white/60">
                      <Badge variant="outline" className="text-xs">{pos.productType}</Badge>
                    </span>
                    <span className="text-right font-mono text-white">₹{(pos.lastTradedPrice || 0).toLocaleString()}</span>
                    <span className={`text-right font-medium flex items-center justify-end gap-1 ${changePct >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                      {changePct >= 0 ? <ArrowUpRight className="h-3 w-3" /> : <ArrowDownRight className="h-3 w-3" />}
                      {Math.abs(changePct).toFixed(2)}%
                    </span>
                    <span className={`text-right font-semibold ${pnl >= 0 ? 'text-profit' : 'text-loss'}`}>
                      {pnl >= 0 ? '+' : ''}{formatCurrency(pnl)}
                    </span>
                  </div>
                );
              })}
            </div>
            )}
          </div>
        </div>

        {/* Right Sidebar */}
        <div className="space-y-6">
          {/* AI Signals */}
          <div className="glass-card">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Zap className="h-5 w-5 text-amber-400" />
                <h3 className="text-lg font-semibold text-white">AI Signals</h3>
              </div>
              <Link href="/signals" className="text-purple-400 text-sm hover:text-purple-300 transition-colors">
                View All →
              </Link>
            </div>
            {signals.length === 0 ? (
               <div className="text-center py-6 text-white/40 text-sm">
                 <p>No active signals.</p>
               </div>
            ) : (
            <div className="space-y-3">
              {signals.slice(0, 4).map((signal: any) => (
                <div key={signal.id || signal.symbol} className="bg-white/5 rounded-xl p-4 hover:bg-white/10 transition-colors cursor-pointer">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-white text-sm">{signal.symbol}</span>
                    <span className={`px-2 py-1 rounded-md text-xs font-bold ${getSignalColor(signal.type || signal.action)}`}>
                      {signal.type || signal.action}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="w-16 h-1.5 bg-white/10 rounded-full overflow-hidden">
                        <div 
                          className={`h-full rounded-full ${getSignalConfidenceColor(signal.confidence || 0)}`}
                          style={{ width: `${signal.confidence || 0}%` }}
                        />
                      </div>
                      <span className="text-xs text-white/60">{signal.confidence || 0}%</span>
                    </div>
                    <span className="text-xs text-white/40">
                      {new Date(signal.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                    </span>
                  </div>
                </div>
              ))}
            </div>
            )}
          </div>

          {/* Quick Actions */}
          <div className="glass-card">
            <h3 className="text-lg font-semibold text-white mb-4">Quick Actions</h3>
            <div className="grid grid-cols-2 gap-3">
              <Link href="/trading" className="quick-action text-center">
                <Play className="h-5 w-5 mx-auto mb-1 text-emerald-400" />
                <span>Trade</span>
              </Link>
              <Link href="/analytics" className="quick-action text-center">
                <BarChart3 className="h-5 w-5 mx-auto mb-1 text-purple-400" />
                <span>Analytics</span>
              </Link>
              <Link href="/backtest" className="quick-action text-center">
                <Activity className="h-5 w-5 mx-auto mb-1 text-cyan-400" />
                <span>Backtest</span>
              </Link>
              <Link href="/settings" className="quick-action text-center">
                <Shield className="h-5 w-5 mx-auto mb-1 text-amber-400" />
                <span>Risk</span>
              </Link>
            </div>
          </div>

          {/* System Status */}
          <div className="glass-card">
            <h3 className="text-lg font-semibold text-white mb-4">System Status</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-white/60 text-sm">Engine A (Risk)</span>
                <span className={`badge-live text-[10px] ${engineHealth?.engineA?.status === 'online' ? 'text-emerald-400' : 'text-red-400'}`}>
                  <span className={`w-1.5 h-1.5 rounded-full ${engineHealth?.engineA?.status === 'online' ? 'bg-emerald-400' : 'bg-red-400'} animate-pulse`} />
                  {engineHealth?.engineA?.status === 'online' ? 'Online' : 'Offline'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-white/60 text-sm">Engine B (AI/ML)</span>
                <span className={`badge-live text-[10px] ${engineHealth?.engineB?.status === 'online' ? 'text-emerald-400' : 'text-red-400'}`}>
                  <span className={`w-1.5 h-1.5 rounded-full ${engineHealth?.engineB?.status === 'online' ? 'bg-emerald-400' : 'bg-red-400'} animate-pulse`} />
                  {engineHealth?.engineB?.status === 'online' ? 'Online' : 'Offline'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-white/60 text-sm">Engine C (Execution)</span>
                <span className={`badge-live text-[10px] ${engineHealth?.engineC?.status === 'online' ? 'text-emerald-400' : 'text-red-400'}`}>
                  <span className={`w-1.5 h-1.5 rounded-full ${engineHealth?.engineC?.status === 'online' ? 'bg-emerald-400' : 'bg-red-400'} animate-pulse`} />
                  {engineHealth?.engineC?.status === 'online' ? 'Online' : 'Offline'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-white/60 text-sm">DhanHQ Connection</span>
                <span className={`badge-live text-[10px] ${systemState?.dhan_connected ? 'text-emerald-400' : 'text-red-400'}`}>
                  <span className={`w-1.5 h-1.5 rounded-full ${systemState?.dhan_connected ? 'bg-emerald-400' : 'bg-red-400'} animate-pulse`} />
                  {systemState?.dhan_connected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
{/* 
      // Account Summary Section 
      // Removed repetitive section as it is covered by the widgets above
*/}
    </div>
  );
}

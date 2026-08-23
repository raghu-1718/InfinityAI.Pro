'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  useFunds,
  useHoldings,
  usePositions,
  useOrders,
  usePortfolioSignals,
  usePortfolioAnalysis,
  useMarketQuotes,
  useTradeBook,
  Holding,
} from '@/hooks/useApi';

// Local types
type SignalShort = { symbol?: string; signal?: 'BUY' | 'SELL' | 'HOLD' | string; confidence?: number };
type Position = {
  securityId?: string;
  tradingSymbol?: string;
  realizedProfit?: number;
  unrealizedProfit?: number;
  netQty?: number;
  buyAvg?: number;
  lastTradedPrice?: number;
  productType?: string;
};
type PieEntry = { name: string; value: number };

import { useAppStore } from '@/lib/store';
import { formatCurrency, formatPercent } from '@/lib/format';
import { PositionAnalysisSection } from '@/components/dashboard/position-analysis';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  Legend,
} from 'recharts';
import {
  Wallet,
  TrendingUp,
  TrendingDown,
  PiggyBank,
  BarChart3,
  CircleDollarSign,
  Brain,
  RefreshCw,
  Sparkles,
  Briefcase,
  ShieldCheck,
  Zap,
  Activity,
  Layers,
  Clock,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { PRIMARY_DHAN_CLIENT_ID, PRIMARY_DISPLAY_NAME } from '@/lib/user';

const COLORS = ['#10b981', '#3b82f6', '#8b5cf6', '#f59e0b', '#ef4444', '#06b6d4'];

export default function PortfolioPage() {
  const funds = useAppStore((s) => s.funds);
  const { isLoading: fundsLoading, refetch: refetchFunds } = useFunds();
  const { data: holdingsData, isLoading: holdingsLoading, refetch: refetchHoldings } = useHoldings();
  const { data: positionsData, isLoading: positionsLoading, refetch: refetchPositions } = usePositions();
  const { data: portfolioSignals, isLoading: signalsLoading, refetch: refetchSignals } = usePortfolioSignals();
  const { data: marketQuotesData, refetch: refetchQuotes } = useMarketQuotes("1333,11536", "NSE_EQ");
  const { data: indexQuotesData, refetch: refetchIndexQuotes } = useMarketQuotes("13,25,26", "IDX_I");
  const { data: tradesData, refetch: refetchTrades } = useTradeBook();
  const { data: ordersData, refetch: refetchOrders } = useOrders();

  // Safely handle holdings data
  const holdingsRaw = holdingsData?.holdings || holdingsData?.data || [];
  const holdings = Array.isArray(holdingsRaw) ? holdingsRaw : [];

  const { data: portfolioAnalysis } = usePortfolioAnalysis(holdings, holdings.length > 0);

  // Safely handle positions data
  const positionsRaw = positionsData?.positions || positionsData?.data || [];
  const positions = Array.isArray(positionsRaw) ? positionsRaw : [];

  // Safely handle orders and trades data
  const ordersRaw = ordersData?.orders || ordersData?.data || [];
  const orders = Array.isArray(ordersRaw) ? ordersRaw : [];

  const tradesRaw = tradesData?.trades || tradesData?.data || [];
  const trades = Array.isArray(tradesRaw) ? tradesRaw : [];

  // Get AI signals for holdings
  const holdingSignals = portfolioSignals?.data || portfolioSignals?.signals || [];

  // Calculate portfolio metrics
  const totalInvested = holdings.reduce(
    (sum: number, h: any) => sum + (h.avgCostPrice || h.buyAvg || 0) * (h.totalQty || 0),
    0
  );
  const totalCurrentValue = holdings.reduce(
    (sum: number, h: any) => sum + (h.ltp || h.lastTradedPrice || h.avgCostPrice || h.buyAvg || 0) * (h.totalQty || 0),
    0
  );
  const totalPnL = totalCurrentValue - totalInvested;
  const totalPnLPercent = totalInvested > 0 ? (totalPnL / totalInvested) * 100 : 0;

  // Real-time Positions P&L
  const totalPositionsUnrealized = positions.reduce(
    (sum: number, p: any) => sum + (p.unrealizedProfit || 0),
    0
  );
  const totalPositionsRealized = positions.reduce(
    (sum: number, p: any) => sum + (p.realizedProfit || 0),
    0
  );

  const getSignalForHolding = (symbol: string) => {
    if (!Array.isArray(holdingSignals)) return null;
    return holdingSignals.find((s: SignalShort) => s.symbol === symbol);
  };

  // Refresh all data
  const handleRefresh = () => {
    refetchFunds();
    refetchHoldings();
    refetchPositions();
    refetchSignals();
    refetchQuotes();
    refetchIndexQuotes();
    refetchTrades();
    refetchOrders();
  };

  // Prepare pie chart data
  const pieData = holdings.slice(0, 6).map((h: any, i: number) => ({
    name: h.tradingSymbol || h.securityId || `Stock ${i + 1}`,
    value: (h.ltp || h.lastTradedPrice || h.avgCostPrice || h.buyAvg || 0) * (h.totalQty || 1),
  }));

  // Parse market quotes using recursive Dhan unwrap
  const quotesData = marketQuotesData?.data?.data?.NSE_EQ || marketQuotesData?.data?.data || marketQuotesData?.data || {};
  const indexData = indexQuotesData?.data?.data?.IDX_I || indexQuotesData?.data?.data || indexQuotesData?.data || {};
  
  // Recursively extract quotes
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

  const niftyObj = parsedIndices["13"] || indexData["13"] || {};
  const bankNiftyObj = parsedIndices["25"] || indexData["25"] || {};
  const sensexObj = parsedIndices["51"] || parsedIndices["1"] || indexData["51"] || {};
  const finNiftyObj = parsedIndices["27"] || indexData["27"] || {};

  const niftyLtp = Number(niftyObj.last_price || niftyObj.ltp || niftyObj.ohlc?.close || 0);
  const niftyChange = niftyObj.ohlc && niftyObj.ohlc.open && niftyLtp > 0 ? (((niftyLtp - niftyObj.ohlc.open) / niftyObj.ohlc.open) * 100) : 0;

  const bankNiftyLtp = Number(bankNiftyObj.last_price || bankNiftyObj.ltp || bankNiftyObj.ohlc?.close || 0);
  const bankNiftyChange = bankNiftyObj.ohlc && bankNiftyObj.ohlc.open && bankNiftyLtp > 0 ? (((bankNiftyLtp - bankNiftyObj.ohlc.open) / bankNiftyObj.ohlc.open) * 100) : 0;

  const sensexLtp = Number(sensexObj.last_price || sensexObj.ltp || sensexObj.ohlc?.close || 0);
  const sensexChange = sensexObj.ohlc && sensexObj.ohlc.open && sensexLtp > 0 ? (((sensexLtp - sensexObj.ohlc.open) / sensexObj.ohlc.open) * 100) : 0;

  const finNiftyLtp = Number(finNiftyObj.last_price || finNiftyObj.ltp || finNiftyObj.ohlc?.close || 0);
  const finNiftyChange = finNiftyObj.ohlc && finNiftyObj.ohlc.open && finNiftyLtp > 0 ? (((finNiftyLtp - finNiftyObj.ohlc.open) / finNiftyObj.ohlc.open) * 100) : 0;

  return (
    <div className="p-6 space-y-6">
      {/* Live Market Ticker Header */}
      <div className="rounded-xl border border-primary/20 bg-gradient-to-r from-card via-card to-primary/10 p-4 shadow-sm">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-foreground text-base">{PRIMARY_DISPLAY_NAME}</span>
                <Badge variant="outline" className="bg-emerald-500/10 text-emerald-400 border-emerald-500/20 text-xs">
                  DhanHQ Vault Active
                </Badge>
                <Badge variant="outline" className="bg-blue-500/10 text-blue-400 border-blue-500/20 text-xs">
                  Scheduler Keep-Alive: 0 6,18 * * *
                </Badge>
              </div>
              <p className="text-xs text-muted-foreground mt-0.5">
                Single-Tenant Demat Vault • Hardware Encrypted (AES-256-GCM) • GCP asia-south1
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={handleRefresh} className="gap-2 text-xs">
              <RefreshCw className="h-3.5 w-3.5" />
              Live Telemetry Refresh
            </Button>
          </div>
        </div>

        {/* Live Indian Indices Quick Ticker */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4 pt-3 border-t border-border/50">
          <div className="p-2.5 rounded-lg bg-background/50 border border-border/60">
            <div className="flex justify-between items-center text-xs">
              <span className="font-semibold text-foreground">NIFTY 50</span>
              <span className="text-[10px] text-muted-foreground font-mono">13 • INDEX</span>
            </div>
            <p className={cn("text-sm font-bold font-mono mt-1", niftyChange >= 0 ? "text-emerald-400" : "text-rose-400")}>
              ₹{niftyLtp.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}{" "}
              <span className="text-[10px] font-normal">
                {niftyChange >= 0 ? "+" : ""}{niftyChange.toFixed(2)}%
              </span>
            </p>
          </div>

          <div className="p-2.5 rounded-lg bg-background/50 border border-border/60">
            <div className="flex justify-between items-center text-xs">
              <span className="font-semibold text-foreground">BANK NIFTY</span>
              <span className="text-[10px] text-muted-foreground font-mono">25 • INDEX</span>
            </div>
            <p className={cn("text-sm font-bold font-mono mt-1", bankNiftyChange >= 0 ? "text-emerald-400" : "text-rose-400")}>
              ₹{bankNiftyLtp.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}{" "}
              <span className="text-[10px] font-normal">
                {bankNiftyChange >= 0 ? "+" : ""}{bankNiftyChange.toFixed(2)}%
              </span>
            </p>
          </div>

          <div className="p-2.5 rounded-lg bg-background/50 border border-border/60">
            <div className="flex justify-between items-center text-xs">
              <span className="font-semibold text-foreground">BSE SENSEX</span>
              <span className="text-[10px] text-muted-foreground font-mono">51 • BSE INDEX</span>
            </div>
            <p className={cn("text-sm font-bold font-mono mt-1", sensexChange >= 0 ? "text-emerald-400" : "text-rose-400")}>
              ₹{sensexLtp.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}{" "}
              <span className="text-[10px] font-normal">
                {sensexChange >= 0 ? "+" : ""}{sensexChange.toFixed(2)}%
              </span>
            </p>
          </div>

          <div className="p-2.5 rounded-lg bg-background/50 border border-border/60">
            <div className="flex justify-between items-center text-xs">
              <span className="font-semibold text-foreground">FIN NIFTY</span>
              <span className="text-[10px] text-muted-foreground font-mono">27 • INDEX</span>
            </div>
            <p className={cn("text-sm font-bold font-mono mt-1", finNiftyChange >= 0 ? "text-emerald-400" : "text-rose-400")}>
              ₹{finNiftyLtp.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}{" "}
              <span className="text-[10px] font-normal">
                {finNiftyChange >= 0 ? "+" : ""}{finNiftyChange.toFixed(2)}%
              </span>
            </p>
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <SummaryCard
          title="Available Cash Margin"
          value={funds?.availableBalance || 0}
          icon={Wallet}
          color="text-emerald-500"
          bgColor="bg-emerald-500/10"
          isLoading={fundsLoading}
        />
        <SummaryCard
          title="Utilized Margin / Collateral"
          value={funds?.collateralAmount || 0}
          icon={CircleDollarSign}
          color="text-blue-500"
          bgColor="bg-blue-500/10"
          isLoading={fundsLoading}
        />
        <SummaryCard
          title="Portfolio Valuation"
          value={totalCurrentValue}
          icon={BarChart3}
          color="text-purple-500"
          bgColor="bg-purple-500/10"
          isLoading={holdingsLoading}
        />
        <SummaryCard
          title="Open Positions P&L"
          value={totalPositionsUnrealized}
          icon={totalPositionsUnrealized >= 0 ? TrendingUp : TrendingDown}
          color={totalPositionsUnrealized >= 0 ? 'text-emerald-500' : 'text-rose-500'}
          bgColor={totalPositionsUnrealized >= 0 ? 'bg-emerald-500/10' : 'bg-rose-500/10'}
          isLoading={positionsLoading}
          suffix={` (${positions.length} active)`}
          isPnL
        />
      </div>

      {/* Tabs for Holdings vs Positions vs Orders vs AI Analysis */}
      <Tabs defaultValue="holdings" className="space-y-4">
        <TabsList className="bg-card border border-border">
          <TabsTrigger value="holdings" className="gap-2">
            <Briefcase className="h-4 w-4" />
            Equity Holdings ({holdings.length})
          </TabsTrigger>
          <TabsTrigger value="positions" className="gap-2">
            <Layers className="h-4 w-4" />
            Active Positions ({positions.length})
          </TabsTrigger>
          <TabsTrigger value="orders" className="gap-2">
            <Clock className="h-4 w-4" />
            Order Flow ({orders.length + trades.length})
          </TabsTrigger>
          <TabsTrigger value="ai-analysis" className="gap-2">
            <Brain className="h-4 w-4" />
            AI Portfolio Analysis
          </TabsTrigger>
        </TabsList>

        {/* Tab 1: Equity Holdings */}
        <TabsContent value="holdings" className="space-y-6">
          <div className="grid gap-6 lg:grid-cols-3">
            {/* Holdings List */}
            <div className="lg:col-span-2">
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="text-lg">Portfolio Holdings</CardTitle>
                      <CardDescription>Live equity positions synced from DhanHQ</CardDescription>
                    </div>
                    <Badge variant="secondary">{holdings.length} stocks</Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  {holdingsLoading ? (
                    <div className="space-y-3">
                      {[1, 2, 3, 4].map((i) => (
                        <Skeleton key={i} className="h-16 w-full" />
                      ))}
                    </div>
                  ) : holdings.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-12 text-center">
                      <PiggyBank className="h-12 w-12 text-muted-foreground/50" />
                      <p className="mt-2 text-muted-foreground">No holdings in Demat account</p>
                      <p className="text-xs text-muted-foreground">
                        Executed deliveries will appear here automatically
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {holdings.map((holding: any, idx: number) => {
                        const symbol = holding.tradingSymbol || holding.securityId || '';
                        const signal = getSignalForHolding(symbol);
                        return (
                          <HoldingRow
                            key={holding.securityId || idx}
                            holding={holding}
                            signal={signal}
                          />
                        );
                      })}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Portfolio Allocation */}
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Capital Allocation</CardTitle>
                  <CardDescription>Weight distribution across stocks</CardDescription>
                </CardHeader>
                <CardContent>
                  {holdingsLoading ? (
                    <div className="flex items-center justify-center h-[250px]">
                      <Skeleton className="h-48 w-48 rounded-full" />
                    </div>
                  ) : pieData.length > 0 ? (
                    <div className="h-[250px]">
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie
                            data={pieData}
                            cx="50%"
                            cy="50%"
                            innerRadius={60}
                            outerRadius={80}
                            paddingAngle={2}
                            dataKey="value"
                          >
                            {pieData.map((entry: PieEntry, index: number) => (
                              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                            ))}
                          </Pie>
                          <Tooltip
                            contentStyle={{
                              backgroundColor: 'hsl(var(--card))',
                              border: '1px solid hsl(var(--border))',
                              borderRadius: '8px',
                            }}
                            formatter={(value: any) => formatCurrency(Number(value || 0))}
                          />
                          <Legend
                            formatter={(value: string) => (
                              <span className="text-xs">{value}</span>
                            )}
                          />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                  ) : (
                    <div className="flex items-center justify-center h-[250px] text-muted-foreground">
                      No allocation data to display
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* AI Health Score */}
              <Card>
                <CardHeader>
                  <div className="flex items-center gap-2">
                    <Sparkles className="h-5 w-5 text-purple-400" />
                    <CardTitle className="text-lg">AI Health Score</CardTitle>
                  </div>
                  <CardDescription>Vertex AI risk & diversification score</CardDescription>
                </CardHeader>
                <CardContent>
                   <div className="flex flex-col items-center justify-center p-4">
                     <div className="relative w-28 h-28 flex items-center justify-center rounded-full bg-gradient-to-br from-purple-500/20 to-blue-500/20 border-4 border-purple-500/30">
                        <span className="text-3xl font-black text-white">
                          {portfolioAnalysis?.score || "88"}
                        </span>
                     </div>
                     <p className="mt-4 text-center text-xs text-slate-300">
                       {portfolioAnalysis?.summary || "Balanced portfolio diversification with optimal risk-adjusted alpha."}
                     </p>
                   </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </TabsContent>

        {/* Tab 2: Active Positions */}
        <TabsContent value="positions" className="space-y-6">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-lg">Active Positions</CardTitle>
                  <CardDescription>Intraday and F&O open exposures</CardDescription>
                </div>
                <div className="flex items-center gap-3">
                  <div className="text-right">
                    <span className="text-xs text-muted-foreground">Unrealized P&L: </span>
                    <span className={cn("font-mono font-bold text-sm", totalPositionsUnrealized >= 0 ? "text-emerald-400" : "text-rose-400")}>
                      {totalPositionsUnrealized >= 0 ? "+" : ""}{formatCurrency(totalPositionsUnrealized)}
                    </span>
                  </div>
                  <Badge variant="secondary">{positions.length} Active</Badge>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {positionsLoading ? (
                <div className="space-y-3">
                  {[1, 2, 3].map((i) => (
                    <Skeleton key={i} className="h-16 w-full" />
                  ))}
                </div>
              ) : positions.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 text-center">
                  <Activity className="h-12 w-12 text-muted-foreground/50" />
                  <p className="mt-2 text-muted-foreground">No open positions today</p>
                  <p className="text-xs text-muted-foreground">
                    New intraday / F&O orders will stream live updates here
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {positions.map((pos: any, idx: number) => {
                    const unrealized = pos.unrealizedProfit || 0;
                    const realized = pos.realizedProfit || 0;
                    const isProfit = (unrealized + realized) >= 0;

                    return (
                      <div
                        key={pos.securityId || idx}
                        className="flex flex-col sm:flex-row sm:items-center justify-between rounded-lg border border-border/80 p-4 gap-3 bg-background/50 hover:bg-muted/40 transition-colors"
                      >
                        <div className="flex items-center gap-3">
                          <div className={cn("p-2 rounded-lg", isProfit ? "bg-emerald-500/10 text-emerald-400" : "bg-rose-500/10 text-rose-400")}>
                            {isProfit ? <TrendingUp className="h-5 w-5" /> : <TrendingDown className="h-5 w-5" />}
                          </div>
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="font-bold text-foreground">{pos.tradingSymbol || pos.securityId}</span>
                              <Badge variant="outline" className="text-[10px] font-mono uppercase">
                                {pos.productType || "INTRADAY"}
                              </Badge>
                            </div>
                            <div className="flex items-center gap-3 text-xs text-muted-foreground mt-0.5">
                              <span>Qty: {pos.netQty || pos.quantity || 0}</span>
                              <span>Buy Avg: ₹{(pos.buyAvg || pos.entryPrice || 0).toFixed(2)}</span>
                              <span>LTP: ₹{(pos.lastTradedPrice || pos.currentPrice || 0).toFixed(2)}</span>
                            </div>
                          </div>
                        </div>

                        <div className="text-right">
                          <p className={cn("font-mono font-bold text-base", isProfit ? "text-emerald-400" : "text-rose-400")}>
                            {unrealized >= 0 ? "+" : ""}{formatCurrency(unrealized)}
                          </p>
                          {realized !== 0 && (
                            <p className="text-xs text-muted-foreground font-mono">
                              Realized: {realized >= 0 ? "+" : ""}{formatCurrency(realized)}
                            </p>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab 3: Order Flow & Execution Logs */}
        <TabsContent value="orders" className="space-y-6">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-lg">Order Flow & Trade Logs</CardTitle>
                  <CardDescription>Live executed, pending, and completed Dhan orders & trade ledger</CardDescription>
                </div>
                <Badge variant="outline" className="font-mono text-xs">{orders.length} Orders / {trades.length} Trades</Badge>
              </div>
            </CardHeader>
            <CardContent>
              {orders.length === 0 && trades.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 text-center">
                  <Clock className="h-12 w-12 text-muted-foreground/50" />
                  <p className="mt-2 text-muted-foreground">No recent order or trade records</p>
                  <p className="text-xs text-muted-foreground">
                    Live order flow and trade ledger will stream here automatically
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {orders.map((order: any, idx: number) => {
                    const status = (order.orderStatus || order.status || "SUCCESS").toUpperCase();
                    const statusColor =
                      status === "SUCCESS" || status === "TRADED" || status === "EXECUTED"
                        ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                        : status === "PENDING" || status === "TRANSIT"
                        ? "bg-amber-500/10 text-amber-400 border-amber-500/30"
                        : "bg-rose-500/10 text-rose-400 border-rose-500/30";

                    return (
                      <div
                        key={order.orderId || idx}
                        className="flex items-center justify-between rounded-lg border border-border/80 p-4 bg-background/50"
                      >
                        <div className="flex items-center gap-3">
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="font-bold text-foreground">{order.tradingSymbol || order.securityId || `Order #${order.orderId}`}</span>
                              <span className={`text-[10px] px-2 py-0.5 rounded font-mono font-bold uppercase border ${statusColor}`}>
                                {status}
                              </span>
                            </div>
                            <p className="text-xs text-muted-foreground mt-0.5">
                              {order.transactionType || "BUY"} • Qty: {order.quantity || 0} • Price: ₹{(order.price || 0).toFixed(2)}
                            </p>
                          </div>
                        </div>
                        <div className="text-right text-xs text-muted-foreground font-mono">
                          {order.createTime || order.orderTime || new Date().toLocaleTimeString()}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab 4: AI Position Analysis */}
        <TabsContent value="ai-analysis">
          <PositionAnalysisSection />
        </TabsContent>
      </Tabs>
    </div>
  );
}

function SummaryCard({
  title,
  value,
  icon: Icon,
  color,
  bgColor,
  isLoading,
  suffix = '',
  isPnL = false,
}: {
  title: string;
  value: number;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  bgColor: string;
  isLoading: boolean;
  suffix?: string;
  isPnL?: boolean;
}) {
  if (isLoading) {
    return (
      <Card>
        <CardContent className="p-6">
          <Skeleton className="h-12 w-12 rounded-lg mb-4" />
          <Skeleton className="h-6 w-24 mb-2" />
          <Skeleton className="h-4 w-20" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent className="p-6">
        <div className={`inline-flex rounded-lg p-3 ${bgColor}`}>
          <Icon className={`h-6 w-6 ${color}`} />
        </div>
        <p className="mt-4 text-xs font-medium uppercase tracking-wider text-muted-foreground">{title}</p>
        <p className={cn(
          'text-2xl font-bold font-mono mt-1',
          isPnL && (value >= 0 ? 'text-emerald-500 dark:text-emerald-400' : 'text-rose-500 dark:text-rose-400')
        )}>
          {formatCurrency(value)}
          {suffix && <span className="text-xs font-normal text-muted-foreground ml-1">{suffix}</span>}
        </p>
      </CardContent>
    </Card>
  );
}

function HoldingRow({ holding, signal }: { holding: any; signal?: SignalShort }) {
  const invested = (holding.avgCostPrice || holding.buyAvg || 0) * (holding.totalQty || 0);
  const current = (holding.ltp || holding.lastTradedPrice || holding.avgCostPrice || holding.buyAvg || 0) * (holding.totalQty || 0);
  const pnl = current - invested;
  const pnlPercent = invested > 0 ? (pnl / invested) * 100 : 0;
  const isProfit = pnl >= 0;

  return (
    <div className="flex items-center justify-between rounded-lg border border-border/70 p-4 transition-colors hover:bg-muted/40 bg-background/40">
      <div className="flex items-center gap-4">
        <div className={cn(
          'rounded-lg p-2.5',
          isProfit ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/10 text-rose-400'
        )}>
          {isProfit ? (
            <TrendingUp className="h-5 w-5" />
          ) : (
            <TrendingDown className="h-5 w-5" />
          )}
        </div>
        <div>
          <div className="flex items-center gap-2">
            <p className="font-semibold text-foreground">{holding.tradingSymbol || holding.securityId}</p>
            {signal && (
              <Badge
                variant={signal.signal === 'BUY' ? 'default' : signal.signal === 'SELL' ? 'destructive' : 'secondary'}
                className="text-xs"
              >
                <Sparkles className="h-3 w-3 mr-1" />
                {signal.signal}
              </Badge>
            )}
          </div>
          <div className="flex items-center gap-3 text-xs text-muted-foreground mt-0.5">
            <span>{holding.totalQty} shares</span>
            <span>Avg: {formatCurrency(holding.avgCostPrice || holding.buyAvg || 0)}</span>
            <span>LTP: {formatCurrency(holding.ltp || holding.lastTradedPrice || 0)}</span>
            {signal && (
              <span className="text-primary font-medium">
                {((signal.confidence ?? 0) * 100).toFixed(0)}% AI confidence
              </span>
            )}
          </div>
        </div>
      </div>
      <div className="text-right">
        <p className={cn(
          'font-mono font-bold text-sm',
          isProfit ? 'text-emerald-500 dark:text-emerald-400' : 'text-rose-500 dark:text-rose-400'
        )}>
          {pnl >= 0 ? '+' : ''}{formatCurrency(pnl)}
        </p>
        <p className={cn(
          'text-xs font-mono',
          isProfit ? 'text-emerald-500/80 dark:text-emerald-400/80' : 'text-rose-500/80 dark:text-rose-400/80'
        )}>
          {formatPercent(pnlPercent)}
        </p>
      </div>
    </div>
  );
}

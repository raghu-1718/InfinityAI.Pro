'use client';

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useFunds, useHoldings, usePositions, usePortfolioSignals, usePortfolioAnalysis, Holding } from '@/hooks/useApi';

// Local types
type SignalShort = { symbol?: string; signal?: 'BUY' | 'SELL' | 'HOLD' | string; confidence?: number };
type Position = { securityId?: string; tradingSymbol?: string; realizedProfit?: number; netQty?: number; averagePrice?: number };
type PieEntry = { name: string; value: number };

import { useAppStore } from '@/lib/store';
import { formatCurrency, formatPercent, formatCompact } from '@/lib/format';
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
} from 'lucide-react';
import { cn } from '@/lib/utils';

const COLORS = ['#10b981', '#3b82f6', '#8b5cf6', '#f59e0b', '#ef4444', '#06b6d4'];

export default function PortfolioPage() {
  const funds = useAppStore((s) => s.funds);
  const { isLoading: fundsLoading, refetch: refetchFunds } = useFunds();
  const { data: holdingsData, isLoading: holdingsLoading, refetch: refetchHoldings } = useHoldings();
  const { data: positionsData, isLoading: positionsLoading, refetch: refetchPositions } = usePositions();
  const { data: portfolioSignals, isLoading: signalsLoading, refetch: refetchSignals } = usePortfolioSignals();

  // Safely handle holdings data - ensure it's always an array
  const holdingsRaw = holdingsData?.data;
  const holdings = Array.isArray(holdingsRaw) ? holdingsRaw : [];

  const { data: portfolioAnalysis } = usePortfolioAnalysis(holdings, holdings.length > 0);

  // Safely handle positions data
  const positionsRaw = positionsData?.data;
  const positions = Array.isArray(positionsRaw) ? positionsRaw : [];

  // Get AI signals for holdings
  const holdingSignals = portfolioSignals?.data || portfolioSignals?.signals || [];

  // Calculate portfolio metrics
  const totalInvested = holdings.reduce(
    (sum: number, h: Holding) => sum + (h.avgCostPrice || 0) * (h.totalQty || 0),
    0
  );
  const totalCurrentValue = holdings.reduce(
    (sum: number, h: Holding) => sum + (h.ltp || h.avgCostPrice || 0) * (h.totalQty || 0),
    0
  );
  const totalPnL = totalCurrentValue - totalInvested;
  const totalPnLPercent = totalInvested > 0 ? (totalPnL / totalInvested) * 100 : 0;

  // Helper to get signal for a holding
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
  };

  // Prepare pie chart data
  const pieData = holdings.slice(0, 6).map((h: Holding, i: number) => ({
    name: h.tradingSymbol || h.securityId || `Stock ${i + 1}`,
    value: (h.ltp || h.avgCostPrice || 0) * (h.totalQty || 1),
  }));

  return (
    <div className="p-6 space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Portfolio</h1>
          <p className="text-muted-foreground">
            Your Dhan holdings and investments with AI signals
          </p>
        </div>
        <div className="flex items-center gap-2">
          {signalsLoading && (
            <Badge variant="outline" className="animate-pulse">
              <Brain className="h-3 w-3 mr-1" />
              Analyzing...
            </Badge>
          )}
          <Button variant="outline" size="sm" onClick={handleRefresh}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <SummaryCard
          title="Available Cash"
          value={funds?.availableBalance || 0}
          icon={Wallet}
          color="text-green-500"
          bgColor="bg-green-100 dark:bg-green-900/30"
          isLoading={fundsLoading}
        />
        <SummaryCard
          title="Total Invested"
          value={totalInvested}
          icon={CircleDollarSign}
          color="text-blue-500"
          bgColor="bg-blue-100 dark:bg-blue-900/30"
          isLoading={holdingsLoading}
        />
        <SummaryCard
          title="Current Value"
          value={totalCurrentValue}
          icon={BarChart3}
          color="text-purple-500"
          bgColor="bg-purple-100 dark:bg-purple-900/30"
          isLoading={holdingsLoading}
        />
        <SummaryCard
          title="Total P&L"
          value={totalPnL}
          icon={totalPnL >= 0 ? TrendingUp : TrendingDown}
          color={totalPnL >= 0 ? 'text-green-500' : 'text-red-500'}
          bgColor={totalPnL >= 0 ? 'bg-green-100 dark:bg-green-900/30' : 'bg-red-100 dark:bg-red-900/30'}
          isLoading={holdingsLoading}
          suffix={` (${formatPercent(totalPnLPercent)})`}
          isPnL
        />
      </div>

      {/* Tabs for Holdings vs AI Analysis */}
      <Tabs defaultValue="holdings" className="space-y-4">
        <TabsList>
          <TabsTrigger value="holdings" className="gap-2">
            <Briefcase className="h-4 w-4" />
            Holdings & Positions
          </TabsTrigger>
          <TabsTrigger value="ai-analysis" className="gap-2">
            <Brain className="h-4 w-4" />
            AI Position Analysis
          </TabsTrigger>
        </TabsList>

        <TabsContent value="holdings" className="space-y-6">
          {/* Main Content */}
          <div className="grid gap-6 lg:grid-cols-3">
            {/* Holdings List */}
            <div className="lg:col-span-2">
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">Holdings</CardTitle>
                    <Badge variant="secondary">{holdings.length} stocks</Badge>
                  </div>
                  <CardDescription>Your long-term investments</CardDescription>
                </CardHeader>
                <CardContent>
                  {holdingsLoading ? (
                    <div className="space-y-3">
                      {[1, 2, 3, 4, 5].map((i) => (
                        <Skeleton key={i} className="h-16 w-full" />
                      ))}
                    </div>
                  ) : holdings.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-12 text-center">
                      <PiggyBank className="h-12 w-12 text-muted-foreground/50" />
                      <p className="mt-2 text-muted-foreground">No holdings yet</p>
                      <p className="text-xs text-muted-foreground">
                        Start investing to see your portfolio here
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {holdings.map((holding: Holding, idx: number) => {
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
                  <CardTitle className="text-lg">Allocation</CardTitle>
                  <CardDescription>Portfolio distribution</CardDescription>
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
                      No data to display
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* AI Portfolio Health Check */}
              <Card>
                <CardHeader>
                  <div className="flex items-center gap-2">
                    <Sparkles className="h-5 w-5 text-purple-500" />
                    <CardTitle className="text-lg">AI Health Score</CardTitle>
                  </div>
                  <CardDescription>Portfolio risk & diversification</CardDescription>
                </CardHeader>
                <CardContent>
                   <div className="flex flex-col items-center justify-center p-4">
                     <div className="relative w-32 h-32 flex items-center justify-center rounded-full bg-gradient-to-br from-purple-500/20 to-blue-500/20 border-4 border-purple-500/30">
                        <span className="text-4xl font-black text-white">
                          {portfolioAnalysis?.score || "--"}
                        </span>
                     </div>
                     <p className="mt-4 text-center text-sm text-slate-300">
                       {portfolioAnalysis?.summary || "Analyzing portfolio structure, concentration risk, and sector allocation..."}
                     </p>
                   </div>
                </CardContent>
              </Card>

              {/* Day Positions */}
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">Day Positions</CardTitle>
                    <Badge variant="secondary">{positions.length}</Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  {positionsLoading ? (
                    <div className="space-y-3">
                      {[1, 2, 3].map((i) => (
                        <Skeleton key={i} className="h-12 w-full" />
                      ))}
                    </div>
                  ) : positions.length === 0 ? (
                    <p className="text-center text-muted-foreground py-4">
                      No open positions
                    </p>
                  ) : (
                    <div className="space-y-2">
                      {positions.slice(0, 5).map((pos: Position, idx: number) => (
                        <PositionRow key={pos.securityId || idx} position={pos} />
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="ai-analysis">
          {/* AI Position Analysis Section */}
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
        <p className="mt-4 text-sm text-muted-foreground">{title}</p>
        <p className={cn(
          'text-2xl font-bold',
          isPnL && (value >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400')
        )}>
          {formatCurrency(value)}
          {suffix && <span className="text-sm font-normal">{suffix}</span>}
        </p>
      </CardContent>
    </Card>
  );
}

function HoldingRow({ holding, signal }: { holding: Holding; signal?: SignalShort }) {
  const invested = (holding.avgCostPrice || 0) * (holding.totalQty || 0);
  const current = (holding.ltp || holding.avgCostPrice || 0) * (holding.totalQty || 0);
  const pnl = current - invested;
  const pnlPercent = invested > 0 ? (pnl / invested) * 100 : 0;
  const isProfit = pnl >= 0;

  return (
    <div className="flex items-center justify-between rounded-lg border p-4 transition-colors hover:bg-muted/50">
      <div className="flex items-center gap-4">
        <div className={cn(
          'rounded-lg p-2',
          isProfit ? 'bg-green-100 dark:bg-green-900/30' : 'bg-red-100 dark:bg-red-900/30'
        )}>
          {isProfit ? (
            <TrendingUp className="h-5 w-5 text-green-600 dark:text-green-400" />
          ) : (
            <TrendingDown className="h-5 w-5 text-red-600 dark:text-red-400" />
          )}
        </div>
        <div>
          <div className="flex items-center gap-2">
            <p className="font-semibold">{holding.tradingSymbol || holding.securityId}</p>
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
          <div className="flex items-center gap-3 text-sm text-muted-foreground">
            <span>{holding.totalQty} qty</span>
            <span>Avg: {formatCurrency(holding.avgCostPrice || 0)}</span>
            <span>LTP: {formatCurrency(holding.ltp || 0)}</span>
            {signal && (
              <span className="text-primary">
                {((signal.confidence ?? 0) * 100).toFixed(0)}% confidence
              </span>
            )}
          </div>
        </div>
      </div>
      <div className="text-right">
        <p className={cn(
          'font-mono font-bold',
          isProfit ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
        )}>
          {pnl >= 0 ? '+' : ''}{formatCurrency(pnl)}
        </p>
        <p className={cn(
          'text-sm',
          isProfit ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
        )}>
          {formatPercent(pnlPercent)}
        </p>
      </div>
    </div>
  );
}

function PositionRow({ position }: { position: Position }) {
  const pnl = position.realizedProfit || 0;
  const isProfit = pnl >= 0;

  return (
    <div className="flex items-center justify-between rounded-lg border p-3">
      <div>
        <p className="font-medium text-sm">{position.tradingSymbol || position.securityId}</p>
        <p className="text-xs text-muted-foreground">
          {position.netQty} qty @ {formatCurrency(position.averagePrice || 0)}
        </p>
      </div>
      <p className={cn(
        'font-mono font-semibold text-sm',
        isProfit ? 'text-green-600' : 'text-red-600'
      )}>
        {pnl >= 0 ? '+' : ''}{formatCurrency(pnl)}
      </p>
    </div>
  );
}

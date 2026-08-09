'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Separator } from '@/components/ui/separator';
import { Skeleton } from '@/components/ui/skeleton';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  useVaR,
  useKellyCriterion,
  usePositionSize,
  useRiskMetrics,
  useExecutionAnalytics,
  useHoldings,
  usePositions,
  useFunds,
  usePortfolioSignals,
  useGeminiAnalysis,
  useMarketPrediction,
  useSectorAnalysis,
  useTradeIdeas,
  usePortfolioOptimization,
} from '@/hooks/useApi';
import { useAppStore } from '@/lib/store';
import { formatCurrency, formatPercent, formatNumber } from '@/lib/format';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart as RePieChart,
  Pie,
  Cell,
} from 'recharts';
import {
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Shield,
  Target,
  Calculator,
  Percent,
  BarChart3,
  PieChart,
  Wallet,
  Brain,
  Sparkles,
  RefreshCw,
  ChevronRight,
  Activity,
  Lightbulb,
  Zap,
  Globe,
  Layers,
  ArrowUpRight,
  ArrowDownRight,
  Clock,
  DollarSign,
} from 'lucide-react';
import { cn } from '@/lib/utils';

const COLORS = ['#10b981', '#3b82f6', '#8b5cf6', '#f59e0b', '#ef4444', '#06b6d4', '#ec4899', '#14b8a6'];

// Helper function to generate chart data from real returns
const generateChartData = (returns: number[]) => {
  return returns.map((ret, i) => ({
    day: i + 1,
    return: ret * 100,
    cumulative: returns.slice(0, i + 1).reduce((a, b) => a + b, 0) * 100,
  }));
};

// Helper function to generate drawdown data from real returns
const generateDrawdownData = (returns: number[]) => {
  return returns.reduce(
    (acc, ret, i) => {
      const cumReturn = (acc[i]?.cumReturn || 0) + ret;
      const peak = Math.max(acc[i]?.peak || 0, cumReturn);
      const drawdown = peak > 0 ? ((cumReturn - peak) / peak) * 100 : 0;
      return [...acc, { day: i + 1, cumReturn: cumReturn * 100, peak: peak * 100, drawdown }];
    },
    [] as { day: number; cumReturn: number; peak: number; drawdown: number }[]
  );
};

export default function AnalyticsPage() {
  const [capital, setCapital] = useState('100000');
  const [riskPerTrade, setRiskPerTrade] = useState('0.02');
  const [stopLoss, setStopLoss] = useState('0.05');
  const [winRate, setWinRate] = useState('0.55');
  const [avgWin, setAvgWin] = useState('0.03');
  const [avgLoss, setAvgLoss] = useState('0.02');
  const [selectedHolding, setSelectedHolding] = useState<string | null>(null);

  const funds = useAppStore((s) => s.funds);
  const riskMetrics = useAppStore((s) => s.riskMetrics);

  // Fetch user's actual portfolio data
  const { data: holdingsData, isLoading: holdingsLoading, refetch: refetchHoldings } = useHoldings();
  const { data: positionsData, isLoading: positionsLoading } = usePositions();
  const { data: portfolioSignals, isLoading: signalsLoading, refetch: refetchSignals } = usePortfolioSignals();

  // Safely get holdings array
  const holdings = Array.isArray(holdingsData?.data) ? holdingsData.data : [];
  const positions = Array.isArray(positionsData?.data) ? positionsData.data : [];

  // Calculate real returns from user's holdings
  const userReturns = holdings.slice(0, 30).map((h: any) => {
    const buyAvg = h.buyAvg || h.avgCostPrice || 0;
    const currentValue = h.currentValue || h.ltp || h.dayClosePrice || buyAvg;
    return buyAvg > 0 ? (currentValue - buyAvg) / buyAvg : 0;
  }).filter((r: number) => !isNaN(r) && isFinite(r));

  // Generate chart data from user's real returns (or show empty if no data)
  const returnChartData = userReturns.length > 0 ? generateChartData(userReturns) : [];
  const drawdownData = userReturns.length > 0 ? generateDrawdownData(userReturns) : [];

  // Get AI analysis for selected holding
  const { data: geminiAnalysis, isLoading: analysisLoading, refetch: refetchAnalysis } = useGeminiAnalysis(
    selectedHolding || '',
    selectedHolding ? `Analyze this stock from user's portfolio with current holding details` : undefined
  );

  // Calculate portfolio metrics from actual holdings
  const totalInvested = holdings.reduce(
    (sum: number, h: any) => sum + (h.avgCostPrice || 0) * (h.totalQty || 0), 0
  );
  const totalCurrentValue = holdings.reduce(
    (sum: number, h: any) => sum + (h.ltp || h.avgCostPrice || 0) * (h.totalQty || 0), 0
  );
  const totalPnL = totalCurrentValue - totalInvested;
  const totalPnLPercent = totalInvested > 0 ? (totalPnL / totalInvested) * 100 : 0;

  // Prepare portfolio allocation data for pie chart
  const allocationData = holdings.slice(0, 8).map((h: any, i: number) => ({
    name: h.tradingSymbol || h.securityId || `Stock ${i + 1}`,
    value: (h.ltp || h.avgCostPrice || 0) * (h.totalQty || 1),
    pnl: ((h.ltp || h.avgCostPrice) - (h.avgCostPrice || 0)) * (h.totalQty || 0),
    pnlPercent: h.avgCostPrice ? (((h.ltp || h.avgCostPrice) - h.avgCostPrice) / h.avgCostPrice) * 100 : 0,
  }));

  // Get signals mapped to holdings
  const holdingSignals = portfolioSignals?.data || portfolioSignals?.signals || [];

  const { data: varData, isLoading: varLoading } = useVaR(userReturns.length > 0 ? userReturns : [0], 0.95, 'historical');
  const { data: kellyData, isLoading: kellyLoading } = useKellyCriterion(
    parseFloat(winRate),
    parseFloat(avgWin),
    parseFloat(avgLoss)
  );
  const { data: positionData, isLoading: positionLoading } = usePositionSize(
    parseFloat(capital),
    parseFloat(riskPerTrade),
    parseFloat(stopLoss)
  );
  const { data: executionData } = useExecutionAnalytics();

  // New AI Features
  const { data: marketPrediction, isLoading: marketLoading, refetch: refetchMarket } = useMarketPrediction('day');
  const { data: sectorAnalysis, isLoading: sectorsLoading } = useSectorAnalysis();
  const { data: tradeIdeas, isLoading: ideasLoading, refetch: refetchIdeas } = useTradeIdeas(
    funds?.availableBalance || 100000,
    'moderate'
  );
  const { data: portfolioOptimization, isLoading: optimizationLoading } = usePortfolioOptimization(
    holdings,
    'medium'
  );

  return (
    <div className="p-6 space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Portfolio Analytics</h1>
          <p className="text-muted-foreground">
            AI-powered analysis of your Dhan portfolio
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              refetchHoldings();
              refetchSignals();
            }}
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh Data
          </Button>
        </div>
      </div>

      {/* User Portfolio Summary */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
        <Card className="bg-gradient-to-br from-green-50 to-green-100/50 dark:from-green-900/20 dark:to-green-800/10 border-green-200 dark:border-green-800">
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-green-100 dark:bg-green-900/50">
                <Wallet className="h-5 w-5 text-green-600" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Available Cash</p>
                <p className="text-xl font-bold">{formatCurrency(funds?.availableBalance || 0)}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-900/50">
                <BarChart3 className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Total Invested</p>
                <p className="text-xl font-bold">{formatCurrency(totalInvested)}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-purple-100 dark:bg-purple-900/50">
                <Activity className="h-5 w-5 text-purple-600" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Current Value</p>
                <p className="text-xl font-bold">{formatCurrency(totalCurrentValue)}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className={cn(
          totalPnL >= 0
            ? "bg-gradient-to-br from-emerald-50 to-emerald-100/50 dark:from-emerald-900/20 dark:to-emerald-800/10 border-emerald-200 dark:border-emerald-800"
            : "bg-gradient-to-br from-red-50 to-red-100/50 dark:from-red-900/20 dark:to-red-800/10 border-red-200 dark:border-red-800"
        )}>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className={cn(
                "p-2 rounded-lg",
                totalPnL >= 0 ? "bg-emerald-100 dark:bg-emerald-900/50" : "bg-red-100 dark:bg-red-900/50"
              )}>
                {totalPnL >= 0 ? (
                  <TrendingUp className="h-5 w-5 text-emerald-600" />
                ) : (
                  <TrendingDown className="h-5 w-5 text-red-600" />
                )}
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Total P&L</p>
                <p className={cn(
                  "text-xl font-bold",
                  totalPnL >= 0 ? "text-emerald-600" : "text-red-600"
                )}>
                  {totalPnL >= 0 ? '+' : ''}{formatCurrency(totalPnL)}
                </p>
                <p className={cn(
                  "text-xs",
                  totalPnL >= 0 ? "text-emerald-600" : "text-red-600"
                )}>
                  {totalPnLPercent >= 0 ? '+' : ''}{totalPnLPercent.toFixed(2)}%
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-amber-100 dark:bg-amber-900/50">
                <Brain className="h-5 w-5 text-amber-600" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Holdings</p>
                <p className="text-xl font-bold">{holdings.length}</p>
                <p className="text-xs text-muted-foreground">{positions.length} positions</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Portfolio Analysis Tabs */}
      <Tabs defaultValue="holdings" className="space-y-4">
        <TabsList className="grid w-full grid-cols-5 lg:w-[650px]">
          <TabsTrigger value="holdings">My Holdings</TabsTrigger>
          <TabsTrigger value="ai-analysis">AI Analysis</TabsTrigger>
          <TabsTrigger value="insights">AI Insights</TabsTrigger>
          <TabsTrigger value="risk">Risk Metrics</TabsTrigger>
          <TabsTrigger value="calculator">Calculator</TabsTrigger>
        </TabsList>

        {/* Holdings Tab - User's actual portfolio */}
        <TabsContent value="holdings" className="space-y-4">
          <div className="grid gap-6 lg:grid-cols-3">
            {/* Holdings List */}
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Wallet className="h-5 w-5" />
                  Your Portfolio Holdings
                </CardTitle>
                <CardDescription>
                  Click on a holding to see AI analysis
                </CardDescription>
              </CardHeader>
              <CardContent>
                {holdingsLoading ? (
                  <div className="space-y-3">
                    {[1, 2, 3, 4, 5].map((i) => (
                      <Skeleton key={i} className="h-16 w-full" />
                    ))}
                  </div>
                ) : holdings.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    <Wallet className="h-12 w-12 mx-auto mb-3 opacity-50" />
                    <p>No holdings found in your Dhan account</p>
                    <p className="text-sm mt-1">Start trading to build your portfolio</p>
                  </div>
                ) : (
                  <ScrollArea className="h-[400px]">
                    <div className="space-y-2">
                      {holdings.map((holding: any, idx: number) => {
                        const symbol = holding.tradingSymbol || holding.securityId || `Stock ${idx + 1}`;
                        const invested = (holding.avgCostPrice || 0) * (holding.totalQty || 0);
                        const current = (holding.ltp || holding.avgCostPrice || 0) * (holding.totalQty || 0);
                        const pnl = current - invested;
                        const pnlPercent = invested > 0 ? (pnl / invested) * 100 : 0;
                        const signal = Array.isArray(holdingSignals)
                          ? holdingSignals.find((s: any) => s.symbol === symbol)
                          : null;

                        return (
                          <button
                            key={idx}
                            onClick={() => setSelectedHolding(symbol)}
                            className={cn(
                              "w-full p-4 rounded-lg border text-left transition-all hover:bg-muted/50",
                              selectedHolding === symbol && "border-primary bg-primary/5 ring-1 ring-primary/20"
                            )}
                          >
                            <div className="flex items-center justify-between">
                              <div className="flex-1">
                                <div className="flex items-center gap-2">
                                  <span className="font-medium">{symbol}</span>
                                  {signal && (
                                    <Badge
                                      variant={signal.signal === 'BUY' ? 'default' : signal.signal === 'SELL' ? 'destructive' : 'secondary'}
                                      className="text-xs"
                                    >
                                      {signal.signal}
                                    </Badge>
                                  )}
                                </div>
                                <div className="flex items-center gap-4 mt-1 text-sm text-muted-foreground">
                                  <span>{holding.totalQty} qty</span>
                                  <span>Avg: {formatCurrency(holding.avgCostPrice || 0)}</span>
                                  <span>LTP: {formatCurrency(holding.ltp || holding.avgCostPrice || 0)}</span>
                                </div>
                              </div>
                              <div className="text-right">
                                <p className={cn(
                                  "font-medium",
                                  pnl >= 0 ? "text-green-600" : "text-red-600"
                                )}>
                                  {pnl >= 0 ? '+' : ''}{formatCurrency(pnl)}
                                </p>
                                <p className={cn(
                                  "text-sm",
                                  pnl >= 0 ? "text-green-600" : "text-red-600"
                                )}>
                                  {pnlPercent >= 0 ? '+' : ''}{pnlPercent.toFixed(2)}%
                                </p>
                              </div>
                              <ChevronRight className="h-4 w-4 text-muted-foreground ml-2" />
                            </div>
                          </button>
                        );
                      })}
                    </div>
                  </ScrollArea>
                )}
              </CardContent>
            </Card>

            {/* Portfolio Allocation Chart */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <PieChart className="h-5 w-5" />
                  Allocation
                </CardTitle>
              </CardHeader>
              <CardContent>
                {allocationData.length > 0 ? (
                  <div className="h-[300px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <RePieChart>
                        <Pie
                          data={allocationData}
                          cx="50%"
                          cy="50%"
                          innerRadius={60}
                          outerRadius={100}
                          paddingAngle={2}
                          dataKey="value"
                        >
                          {allocationData.map((_: any, index: number) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip
                          formatter={(value: any) => formatCurrency(Number(value || 0))}
                          contentStyle={{
                            backgroundColor: 'hsl(var(--card))',
                            border: '1px solid hsl(var(--border))',
                            borderRadius: '8px',
                          }}
                        />
                      </RePieChart>
                    </ResponsiveContainer>
                  </div>
                ) : (
                  <div className="h-[300px] flex items-center justify-center text-muted-foreground">
                    No data available
                  </div>
                )}
                <div className="mt-4 space-y-2">
                  {allocationData.slice(0, 5).map((item: { name: string; value: number; pnl: number; pnlPercent: number }, idx: number) => (
                    <div key={idx} className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-2">
                        <div
                          className="w-3 h-3 rounded-full"
                          style={{ backgroundColor: COLORS[idx % COLORS.length] }}
                        />
                        <span className="truncate max-w-[100px]">{item.name}</span>
                      </div>
                      <span className={cn(
                        "font-medium",
                        item.pnl >= 0 ? "text-green-600" : "text-red-600"
                      )}>
                        {item.pnlPercent >= 0 ? '+' : ''}{item.pnlPercent.toFixed(1)}%
                      </span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* AI Analysis Tab */}
        <TabsContent value="ai-analysis" className="space-y-4">
          <div className="grid gap-6 lg:grid-cols-2">
            {/* AI Signals for Portfolio */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Brain className="h-5 w-5 text-purple-500" />
                  AI Signals for Your Holdings
                </CardTitle>
                <CardDescription>
                  ML-generated signals for your portfolio stocks
                </CardDescription>
              </CardHeader>
              <CardContent>
                {signalsLoading ? (
                  <div className="space-y-3">
                    {[1, 2, 3].map((i) => (
                      <Skeleton key={i} className="h-16 w-full" />
                    ))}
                  </div>
                ) : Array.isArray(holdingSignals) && holdingSignals.length > 0 ? (
                  <ScrollArea className="h-[350px]">
                    <div className="space-y-3">
                      {holdingSignals.map((signal: any, idx: number) => (
                        <div key={idx} className="p-3 rounded-lg border">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <span className="font-medium">{signal.symbol}</span>
                              <Badge
                                variant={signal.signal === 'BUY' ? 'default' : signal.signal === 'SELL' ? 'destructive' : 'secondary'}
                              >
                                {signal.signal}
                              </Badge>
                            </div>
                            <div className="text-right">
                              <p className="text-sm font-medium">
                                {((signal.confidence ?? 0) * 100).toFixed(0)}% confidence
                              </p>
                            </div>
                          </div>
                          {signal.analysis && (
                            <div className="mt-2 grid grid-cols-3 gap-2 text-xs">
                              <div className="p-2 bg-muted rounded">
                                <p className="text-muted-foreground">Technical</p>
                                <p className="font-medium">{((signal.analysis.technical_score ?? 0) * 100).toFixed(0)}%</p>
                              </div>
                              <div className="p-2 bg-muted rounded">
                                <p className="text-muted-foreground">Sentiment</p>
                                <p className="font-medium">{((signal.analysis.sentiment_score ?? 0) * 100).toFixed(0)}%</p>
                              </div>
                              <div className="p-2 bg-muted rounded">
                                <p className="text-muted-foreground">ML Score</p>
                                <p className="font-medium">{((signal.analysis.ml_prediction ?? 0) * 100).toFixed(0)}%</p>
                              </div>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    <Brain className="h-12 w-12 mx-auto mb-3 opacity-50" />
                    <p>Add holdings to get AI signals</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Gemini Deep Analysis */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Sparkles className="h-5 w-5 text-amber-500" />
                  Gemini AI Deep Analysis
                </CardTitle>
                <CardDescription>
                  {selectedHolding
                    ? `Detailed analysis for ${selectedHolding}`
                    : 'Select a holding from the list to analyze'}
                </CardDescription>
              </CardHeader>
              <CardContent>
                {!selectedHolding ? (
                  <div className="text-center py-12 text-muted-foreground">
                    <Target className="h-12 w-12 mx-auto mb-3 opacity-50" />
                    <p>Click on a holding in the Holdings tab</p>
                    <p className="text-sm mt-1">to get detailed AI analysis</p>
                  </div>
                ) : analysisLoading ? (
                  <div className="space-y-3">
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-3/4" />
                    <Skeleton className="h-4 w-5/6" />
                    <Skeleton className="h-20 w-full" />
                  </div>
                ) : geminiAnalysis ? (
                  <ScrollArea className="h-[350px]">
                    <div className="space-y-4">
                      <div className="p-4 rounded-lg bg-gradient-to-r from-amber-50 to-orange-50 dark:from-amber-900/20 dark:to-orange-900/20 border border-amber-200 dark:border-amber-800">
                        <h4 className="font-medium mb-2 flex items-center gap-2">
                          <Sparkles className="h-4 w-4 text-amber-500" />
                          AI Recommendation
                        </h4>
                        <p className="text-sm">{geminiAnalysis.recommendation || geminiAnalysis.analysis || 'Analysis pending...'}</p>
                      </div>
                      {geminiAnalysis.key_points && (
                        <div>
                          <h4 className="font-medium mb-2">Key Points</h4>
                          <ul className="space-y-1 text-sm">
                            {geminiAnalysis.key_points.map((point: string, i: number) => (
                              <li key={i} className="flex items-start gap-2">
                                <span className="text-primary">•</span>
                                {point}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {geminiAnalysis.risk_factors && (
                        <div>
                          <h4 className="font-medium mb-2 text-red-600">Risk Factors</h4>
                          <ul className="space-y-1 text-sm">
                            {geminiAnalysis.risk_factors.map((risk: string, i: number) => (
                              <li key={i} className="flex items-start gap-2">
                                <AlertTriangle className="h-3 w-3 text-red-500 mt-1 shrink-0" />
                                {risk}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => refetchAnalysis()}
                        className="w-full"
                      >
                        <RefreshCw className="h-4 w-4 mr-2" />
                        Refresh Analysis
                      </Button>
                    </div>
                  </ScrollArea>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    <p>No analysis available</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* AI Insights Tab - Market Predictions, Trade Ideas, Sector Analysis */}
        <TabsContent value="insights" className="space-y-4">
          <div className="grid gap-6 lg:grid-cols-3">
            {/* Market Prediction */}
            <Card className="lg:col-span-1">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Globe className="h-5 w-5 text-blue-500" />
                  Market Prediction
                </CardTitle>
                <CardDescription>AI-powered market outlook</CardDescription>
              </CardHeader>
              <CardContent>
                {marketLoading ? (
                  <div className="space-y-3">
                    <Skeleton className="h-20 w-full" />
                    <Skeleton className="h-4 w-3/4" />
                  </div>
                ) : marketPrediction ? (
                  <div className="space-y-4">
                    <div className={cn(
                      "p-4 rounded-lg text-center",
                      marketPrediction.direction === 'bullish'
                        ? "bg-green-100 dark:bg-green-900/30 border border-green-200 dark:border-green-800"
                        : marketPrediction.direction === 'bearish'
                        ? "bg-red-100 dark:bg-red-900/30 border border-red-200 dark:border-red-800"
                        : "bg-yellow-100 dark:bg-yellow-900/30 border border-yellow-200 dark:border-yellow-800"
                    )}>
                      <div className="flex items-center justify-center gap-2 mb-2">
                        {marketPrediction.direction === 'bullish' ? (
                          <ArrowUpRight className="h-6 w-6 text-green-600" />
                        ) : marketPrediction.direction === 'bearish' ? (
                          <ArrowDownRight className="h-6 w-6 text-red-600" />
                        ) : (
                          <Activity className="h-6 w-6 text-yellow-600" />
                        )}
                        <span className="text-lg font-bold capitalize">
                          {marketPrediction.direction || 'Neutral'}
                        </span>
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {((marketPrediction.confidence ?? 0) * 100).toFixed(0)}% confidence
                      </p>
                    </div>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Nifty Prediction</span>
                        <span className={cn(
                          "font-medium",
                          (marketPrediction.nifty_change || 0) >= 0 ? "text-green-600" : "text-red-600"
                        )}>
                          {(marketPrediction.nifty_change || 0) >= 0 ? '+' : ''}
                          {(marketPrediction.nifty_change || 0).toFixed(2)}%
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Volatility</span>
                        <span className="font-medium">{marketPrediction.volatility || 'Moderate'}</span>
                      </div>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      className="w-full"
                      onClick={() => refetchMarket()}
                    >
                      <RefreshCw className="h-4 w-4 mr-2" />
                      Refresh
                    </Button>
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <Globe className="h-12 w-12 mx-auto mb-3 text-muted-foreground opacity-50" />
                    <p className="text-muted-foreground">Market prediction unavailable</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* AI Trade Ideas */}
            <Card className="lg:col-span-2">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <Lightbulb className="h-5 w-5 text-yellow-500" />
                      AI Trade Ideas
                    </CardTitle>
                    <CardDescription>Personalized recommendations based on your portfolio</CardDescription>
                  </div>
                  <Button variant="outline" size="sm" onClick={() => refetchIdeas()}>
                    <RefreshCw className="h-4 w-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {ideasLoading ? (
                  <div className="space-y-3">
                    {[1, 2, 3].map((i) => (
                      <Skeleton key={i} className="h-20 w-full" />
                    ))}
                  </div>
                ) : tradeIdeas?.ideas && tradeIdeas.ideas.length > 0 ? (
                  <ScrollArea className="h-[300px]">
                    <div className="space-y-3">
                      {tradeIdeas.ideas.map((idea: any, idx: number) => (
                        <div
                          key={idx}
                          className="p-4 rounded-lg border hover:bg-muted/50 transition-colors"
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center gap-2">
                                <span className="font-semibold">{idea.symbol}</span>
                                <Badge
                                  variant={idea.action === 'BUY' ? 'default' : 'destructive'}
                                  className="text-xs"
                                >
                                  {idea.action}
                                </Badge>
                                <Badge variant="outline" className="text-xs">
                                  {((idea.confidence ?? 0) * 100).toFixed(0)}%
                                </Badge>
                              </div>
                              <p className="text-sm text-muted-foreground mt-1">{idea.rationale}</p>
                              <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                                <span className="flex items-center gap-1">
                                  <Target className="h-3 w-3" />
                                  Target: {formatCurrency(idea.target_price || 0)}
                                </span>
                                <span className="flex items-center gap-1">
                                  <AlertTriangle className="h-3 w-3" />
                                  Stop: {formatCurrency(idea.stop_loss || 0)}
                                </span>
                                <span className="flex items-center gap-1">
                                  <Clock className="h-3 w-3" />
                                  {idea.timeframe || 'Short-term'}
                                </span>
                              </div>
                            </div>
                            <div className="text-right">
                              <p className="text-lg font-bold text-green-600">
                                +{((idea.expected_return ?? 0) * 100).toFixed(1)}%
                              </p>
                              <p className="text-xs text-muted-foreground">Expected</p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                ) : (
                  <div className="text-center py-8">
                    <Lightbulb className="h-12 w-12 mx-auto mb-3 text-muted-foreground opacity-50" />
                    <p className="text-muted-foreground">No trade ideas available</p>
                    <p className="text-sm text-muted-foreground mt-1">Check back later for AI recommendations</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Portfolio Optimization & Sector Analysis */}
          <div className="grid gap-6 lg:grid-cols-2">
            {/* Portfolio Optimization */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Zap className="h-5 w-5 text-orange-500" />
                  Portfolio Optimization
                </CardTitle>
                <CardDescription>AI-suggested portfolio adjustments</CardDescription>
              </CardHeader>
              <CardContent>
                {optimizationLoading ? (
                  <div className="space-y-3">
                    <Skeleton className="h-16 w-full" />
                    <Skeleton className="h-16 w-full" />
                  </div>
                ) : portfolioOptimization ? (
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="p-3 rounded-lg bg-muted">
                        <p className="text-xs text-muted-foreground">Current Score</p>
                        <p className="text-xl font-bold">{portfolioOptimization.current_score || 75}/100</p>
                      </div>
                      <div className="p-3 rounded-lg bg-green-100 dark:bg-green-900/30">
                        <p className="text-xs text-muted-foreground">Optimized Score</p>
                        <p className="text-xl font-bold text-green-600">{portfolioOptimization.optimized_score || 85}/100</p>
                      </div>
                    </div>
                    {portfolioOptimization.suggestions && Array.isArray(portfolioOptimization.suggestions) && (
                      <div className="space-y-2">
                        <h4 className="text-sm font-medium">Suggestions:</h4>
                        <ul className="space-y-1 text-sm">
                          {portfolioOptimization.suggestions.slice(0, 4).map((s: string, i: number) => (
                            <li key={i} className="flex items-start gap-2">
                              <ChevronRight className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                              {s}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {portfolioOptimization.rebalance_actions && Array.isArray(portfolioOptimization.rebalance_actions) && (
                      <div className="space-y-2">
                        <h4 className="text-sm font-medium">Rebalance Actions:</h4>
                        <div className="space-y-1">
                          {portfolioOptimization.rebalance_actions.slice(0, 3).map((action: any, i: number) => (
                            <div key={i} className="flex items-center justify-between text-sm p-2 rounded bg-muted">
                              <span>{action.symbol}</span>
                              <Badge variant={action.action === 'increase' ? 'default' : 'destructive'}>
                                {action.action === 'increase' ? '+' : '-'}{action.percent}%
                              </Badge>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <Zap className="h-12 w-12 mx-auto mb-3 text-muted-foreground opacity-50" />
                    <p className="text-muted-foreground">Add holdings to optimize</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Sector Analysis */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Layers className="h-5 w-5 text-purple-500" />
                  Sector Analysis
                </CardTitle>
                <CardDescription>Market sector performance insights</CardDescription>
              </CardHeader>
              <CardContent>
                {sectorsLoading ? (
                  <div className="space-y-3">
                    {[1, 2, 3, 4, 5].map((i) => (
                      <Skeleton key={i} className="h-12 w-full" />
                    ))}
                  </div>
                ) : sectorAnalysis?.sectors ? (
                  <ScrollArea className="h-[300px]">
                    <div className="space-y-2">
                      {sectorAnalysis.sectors.map((sector: any, idx: number) => (
                        <div
                          key={idx}
                          className="flex items-center justify-between p-3 rounded-lg border"
                        >
                          <div className="flex items-center gap-3">
                            <div className={cn(
                              "p-2 rounded-lg",
                              sector.trend === 'bullish'
                                ? "bg-green-100 dark:bg-green-900/30"
                                : sector.trend === 'bearish'
                                ? "bg-red-100 dark:bg-red-900/30"
                                : "bg-gray-100 dark:bg-gray-800"
                            )}>
                              {sector.trend === 'bullish' ? (
                                <TrendingUp className="h-4 w-4 text-green-600" />
                              ) : sector.trend === 'bearish' ? (
                                <TrendingDown className="h-4 w-4 text-red-600" />
                              ) : (
                                <Activity className="h-4 w-4 text-gray-600" />
                              )}
                            </div>
                            <div>
                              <p className="font-medium">{sector.name}</p>
                              <p className="text-xs text-muted-foreground">{sector.outlook}</p>
                            </div>
                          </div>
                          <div className="text-right">
                            <p className={cn(
                              "font-medium",
                              sector.change >= 0 ? "text-green-600" : "text-red-600"
                            )}>
                              {sector.change >= 0 ? '+' : ''}{sector.change?.toFixed(2)}%
                            </p>
                            <Badge variant="outline" className="text-xs">
                              {sector.signal || 'HOLD'}
                            </Badge>
                          </div>
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                ) : (
                  <div className="text-center py-8">
                    <Layers className="h-12 w-12 mx-auto mb-3 text-muted-foreground opacity-50" />
                    <p className="text-muted-foreground">Sector analysis unavailable</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Risk Metrics Tab */}
        <TabsContent value="risk" className="space-y-4">
      {/* Risk Overview Cards */}
      {riskMetrics && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <MetricCard
            title="Sharpe Ratio"
            value={riskMetrics.sharpe_ratio.toFixed(2)}
            icon={TrendingUp}
            description="Risk-adjusted return"
            trend={riskMetrics.sharpe_ratio > 1 ? 'up' : 'down'}
          />
          <MetricCard
            title="Sortino Ratio"
            value={riskMetrics.sortino_ratio.toFixed(2)}
            icon={Shield}
            description="Downside risk adjusted"
            trend={riskMetrics.sortino_ratio > 1.5 ? 'up' : 'down'}
          />
          <MetricCard
            title="Max Drawdown"
            value={formatPercent(-riskMetrics.max_drawdown_pct)}
            icon={TrendingDown}
            description="Largest peak-to-trough"
            trend={riskMetrics.max_drawdown_pct < 10 ? 'up' : 'down'}
          />
          <MetricCard
            title="Ann. Volatility"
            value={formatPercent(riskMetrics.annualized_volatility * 100)}
            icon={Percent}
            description="Annualized std dev"
            trend={riskMetrics.annualized_volatility < 0.25 ? 'up' : 'down'}
          />
        </div>
      )}

      {/* Charts Section */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Returns Chart */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Cumulative Returns</CardTitle>
            <CardDescription>Performance over time</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={returnChartData}>
                  <defs>
                    <linearGradient id="returnGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                  <XAxis dataKey="day" className="text-xs" />
                  <YAxis className="text-xs" tickFormatter={(v) => `${v}%`} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'hsl(var(--card))',
                      border: '1px solid hsl(var(--border))',
                      borderRadius: '8px',
                    }}
                    formatter={(value: any) => [`${Number(value || 0).toFixed(2)}%`, 'Cumulative Return']}
                  />
                  <Area
                    type="monotone"
                    dataKey="cumulative"
                    stroke="hsl(var(--primary))"
                    fill="url(#returnGradient)"
                    strokeWidth={2}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Drawdown Chart */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Drawdown Analysis</CardTitle>
            <CardDescription>Peak-to-trough declines</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={drawdownData}>
                  <defs>
                    <linearGradient id="drawdownGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="hsl(var(--destructive))" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="hsl(var(--destructive))" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                  <XAxis dataKey="day" className="text-xs" />
                  <YAxis className="text-xs" tickFormatter={(v) => `${v}%`} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'hsl(var(--card))',
                      border: '1px solid hsl(var(--border))',
                      borderRadius: '8px',
                    }}
                    formatter={(value: any) => [`${Number(value || 0).toFixed(2)}%`, 'Drawdown']}
                  />
                  <Area
                    type="monotone"
                    dataKey="drawdown"
                    stroke="hsl(var(--destructive))"
                    fill="url(#drawdownGradient)"
                    strokeWidth={2}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Risk Calculators */}
      <Tabs defaultValue="var" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="var">VaR Analysis</TabsTrigger>
          <TabsTrigger value="kelly">Kelly Criterion</TabsTrigger>
          <TabsTrigger value="position">Position Sizing</TabsTrigger>
          <TabsTrigger value="execution">Execution</TabsTrigger>
        </TabsList>

        {/* VaR Tab */}
        <TabsContent value="var" className="mt-6">
          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 text-yellow-500" />
                  Value at Risk (VaR)
                </CardTitle>
                <CardDescription>
                  Maximum expected loss at 95% confidence level
                </CardDescription>
              </CardHeader>
              <CardContent>
                {varLoading ? (
                  <div className="space-y-4">
                    <Skeleton className="h-12 w-full" />
                    <Skeleton className="h-8 w-3/4" />
                  </div>
                ) : varData ? (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between rounded-lg bg-yellow-100 dark:bg-yellow-900/20 p-4">
                      <span className="text-sm">VaR (95%)</span>
                      <span className="text-2xl font-bold text-yellow-700 dark:text-yellow-400">
                        {formatPercent(varData.var_pct || Math.abs(varData.var) * 100)}
                      </span>
                    </div>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <p className="text-muted-foreground">Method</p>
                        <p className="font-medium capitalize">{varData.method}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Confidence</p>
                        <p className="font-medium">{((varData.confidence ?? 0) * 100).toFixed(0)}%</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Sample Size</p>
                        <p className="font-medium">{varData.samples} days</p>
                      </div>
                    </div>
                  </div>
                ) : (
                  <p className="text-muted-foreground">Unable to calculate VaR</p>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Target className="h-5 w-5 text-red-500" />
                  Conditional VaR (CVaR)
                </CardTitle>
                <CardDescription>
                  Expected loss when VaR is breached
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="rounded-lg bg-red-100 dark:bg-red-900/20 p-4">
                    <p className="text-sm text-muted-foreground mb-1">Expected Shortfall</p>
                    <p className="text-2xl font-bold text-red-700 dark:text-red-400">
                      {riskMetrics ? formatPercent(Math.abs(riskMetrics.cvar_95) * 100) : 'N/A'}
                    </p>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    CVaR represents the average loss in the worst 5% of scenarios.
                    It provides a more complete picture of tail risk than VaR alone.
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Kelly Tab */}
        <TabsContent value="kelly" className="mt-6">
          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Calculator className="h-5 w-5 text-blue-500" />
                  Kelly Criterion Calculator
                </CardTitle>
                <CardDescription>
                  Optimal position sizing based on edge
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4">
                  <div className="space-y-2">
                    <Label>Win Rate (%)</Label>
                    <Input
                      type="number"
                      value={(parseFloat(winRate) * 100).toString()}
                      onChange={(e) => setWinRate((parseFloat(e.target.value) / 100).toString())}
                      step="1"
                      min="0"
                      max="100"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Average Win (%)</Label>
                    <Input
                      type="number"
                      value={(parseFloat(avgWin) * 100).toString()}
                      onChange={(e) => setAvgWin((parseFloat(e.target.value) / 100).toString())}
                      step="0.5"
                      min="0"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Average Loss (%)</Label>
                    <Input
                      type="number"
                      value={(parseFloat(avgLoss) * 100).toString()}
                      onChange={(e) => setAvgLoss((parseFloat(e.target.value) / 100).toString())}
                      step="0.5"
                      min="0"
                    />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Kelly Results</CardTitle>
                <CardDescription>Optimal allocation percentages</CardDescription>
              </CardHeader>
              <CardContent>
                {kellyLoading ? (
                  <div className="space-y-4">
                    <Skeleton className="h-12 w-full" />
                    <Skeleton className="h-8 w-3/4" />
                  </div>
                ) : kellyData ? (
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="rounded-lg bg-blue-100 dark:bg-blue-900/20 p-4 text-center">
                        <p className="text-xs text-muted-foreground">Full Kelly</p>
                        <p className="text-2xl font-bold text-blue-700 dark:text-blue-400">
                          {kellyData.kelly_pct?.toFixed(1) || 0}%
                        </p>
                      </div>
                      <div className="rounded-lg bg-green-100 dark:bg-green-900/20 p-4 text-center">
                        <p className="text-xs text-muted-foreground">Half Kelly (Recommended)</p>
                        <p className="text-2xl font-bold text-green-700 dark:text-green-400">
                          {((kellyData.half_kelly || 0) * 100).toFixed(1)}%
                        </p>
                      </div>
                    </div>
                    <div className="rounded-lg bg-muted p-3">
                      <p className="text-xs">
                        <strong>Recommendation:</strong>{' '}
                        <Badge variant="outline" className="ml-1">
                          {kellyData.recommendation?.replace('_', ' ').toUpperCase()}
                        </Badge>
                      </p>
                      <p className="text-xs text-muted-foreground mt-1">
                        Win/Loss Ratio: {kellyData.win_loss_ratio?.toFixed(2)}
                      </p>
                    </div>
                  </div>
                ) : (
                  <p className="text-muted-foreground">Enter values to calculate</p>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Position Sizing Tab */}
        <TabsContent value="position" className="mt-6">
          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <PieChart className="h-5 w-5 text-purple-500" />
                  Position Size Calculator
                </CardTitle>
                <CardDescription>
                  Calculate optimal position size based on risk
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4">
                  <div className="space-y-2">
                    <Label>Capital (₹)</Label>
                    <Input
                      type="number"
                      value={capital}
                      onChange={(e) => setCapital(e.target.value)}
                      min="0"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Risk Per Trade (%)</Label>
                    <Input
                      type="number"
                      value={(parseFloat(riskPerTrade) * 100).toString()}
                      onChange={(e) => setRiskPerTrade((parseFloat(e.target.value) / 100).toString())}
                      step="0.5"
                      min="0"
                      max="10"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Stop Loss (%)</Label>
                    <Input
                      type="number"
                      value={(parseFloat(stopLoss) * 100).toString()}
                      onChange={(e) => setStopLoss((parseFloat(e.target.value) / 100).toString())}
                      step="0.5"
                      min="0"
                    />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Position Results</CardTitle>
                <CardDescription>Recommended position size</CardDescription>
              </CardHeader>
              <CardContent>
                {positionLoading ? (
                  <div className="space-y-4">
                    <Skeleton className="h-12 w-full" />
                    <Skeleton className="h-8 w-3/4" />
                  </div>
                ) : positionData ? (
                  <div className="space-y-4">
                    <div className="rounded-lg bg-purple-100 dark:bg-purple-900/20 p-4 text-center">
                      <p className="text-xs text-muted-foreground">Optimal Position Size</p>
                      <p className="text-3xl font-bold text-purple-700 dark:text-purple-400">
                        {formatCurrency(positionData.optimal_position_size || 0)}
                      </p>
                    </div>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div className="rounded-lg border p-3">
                        <p className="text-muted-foreground">Risk Amount</p>
                        <p className="font-mono font-semibold">
                          {formatCurrency(positionData.risk_amount || 0)}
                        </p>
                      </div>
                      <div className="rounded-lg border p-3">
                        <p className="text-muted-foreground">% of Capital</p>
                        <p className="font-mono font-semibold">
                          {positionData.position_pct_of_capital?.toFixed(1) || 0}%
                        </p>
                      </div>
                    </div>
                  </div>
                ) : (
                  <p className="text-muted-foreground">Enter values to calculate</p>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Execution Tab */}
        <TabsContent value="execution" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5 text-green-500" />
                Execution Analytics
              </CardTitle>
              <CardDescription>
                TWAP/VWAP execution performance metrics
              </CardDescription>
            </CardHeader>
            <CardContent>
              {executionData ? (
                <div className="grid gap-4 md:grid-cols-3">
                  <div className="rounded-lg border p-4">
                    <p className="text-sm text-muted-foreground">Total Executions</p>
                    <p className="text-2xl font-bold">{executionData.total_executions || 0}</p>
                  </div>
                  <div className="rounded-lg border p-4">
                    <p className="text-sm text-muted-foreground">Avg Slippage</p>
                    <p className="text-2xl font-bold">
                      {formatPercent(executionData.avg_slippage || 0)}
                    </p>
                  </div>
                  <div className="rounded-lg border p-4">
                    <p className="text-sm text-muted-foreground">Fill Rate</p>
                    <p className="text-2xl font-bold">
                      {formatPercent(executionData.fill_rate || 0)}
                    </p>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  No execution data available
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
        </TabsContent>

        {/* Calculator Tab */}
        <TabsContent value="calculator" className="space-y-4">
          <div className="grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Calculator className="h-5 w-5" />
                  Position Size Calculator
                </CardTitle>
                <CardDescription>
                  Calculate optimal position size based on risk parameters
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4">
                  <div className="space-y-2">
                    <Label>Capital (₹)</Label>
                    <Input
                      type="number"
                      value={capital}
                      onChange={(e) => setCapital(e.target.value)}
                      placeholder="100000"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Risk Per Trade (%)</Label>
                    <Input
                      type="number"
                      step="0.01"
                      value={riskPerTrade}
                      onChange={(e) => setRiskPerTrade(e.target.value)}
                      placeholder="0.02"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Stop Loss (%)</Label>
                    <Input
                      type="number"
                      step="0.01"
                      value={stopLoss}
                      onChange={(e) => setStopLoss(e.target.value)}
                      placeholder="0.05"
                    />
                  </div>
                </div>
                {positionLoading ? (
                  <Skeleton className="h-20 w-full" />
                ) : positionData ? (
                  <div className="p-4 rounded-lg bg-primary/10 border border-primary/20">
                    <p className="text-sm text-muted-foreground">Recommended Position Size</p>
                    <p className="text-2xl font-bold text-primary">
                      {formatCurrency(positionData.position_size || 0)}
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">
                      Risk Amount: {formatCurrency(positionData.risk_amount || 0)}
                    </p>
                  </div>
                ) : null}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Target className="h-5 w-5" />
                  Kelly Criterion Calculator
                </CardTitle>
                <CardDescription>
                  Calculate optimal bet size based on win rate
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4">
                  <div className="space-y-2">
                    <Label>Win Rate (0-1)</Label>
                    <Input
                      type="number"
                      step="0.01"
                      value={winRate}
                      onChange={(e) => setWinRate(e.target.value)}
                      placeholder="0.55"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Average Win (0-1)</Label>
                    <Input
                      type="number"
                      step="0.01"
                      value={avgWin}
                      onChange={(e) => setAvgWin(e.target.value)}
                      placeholder="0.03"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Average Loss (0-1)</Label>
                    <Input
                      type="number"
                      step="0.01"
                      value={avgLoss}
                      onChange={(e) => setAvgLoss(e.target.value)}
                      placeholder="0.02"
                    />
                  </div>
                </div>
                {kellyLoading ? (
                  <Skeleton className="h-20 w-full" />
                ) : kellyData ? (
                  <div className="p-4 rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800">
                    <p className="text-sm text-muted-foreground">Kelly Fraction</p>
                    <p className="text-2xl font-bold text-green-600">
                      {formatPercent((kellyData.kelly_fraction || 0) * 100)}
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">
                      Half Kelly: {formatPercent((kellyData.half_kelly || 0) * 100)}
                    </p>
                  </div>
                ) : null}
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}

function MetricCard({
  title,
  value,
  icon: Icon,
  description,
  trend,
}: {
  title: string;
  value: string;
  icon: any;
  description: string;
  trend: 'up' | 'down';
}) {
  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div className={`rounded-lg p-2 ${trend === 'up' ? 'bg-green-100 dark:bg-green-900/30' : 'bg-yellow-100 dark:bg-yellow-900/30'}`}>
            <Icon className={`h-5 w-5 ${trend === 'up' ? 'text-green-600' : 'text-yellow-600'}`} />
          </div>
          {trend === 'up' ? (
            <TrendingUp className="h-4 w-4 text-green-500" />
          ) : (
            <TrendingDown className="h-4 w-4 text-yellow-500" />
          )}
        </div>
        <p className="mt-4 text-2xl font-bold">{value}</p>
        <p className="text-sm font-medium">{title}</p>
        <p className="text-xs text-muted-foreground">{description}</p>
      </CardContent>
    </Card>
  );
}

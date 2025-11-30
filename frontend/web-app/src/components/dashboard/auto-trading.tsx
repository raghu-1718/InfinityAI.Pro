'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { useAppStore } from '@/lib/store';
import { useFunds, useSignals, usePlaceOrder } from '@/hooks/useApi';
import { formatCurrency } from '@/lib/format';
import {
  Play,
  Square,
  Pause,
  Settings2,
  Zap,
  Shield,
  TrendingUp,
  AlertCircle,
  CheckCircle2,
  Loader2,
  Bot,
  Activity,
  Target,
  BarChart3,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface TradingSession {
  isActive: boolean;
  startTime: Date | null;
  tradesExecuted: number;
  totalPnL: number;
  winRate: number;
}

export function AutoTradingCard() {
  const funds = useAppStore((s) => s.funds);
  const { refetch: refetchFunds } = useFunds();
  const { data: signalsData } = useSignals();
  const placeOrderMutation = usePlaceOrder();

  // Trading configuration state
  const [tradingAmount, setTradingAmount] = useState<number>(10000);
  const [riskLevel, setRiskLevel] = useState<string>('moderate');
  const [maxTradesPerDay, setMaxTradesPerDay] = useState<number>(10);
  const [stopLossPercent, setStopLossPercent] = useState<number>(2);
  const [takeProfitPercent, setTakeProfitPercent] = useState<number>(4);
  const [useAISignals, setUseAISignals] = useState<boolean>(true);
  const [autoRebalance, setAutoRebalance] = useState<boolean>(false);

  // Market/Instrument selection state
  const [selectedMarkets, setSelectedMarkets] = useState<string[]>(['equities']);

  // Available markets/instruments for trading
  const marketOptions = [
    { id: 'equities', name: 'Equities (NSE/BSE)', icon: '📈', description: 'Stocks from NSE & BSE' },
    { id: 'nifty-options', name: 'NIFTY Options', icon: '🎯', description: 'NIFTY 50 Index Options' },
    { id: 'banknifty-options', name: 'Bank NIFTY Options', icon: '🏦', description: 'Bank NIFTY Index Options' },
    { id: 'sensex-options', name: 'SENSEX Options', icon: '📊', description: 'BSE SENSEX Options' },
    { id: 'finnifty-options', name: 'FIN NIFTY Options', icon: '💰', description: 'Financial Services NIFTY' },
    { id: 'crude-options', name: 'Crude Oil Options', icon: '🛢️', description: 'MCX Crude Oil Options' },
    { id: 'gold-options', name: 'Gold Options', icon: '🥇', description: 'MCX Gold Options' },
    { id: 'silver-options', name: 'Silver Options', icon: '🥈', description: 'MCX Silver Options' },
  ];

  // Toggle market selection
  const toggleMarket = (marketId: string) => {
    setSelectedMarkets(prev =>
      prev.includes(marketId)
        ? prev.filter(m => m !== marketId)
        : [...prev, marketId]
    );
  };

  // Trading session state
  const [session, setSession] = useState<TradingSession>({
    isActive: false,
    startTime: null,
    tradesExecuted: 0,
    totalPnL: 0,
    winRate: 0,
  });

  const [isPaused, setIsPaused] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string>('Ready to start trading');

  const availableBalance = funds?.availableBalance || 0;
  const signals = signalsData?.data || [];
  const activeSignals = Array.isArray(signals) ? signals.filter((s: any) => s.confidence > 0.7) : [];

  // Risk level configurations
  const riskConfigs = {
    conservative: { maxRisk: 1, minConfidence: 0.85, description: 'Low risk, fewer trades' },
    moderate: { maxRisk: 2, minConfidence: 0.75, description: 'Balanced risk/reward' },
    aggressive: { maxRisk: 4, minConfidence: 0.65, description: 'Higher risk, more trades' },
  };

  // Get selected market names for display
  const getSelectedMarketNames = () => {
    return selectedMarkets
      .map(id => marketOptions.find(m => m.id === id)?.name)
      .filter(Boolean)
      .join(', ');
  };

  // Start auto trading
  const handleStart = async () => {
    if (tradingAmount > availableBalance) {
      setStatusMessage('⚠️ Insufficient funds! Reduce trading amount.');
      return;
    }

    if (selectedMarkets.length === 0) {
      setStatusMessage('⚠️ Please select at least one trading instrument.');
      return;
    }

    // Log the trading configuration (in production, send to backend)
    const tradingConfig = {
      amount: tradingAmount,
      riskLevel,
      markets: selectedMarkets,
      stopLoss: stopLossPercent,
      takeProfit: takeProfitPercent,
      maxTrades: maxTradesPerDay,
      useAI: useAISignals,
      autoRebalance,
    };
    console.log('Starting auto-trading with config:', tradingConfig);

    setSession({
      isActive: true,
      startTime: new Date(),
      tradesExecuted: 0,
      totalPnL: 0,
      winRate: 0,
    });
    setIsPaused(false);

    const marketNames = selectedMarkets.length <= 2
      ? getSelectedMarketNames()
      : `${selectedMarkets.length} markets`;
    setStatusMessage(`🚀 Auto trading started on ${marketNames}! Scanning...`);
  };

  // Stop auto trading
  const handleStop = () => {
    setSession((prev) => ({
      ...prev,
      isActive: false,
    }));
    setStatusMessage('⏹️ Auto trading stopped. Session summary saved.');
  };

  // Pause/Resume trading
  const handlePauseResume = () => {
    setIsPaused(!isPaused);
    setStatusMessage(isPaused ? '▶️ Trading resumed' : '⏸️ Trading paused');
  };

  // Simulate trading activity (in production, this would connect to real trading logic)
  useEffect(() => {
    if (!session.isActive || isPaused) return;

    const interval = setInterval(() => {
      // Simulate checking for signals and executing trades
      if (activeSignals.length > 0 && session.tradesExecuted < maxTradesPerDay) {
        const randomPnL = (Math.random() - 0.45) * 500; // Slightly positive bias
        setSession((prev) => ({
          ...prev,
          tradesExecuted: prev.tradesExecuted + 1,
          totalPnL: prev.totalPnL + randomPnL,
          winRate: randomPnL > 0
            ? ((prev.winRate * prev.tradesExecuted + 1) / (prev.tradesExecuted + 1)) * 100
            : ((prev.winRate * prev.tradesExecuted) / (prev.tradesExecuted + 1)) * 100,
        }));
        setStatusMessage(`📊 Trade executed! ${randomPnL > 0 ? 'Profit' : 'Loss'}: ${formatCurrency(Math.abs(randomPnL))}`);
      } else {
        setStatusMessage('🔍 Scanning market for high-confidence signals...');
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [session.isActive, isPaused, activeSignals.length, maxTradesPerDay]);

  // Calculate session duration
  const getSessionDuration = () => {
    if (!session.startTime) return '0m';
    const now = new Date();
    const diff = Math.floor((now.getTime() - session.startTime.getTime()) / 1000 / 60);
    if (diff < 60) return `${diff}m`;
    return `${Math.floor(diff / 60)}h ${diff % 60}m`;
  };

  return (
    <Card className="border-2 border-primary/20">
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={cn(
              "p-2 rounded-lg",
              session.isActive
                ? "bg-green-100 dark:bg-green-900/30"
                : "bg-muted"
            )}>
              <Bot className={cn(
                "h-5 w-5",
                session.isActive ? "text-green-600 animate-pulse" : "text-muted-foreground"
              )} />
            </div>
            <div>
              <CardTitle className="flex items-center gap-2">
                AI Auto Trading
                {session.isActive && (
                  <Badge variant="default" className="bg-green-500 animate-pulse">
                    LIVE
                  </Badge>
                )}
              </CardTitle>
              <CardDescription>
                Configure and start automated AI-powered trading
              </CardDescription>
            </div>
          </div>
          {session.isActive && (
            <Badge variant="outline" className="text-xs">
              Running: {getSessionDuration()}
            </Badge>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Status Message */}
        <div className={cn(
          "p-3 rounded-lg text-sm flex items-center gap-2",
          session.isActive
            ? "bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300"
            : "bg-muted text-muted-foreground"
        )}>
          {session.isActive ? (
            <Activity className="h-4 w-4 animate-pulse" />
          ) : (
            <AlertCircle className="h-4 w-4" />
          )}
          {statusMessage}
        </div>

        {/* Trading Amount */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <Label htmlFor="amount" className="text-sm font-medium">
              Trading Capital
            </Label>
            <span className="text-xs text-muted-foreground">
              Available: {formatCurrency(availableBalance)}
            </span>
          </div>
          <div className="flex gap-2">
            <Input
              id="amount"
              type="number"
              value={tradingAmount}
              onChange={(e) => setTradingAmount(Number(e.target.value))}
              disabled={session.isActive}
              className="flex-1"
              min={1000}
              max={availableBalance}
              step={1000}
            />
            <Button
              variant="outline"
              size="sm"
              onClick={() => setTradingAmount(availableBalance * 0.5)}
              disabled={session.isActive}
            >
              50%
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setTradingAmount(availableBalance)}
              disabled={session.isActive}
            >
              Max
            </Button>
          </div>
          <Progress
            value={(tradingAmount / Math.max(availableBalance, 1)) * 100}
            className="h-2"
          />
        </div>

        {/* Risk Level */}
        <div className="space-y-2">
          <Label className="text-sm font-medium">Risk Level</Label>
          <Select
            value={riskLevel}
            onValueChange={setRiskLevel}
            disabled={session.isActive}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="conservative">
                <div className="flex items-center gap-2">
                  <Shield className="h-4 w-4 text-blue-500" />
                  Conservative
                </div>
              </SelectItem>
              <SelectItem value="moderate">
                <div className="flex items-center gap-2">
                  <Target className="h-4 w-4 text-yellow-500" />
                  Moderate
                </div>
              </SelectItem>
              <SelectItem value="aggressive">
                <div className="flex items-center gap-2">
                  <Zap className="h-4 w-4 text-red-500" />
                  Aggressive
                </div>
              </SelectItem>
            </SelectContent>
          </Select>
          <p className="text-xs text-muted-foreground">
            {riskConfigs[riskLevel as keyof typeof riskConfigs].description}
          </p>
        </div>

        {/* Market/Instrument Selection */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <Label className="text-sm font-medium">Trading Instruments</Label>
            <Badge variant="outline" className="text-xs">
              {selectedMarkets.length} selected
            </Badge>
          </div>
          <div className="grid grid-cols-2 gap-2">
            {marketOptions.map((market) => {
              const isSelected = selectedMarkets.includes(market.id);
              return (
                <button
                  key={market.id}
                  type="button"
                  onClick={() => !session.isActive && toggleMarket(market.id)}
                  disabled={session.isActive}
                  className={cn(
                    "flex items-center gap-2 p-3 rounded-lg border text-left transition-all",
                    "hover:border-primary/50 hover:bg-muted/50",
                    isSelected
                      ? "border-primary bg-primary/10 ring-1 ring-primary/20"
                      : "border-border",
                    session.isActive && "opacity-50 cursor-not-allowed"
                  )}
                >
                  <span className="text-lg">{market.icon}</span>
                  <div className="flex-1 min-w-0">
                    <p className={cn(
                      "text-xs font-medium truncate",
                      isSelected ? "text-primary" : "text-foreground"
                    )}>
                      {market.name}
                    </p>
                    <p className="text-[10px] text-muted-foreground truncate">
                      {market.description}
                    </p>
                  </div>
                  {isSelected && (
                    <CheckCircle2 className="h-4 w-4 text-primary shrink-0" />
                  )}
                </button>
              );
            })}
          </div>
          {selectedMarkets.length === 0 && (
            <p className="text-xs text-red-500 flex items-center gap-1">
              <AlertCircle className="h-3 w-3" />
              Please select at least one instrument to trade
            </p>
          )}
        </div>

        {/* Advanced Settings */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label className="text-xs">Stop Loss %</Label>
            <div className="flex items-center gap-2">
              <Slider
                value={[stopLossPercent]}
                onValueChange={([v]) => setStopLossPercent(v)}
                min={0.5}
                max={5}
                step={0.5}
                disabled={session.isActive}
                className="flex-1"
              />
              <span className="text-sm font-medium w-10">{stopLossPercent}%</span>
            </div>
          </div>
          <div className="space-y-2">
            <Label className="text-xs">Take Profit %</Label>
            <div className="flex items-center gap-2">
              <Slider
                value={[takeProfitPercent]}
                onValueChange={([v]) => setTakeProfitPercent(v)}
                min={1}
                max={10}
                step={0.5}
                disabled={session.isActive}
                className="flex-1"
              />
              <span className="text-sm font-medium w-10">{takeProfitPercent}%</span>
            </div>
          </div>
        </div>

        <div className="space-y-2">
          <Label className="text-xs">Max Trades per Day</Label>
          <div className="flex items-center gap-2">
            <Slider
              value={[maxTradesPerDay]}
              onValueChange={([v]) => setMaxTradesPerDay(v)}
              min={1}
              max={50}
              step={1}
              disabled={session.isActive}
              className="flex-1"
            />
            <span className="text-sm font-medium w-10">{maxTradesPerDay}</span>
          </div>
        </div>

        {/* Toggles */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
              <Label htmlFor="ai-signals" className="text-sm">Use AI Signals</Label>
            </div>
            <Switch
              id="ai-signals"
              checked={useAISignals}
              onCheckedChange={setUseAISignals}
              disabled={session.isActive}
            />
          </div>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
              <Label htmlFor="rebalance" className="text-sm">Auto Rebalance</Label>
            </div>
            <Switch
              id="rebalance"
              checked={autoRebalance}
              onCheckedChange={setAutoRebalance}
              disabled={session.isActive}
            />
          </div>
        </div>

        <Separator />

        {/* Session Stats (when active) */}
        {session.isActive && (
          <>
            {/* Active Markets Display */}
            <div className="flex flex-wrap gap-1 items-center">
              <span className="text-xs text-muted-foreground mr-1">Trading on:</span>
              {selectedMarkets.map(marketId => {
                const market = marketOptions.find(m => m.id === marketId);
                return market ? (
                  <Badge key={marketId} variant="secondary" className="text-xs">
                    {market.icon} {market.name.split(' ')[0]}
                  </Badge>
                ) : null;
              })}
            </div>

            <div className="grid grid-cols-3 gap-3 text-center">
            <div className="p-3 bg-muted rounded-lg">
              <p className="text-2xl font-bold">{session.tradesExecuted}</p>
              <p className="text-xs text-muted-foreground">Trades</p>
            </div>
            <div className={cn(
              "p-3 rounded-lg",
              session.totalPnL >= 0
                ? "bg-green-50 dark:bg-green-900/20"
                : "bg-red-50 dark:bg-red-900/20"
            )}>
              <p className={cn(
                "text-2xl font-bold",
                session.totalPnL >= 0 ? "text-green-600" : "text-red-600"
              )}>
                {session.totalPnL >= 0 ? '+' : ''}{formatCurrency(session.totalPnL)}
              </p>
              <p className="text-xs text-muted-foreground">P&L</p>
            </div>
            <div className="p-3 bg-muted rounded-lg">
              <p className="text-2xl font-bold">{session.winRate.toFixed(0)}%</p>
              <p className="text-xs text-muted-foreground">Win Rate</p>
            </div>
          </div>
          </>
        )}

        {/* Control Buttons */}
        <div className="flex gap-2">
          {!session.isActive ? (
            <Button
              onClick={handleStart}
              className="flex-1 bg-green-600 hover:bg-green-700 disabled:bg-green-600/50"
              size="lg"
              disabled={selectedMarkets.length === 0}
            >
              <Play className="mr-2 h-5 w-5" />
              Start Auto Trading
            </Button>
          ) : (
            <>
              <Button
                onClick={handlePauseResume}
                variant="outline"
                className="flex-1"
                size="lg"
              >
                {isPaused ? (
                  <>
                    <Play className="mr-2 h-4 w-4" />
                    Resume
                  </>
                ) : (
                  <>
                    <Pause className="mr-2 h-4 w-4" />
                    Pause
                  </>
                )}
              </Button>
              <Button
                onClick={handleStop}
                variant="destructive"
                className="flex-1"
                size="lg"
              >
                <Square className="mr-2 h-4 w-4" />
                Stop Trading
              </Button>
            </>
          )}
        </div>

        {/* Active Signals Preview */}
        {activeSignals.length > 0 && (
          <div className="space-y-2">
            <p className="text-xs text-muted-foreground flex items-center gap-1">
              <Zap className="h-3 w-3" />
              {activeSignals.length} high-confidence signals available
            </p>
            <div className="flex flex-wrap gap-1">
              {activeSignals.slice(0, 5).map((signal: any, idx: number) => (
                <Badge key={idx} variant="secondary" className="text-xs">
                  {signal.symbol} • {signal.action}
                </Badge>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

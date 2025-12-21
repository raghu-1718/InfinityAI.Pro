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
import { useAppStore, TradingInstrument } from '@/lib/store';
import { useFunds, useSignals, usePlaceOrder, useStartAutoTrading, useStopAutoTrading } from '@/hooks/useApi';
import { useCouponAuth } from '@/contexts/DualAuthContext';
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

// Minimal Signal type used by Auto Trading
interface Signal {
  symbol?: string;
  confidence?: number;
  signal?: 'BUY' | 'SELL' | 'HOLD' | string;
  security_id?: string;
  current_price?: number;
  [key: string]: unknown;
}

export function AutoTradingCard() {
  const funds = useAppStore((s) => s.funds);
  const tradingConfig = useAppStore((s) => s.tradingConfig);
  const storeTradingSession = useAppStore((s) => s.tradingSession);
  const setTradingConfig = useAppStore((s) => s.setTradingConfig);
  const startTradingSession = useAppStore((s) => s.startTradingSession);
  const stopTradingSession = useAppStore((s) => s.stopTradingSession);
  const updateStoreTradingSession = useAppStore((s) => s.updateTradingSession);

  // Get user context for user_id
  const { user, session: authSession } = useCouponAuth();

  const { refetch: refetchFunds } = useFunds();
  const { data: signalsData } = useSignals();
  const placeOrderMutation = usePlaceOrder();
  const startAutoTradeMutation = useStartAutoTrading();
  const stopAutoTradeMutation = useStopAutoTrading();

  // Initialize local state from persisted store config
  const [tradingAmount, setTradingAmount] = useState<number>(tradingConfig.tradingAmount);
  const [riskLevel, setRiskLevel] = useState<string>(tradingConfig.riskLevel);
  const [maxTradesPerDay, setMaxTradesPerDay] = useState<number>(tradingConfig.maxTradesPerDay);
  const [stopLossPercent, setStopLossPercent] = useState<number>(tradingConfig.stopLossPercent);
  const [takeProfitPercent, setTakeProfitPercent] = useState<number>(tradingConfig.takeProfitPercent);
  const [useAISignals, setUseAISignals] = useState<boolean>(tradingConfig.useAISignals);
  const [autoRebalance, setAutoRebalance] = useState<boolean>(tradingConfig.autoRebalance);
  // Extended settings
  const [minCapital, setMinCapital] = useState<number>(tradingConfig.minCapital || 5000);
  const [maxCapital, setMaxCapital] = useState<number>(tradingConfig.maxCapital || 100000);
  const [maxRiskPerTrade, setMaxRiskPerTrade] = useState<number>(tradingConfig.maxRiskPerTrade || 0.02);
  const [minConfidence, setMinConfidence] = useState<number>(tradingConfig.minConfidence || 0.75);
  const [trailingStopLoss, setTrailingStopLoss] = useState<boolean>(tradingConfig.trailingStopLoss || false);
  const [positionSizingMethod, setPositionSizingMethod] = useState<string>(tradingConfig.positionSizingMethod || 'fixed');
  const [settingsLoading, setSettingsLoading] = useState<boolean>(false);
  const [settingsSaved, setSettingsSaved] = useState<boolean>(false);

  // Market/Instrument selection state - sync with store
  const [selectedMarkets, setSelectedMarkets] = useState<TradingInstrument[]>(tradingConfig.selectedInstruments);
  const [showConfig, setShowConfig] = useState(false);

  // Load settings from backend on mount
  useEffect(() => {
    const userId = user?.dhanClientId || authSession?.userId;
    if (userId) {
      loadSettingsFromBackend(userId);
    }
  }, [user?.dhanClientId, authSession?.userId]);

  // Function to load settings from backend
  const loadSettingsFromBackend = async (userId: string) => {
    try {
      setSettingsLoading(true);
      const response = await fetch(
        `https://engine-c-429140669077.us-central1.run.app/api/trading-settings/${userId}`
      );
      if (response.ok) {
        const data = await response.json();
        const settings = data.settings;
        // Update local state with backend settings
        if (!data.is_default) {
          setStopLossPercent(settings.stop_loss_percent || 2);
          setTakeProfitPercent(settings.take_profit_percent || 4);
          setMaxTradesPerDay(settings.max_trades_per_day || 10);
          setTradingAmount(settings.trading_amount || 10000);
          setMinCapital(settings.min_capital || 5000);
          setMaxCapital(settings.max_capital || 100000);
          setRiskLevel(settings.risk_level || 'moderate');
          setMaxRiskPerTrade(settings.max_risk_per_trade || 0.02);
          setMinConfidence(settings.min_confidence || 0.75);
          setSelectedMarkets((settings.selected_instruments || ['equities']) as TradingInstrument[]);
          setUseAISignals(settings.use_ai_signals ?? true);
          setAutoRebalance(settings.auto_rebalance ?? false);
          setTrailingStopLoss(settings.trailing_stop_loss ?? false);
          setPositionSizingMethod(settings.position_sizing_method || 'fixed');
        }
      }
    } catch (error) {
      console.error('Failed to load trading settings:', error);
    } finally {
      setSettingsLoading(false);
    }
  };

  // Function to save settings to backend
  const saveSettingsToBackend = async () => {
    const userId = user?.dhanClientId || authSession?.userId;
    if (!userId) return;

    try {
      setSettingsLoading(true);
      const response = await fetch(
        `https://engine-c-429140669077.us-central1.run.app/api/trading-settings/${userId}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            stop_loss_percent: stopLossPercent,
            take_profit_percent: takeProfitPercent,
            max_trades_per_day: maxTradesPerDay,
            trading_amount: tradingAmount,
            min_capital: minCapital,
            max_capital: maxCapital,
            risk_level: riskLevel,
            max_risk_per_trade: maxRiskPerTrade,
            min_confidence: minConfidence,
            selected_instruments: selectedMarkets,
            use_ai_signals: useAISignals,
            auto_rebalance: autoRebalance,
            trailing_stop_loss: trailingStopLoss,
            position_sizing_method: positionSizingMethod,
          }),
        }
      );
      if (response.ok) {
        setSettingsSaved(true);
        setTimeout(() => setSettingsSaved(false), 3000);
      }
    } catch (error) {
      console.error('Failed to save trading settings:', error);
    } finally {
      setSettingsLoading(false);
    }
  };

  // Sync config changes to store
  useEffect(() => {
    setTradingConfig({
      selectedInstruments: selectedMarkets,
      riskLevel: riskLevel as 'conservative' | 'moderate' | 'aggressive',
      stopLossPercent,
      takeProfitPercent,
      maxTradesPerDay,
      tradingAmount,
      useAISignals,
      autoRebalance,
      minCapital,
      maxCapital,
      maxRiskPerTrade,
      minConfidence,
      trailingStopLoss,
      positionSizingMethod: positionSizingMethod as 'fixed' | 'percentage' | 'kelly',
    });
  }, [selectedMarkets, riskLevel, stopLossPercent, takeProfitPercent, maxTradesPerDay, tradingAmount, useAISignals, autoRebalance, minCapital, maxCapital, maxRiskPerTrade, minConfidence, trailingStopLoss, positionSizingMethod, setTradingConfig]);

  // Available markets/instruments for trading (with typed IDs)
  const marketOptions: { id: TradingInstrument; name: string; icon: string; description: string }[] = [
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
  const toggleMarket = (marketId: TradingInstrument) => {
    setSelectedMarkets(prev =>
      prev.includes(marketId)
        ? prev.filter(m => m !== marketId)
        : [...prev, marketId]
    );
  };

  // Trading session state - use store for sync
  const [session, setSession] = useState<TradingSession>({
    isActive: storeTradingSession?.isActive || false,
    startTime: storeTradingSession?.startTime || null,
    tradesExecuted: storeTradingSession?.tradesExecuted || 0,
    totalPnL: storeTradingSession?.totalPnL || 0,
    winRate: storeTradingSession?.winRate || 0,
  });

  // Sync local session changes to store
  useEffect(() => {
    if (session.isActive) {
      updateStoreTradingSession({
        tradesExecuted: session.tradesExecuted,
        totalPnL: session.totalPnL,
        winRate: session.winRate,
      });
    }
  }, [session.tradesExecuted, session.totalPnL, session.winRate, session.isActive, updateStoreTradingSession]);

  const [isPaused, setIsPaused] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string>('Ready to start trading');

  const availableBalance = funds?.availableBalance || 0;
  const signals = signalsData?.data || [];
  const activeSignals: Signal[] = Array.isArray(signals) ? signals.filter((s: any) => typeof (s as any).confidence === 'number' && (s as any).confidence > 0.7) : [];

  // Risk level configurations
  const riskConfigs = {
    conservative: { maxRisk: 1, minConfidence: 0.85, description: 'Low risk, fewer trades' },
    moderate: { maxRisk: 2, minConfidence: 0.75, description: 'Balanced risk/reward' },
    aggressive: { maxRisk: 4, minConfidence: 0.65, description: 'Higher risk, more trades' },
  };

  // Get selected market names for display
  const getSelectedMarketNames = () => {
    const names = selectedMarkets
      .map(id => marketOptions.find(m => m.id === id)?.name)
      .filter((v): v is string => Boolean(v));
    return names.join(', ');
  };

  // Start auto trading - calls backend with full configuration
  const handleStart = async () => {
    if (tradingAmount > availableBalance) {
      setStatusMessage('⚠️ Insufficient funds! Reduce trading amount.');
      return;
    }

    if (selectedMarkets.length === 0) {
      setStatusMessage('⚠️ Please select at least one trading instrument.');
      return;
    }

    // Get user_id from auth context (use dhanClientId or session userId)
    const userId = user?.dhanClientId || authSession?.userId || 'default';

    // Build complete trading configuration for backend
    const tradingConfigPayload = {
      user_id: userId,
      instruments: selectedMarkets,
      tradingAmount: tradingAmount,
      riskLevel,
      stopLossPercent,
      takeProfitPercent,
      maxTradesPerDay,
      useAISignals,
      min_confidence: riskConfigs[riskLevel as keyof typeof riskConfigs].minConfidence,
    };

    console.log('Starting auto-trading with config:', tradingConfigPayload);

    try {
      // Call backend to start auto-trading with full config
      await startAutoTradeMutation.mutateAsync(tradingConfigPayload);

      // Update local state
      setSession({
        isActive: true,
        startTime: new Date(),
        tradesExecuted: 0,
        totalPnL: 0,
        winRate: 0,
      });

      // Update global store
      startTradingSession(selectedMarkets);
      setIsPaused(false);

      const marketNames = selectedMarkets.length <= 2
        ? getSelectedMarketNames()
        : `${selectedMarkets.length} markets`;
      setStatusMessage(`🚀 Auto trading started on ${marketNames}! Scanning for signals...`);
    } catch (error: unknown) {
      const msg = error instanceof Error ? error.message : String(error);
      setStatusMessage(`❌ Failed to start trading: ${msg || 'Backend error'}`);
    }
  };

  // Stop auto trading
  const handleStop = async () => {
    try {
      // Call backend to stop auto-trading
      await stopAutoTradeMutation.mutateAsync();

      setSession((prev) => ({
        ...prev,
        isActive: false,
      }));
      // Update global store
      stopTradingSession();
      setStatusMessage('⏹️ Auto trading stopped. Session summary saved.');
    } catch (error: unknown) {
      const msg = error instanceof Error ? error.message : String(error);
      setStatusMessage(`❌ Failed to stop trading: ${msg || 'Backend error'}`);
    }
  };

  // Pause/Resume trading
  const handlePauseResume = () => {
    setIsPaused(!isPaused);
    setStatusMessage(isPaused ? '▶️ Trading resumed' : '⏸️ Trading paused');
  };

  // Real trading activity - uses actual API to execute trades based on signals
  // Filters signals based on selected instruments
  useEffect(() => {
    if (!session.isActive || isPaused) return;

    // Helper function to determine if a signal matches selected instruments
    const signalMatchesInstruments = (signal: Signal): boolean => {
      const symbol = (signal.symbol || '').toUpperCase();

      // Check equities (no options suffix)
      if (selectedMarkets.includes('equities') &&
          !symbol.includes('CE') && !symbol.includes('PE') &&
          !symbol.includes('FUT') && !symbol.includes('OPT')) {
        return true;
      }

      // Check NIFTY Options
      if (selectedMarkets.includes('nifty-options') &&
          (symbol.includes('NIFTY') && (symbol.includes('CE') || symbol.includes('PE'))) &&
          !symbol.includes('BANKNIFTY') && !symbol.includes('FINNIFTY')) {
        return true;
      }

      // Check Bank NIFTY Options
      if (selectedMarkets.includes('banknifty-options') &&
          symbol.includes('BANKNIFTY') && (symbol.includes('CE') || symbol.includes('PE'))) {
        return true;
      }

      // Check SENSEX Options
      if (selectedMarkets.includes('sensex-options') &&
          symbol.includes('SENSEX') && (symbol.includes('CE') || symbol.includes('PE'))) {
        return true;
      }

      // Check FIN NIFTY Options
      if (selectedMarkets.includes('finnifty-options') &&
          symbol.includes('FINNIFTY') && (symbol.includes('CE') || symbol.includes('PE'))) {
        return true;
      }

      // Check Crude Options
      if (selectedMarkets.includes('crude-options') &&
          symbol.includes('CRUDE') && (symbol.includes('CE') || symbol.includes('PE'))) {
        return true;
      }

      // Check Gold Options
      if (selectedMarkets.includes('gold-options') &&
          symbol.includes('GOLD') && (symbol.includes('CE') || symbol.includes('PE'))) {
        return true;
      }

      // Check Silver Options
      if (selectedMarkets.includes('silver-options') &&
          symbol.includes('SILVER') && (symbol.includes('CE') || symbol.includes('PE'))) {
        return true;
      }

      return false;
    };

    const interval = setInterval(async () => {
      // Filter signals based on selected instruments
      const filteredSignals = activeSignals.filter(signalMatchesInstruments);

      if (filteredSignals.length > 0 && session.tradesExecuted < maxTradesPerDay) {
        const signal = filteredSignals.find((s: any) =>
          s.confidence >= riskConfigs[riskLevel as keyof typeof riskConfigs].minConfidence &&
          (s.signal === 'BUY' || s.signal === 'SELL')
        );

        if (signal) {
          const instrumentType = selectedMarkets.length === 1
            ? (marketOptions.find(m => m.id === selectedMarkets[0])?.name ?? 'selected instrument')
            : 'selected instruments';
          setStatusMessage(`📊 Found ${signal.signal} signal for ${signal.symbol} on ${instrumentType} (${((signal.confidence ?? 0) * 100).toFixed(0)}% confidence). Executing...`);

          try {
            // Use real startTrade mutation through Engine A orchestration
            await placeOrderMutation.mutateAsync({
              transaction_type: signal.signal === 'SELL' ? 'SELL' : 'BUY',
              validity: 'DAY',
              security_id: signal.security_id || signal.symbol || '',
              quantity: Math.floor(tradingAmount / (signal.current_price || 1000)),
              // Required by OrderRequest - set sensible defaults; adjust if needed
              exchange_segment: 'NSE',
              product_type: 'CNC',
              order_type: 'MARKET',
            });

            setSession((prev) => ({
              ...prev,
              tradesExecuted: prev.tradesExecuted + 1,
            }));
            setStatusMessage(`✅ Trade executed: ${signal.signal} ${signal.symbol}`);
          } catch (error: unknown) {
            const msg = error instanceof Error ? error.message : String(error);
            setStatusMessage(`❌ Trade failed: ${msg || 'Unknown error'}`);
          }
        } else {
          setStatusMessage('🔍 Scanning market for high-confidence signals...');
        }
      } else if (session.tradesExecuted >= maxTradesPerDay) {
        setStatusMessage('📈 Max daily trades reached. Auto-trading paused until next session.');
        setIsPaused(true);
      } else {
        const instrumentNames = selectedMarkets.length <= 2
          ? getSelectedMarketNames()
          : `${selectedMarkets.length} instruments`;
        setStatusMessage(`🔍 Scanning ${instrumentNames} for high-confidence signals...`);
      }
    }, 10000); // Check every 10 seconds

    return () => clearInterval(interval);
  }, [session.isActive, isPaused, activeSignals, maxTradesPerDay, riskLevel, tradingAmount, selectedMarkets, placeOrderMutation, refetchFunds]);

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

        {/* Trading Amount - Always Visible */}
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

        {/* Risk Level - Always Visible */}
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

        {/* Configuration Toggle */}
        <div className="flex justify-end">
           <Button variant="ghost" size="sm" onClick={() => setShowConfig(!showConfig)} className="text-xs">
             <Settings2 className="mr-2 h-3 w-3" />
             {showConfig ? 'Hide Configuration' : 'Configure Strategy'}
           </Button>
        </div>

        {/* Collapsible Configuration */}
        {showConfig && (
          <div className="space-y-6 pt-4 border-t animate-in fade-in slide-in-from-top-2">
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
                        <p className="text-xs text-muted-foreground truncate hidden sm:block">
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

            {/* Advanced Settings Grid */}
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
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Shield className="h-4 w-4 text-muted-foreground" />
                  <Label htmlFor="trailing-sl" className="text-sm">Trailing Stop Loss</Label>
                </div>
                <Switch
                  id="trailing-sl"
                  checked={trailingStopLoss}
                  onCheckedChange={setTrailingStopLoss}
                  disabled={session.isActive}
                />
              </div>
            </div>

            {/* Extended Risk Settings */}
            <div className="space-y-4 p-4 bg-muted/30 rounded-lg">
              <div className="flex items-center gap-2">
                <Settings2 className="h-4 w-4 text-muted-foreground" />
                <Label className="text-sm font-medium">Advanced Risk Settings</Label>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label className="text-xs">Min Capital (₹)</Label>
                  <Input
                    type="number"
                    value={minCapital}
                    onChange={(e) => setMinCapital(Number(e.target.value))}
                    disabled={session.isActive}
                    min={1000}
                    step={1000}
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-xs">Max Capital (₹)</Label>
                  <Input
                    type="number"
                    value={maxCapital}
                    onChange={(e) => setMaxCapital(Number(e.target.value))}
                    disabled={session.isActive}
                    min={1000}
                    step={1000}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label className="text-xs">Max Risk per Trade (%)</Label>
                  <div className="flex items-center gap-2">
                    <Slider
                      value={[maxRiskPerTrade * 100]}
                      onValueChange={([v]) => setMaxRiskPerTrade(v / 100)}
                      min={0.5}
                      max={10}
                      step={0.5}
                      disabled={session.isActive}
                      className="flex-1"
                    />
                    <span className="text-sm font-medium w-12">{(maxRiskPerTrade * 100).toFixed(1)}%</span>
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <Label className="text-xs">Min AI Confidence (%)</Label>
                <div className="flex items-center gap-2">
                  <Slider
                    value={[minConfidence * 100]}
                    onValueChange={([v]) => setMinConfidence(v / 100)}
                    min={50}
                    max={99}
                    step={1}
                    disabled={session.isActive}
                    className="flex-1"
                  />
                  <span className="text-sm font-medium w-12">{(minConfidence * 100).toFixed(0)}%</span>
                </div>
              </div>

              <div className="space-y-2">
                <Label className="text-xs">Position Sizing Method</Label>
                <Select
                  value={positionSizingMethod}
                  onValueChange={setPositionSizingMethod}
                  disabled={session.isActive}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="fixed">Fixed Amount</SelectItem>
                    <SelectItem value="percentage">Percentage of Capital</SelectItem>
                    <SelectItem value="kelly">Kelly Criterion</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Save Settings Button - Inside collapsible */}
            <div className="flex items-center gap-2">
              <Button
                onClick={saveSettingsToBackend}
                variant="outline"
                className="flex-1"
                disabled={session.isActive || settingsLoading}
              >
                {settingsLoading ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <CheckCircle2 className="mr-2 h-4 w-4" />
                )}
                {settingsSaved ? 'Settings Saved!' : 'Save Settings to Cloud'}
              </Button>
              {settingsSaved && (
                <Badge variant="default" className="bg-green-500">
                  ✓ Saved
                </Badge>
              )}
            </div>
          </div>
        )}

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
              {activeSignals.slice(0, 5).map((signal: Signal, idx: number) => (
                <Badge key={idx} variant="secondary" className="text-xs">
                  {signal.symbol} • {signal.signal ?? 'HOLD'}
                </Badge>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

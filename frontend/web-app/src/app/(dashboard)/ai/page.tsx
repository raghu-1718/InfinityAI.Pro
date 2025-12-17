'use client';

import { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Separator } from '@/components/ui/separator';
import { Skeleton } from '@/components/ui/skeleton';
import { Switch } from '@/components/ui/switch';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { GeminiChat } from '@/components/dashboard/gemini-chat';
import { engineB, engineC } from '@/lib/api';
import { getUserId, getUserDisplayInfo } from '@/lib/user';
import {
  Sparkles,
  TrendingUp,
  TrendingDown,
  Target,
  Shield,
  Brain,
  BarChart3,
  Loader2,
  ArrowUpRight,
  ArrowDownRight,
  Minus,
  AlertTriangle,
  CheckCircle2,
  Zap,
  Bot,
  MessageSquare,
  Send,
  Play,
  Pause,
  Activity,
  UserCircle,
} from 'lucide-react';
import { cn } from '@/lib/utils';

// Popular stocks for quick selection
const popularStocks = [
  { symbol: 'RELIANCE', name: 'Reliance Industries' },
  { symbol: 'TCS', name: 'Tata Consultancy' },
  { symbol: 'HDFCBANK', name: 'HDFC Bank' },
  { symbol: 'INFY', name: 'Infosys' },
  { symbol: 'ICICIBANK', name: 'ICICI Bank' },
  { symbol: 'SBIN', name: 'State Bank of India' },
  { symbol: 'BHARTIARTL', name: 'Bharti Airtel' },
  { symbol: 'ITC', name: 'ITC Limited' },
  { symbol: 'KOTAKBANK', name: 'Kotak Mahindra Bank' },
  { symbol: 'LT', name: 'Larsen & Toubro' },
];

// --- Types for AI results (narrowed to avoid `any`) ---
type Signal = {
  action?: 'BUY' | 'SELL' | 'HOLD';
  confidence?: number;
  entry_price?: number;
  stop_loss?: number;
  target?: number;
  timeframe?: string;
  risk_level?: string;
  target_1?: number;
  target_2?: number;
  target_3?: number;
  risk_reward_ratio?: number;
};

type Analysis = {
  trend?: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
  trend_strength?: number;
  sentiment_score?: number;
  key_indicators?: { rsi?: number };
  support_levels?: number[];
  resistance_levels?: number[];
  volume_analysis?: string;
  sector_outlook?: string;
  global_cues?: string;
};

type StrategyLeg = {
  type?: string;
  option_type?: string;
  strike_price?: number | string;
  expiry_date?: string;
  entry_price?: number;
  quantity?: number;
  total_premium?: number;
};

type AIResult = {
  symbol?: string;
  model?: string;
  recommendation?: { action?: string; confidence?: number; reasoning?: string };
  signal?: Signal;
  analysis?: Analysis;
  index?: string | number;
  spot_price?: number | string;
  outlook?: 'BULLISH' | 'BEARISH' | 'NEUTRAL' | string;
  strategy?: {
    strategy_name?: string;
    strategy_description?: string;
    legs?: StrategyLeg[];
    max_profit?: number;
    max_loss?: number;
    breakeven_point?: number;
  };
  reasoning?: string;
  key_factors?: string[];
  response?: string;
};

type AgentStatus = { status?: string; model?: string; region?: string };

export default function GeminiAIPage() {
  const [activeTab, setActiveTab] = useState('signal');
  const [symbol, setSymbol] = useState('RELIANCE');
  const [currentPrice, setCurrentPrice] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<AIResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Options strategy state
  const [optionsIndex, setOptionsIndex] = useState('NIFTY');
  const [spotPrice, setSpotPrice] = useState('24650');
  const [outlook, setOutlook] = useState<'BULLISH' | 'BEARISH' | 'NEUTRAL'>('NEUTRAL');
  const [capital, setCapital] = useState('200000');
  const [riskAppetite, setRiskAppetite] = useState<'LOW' | 'MODERATE' | 'HIGH'>('MODERATE');

  // AI Agent state
  const [agentStatus, setAgentStatus] = useState<AgentStatus | null>(null);
  const [agentMessages, setAgentMessages] = useState<Array<{role: string; content: string; timestamp: Date}>>([]);
  const [agentInput, setAgentInput] = useState('');
  const [isAgentLoading, setIsAgentLoading] = useState(false);
  const [autoTradingEnabled, setAutoTradingEnabled] = useState(false);
  const [agentConfig, setAgentConfig] = useState({
    min_confidence: 0.7,
    max_risk_per_trade: 0.02,
    max_daily_trades: 10,
    trading_amount: 1000,
  });
  const [watchlist, setWatchlist] = useState<string[]>(['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK']);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Dynamic user identification
  const [currentUserId, setCurrentUserId] = useState<string>('');
  const [userInfo, setUserInfo] = useState<{ userId: string; isDhanConnected: boolean; displayName: string } | null>(null);

  // Initialize user ID on client side
  useEffect(() => {
    const id = getUserId();
    const info = getUserDisplayInfo();
    setCurrentUserId(id);
    setUserInfo(info);
  }, []);

  // Fetch agent status on mount
  useEffect(() => {
    const fetchAgentStatus = async () => {
      try {
        const status = await engineC.getAgentStatus();
        setAgentStatus(status);
      } catch (err) {
        console.error('Failed to fetch agent status:', err);
      }
    };
    fetchAgentStatus();
  }, []);

  // Scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [agentMessages]);

  // Handle sending message to AI Agent
  const handleSendToAgent = async () => {
    if (!agentInput.trim()) return;

    const userMessage = agentInput.trim();
    setAgentInput('');
    setAgentMessages(prev => [...prev, { role: 'user', content: userMessage, timestamp: new Date() }]);
    setIsAgentLoading(true);

    try {
      const response = await engineC.chatWithAgent({
        user_id: currentUserId,
        message: userMessage,
        context: { market: 'NSE', session_type: 'trading_consultation' }
      });

      if (response.success) {
        setAgentMessages(prev => [...prev, {
          role: 'assistant',
          content: response.response || response.message || 'Response received',
          timestamp: new Date()
        }]);
      } else {
        setAgentMessages(prev => [...prev, {
          role: 'assistant',
          content: `Error: ${response.error || 'Failed to get response'}`,
          timestamp: new Date()
        }]);
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      setAgentMessages(prev => [...prev, {
        role: 'assistant',
        content: `Error: ${message || 'Connection failed'}`,
        timestamp: new Date()
      }]);
    } finally {
      setIsAgentLoading(false);
    }
  };

  // Handle AI Agent trade analysis
  const handleAgentAnalyze = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await engineC.analyzeTradeOpportunity({
        user_id: currentUserId,
        symbol,
        current_price: parseFloat(currentPrice) || undefined,
      });
      setResult(response);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      setError(message || 'Failed to get AI analysis');
    } finally {
      setIsLoading(false);
    }
  };

  // Handle real-time signal from AI Agent
  const handleGetAgentSignal = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await engineC.getRealtimeSignal(currentUserId, symbol, 'intraday');
      setResult(response);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      setError(message || 'Failed to get AI signal');
    } finally {
      setIsLoading(false);
    }
  };

  // Toggle automated trading
  const handleToggleAutoTrading = async () => {
    try {
      if (!autoTradingEnabled) {
        // Start auto trading
        await engineC.runAutomatedTrading({
          user_id: currentUserId,
          watchlist,
          config: agentConfig
        });
        setAutoTradingEnabled(true);
      } else {
        // Stop - just disable locally (Cloud Scheduler handles actual cycles)
        setAutoTradingEnabled(false);
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      setError(message || 'Failed to toggle auto trading');
    }
  };

  const handleGetSignal = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await engineB.getFinanceAISignal({
        symbol,
        current_price: parseFloat(currentPrice) || 0,
        model_type: 'stock_analyst',
      });
      setResult(response);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      setError(message || 'Failed to get signal');
    } finally {
      setIsLoading(false);
    }
  };

  const handleGetMarketAnalysis = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await engineB.getFinanceAIMarketAnalysis({
        symbol,
        current_price: parseFloat(currentPrice) || 0,
      });
      setResult(response);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      setError(message || 'Failed to get analysis');
    } finally {
      setIsLoading(false);
    }
  };

  const handleGetOptionsStrategy = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await engineB.getFinanceAIOptionsStrategy({
        index: optionsIndex,
        spot_price: parseFloat(spotPrice) || 24650,
        outlook,
        capital: parseFloat(capital) || 200000,
        risk_appetite: riskAppetite,
      });
      setResult(response);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      setError(message || 'Failed to get options strategy');
    } finally {
      setIsLoading(false);
    }
  };

  const renderSignalResult = () => {
    if (!result?.signal) return null;
    const s = result.signal;
    const actionColor = s.action === 'BUY' ? 'text-green-500' : s.action === 'SELL' ? 'text-red-500' : 'text-yellow-500';
    const actionBg = s.action === 'BUY' ? 'bg-green-100 dark:bg-green-900/30' : s.action === 'SELL' ? 'bg-red-100 dark:bg-red-900/30' : 'bg-yellow-100 dark:bg-yellow-900/30';

    return (
      <div className="space-y-4">
        {/* Signal Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={cn('p-3 rounded-lg', actionBg)}>
              {s.action === 'BUY' ? (
                <ArrowUpRight className={cn('h-6 w-6', actionColor)} />
              ) : s.action === 'SELL' ? (
                <ArrowDownRight className={cn('h-6 w-6', actionColor)} />
              ) : (
                <Minus className={cn('h-6 w-6', actionColor)} />
              )}
            </div>
            <div>
              <h3 className="text-2xl font-bold">{result.symbol}</h3>
              <p className="text-sm text-muted-foreground">Trading Signal</p>
            </div>
          </div>
          <Badge className={cn('text-lg px-4 py-2', actionBg, actionColor)}>
            {s.action}
          </Badge>
        </div>

        {/* Confidence */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-4">
              <p className="text-xs text-muted-foreground">Confidence</p>
              <p className="text-2xl font-bold">{((s.confidence ?? 0) * 100).toFixed(0)}%</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <p className="text-xs text-muted-foreground">Entry Price</p>
              <p className="text-2xl font-bold">₹{s.entry_price?.toFixed(2) || 'Market'}</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <p className="text-xs text-muted-foreground">Stop Loss</p>
              <p className="text-2xl font-bold text-red-500">₹{s.stop_loss?.toFixed(2) || 'N/A'}</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <p className="text-xs text-muted-foreground">Risk/Reward</p>
              <p className="text-2xl font-bold">{s.risk_reward_ratio?.toFixed(2) || 'N/A'}</p>
            </CardContent>
          </Card>
        </div>

        {/* Targets */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Target Prices</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex gap-4">
              <div className="flex-1 p-3 bg-green-50 dark:bg-green-900/20 rounded-lg text-center">
                <p className="text-xs text-muted-foreground">Target 1</p>
                <p className="text-lg font-bold text-green-600">₹{s.target_1?.toFixed(2) || 'N/A'}</p>
              </div>
              <div className="flex-1 p-3 bg-green-100 dark:bg-green-900/30 rounded-lg text-center">
                <p className="text-xs text-muted-foreground">Target 2</p>
                <p className="text-lg font-bold text-green-600">₹{s.target_2?.toFixed(2) || 'N/A'}</p>
              </div>
              <div className="flex-1 p-3 bg-green-200 dark:bg-green-900/40 rounded-lg text-center">
                <p className="text-xs text-muted-foreground">Target 3</p>
                <p className="text-lg font-bold text-green-600">₹{s.target_3?.toFixed(2) || 'N/A'}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Reasoning */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2">
              <Brain className="h-4 w-4" />
              AI Reasoning
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">{result.reasoning}</p>
            {result.key_factors && result.key_factors.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-2">
                {result.key_factors.map((factor: string, i: number) => (
                  <Badge key={i} variant="outline">{factor}</Badge>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Meta */}
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>Model: {result.model}</span>
          <span>Timeframe: {s.timeframe}</span>
          <span>Risk Level: {s.risk_level}</span>
        </div>
      </div>
    );
  };

  const renderAnalysisResult = () => {
    if (!result?.analysis) return null;
    const a = result.analysis;
    const trendColor = a.trend === 'BULLISH' ? 'text-green-500' : a.trend === 'BEARISH' ? 'text-red-500' : 'text-yellow-500';

    return (
      <div className="space-y-4">
        {/* Analysis Header */}
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-2xl font-bold">{result.symbol}</h3>
            <p className="text-sm text-muted-foreground">Market Analysis</p>
          </div>
          <Badge className={cn('text-lg px-4 py-2', trendColor)}>
            {a.trend === 'BULLISH' && <TrendingUp className="h-4 w-4 mr-1" />}
            {a.trend === 'BEARISH' && <TrendingDown className="h-4 w-4 mr-1" />}
            {a.trend}
          </Badge>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <Card>
            <CardContent className="pt-4">
              <p className="text-xs text-muted-foreground">Trend Strength</p>
              <p className="text-2xl font-bold">{(((a.trend_strength ?? 0)) * 100).toFixed(0)}%</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <p className="text-xs text-muted-foreground">Sentiment Score</p>
              <p className="text-2xl font-bold">{(((a.sentiment_score ?? 0)) * 100).toFixed(0)}%</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <p className="text-xs text-muted-foreground">Key Indicator</p>
              <p className="text-2xl font-bold">RSI {a.key_indicators?.rsi?.toFixed(0) || 'N/A'}</p>
            </CardContent>
          </Card>
        </div>

        {/* Support & Resistance */}
        <div className="grid grid-cols-2 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-green-600">Support Levels</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col gap-2">
                {a.support_levels?.map((level: number, i: number) => (
                  <div key={i} className="flex justify-between items-center">
                    <span className="text-sm">S{i + 1}</span>
                    <span className="font-mono font-bold">₹{level.toFixed(2)}</span>
                  </div>
                )) || <p className="text-muted-foreground">N/A</p>}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-red-600">Resistance Levels</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col gap-2">
                {a.resistance_levels?.map((level: number, i: number) => (
                  <div key={i} className="flex justify-between items-center">
                    <span className="text-sm">R{i + 1}</span>
                    <span className="font-mono font-bold">₹{level.toFixed(2)}</span>
                  </div>
                )) || <p className="text-muted-foreground">N/A</p>}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Volume & Sector */}
        <Card>
          <CardContent className="pt-4 space-y-3">
            {a.volume_analysis && (
              <div>
                <p className="text-sm font-medium">Volume Analysis</p>
                <p className="text-sm text-muted-foreground">{a.volume_analysis}</p>
              </div>
            )}
            {a.sector_outlook && (
              <div>
                <p className="text-sm font-medium">Sector Outlook</p>
                <p className="text-sm text-muted-foreground">{a.sector_outlook}</p>
              </div>
            )}
            {a.global_cues && (
              <div>
                <p className="text-sm font-medium">Global Cues</p>
                <p className="text-sm text-muted-foreground">{a.global_cues}</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recommendation */}
        <Card className="bg-primary/5 border-primary/20">
          <CardContent className="pt-4">
            <div className="flex items-start gap-3">
              <Zap className="h-5 w-5 text-primary mt-0.5" />
              <div>
                <p className="font-medium">Recommendation</p>
                <p className="text-sm text-muted-foreground">{result.recommendation}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  };

  const renderOptionsResult = () => {
    if (!result?.strategy) return null;
    const s = result.strategy;

    return (
      <div className="space-y-4">
        {/* Strategy Header */}
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-2xl font-bold">{s.strategy_name}</h3>
            <p className="text-sm text-muted-foreground">{result.index} @ ₹{result.spot_price}</p>
          </div>
          <Badge>{result.outlook}</Badge>
        </div>

        {/* Strategy Description */}
        {s.strategy_description && (
          <Card>
            <CardContent className="pt-4">
              <p className="text-sm text-muted-foreground">{s.strategy_description}</p>
            </CardContent>
          </Card>
        )}

        {/* Legs */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Strategy Legs</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {s.legs?.map((leg: StrategyLeg, i: number) => (
                <div key={i} className="flex items-center justify-between p-3 bg-muted rounded-lg">
                  <div className="flex items-center gap-3">
                    <Badge variant={leg.type === 'BUY' ? 'default' : 'destructive'}>
                      {leg.type}
                    </Badge>
                    <div>
                      <p className="font-medium">{leg.option_type} {leg.strike_price}</p>
                      <p className="text-xs text-muted-foreground">{leg.expiry_date}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-mono font-bold">₹{leg.entry_price} × {leg.quantity}</p>
                    <p className="text-xs text-muted-foreground">Total: ₹{leg.total_premium}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Risk/Reward */}
        <div className="grid grid-cols-3 gap-4">
          <Card>
            <CardContent className="pt-4 text-center">
              <p className="text-xs text-muted-foreground">Max Profit</p>
              <p className="text-xl font-bold text-green-600">₹{s.max_profit?.toLocaleString()}</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4 text-center">
              <p className="text-xs text-muted-foreground">Max Loss</p>
              <p className="text-xl font-bold text-red-600">₹{s.max_loss?.toLocaleString()}</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4 text-center">
              <p className="text-xs text-muted-foreground">Breakeven</p>
              <p className="text-xl font-bold">₹{s.breakeven_point?.toLocaleString()}</p>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  };

  return (
    <div className="p-6 space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
          <Sparkles className="h-6 w-6 text-purple-500" />
          Gemini AI Analysis
        </h1>
        <p className="text-muted-foreground">
          AI-powered trading analysis, signals, and strategies using Google Gemini
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Left Column - Analysis Tools */}
        <div className="space-y-6">
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid grid-cols-4 w-full">
              <TabsTrigger value="agent" className="flex items-center gap-1">
                <Bot className="h-4 w-4" />
                AI Agent
              </TabsTrigger>
              <TabsTrigger value="signal" className="flex items-center gap-1">
                <Target className="h-4 w-4" />
                Signal
              </TabsTrigger>
              <TabsTrigger value="analysis" className="flex items-center gap-1">
                <BarChart3 className="h-4 w-4" />
                Analysis
              </TabsTrigger>
              <TabsTrigger value="options" className="flex items-center gap-1">
                <Shield className="h-4 w-4" />
                Options
              </TabsTrigger>
            </TabsList>

            {/* AI Agent Tab - Vertex AI Financial Advisor */}
            <TabsContent value="agent" className="space-y-4">
              {/* User Identity Card */}
              <Card className={cn(
                "border",
                userInfo?.isDhanConnected ? "border-green-500/30 bg-green-50/30 dark:bg-green-950/10" : "border-yellow-500/30 bg-yellow-50/30 dark:bg-yellow-950/10"
              )}>
                <CardContent className="py-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <UserCircle className="h-5 w-5 text-muted-foreground" />
                      <span className="text-sm">
                        {userInfo?.isDhanConnected ? (
                          <>Trading as <span className="font-medium text-green-600">Dhan User {currentUserId}</span></>
                        ) : (
                          <span className="text-yellow-600">Connect your Dhan account in Settings to enable trading</span>
                        )}
                      </span>
                    </div>
                    {userInfo?.isDhanConnected && (
                      <Badge variant="outline" className="text-green-600 border-green-500">
                        <CheckCircle2 className="h-3 w-3 mr-1" />
                        Connected
                      </Badge>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* Agent Status Card */}
              <Card className={cn(
                "border-2",
                agentStatus?.status === 'operational' ? "border-green-500/50 bg-green-50/50 dark:bg-green-950/20" : "border-yellow-500/50"
              )}>
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg flex items-center gap-2">
                      <Bot className="h-5 w-5 text-purple-500" />
                      Vertex AI Financial Advisor
                    </CardTitle>
                    <Badge variant={agentStatus?.status === 'operational' ? 'default' : 'secondary'}>
                      {agentStatus?.status || 'Checking...'}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-muted-foreground">Model:</span>{' '}
                      <span className="font-medium">{agentStatus?.model || 'gemini-2.5-pro'}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Region:</span>{' '}
                      <span className="font-medium">{agentStatus?.region || 'us-central1'}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Auto Trading Controls */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Activity className="h-5 w-5" />
                    Automated AI Trading
                  </CardTitle>
                  <CardDescription>Let AI analyze and execute trades during market hours</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between p-4 bg-muted rounded-lg">
                    <div className="flex items-center gap-3">
                      {autoTradingEnabled ? (
                        <Play className="h-5 w-5 text-green-500" />
                      ) : (
                        <Pause className="h-5 w-5 text-muted-foreground" />
                      )}
                      <div>
                        <p className="font-medium">Auto Trading</p>
                        <p className="text-sm text-muted-foreground">
                          {autoTradingEnabled ? 'Running - AI is monitoring markets' : 'Paused'}
                        </p>
                      </div>
                    </div>
                    <Switch
                      checked={autoTradingEnabled}
                      disabled={!userInfo?.isDhanConnected}
                      onCheckedChange={handleToggleAutoTrading}
                    />
                  </div>

                  <Separator />

                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Min Confidence</Label>
                      <Input
                        type="number"
                        min="0"
                        max="1"
                        step="0.1"
                        value={agentConfig.min_confidence}
                        onChange={(e) => setAgentConfig(prev => ({...prev, min_confidence: parseFloat(e.target.value)}))}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Max Risk/Trade</Label>
                      <Input
                        type="number"
                        min="0"
                        max="0.1"
                        step="0.01"
                        value={agentConfig.max_risk_per_trade}
                        onChange={(e) => setAgentConfig(prev => ({...prev, max_risk_per_trade: parseFloat(e.target.value)}))}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Max Daily Trades</Label>
                      <Input
                        type="number"
                        min="1"
                        max="50"
                        value={agentConfig.max_daily_trades}
                        onChange={(e) => setAgentConfig(prev => ({...prev, max_daily_trades: parseInt(e.target.value)}))}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Amount/Trade (₹)</Label>
                      <Input
                        type="number"
                        min="100"
                        value={agentConfig.trading_amount}
                        onChange={(e) => setAgentConfig(prev => ({...prev, trading_amount: parseInt(e.target.value)}))}
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label>Watchlist Symbols</Label>
                    <div className="flex flex-wrap gap-2">
                      {watchlist.map((sym) => (
                        <Badge key={sym} variant="outline" className="cursor-pointer hover:bg-destructive/10" onClick={() => setWatchlist(prev => prev.filter(s => s !== sym))}>
                          {sym} ×
                        </Badge>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Quick AI Analysis */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Quick AI Analysis</CardTitle>
                  <CardDescription>Get instant analysis from Financial Advisor</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label>Symbol</Label>
                    <Select value={symbol} onValueChange={setSymbol}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {popularStocks.map((stock) => (
                          <SelectItem key={stock.symbol} value={stock.symbol}>
                            {stock.symbol}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <Button onClick={handleAgentAnalyze} disabled={isLoading} variant="outline">
                      {isLoading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Brain className="h-4 w-4 mr-2" />}
                      Analyze
                    </Button>
                    <Button onClick={handleGetAgentSignal} disabled={isLoading}>
                      {isLoading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Zap className="h-4 w-4 mr-2" />}
                      Get Signal
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Signal Tab */}
            <TabsContent value="signal" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Get Trading Signal</CardTitle>
                  <CardDescription>AI-powered buy/sell/hold recommendation</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label>Stock Symbol</Label>
                    <Select value={symbol} onValueChange={setSymbol}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select stock" />
                      </SelectTrigger>
                      <SelectContent>
                        {popularStocks.map((stock) => (
                          <SelectItem key={stock.symbol} value={stock.symbol}>
                            {stock.symbol} - {stock.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Current Price (optional)</Label>
                    <Input
                      type="number"
                      placeholder="Leave empty to auto-fetch"
                      value={currentPrice}
                      onChange={(e) => setCurrentPrice(e.target.value)}
                    />
                  </div>
                  <Button className="w-full" onClick={handleGetSignal} disabled={isLoading}>
                    {isLoading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Target className="h-4 w-4 mr-2" />}
                    Get Signal
                  </Button>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Analysis Tab */}
            <TabsContent value="analysis" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Market Analysis</CardTitle>
                  <CardDescription>Comprehensive trend and technical analysis</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label>Stock/Index Symbol</Label>
                    <Select value={symbol} onValueChange={setSymbol}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select stock" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="NIFTY">NIFTY 50</SelectItem>
                        <SelectItem value="BANKNIFTY">Bank NIFTY</SelectItem>
                        <SelectItem value="SENSEX">SENSEX</SelectItem>
                        {popularStocks.map((stock) => (
                          <SelectItem key={stock.symbol} value={stock.symbol}>
                            {stock.symbol}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Current Price (optional)</Label>
                    <Input
                      type="number"
                      placeholder="Leave empty to auto-fetch"
                      value={currentPrice}
                      onChange={(e) => setCurrentPrice(e.target.value)}
                    />
                  </div>
                  <Button className="w-full" onClick={handleGetMarketAnalysis} disabled={isLoading}>
                    {isLoading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <BarChart3 className="h-4 w-4 mr-2" />}
                    Analyze
                  </Button>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Options Tab */}
            <TabsContent value="options" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Options Strategy</CardTitle>
                  <CardDescription>AI-recommended options strategy</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Index</Label>
                      <Select value={optionsIndex} onValueChange={setOptionsIndex}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="NIFTY">NIFTY 50</SelectItem>
                          <SelectItem value="BANKNIFTY">Bank NIFTY</SelectItem>
                          <SelectItem value="FINNIFTY">FIN NIFTY</SelectItem>
                          <SelectItem value="SENSEX">SENSEX</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label>Spot Price</Label>
                      <Input
                        type="number"
                        value={spotPrice}
                        onChange={(e) => setSpotPrice(e.target.value)}
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Market Outlook</Label>
                      <Select value={outlook} onValueChange={(v) => setOutlook(v as 'BULLISH' | 'BEARISH' | 'NEUTRAL')}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="BULLISH">Bullish 📈</SelectItem>
                          <SelectItem value="BEARISH">Bearish 📉</SelectItem>
                          <SelectItem value="NEUTRAL">Neutral ➡️</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label>Risk Appetite</Label>
                      <Select value={riskAppetite} onValueChange={(v) => setRiskAppetite(v as 'LOW' | 'MODERATE' | 'HIGH')}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="LOW">Conservative</SelectItem>
                          <SelectItem value="MODERATE">Moderate</SelectItem>
                          <SelectItem value="HIGH">Aggressive</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label>Capital (₹)</Label>
                    <Input
                      type="number"
                      value={capital}
                      onChange={(e) => setCapital(e.target.value)}
                    />
                  </div>
                  <Button className="w-full" onClick={handleGetOptionsStrategy} disabled={isLoading}>
                    {isLoading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Shield className="h-4 w-4 mr-2" />}
                    Get Strategy
                  </Button>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>

          {/* Results */}
          {error && (
            <Card className="border-destructive">
              <CardContent className="pt-4">
                <div className="flex items-center gap-2 text-destructive">
                  <AlertTriangle className="h-4 w-4" />
                  <span>{error}</span>
                </div>
              </CardContent>
            </Card>
          )}

          {isLoading && (
            <Card>
              <CardContent className="pt-4 space-y-4">
                <Skeleton className="h-8 w-1/2" />
                <Skeleton className="h-20 w-full" />
                <Skeleton className="h-20 w-full" />
              </CardContent>
            </Card>
          )}

          {!isLoading && result && (
            <Card>
              <CardContent className="pt-4">
                {activeTab === 'agent' && result && (
                  <div className="space-y-4">
                    <div className="flex items-center gap-2">
                      <Bot className="h-5 w-5 text-purple-500" />
                      <h3 className="font-semibold">AI Agent Analysis Result</h3>
                    </div>
                    {result.recommendation && (
                      <Card className="bg-primary/5">
                        <CardContent className="pt-4">
                          <div className="flex items-center gap-2 mb-2">
                            <Badge className={cn(
                              result.recommendation.action === 'BUY' ? 'bg-green-500' :
                              result.recommendation.action === 'SELL' ? 'bg-red-500' : 'bg-yellow-500'
                            )}>
                              {result.recommendation.action}
                            </Badge>
                            <span className="text-sm text-muted-foreground">
                              Confidence: {((result.recommendation.confidence ?? 0) * 100).toFixed(0)}%
                            </span>
                          </div>
                          <p className="text-sm">{result.recommendation.reasoning || result.response}</p>
                        </CardContent>
                      </Card>
                    )}
                    {result.signal && (
                      <div className="grid grid-cols-3 gap-4">
                        <Card>
                          <CardContent className="pt-4 text-center">
                            <p className="text-xs text-muted-foreground">Entry</p>
                            <p className="text-lg font-bold">₹{result.signal.entry_price?.toFixed(2) || 'Market'}</p>
                          </CardContent>
                        </Card>
                        <Card>
                          <CardContent className="pt-4 text-center">
                            <p className="text-xs text-muted-foreground">Stop Loss</p>
                            <p className="text-lg font-bold text-red-500">₹{result.signal.stop_loss?.toFixed(2) || 'N/A'}</p>
                          </CardContent>
                        </Card>
                        <Card>
                          <CardContent className="pt-4 text-center">
                            <p className="text-xs text-muted-foreground">Target</p>
                            <p className="text-lg font-bold text-green-500">₹{result.signal.target?.toFixed(2) || 'N/A'}</p>
                          </CardContent>
                        </Card>
                      </div>
                    )}
                  </div>
                )}
                {activeTab === 'signal' && renderSignalResult()}
                {activeTab === 'analysis' && renderAnalysisResult()}
                {activeTab === 'options' && renderOptionsResult()}
              </CardContent>
            </Card>
          )}
        </div>

        {/* Right Column - Chat */}
        <div>
          {activeTab === 'agent' ? (
            /* AI Agent Chat Interface */
            <Card className="h-[calc(100vh-200px)] sticky top-6 flex flex-col">
              <CardHeader className="pb-2">
                <CardTitle className="text-lg flex items-center gap-2">
                  <MessageSquare className="h-5 w-5 text-purple-500" />
                  Chat with Financial Advisor
                </CardTitle>
              </CardHeader>
              <CardContent className="flex-1 flex flex-col overflow-hidden">
                <ScrollArea className="flex-1 pr-4">
                  <div className="space-y-4">
                    {agentMessages.length === 0 && (
                      <div className="text-center text-muted-foreground py-8">
                        <Bot className="h-12 w-12 mx-auto mb-4 opacity-50" />
                        <p>Start a conversation with your AI Financial Advisor</p>
                        <p className="text-sm mt-2">Ask about market analysis, trade recommendations, or portfolio advice</p>
                      </div>
                    )}
                    {agentMessages.map((msg, i) => (
                      <div key={i} className={cn(
                        "flex",
                        msg.role === 'user' ? 'justify-end' : 'justify-start'
                      )}>
                        <div className={cn(
                          "max-w-[80%] rounded-lg p-3",
                          msg.role === 'user'
                            ? 'bg-primary text-primary-foreground'
                            : 'bg-muted'
                        )}>
                          <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                          <p className="text-xs opacity-60 mt-1">
                            {msg.timestamp.toLocaleTimeString()}
                          </p>
                        </div>
                      </div>
                    ))}
                    {isAgentLoading && (
                      <div className="flex justify-start">
                        <div className="bg-muted rounded-lg p-3">
                          <Loader2 className="h-4 w-4 animate-spin" />
                        </div>
                      </div>
                    )}
                    <div ref={messagesEndRef} />
                  </div>
                </ScrollArea>
                <div className="flex gap-2 mt-4">
                  <Input
                    placeholder="Ask about trading, markets, or your portfolio..."
                    value={agentInput}
                    onChange={(e) => setAgentInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSendToAgent()}
                    disabled={isAgentLoading}
                  />
                  <Button onClick={handleSendToAgent} disabled={isAgentLoading || !agentInput.trim()}>
                    <Send className="h-4 w-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ) : (
            <GeminiChat expanded className="h-[calc(100vh-200px)] sticky top-6" />
          )}
        </div>
      </div>
    </div>
  );
}

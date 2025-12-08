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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { GeminiChat } from '@/components/dashboard/gemini-chat';
import { engineB } from '@/lib/api';
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
  RefreshCw,
  Zap,
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

export default function GeminiAIPage() {
  const [activeTab, setActiveTab] = useState('signal');
  const [symbol, setSymbol] = useState('RELIANCE');
  const [currentPrice, setCurrentPrice] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  // Options strategy state
  const [optionsIndex, setOptionsIndex] = useState('NIFTY');
  const [spotPrice, setSpotPrice] = useState('24650');
  const [outlook, setOutlook] = useState<'BULLISH' | 'BEARISH' | 'NEUTRAL'>('NEUTRAL');
  const [capital, setCapital] = useState('200000');
  const [riskAppetite, setRiskAppetite] = useState<'LOW' | 'MODERATE' | 'HIGH'>('MODERATE');

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
    } catch (err: any) {
      setError(err.message || 'Failed to get signal');
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
    } catch (err: any) {
      setError(err.message || 'Failed to get analysis');
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
    } catch (err: any) {
      setError(err.message || 'Failed to get options strategy');
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
              <p className="text-2xl font-bold">{(s.confidence * 100).toFixed(0)}%</p>
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
              <p className="text-2xl font-bold">{((a.trend_strength || 0) * 100).toFixed(0)}%</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <p className="text-xs text-muted-foreground">Sentiment Score</p>
              <p className="text-2xl font-bold">{((a.sentiment_score || 0) * 100).toFixed(0)}%</p>
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
              {s.legs?.map((leg: any, i: number) => (
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
            <TabsList className="grid grid-cols-3 w-full">
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
                      <Select value={outlook} onValueChange={(v) => setOutlook(v as any)}>
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
                      <Select value={riskAppetite} onValueChange={(v) => setRiskAppetite(v as any)}>
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
                {activeTab === 'signal' && renderSignalResult()}
                {activeTab === 'analysis' && renderAnalysisResult()}
                {activeTab === 'options' && renderOptionsResult()}
              </CardContent>
            </Card>
          )}
        </div>

        {/* Right Column - Chat */}
        <div>
          <GeminiChat expanded className="h-[calc(100vh-200px)] sticky top-6" />
        </div>
      </div>
    </div>
  );
}

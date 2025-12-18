'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Skeleton } from '@/components/ui/skeleton';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useSignal, useBatchSignals, useGeminiAnalysis, useModelStatus } from '@/hooks/useApi';
import { useAppStore } from '@/lib/store';
import { formatPercent, formatRelativeTime } from '@/lib/format';
import {
  Brain,
  Sparkles,
  TrendingUp,
  TrendingDown,
  Minus,
  RefreshCw,
  Cpu,
  Zap,
  CheckCircle,
  AlertCircle,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { toast } from 'sonner';

const watchlistSymbols = ['NIFTY', 'BANKNIFTY', 'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK'];

export default function SignalsPage() {
  const signals = useAppStore((s) => s.signals);
  const [selectedSymbol, setSelectedSymbol] = useState('NIFTY');
  const [customSymbol, setCustomSymbol] = useState('');

  const { data: signalData, isLoading: signalLoading, refetch } = useSignal(selectedSymbol);
  const { data: geminiData, isLoading: geminiLoading, refetch: refetchGemini } = useGeminiAnalysis(
    selectedSymbol,
    'Provide trading analysis with support/resistance levels and market sentiment'
  );
  const { data: modelStatus, isLoading: modelLoading } = useModelStatus();
  const { data: batchSignals, isLoading: batchLoading, refetch: refetchBatch } = useBatchSignals(watchlistSymbols);

  const handleAnalyze = () => {
    if (customSymbol.trim()) {
      setSelectedSymbol(customSymbol.trim().toUpperCase());
      toast.info(`Analyzing ${customSymbol.trim().toUpperCase()}...`);
    }
  };

  const handleRefreshAll = () => {
    refetch();
    refetchGemini();
    refetchBatch();
    toast.success('Refreshing all signals...');
  };

  return (
    <div className="p-6 space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">AI Signals</h1>
          <p className="text-muted-foreground">
            ML predictions and Gemini AI analysis
          </p>
        </div>
        <Button onClick={handleRefreshAll} variant="outline">
          <RefreshCw className="mr-2 h-4 w-4" />
          Refresh All
        </Button>
      </div>

      {/* Model Status */}
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg flex items-center gap-2">
              <Cpu className="h-5 w-5 text-blue-500" />
              ML Models Status
            </CardTitle>
            <Badge variant="outline">Engine B</Badge>
          </div>
        </CardHeader>
        <CardContent>
          {modelLoading ? (
            <div className="flex gap-4">
              {[1, 2, 3, 4].map((i) => (
                <Skeleton key={i} className="h-16 w-32" />
              ))}
            </div>
          ) : (
            <div className="flex flex-wrap gap-3">
              {modelStatus?.models ? (
                Object.entries(modelStatus.models).map(([name, status]: [string, any]) => (
                  <div
                    key={name}
                    className={cn(
                      'flex items-center gap-2 rounded-lg border px-4 py-2',
                      status?.loaded ? 'border-green-500/50 bg-green-50 dark:bg-green-900/20' : 'border-yellow-500/50 bg-yellow-50 dark:bg-yellow-900/20'
                    )}
                  >
                    {status?.loaded ? (
                      <CheckCircle className="h-4 w-4 text-green-500" />
                    ) : (
                      <AlertCircle className="h-4 w-4 text-yellow-500" />
                    )}
                    <span className="text-sm font-medium capitalize">{name}</span>
                    {status?.weight && (
                      <Badge variant="secondary" className="text-xs">
                        {((status.weight ?? 0) * 100).toFixed(0)}%
                      </Badge>
                    )}
                  </div>
                ))
              ) : (
                <div className="flex flex-wrap gap-3">
                  <ModelBadge name="XGBoost" weight={40} />
                  <ModelBadge name="LightGBM" weight={35} />
                  <ModelBadge name="CatBoost" weight={15} />
                  <ModelBadge name="RandomForest" weight={10} />
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Main Content Grid */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Signal Analysis */}
        <div className="lg:col-span-2 space-y-6">
          {/* Symbol Input */}
          <Card>
            <CardContent className="p-4">
              <div className="flex gap-4">
                <div className="flex-1">
                  <Label htmlFor="symbol">Analyze Symbol</Label>
                  <Input
                    id="symbol"
                    value={customSymbol}
                    onChange={(e) => setCustomSymbol(e.target.value)}
                    placeholder="Enter symbol (e.g., RELIANCE)"
                    onKeyDown={(e) => e.key === 'Enter' && handleAnalyze()}
                  />
                </div>
                <div className="flex items-end">
                  <Button onClick={handleAnalyze}>
                    <Brain className="mr-2 h-4 w-4" />
                    Analyze
                  </Button>
                </div>
              </div>
              <div className="flex flex-wrap gap-2 mt-3">
                {watchlistSymbols.map((sym) => (
                  <Button
                    key={sym}
                    variant={selectedSymbol === sym ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setSelectedSymbol(sym)}
                  >
                    {sym}
                  </Button>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Current Signal */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">
                  Signal Analysis: {selectedSymbol}
                </CardTitle>
                <Button variant="ghost" size="sm" onClick={() => refetch()}>
                  <RefreshCw className={cn('h-4 w-4', signalLoading && 'animate-spin')} />
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {signalLoading ? (
                <div className="space-y-4">
                  <Skeleton className="h-24 w-full" />
                  <Skeleton className="h-16 w-full" />
                </div>
              ) : signalData ? (
                <div className="space-y-4">
                  {/* Main Signal */}
                  <div className={cn(
                    'rounded-xl p-6 text-center',
                    signalData.signal === 'BUY' && 'bg-green-100 dark:bg-green-900/30',
                    signalData.signal === 'SELL' && 'bg-red-100 dark:bg-red-900/30',
                    signalData.signal === 'HOLD' && 'bg-gray-100 dark:bg-gray-800'
                  )}>
                    <div className="flex items-center justify-center gap-3 mb-2">
                      {signalData.signal === 'BUY' && <TrendingUp className="h-8 w-8 text-green-600" />}
                      {signalData.signal === 'SELL' && <TrendingDown className="h-8 w-8 text-red-600" />}
                      {signalData.signal === 'HOLD' && <Minus className="h-8 w-8 text-gray-600" />}
                      <span className={cn(
                        'text-4xl font-bold',
                        signalData.signal === 'BUY' && 'text-green-700 dark:text-green-400',
                        signalData.signal === 'SELL' && 'text-red-700 dark:text-red-400',
                        signalData.signal === 'HOLD' && 'text-gray-700 dark:text-gray-400'
                      )}>
                        {signalData.signal}
                      </span>
                    </div>
                    <p className="text-lg font-medium">
                      Confidence: {formatPercent(signalData.confidence * 100, 0)}
                    </p>
                  </div>

                  {/* Analysis Breakdown */}
                  {signalData.analysis && (
                    <div className="grid grid-cols-3 gap-4">
                      <div className="rounded-lg border p-4 text-center">
                        <p className="text-xs text-muted-foreground">Technical</p>
                        <p className="text-xl font-bold">
                          {formatPercent(signalData.analysis.technical_score * 100, 0)}
                        </p>
                      </div>
                      <div className="rounded-lg border p-4 text-center">
                        <p className="text-xs text-muted-foreground">Sentiment</p>
                        <p className="text-xl font-bold">
                          {formatPercent(signalData.analysis.sentiment_score * 100, 0)}
                        </p>
                      </div>
                      <div className="rounded-lg border p-4 text-center">
                        <p className="text-xs text-muted-foreground">ML Prediction</p>
                        <p className="text-xl font-bold">
                          {formatPercent(signalData.analysis.ml_prediction * 100, 0)}
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-center text-muted-foreground py-8">
                  Select a symbol to analyze
                </p>
              )}
            </CardContent>
          </Card>

          {/* Gemini Analysis */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg flex items-center gap-2">
                  <Sparkles className="h-5 w-5 text-purple-500" />
                  Gemini AI Analysis
                </CardTitle>
                <Button variant="ghost" size="sm" onClick={() => refetchGemini()}>
                  <RefreshCw className={cn('h-4 w-4', geminiLoading && 'animate-spin')} />
                </Button>
              </div>
              <CardDescription>
                Advanced market analysis powered by Google Gemini
              </CardDescription>
            </CardHeader>
            <CardContent>
              {geminiLoading ? (
                <div className="space-y-3">
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-4 w-5/6" />
                  <Skeleton className="h-4 w-4/6" />
                  <Skeleton className="h-4 w-full" />
                </div>
              ) : geminiData?.analysis ? (
                <div className="prose prose-sm dark:prose-invert max-w-none">
                  <div className="rounded-lg bg-muted p-4 whitespace-pre-wrap text-sm">
                    {typeof geminiData.analysis === 'string'
                      ? geminiData.analysis
                      : JSON.stringify(geminiData.analysis, null, 2)}
                  </div>
                </div>
              ) : (
                <p className="text-center text-muted-foreground py-8">
                  Gemini analysis will appear here
                </p>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Sidebar - Watchlist & History */}
        <div className="space-y-6">
          {/* Batch Signals */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">Watchlist Signals</CardTitle>
                <Button variant="ghost" size="sm" onClick={() => refetchBatch()}>
                  <RefreshCw className={cn('h-4 w-4', batchLoading && 'animate-spin')} />
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[300px]">
                <div className="space-y-2">
                  {batchLoading ? (
                    [...Array(5)].map((_, i) => (
                      <div key={i} className="flex items-center justify-between rounded-lg border p-3">
                        <Skeleton className="h-5 w-20" />
                        <Skeleton className="h-6 w-16" />
                      </div>
                    ))
                  ) : batchSignals?.signals ? (
                    Object.entries(batchSignals.signals).map(([symbol, data]: [string, any]) => (
                      <SignalRow
                        key={symbol}
                        symbol={symbol}
                        signal={data.signal}
                        confidence={data.confidence}
                        onClick={() => setSelectedSymbol(symbol)}
                        isSelected={selectedSymbol === symbol}
                      />
                    ))
                  ) : (
                    watchlistSymbols.map((sym) => (
                      <SignalRow
                        key={sym}
                        symbol={sym}
                        onClick={() => setSelectedSymbol(sym)}
                        isSelected={selectedSymbol === sym}
                      />
                    ))
                  )}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>

          {/* Signal History */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Recent Signals</CardTitle>
              <CardDescription>Last {signals.length} signals generated</CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[250px]">
                {signals.length === 0 ? (
                  <p className="text-center text-muted-foreground py-8">
                    No signal history yet
                  </p>
                ) : (
                  <div className="space-y-2">
                    {signals.map((sig, i) => (
                      <div
                        key={`${sig.symbol}-${sig.timestamp}-${i}`}
                        className="flex items-center justify-between rounded-lg border p-3"
                      >
                        <div>
                          <p className="font-medium">{sig.symbol}</p>
                          <p className="text-xs text-muted-foreground">
                            {formatRelativeTime(sig.timestamp)}
                          </p>
                        </div>
                        <SignalBadge signal={sig.signal} />
                      </div>
                    ))}
                  </div>
                )}
              </ScrollArea>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

function ModelBadge({ name, weight }: { name: string; weight: number }) {
  return (
    <div className="flex items-center gap-2 rounded-lg border border-green-500/50 bg-green-50 dark:bg-green-900/20 px-4 py-2">
      <CheckCircle className="h-4 w-4 text-green-500" />
      <span className="text-sm font-medium">{name}</span>
      <Badge variant="secondary" className="text-xs">{weight}%</Badge>
    </div>
  );
}

function SignalRow({
  symbol,
  signal,
  confidence,
  onClick,
  isSelected,
}: {
  symbol: string;
  signal?: string;
  confidence?: number;
  onClick?: () => void;
  isSelected?: boolean;
}) {
  return (
    <div
      className={cn(
        'flex items-center justify-between rounded-lg border p-3 cursor-pointer transition-colors',
        isSelected ? 'border-primary bg-primary/5' : 'hover:bg-muted/50'
      )}
      onClick={onClick}
    >
      <div className="flex items-center gap-2">
        {signal === 'BUY' && <TrendingUp className="h-4 w-4 text-green-500" />}
        {signal === 'SELL' && <TrendingDown className="h-4 w-4 text-red-500" />}
        {(!signal || signal === 'HOLD') && <Minus className="h-4 w-4 text-gray-500" />}
        <span className="font-medium">{symbol}</span>
      </div>
      {signal ? (
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground">
            {confidence ? formatPercent(confidence * 100, 0) : ''}
          </span>
          <SignalBadge signal={signal} />
        </div>
      ) : (
        <Badge variant="outline">--</Badge>
      )}
    </div>
  );
}

function SignalBadge({ signal }: { signal: string }) {
  if (signal === 'BUY') {
    return (
      <Badge className="bg-green-100 text-green-700 hover:bg-green-200 dark:bg-green-900/30 dark:text-green-400">
        BUY
      </Badge>
    );
  }
  if (signal === 'SELL') {
    return (
      <Badge className="bg-red-100 text-red-700 hover:bg-red-200 dark:bg-red-900/30 dark:text-red-400">
        SELL
      </Badge>
    );
  }
  return <Badge variant="secondary">HOLD</Badge>;
}

'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Skeleton } from '@/components/ui/skeleton';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  useAllPositionsAnalysis,
  usePositionRiskSummary,
  usePositions
} from '@/hooks/useApi';
import type { PositionAnalysisResponse, PositionGreeks } from '@/lib/api';
import {
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Shield,
  Brain,
  ChevronDown,
  ChevronUp,
  Target,
  Activity,
  DollarSign,
  BarChart3,
  Sparkles,
  AlertCircle,
  CheckCircle2,
  MinusCircle,
  ArrowUpCircle,
  ArrowDownCircle,
  Clock
} from 'lucide-react';
import { formatNumber } from '@/lib/format';

// Action Badge Component
function ActionBadge({ action }: { action: string }) {
  const variants: Record<string, { variant: 'default' | 'secondary' | 'destructive' | 'outline'; icon: React.ReactNode; className: string }> = {
    'BUY': { variant: 'default', icon: <ArrowUpCircle className="h-3 w-3" />, className: 'bg-green-600 hover:bg-green-700' },
    'ADD': { variant: 'default', icon: <ArrowUpCircle className="h-3 w-3" />, className: 'bg-green-500 hover:bg-green-600' },
    'SELL': { variant: 'destructive', icon: <ArrowDownCircle className="h-3 w-3" />, className: '' },
    'REDUCE': { variant: 'destructive', icon: <ArrowDownCircle className="h-3 w-3" />, className: 'bg-orange-500 hover:bg-orange-600' },
    'HOLD': { variant: 'secondary', icon: <MinusCircle className="h-3 w-3" />, className: '' },
    'MONITOR': { variant: 'secondary', icon: <Activity className="h-3 w-3" />, className: '' },
    'REVIEW': { variant: 'outline', icon: <AlertTriangle className="h-3 w-3" />, className: 'border-yellow-500 text-yellow-600' },
    'EXIT': { variant: 'destructive', icon: <AlertCircle className="h-3 w-3" />, className: 'bg-red-600 hover:bg-red-700' },
    'EXIT_CONSIDERATION': { variant: 'destructive', icon: <AlertCircle className="h-3 w-3" />, className: 'bg-red-500 hover:bg-red-600' },
  };

  const config = variants[action] || variants['HOLD'];

  return (
    <Badge variant={config.variant} className={`gap-1 ${config.className}`}>
      {config.icon}
      {action.replace('_', ' ')}
    </Badge>
  );
}

// Greeks Display Component
function GreeksDisplay({ greeks }: { greeks: PositionGreeks | null }) {
  if (!greeks) return null;

  const items = [
    { label: 'Delta', value: greeks.delta, format: (v: number) => v.toFixed(4) },
    { label: 'Gamma', value: greeks.gamma, format: (v: number) => v.toFixed(4) },
    { label: 'Theta', value: greeks.theta, format: (v: number) => `₹${v.toFixed(2)}` },
    { label: 'Vega', value: greeks.vega, format: (v: number) => v.toFixed(4) },
    { label: 'Moneyness', value: greeks.moneyness, format: (v: number) => v.toFixed(2) },
  ];

  return (
    <div className="grid grid-cols-5 gap-2 rounded-lg bg-muted/50 p-3">
      {items.map((item) => (
        <div key={item.label} className="text-center">
          <p className="text-xs text-muted-foreground">{item.label}</p>
          <p className="font-mono text-sm font-medium">{item.format(item.value)}</p>
        </div>
      ))}
    </div>
  );
}

// Position Card Component
function PositionAnalysisCard({ analysis }: { analysis: PositionAnalysisResponse }) {
  const [isOpen, setIsOpen] = useState(false);
  const { symbol, analysis: positionDetails, risk_metrics, ai_recommendation, market_context, timestamp } = analysis;

  const unrealizedPnL = risk_metrics?.unrealized_pnl || 0;
  const pnlPercent = risk_metrics?.unrealized_pnl_pct || 0;
  const isProfitable = positionDetails?.is_profitable ?? unrealizedPnL >= 0;

  return (
    <Card className="overflow-hidden">
      <Collapsible open={isOpen} onOpenChange={setIsOpen}>
        <CollapsibleTrigger asChild>
          <div className="flex cursor-pointer items-center justify-between p-4 hover:bg-muted/50 transition-colors">
            <div className="flex items-center gap-4">
              <div className="flex flex-col">
                <div className="flex items-center gap-2">
                  <span className="font-semibold">{symbol}</span>
                  <Badge variant="outline" className="text-xs">
                    {positionDetails?.position_type || 'EQUITY'}
                  </Badge>
                  {positionDetails?.direction === 'LONG' ? (
                    <TrendingUp className="h-4 w-4 text-green-500" />
                  ) : (
                    <TrendingDown className="h-4 w-4 text-red-500" />
                  )}
                </div>
                <span className="text-sm text-muted-foreground">
                  Qty: {positionDetails?.quantity || 0} @ ₹{formatNumber(positionDetails?.entry_price || 0)}
                </span>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <div className="text-right">
                <p className={`font-mono font-semibold ${isProfitable ? 'text-green-600' : 'text-red-600'}`}>
                  {isProfitable ? '+' : ''}₹{formatNumber(unrealizedPnL)}
                </p>
                <p className={`text-xs ${isProfitable ? 'text-green-500' : 'text-red-500'}`}>
                  {isProfitable ? '+' : ''}{pnlPercent.toFixed(2)}%
                </p>
              </div>

              <div className="flex items-center gap-2">
                <Badge variant="outline" className="gap-1">
                  <Target className="h-3 w-3" />
                  {ai_recommendation?.confidence || 'N/A'}
                </Badge>
                <ActionBadge action={ai_recommendation?.action || 'HOLD'} />
              </div>

              {isOpen ? <ChevronUp className="h-5 w-5" /> : <ChevronDown className="h-5 w-5" />}
            </div>
          </div>
        </CollapsibleTrigger>

        <CollapsibleContent>
          <div className="border-t px-4 pb-4 pt-3 space-y-4">
            {/* Greeks Section - Only for options */}
            {risk_metrics?.greeks && positionDetails?.position_type === 'OPTION' && (
              <div className="space-y-2">
                <h4 className="flex items-center gap-2 text-sm font-medium">
                  <BarChart3 className="h-4 w-4" />
                  Option Greeks
                </h4>
                <GreeksDisplay greeks={risk_metrics.greeks} />
              </div>
            )}

            {/* Risk Metrics */}
            <div className="space-y-2">
              <h4 className="flex items-center gap-2 text-sm font-medium">
                <Shield className="h-4 w-4" />
                Risk Metrics
              </h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div className="rounded-lg border p-2">
                  <p className="text-xs text-muted-foreground">Position Value</p>
                  <p className="font-mono text-sm">₹{formatNumber(risk_metrics?.position_value || 0)}</p>
                </div>
                <div className="rounded-lg border p-2">
                  <p className="text-xs text-muted-foreground">Max Loss</p>
                  <p className="font-mono text-sm text-red-500">
                    {typeof risk_metrics?.max_loss === 'number'
                      ? `₹${formatNumber(risk_metrics.max_loss)}`
                      : risk_metrics?.max_loss || 'N/A'}
                  </p>
                </div>
                <div className="rounded-lg border p-2">
                  <p className="text-xs text-muted-foreground">Breakeven</p>
                  <p className="font-mono text-sm">
                    {risk_metrics?.breakeven ? `₹${formatNumber(risk_metrics.breakeven)}` : 'N/A'}
                  </p>
                </div>
                <div className="rounded-lg border p-2">
                  <p className="text-xs text-muted-foreground">Days to Expiry</p>
                  <p className="font-mono text-sm">{risk_metrics?.days_to_expiry ?? 'N/A'}</p>
                </div>
              </div>
            </div>

            {/* AI Recommendation */}
            <div className="space-y-2">
              <h4 className="flex items-center gap-2 text-sm font-medium">
                <Brain className="h-4 w-4" />
                AI Recommendation
              </h4>
              <div className="rounded-lg border p-3 bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-900/20 dark:to-blue-900/20">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <ActionBadge action={ai_recommendation?.action || 'HOLD'} />
                    <Badge variant="outline" className="gap-1">
                      <Target className="h-3 w-3" />
                      {ai_recommendation?.confidence || 'N/A'} confidence
                    </Badge>
                  </div>
                  <span className="text-xs text-muted-foreground">
                    Score: {ai_recommendation?.score || 0}/100
                  </span>
                </div>
                <p className="text-sm text-muted-foreground mb-3">{ai_recommendation?.summary || 'No analysis available'}</p>

                {/* Suggested Actions */}
                {ai_recommendation?.suggested_actions && ai_recommendation.suggested_actions.length > 0 && (
                  <div className="space-y-2">
                    {ai_recommendation.suggested_actions.map((action, idx) => (
                      <div key={idx} className="rounded bg-gray-100 dark:bg-gray-800 p-2">
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium">{action.action}</span>
                          <Badge variant={action.urgency === 'HIGH' ? 'destructive' : action.urgency === 'MEDIUM' ? 'secondary' : 'outline'} className="text-xs">
                            {action.urgency}
                          </Badge>
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">{action.reason}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Market Context */}
            <div className="space-y-2">
              <h4 className="flex items-center gap-2 text-sm font-medium">
                <Activity className="h-4 w-4" />
                Market Context
              </h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                <div className="rounded-lg border p-2 text-center">
                  <p className="text-xs text-muted-foreground">Underlying</p>
                  <p className="font-mono text-sm">₹{formatNumber(market_context?.underlying_price || 0)}</p>
                </div>
                <div className="rounded-lg border p-2 text-center">
                  <p className="text-xs text-muted-foreground">Trend</p>
                  <Badge variant="outline">{market_context?.trend || 'N/A'}</Badge>
                </div>
                <div className="rounded-lg border p-2 text-center">
                  <p className="text-xs text-muted-foreground">Volatility</p>
                  <p className="font-mono text-sm">{((market_context?.volatility || 0) * 100).toFixed(1)}%</p>
                </div>
                <div className="rounded-lg border p-2 text-center">
                  <p className="text-xs text-muted-foreground">Status</p>
                  <Badge variant="outline">{market_context?.market_status || 'N/A'}</Badge>
                </div>
              </div>
            </div>

            {/* Timestamp */}
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <Clock className="h-3 w-3" />
              Analysis updated: {new Date(timestamp).toLocaleString()}
            </div>
          </div>
        </CollapsibleContent>
      </Collapsible>
    </Card>
  );
}

// Risk Summary Card
function RiskSummaryCard() {
  const { summary, isLoading, error } = usePositionRiskSummary();

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Portfolio Risk Summary
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <Skeleton key={i} className="h-20" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error || !summary) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Portfolio Risk Summary
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">No positions to analyze</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Portfolio Risk Summary
          </CardTitle>
          <Badge variant="outline" className="gap-1">
            <Activity className="h-3 w-3" />
            {summary.totalPositions} positions
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Main Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="rounded-lg border p-3">
            <p className="text-xs text-muted-foreground flex items-center gap-1">
              <DollarSign className="h-3 w-3" />
              Unrealized P&L
            </p>
            <p className={`font-mono text-xl font-semibold ${summary.totalUnrealizedPnL >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {summary.totalUnrealizedPnL >= 0 ? '+' : ''}₹{formatNumber(summary.totalUnrealizedPnL)}
            </p>
          </div>
          <div className="rounded-lg border p-3">
            <p className="text-xs text-muted-foreground flex items-center gap-1">
              <Target className="h-3 w-3" />
              Avg Risk Score
            </p>
            <div className="flex items-center gap-2">
              <Progress value={summary.averageRiskScore} className="h-2 flex-1" />
              <span className="font-mono text-lg font-semibold">{summary.averageRiskScore.toFixed(0)}</span>
            </div>
          </div>
          <div className="rounded-lg border p-3">
            <p className="text-xs text-muted-foreground flex items-center gap-1">
              <AlertTriangle className="h-3 w-3" />
              Max Loss
            </p>
            <p className="font-mono text-xl font-semibold text-red-500">
              ₹{formatNumber(summary.totalMaxLoss)}
            </p>
          </div>
          <div className="rounded-lg border p-3">
            <p className="text-xs text-muted-foreground flex items-center gap-1">
              <AlertCircle className="h-3 w-3" />
              High Risk
            </p>
            <p className="font-mono text-xl font-semibold text-orange-500">
              {summary.highRiskCount} positions
            </p>
          </div>
        </div>

        {/* Recommendations Summary */}
        <div className="rounded-lg border p-3">
          <p className="text-xs text-muted-foreground mb-2 flex items-center gap-1">
            <Brain className="h-3 w-3" />
            AI Recommendations
          </p>
          <div className="flex gap-2">
            <Badge className="bg-green-600 gap-1">
              <ArrowUpCircle className="h-3 w-3" />
              {summary.buyRecommendations} BUY/ADD
            </Badge>
            <Badge variant="secondary" className="gap-1">
              <MinusCircle className="h-3 w-3" />
              {summary.holdRecommendations} HOLD
            </Badge>
            <Badge variant="destructive" className="gap-1">
              <ArrowDownCircle className="h-3 w-3" />
              {summary.sellRecommendations} SELL/REDUCE
            </Badge>
          </div>
        </div>

        {/* Risk Distribution */}
        <div className="rounded-lg border p-3">
          <p className="text-xs text-muted-foreground mb-2">Confidence Distribution</p>
          <div className="flex gap-2">
            <div className="flex items-center gap-1">
              <div className="h-2 w-2 rounded-full bg-green-500" />
              <span className="text-xs">High: {summary.positionsByConfidence.high}</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="h-2 w-2 rounded-full bg-yellow-500" />
              <span className="text-xs">Medium: {summary.positionsByConfidence.medium}</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="h-2 w-2 rounded-full bg-red-500" />
              <span className="text-xs">Low: {summary.positionsByConfidence.low}</span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Main Position Analysis Component
export function PositionAnalysisSection() {
  const { data: analysisData, isLoading, error, refetch } = useAllPositionsAnalysis();
  const { data: positionsData } = usePositions();
  const positions = Array.isArray(positionsData?.data) ? positionsData.data : [];

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="h-6 w-6 text-purple-500" />
          <h2 className="text-2xl font-bold">AI Position Analysis</h2>
        </div>
        <Button variant="outline" onClick={() => refetch()} disabled={isLoading}>
          {isLoading ? 'Analyzing...' : 'Refresh Analysis'}
        </Button>
      </div>

      {/* Risk Summary */}
      <RiskSummaryCard />

      {/* Position Cards */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Brain className="h-5 w-5" />
            Position-wise Analysis
          </CardTitle>
          <CardDescription>
            Click on each position to view detailed AI analysis, Greeks, and recommendations
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-24" />
              ))}
            </div>
          ) : error ? (
            <div className="text-center py-8 text-muted-foreground">
              <AlertCircle className="h-12 w-12 mx-auto mb-2" />
              <p>Error loading position analysis</p>
              <p className="text-sm">{error.message}</p>
            </div>
          ) : positions.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <CheckCircle2 className="h-12 w-12 mx-auto mb-2" />
              <p>No open positions</p>
              <p className="text-sm">Your position analysis will appear here once you have open trades</p>
            </div>
          ) : analysisData && analysisData.length > 0 ? (
            <ScrollArea className="h-[600px] pr-4">
              <div className="space-y-3">
                {analysisData.map((analysis, index) => (
                  <PositionAnalysisCard key={`${analysis.symbol}-${index}`} analysis={analysis} />
                ))}
              </div>
            </ScrollArea>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              <Brain className="h-12 w-12 mx-auto mb-2 animate-pulse" />
              <p>Analyzing your positions...</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

// Export individual components for flexible usage
export { PositionAnalysisCard, RiskSummaryCard, GreeksDisplay, ActionBadge };

'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { useUserAccount, usePositions, useAllPositionsAnalysis } from '@/hooks/useApi';
import { useAppStore } from '@/lib/store';
import { Wallet, TrendingUp, TrendingDown, Shield, PiggyBank, Activity, AlertTriangle, Brain, Clock, Target } from 'lucide-react';
import { formatCurrency } from '@/lib/format';

export function PortfolioSummary() {
  const funds = useAppStore((s) => s.funds);
  const dematData = useAppStore((s) => s.dematData);
  const userProfile = useAppStore((s) => s.userProfile);
  const { isLoading: isAccountLoading, data: accountData } = useUserAccount();
  const { data: positionsData } = usePositions();
  const { data: analysisData, isLoading: isAnalysisLoading } = useAllPositionsAnalysis();

  // Calculate positions P&L
  const positions = positionsData?.data || dematData?.positions?.items || [];
  const positionsPnL = Array.isArray(positions)
    ? positions.reduce((sum: number, p: any) => sum + (p.unrealizedProfit || p.pnl || 0), 0)
    : accountData?.account_summary?.total_positions_pnl || 0;
  const positionsCount = Array.isArray(positions) ? positions.length : 0;

  if (isAccountLoading || !funds) {
    return <PortfolioSummarySkeleton />;
  }

  const isPnlPositive = positionsPnL >= 0;

  const metrics = [
    {
      label: 'Available Balance',
      value: funds.availableBalance,
      icon: Wallet,
      color: 'text-green-500',
      bgColor: 'bg-green-100 dark:bg-green-900/30',
      format: 'currency',
    },
    {
      label: 'Margin Used',
      value: funds.collateralAmount,
      icon: Shield,
      color: 'text-purple-500',
      bgColor: 'bg-purple-100 dark:bg-purple-900/30',
      format: 'currency',
    },
    {
      label: "Today's P&L",
      value: positionsPnL,
      icon: isPnlPositive ? TrendingUp : TrendingDown,
      color: isPnlPositive ? 'text-green-500' : 'text-red-500',
      bgColor: isPnlPositive ? 'bg-green-100 dark:bg-green-900/30' : 'bg-red-100 dark:bg-red-900/30',
      format: 'pnl',
    },
    {
      label: 'Open Positions',
      value: positionsCount,
      icon: Activity,
      color: 'text-blue-500',
      bgColor: 'bg-blue-100 dark:bg-blue-900/30',
      format: 'number',
    },
  ];

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Portfolio Summary</CardTitle>
          <div className="flex items-center gap-2">
            {userProfile?.isConnected ? (
              <Badge variant="default" className="bg-green-500">
                Connected: {funds.dhanClientId}
              </Badge>
            ) : (
              <Badge variant="destructive">Not Connected</Badge>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {metrics.map((metric) => {
            const Icon = metric.icon;
            let displayValue: string;

            if (metric.format === 'currency') {
              displayValue = formatCurrency(metric.value);
            } else if (metric.format === 'pnl') {
              const prefix = metric.value >= 0 ? '+' : '';
              displayValue = `${prefix}${formatCurrency(metric.value)}`;
            } else {
              displayValue = String(metric.value);
            }

            return (
              <div
                key={metric.label}
                className="flex items-center gap-3 rounded-lg border p-4"
              >
                <div className={`rounded-lg p-2.5 ${metric.bgColor}`}>
                  <Icon className={`h-5 w-5 ${metric.color}`} />
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">{metric.label}</p>
                  <p className={`font-mono text-lg font-bold ${metric.format === 'pnl' ? metric.color : ''}`}>
                    {displayValue}
                  </p>
                </div>
              </div>
            );
          })}
        </div>

        {/* Open Positions Details with AI Analysis */}
        {positionsCount > 0 && Array.isArray(positions) && (
          <div className="mt-4 border-t pt-4">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-sm font-medium flex items-center gap-2">
                <Activity className="h-4 w-4" />
                Open Positions
              </h4>
              {isAnalysisLoading && (
                <Badge variant="outline" className="text-xs">
                  <Brain className="h-3 w-3 mr-1 animate-pulse" />
                  Analyzing...
                </Badge>
              )}
            </div>
            <div className="space-y-3">
              {positions.slice(0, 5).map((pos: any, idx: number) => {
                const pnl = pos.unrealizedProfit || pos.pnl || 0;
                const isPosPositive = pnl >= 0;

                // Find AI analysis for this position (with defensive array check)
                const analysisArray = Array.isArray(analysisData) ? analysisData : [];
                const analysis = analysisArray.find((a) =>
                  a.symbol === pos.tradingSymbol ||
                  a.symbol?.includes(pos.tradingSymbol?.split('-')[0])
                );
                const aiAction = analysis?.ai_recommendation?.action;
                const aiConfidence = analysis?.ai_recommendation?.confidence;
                const daysToExpiry = analysis?.risk_metrics?.days_to_expiry;
                const greeks = analysis?.risk_metrics?.greeks;

                return (
                  <div key={idx} className="p-3 rounded-lg bg-muted/50 border">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="text-xs">
                          {pos.positionType || pos.productType || 'OPEN'}
                        </Badge>
                        <span className="font-medium">{pos.tradingSymbol || pos.symbol}</span>
                        <span className="text-muted-foreground text-sm">Qty: {pos.netQty || pos.quantity}</span>
                      </div>
                      <div className={`font-mono font-medium ${isPosPositive ? 'text-green-500' : 'text-red-500'}`}>
                        {isPosPositive ? '+' : ''}{formatCurrency(pnl)}
                      </div>
                    </div>

                    {/* AI Analysis Row */}
                    {analysis && (
                      <div className="mt-2 pt-2 border-t border-dashed flex items-center justify-between text-xs">
                        <div className="flex items-center gap-3">
                          <div className="flex items-center gap-1">
                            <Brain className="h-3 w-3 text-purple-500" />
                            <Badge
                              variant={aiAction === 'EXIT_CONSIDERATION' ? 'destructive' : aiAction === 'HOLD' ? 'default' : 'secondary'}
                              className="text-xs"
                            >
                              {aiAction?.replace('_', ' ')}
                            </Badge>
                          </div>
                          <div className="flex items-center gap-1">
                            <Target className="h-3 w-3 text-blue-500" />
                            <span className="text-muted-foreground">{typeof aiConfidence === 'number' ? `${((aiConfidence ?? 0) * 100).toFixed(0)}%` : aiConfidence ?? 'N/A'}</span>
                          </div>
                          {daysToExpiry !== null && daysToExpiry !== undefined && (
                            <div className="flex items-center gap-1">
                              <Clock className={`h-3 w-3 ${daysToExpiry <= 2 ? 'text-red-500' : 'text-yellow-500'}`} />
                              <span className={daysToExpiry <= 2 ? 'text-red-500 font-medium' : 'text-muted-foreground'}>
                                {daysToExpiry}d to expiry
                              </span>
                            </div>
                          )}
                        </div>
                        {greeks && (
                          <div className="flex items-center gap-2 text-muted-foreground">
                            <span>Δ: {greeks.delta?.toFixed(2)}</span>
                            <span>θ: ₹{greeks.theta?.toFixed(2)}</span>
                            <Badge variant="outline" className={`text-xs ${
                              greeks.moneyness_status === 'ITM' ? 'border-green-500 text-green-500' :
                              greeks.moneyness_status === 'OTM' ? 'border-red-500 text-red-500' : ''
                            }`}>
                              {greeks.moneyness_status}
                            </Badge>
                          </div>
                        )}
                      </div>
                    )}

                    {/* AI Urgent Alerts */}
                    {analysis?.ai_recommendation?.suggested_actions?.some((a: any) => a.urgency === 'HIGH') && (
                      <div className="mt-2 flex items-center gap-2 text-xs text-red-500 bg-red-50 dark:bg-red-900/20 p-2 rounded">
                        <AlertTriangle className="h-3 w-3" />
                        <span>
                          {analysis.ai_recommendation.suggested_actions.find((a: any) => a.urgency === 'HIGH')?.reason}
                        </span>
                      </div>
                    )}
                  </div>
                );
              })}
              {positions.length > 5 && (
                <p className="text-xs text-muted-foreground text-center">
                  +{positions.length - 5} more positions
                </p>
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function PortfolioSummarySkeleton() {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Portfolio Summary</CardTitle>
          <Skeleton className="h-5 w-24" />
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="flex items-center gap-3 rounded-lg border p-4">
              <Skeleton className="h-12 w-12 rounded-lg" />
              <div className="space-y-1">
                <Skeleton className="h-3 w-20" />
                <Skeleton className="h-6 w-24" />
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

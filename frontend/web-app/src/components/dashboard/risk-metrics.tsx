'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Skeleton } from '@/components/ui/skeleton';
import { useAppStore } from '@/lib/store';
import { TrendingUp, TrendingDown, AlertTriangle, Shield, Target, Percent } from 'lucide-react';
import { formatPercent, formatNumber } from '@/lib/format';

export function RiskMetricsCard() {
  const riskMetrics = useAppStore((s) => s.riskMetrics);

  if (!riskMetrics) {
    return <RiskMetricsSkeleton />;
  }

  const metrics = [
    {
      label: 'Sharpe Ratio',
      value: riskMetrics.sharpe_ratio,
      format: (v: number) => v.toFixed(2),
      icon: TrendingUp,
      good: riskMetrics.sharpe_ratio > 1,
    },
    {
      label: 'Sortino Ratio',
      value: riskMetrics.sortino_ratio,
      format: (v: number) => v.toFixed(2),
      icon: Shield,
      good: riskMetrics.sortino_ratio > 1.5,
    },
    {
      label: 'VaR (95%)',
      value: riskMetrics.var_95,
      format: (v: number) => formatPercent(v * 100),
      icon: AlertTriangle,
      good: Math.abs(riskMetrics.var_95) < 0.03,
    },
    {
      label: 'CVaR (95%)',
      value: riskMetrics.cvar_95,
      format: (v: number) => formatPercent(v * 100),
      icon: Target,
      good: Math.abs(riskMetrics.cvar_95) < 0.05,
    },
    {
      label: 'Max Drawdown',
      value: riskMetrics.max_drawdown_pct,
      format: (v: number) => formatPercent(-v),
      icon: TrendingDown,
      good: riskMetrics.max_drawdown_pct < 10,
    },
    {
      label: 'Ann. Volatility',
      value: riskMetrics.annualized_volatility,
      format: (v: number) => formatPercent(v * 100),
      icon: Percent,
      good: riskMetrics.annualized_volatility < 0.25,
    },
  ];

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Risk Analytics</CardTitle>
          <Badge variant="outline">
            Return: {formatPercent(riskMetrics.annualized_return * 100)}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {metrics.map((metric) => {
            const Icon = metric.icon;
            return (
              <div
                key={metric.label}
                className="flex items-center gap-3 rounded-lg border p-3"
              >
                <div
                  className={`rounded-lg p-2 ${
                    metric.good ? 'bg-green-100 dark:bg-green-900/30' : 'bg-yellow-100 dark:bg-yellow-900/30'
                  }`}
                >
                  <Icon
                    className={`h-4 w-4 ${
                      metric.good ? 'text-green-600 dark:text-green-400' : 'text-yellow-600 dark:text-yellow-400'
                    }`}
                  />
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">{metric.label}</p>
                  <p className="font-mono text-lg font-semibold">
                    {metric.format(metric.value)}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

function RiskMetricsSkeleton() {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Risk Analytics</CardTitle>
          <Skeleton className="h-5 w-20" />
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="flex items-center gap-3 rounded-lg border p-3">
              <Skeleton className="h-10 w-10 rounded-lg" />
              <div className="space-y-1">
                <Skeleton className="h-3 w-16" />
                <Skeleton className="h-6 w-12" />
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

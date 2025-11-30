'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { useFunds } from '@/hooks/useApi';
import { useAppStore } from '@/lib/store';
import { Wallet, TrendingUp, Shield, PiggyBank } from 'lucide-react';
import { formatCurrency, formatCompact } from '@/lib/format';

export function PortfolioSummary() {
  const funds = useAppStore((s) => s.funds);
  const { isLoading } = useFunds();

  if (isLoading || !funds) {
    return <PortfolioSummarySkeleton />;
  }

  const metrics = [
    {
      label: 'Available Balance',
      value: funds.availableBalance,
      icon: Wallet,
      color: 'text-green-500',
      bgColor: 'bg-green-100 dark:bg-green-900/30',
    },
    {
      label: 'SOD Limit',
      value: funds.sodLimit,
      icon: TrendingUp,
      color: 'text-blue-500',
      bgColor: 'bg-blue-100 dark:bg-blue-900/30',
    },
    {
      label: 'Collateral',
      value: funds.collateralAmount,
      icon: Shield,
      color: 'text-purple-500',
      bgColor: 'bg-purple-100 dark:bg-purple-900/30',
    },
    {
      label: 'Total',
      value: funds.availableBalance + funds.collateralAmount,
      icon: PiggyBank,
      color: 'text-orange-500',
      bgColor: 'bg-orange-100 dark:bg-orange-900/30',
    },
  ];

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Portfolio Summary</CardTitle>
          <Badge variant="outline">ID: {funds.dhanClientId}</Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {metrics.map((metric) => {
            const Icon = metric.icon;
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
                  <p className="font-mono text-lg font-bold">
                    {formatCurrency(metric.value)}
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

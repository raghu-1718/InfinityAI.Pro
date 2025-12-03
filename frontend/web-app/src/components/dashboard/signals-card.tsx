'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { useSignal } from '@/hooks/useApi';
import { useAppStore } from '@/lib/store';
import { ArrowUp, ArrowDown, Minus, RefreshCw, Brain } from 'lucide-react';
import { formatPercent } from '@/lib/format';
import { cn } from '@/lib/utils';

const watchlistSymbols = ['NIFTY', 'BANKNIFTY', 'RELIANCE', 'TCS', 'HDFCBANK', 'INFY'];

export function SignalsCard() {
  const signalsRaw = useAppStore((s) => s.signals);
  const signals = Array.isArray(signalsRaw) ? signalsRaw : [];

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-lg">
            <Brain className="h-5 w-5 text-purple-500" />
            AI Signals
          </CardTitle>
          <Badge variant="secondary">{signals.length} signals</Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {watchlistSymbols.slice(0, 4).map((symbol) => (
            <SignalRow key={symbol} symbol={symbol} />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function SignalRow({ symbol }: { symbol: string }) {
  const { data, isLoading, refetch, isFetching } = useSignal(symbol, true);

  if (isLoading) {
    return (
      <div className="flex items-center justify-between rounded-lg border p-3">
        <Skeleton className="h-5 w-20" />
        <Skeleton className="h-6 w-16" />
      </div>
    );
  }

  const signal = data?.signal || 'HOLD';
  const confidence = data?.confidence || 0;

  return (
    <div className="flex items-center justify-between rounded-lg border p-3 transition-colors hover:bg-muted/50">
      <div className="flex items-center gap-3">
        <SignalIcon signal={signal} />
        <div>
          <p className="font-medium">{symbol}</p>
          <p className="text-xs text-muted-foreground">
            Confidence: {formatPercent(confidence * 100, 0)}
          </p>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <SignalBadge signal={signal} />
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7"
          onClick={() => refetch()}
          disabled={isFetching}
        >
          <RefreshCw className={cn('h-3 w-3', isFetching && 'animate-spin')} />
        </Button>
      </div>
    </div>
  );
}

function SignalIcon({ signal }: { signal: string }) {
  if (signal === 'BUY') {
    return (
      <div className="rounded-lg bg-green-100 p-2 dark:bg-green-900/30">
        <ArrowUp className="h-4 w-4 text-green-600 dark:text-green-400" />
      </div>
    );
  }
  if (signal === 'SELL') {
    return (
      <div className="rounded-lg bg-red-100 p-2 dark:bg-red-900/30">
        <ArrowDown className="h-4 w-4 text-red-600 dark:text-red-400" />
      </div>
    );
  }
  return (
    <div className="rounded-lg bg-gray-100 p-2 dark:bg-gray-800">
      <Minus className="h-4 w-4 text-gray-600 dark:text-gray-400" />
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
  return (
    <Badge variant="secondary">HOLD</Badge>
  );
}

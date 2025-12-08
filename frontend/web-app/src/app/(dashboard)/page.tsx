'use client';

import { EngineStatusCards } from '@/components/dashboard/engine-status';
import { PortfolioSummary } from '@/components/dashboard/portfolio-summary';
import { RiskMetricsCard } from '@/components/dashboard/risk-metrics';
import { SignalsCard } from '@/components/dashboard/signals-card';
import { QuickTradeCard } from '@/components/dashboard/quick-trade';
import { RecentOrdersCard } from '@/components/dashboard/recent-orders';
import { AutoTradingCard } from '@/components/dashboard/auto-trading';
import { GeminiChat } from '@/components/dashboard/gemini-chat';
import { useEngineHealth, useFunds, useHoldings, useRiskMetrics } from '@/hooks/useApi';
import { useMemo, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Sparkles } from 'lucide-react';
import Link from 'next/link';

export default function DashboardPage() {
  // Initialize data fetching
  useEngineHealth();
  useFunds();

  // Fetch user's actual holdings to calculate real returns
  const { data: holdingsData } = useHoldings();

  // Calculate real returns from user's holdings (day-over-day price changes)
  const userReturns = useMemo(() => {
    // Safely extract holdings array from API response
    const holdingsRaw = holdingsData?.data;
    const holdings = Array.isArray(holdingsRaw) ? holdingsRaw : [];

    if (holdings.length === 0) {
      // Return empty array - risk metrics will show loading state
      return [];
    }

    // Calculate returns from each holding's PnL
    return holdings.slice(0, 30).map((h: any) => {
      const buyAvg = h.buyAvg || h.avgCostPrice || 0;
      const currentValue = h.currentValue || h.dayClosePrice || buyAvg;
      // Return as decimal (e.g., 0.02 for 2%)
      return buyAvg > 0 ? (currentValue - buyAvg) / buyAvg : 0;
    }).filter((r: number) => !isNaN(r) && isFinite(r));
  }, [holdingsData]);

  // Only fetch risk metrics if we have actual returns data
  useRiskMetrics(userReturns.length > 0 ? userReturns : []);

  return (
    <div className="p-6 space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">
            Welcome back! Here's an overview of your trading activity.
          </p>
        </div>
        <Link href="/ai">
          <Button className="gap-2">
            <Sparkles className="h-4 w-4" />
            Ask Gemini AI
          </Button>
        </Link>
      </div>

      {/* Auto Trading - Prominently at the top */}
      <AutoTradingCard />

      {/* Engine Status */}
      <EngineStatusCards />

      {/* Portfolio Summary */}
      <PortfolioSummary />

      {/* Main Grid */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left Column - Risk & Orders */}
        <div className="lg:col-span-2 space-y-6">
          <RiskMetricsCard />
          <RecentOrdersCard />
        </div>

        {/* Right Column - Gemini AI Chat & Signals */}
        <div className="space-y-6">
          <GeminiChat />
          <SignalsCard />
        </div>
      </div>
    </div>
  );
}

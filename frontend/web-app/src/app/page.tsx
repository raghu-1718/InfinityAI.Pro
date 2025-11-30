'use client';

import { EngineStatusCards } from '@/components/dashboard/engine-status';
import { PortfolioSummary } from '@/components/dashboard/portfolio-summary';
import { RiskMetricsCard } from '@/components/dashboard/risk-metrics';
import { SignalsCard } from '@/components/dashboard/signals-card';
import { QuickTradeCard } from '@/components/dashboard/quick-trade';
import { RecentOrdersCard } from '@/components/dashboard/recent-orders';
import { AutoTradingCard } from '@/components/dashboard/auto-trading';
import { useEngineHealth, useFunds, useRiskMetrics } from '@/hooks/useApi';

// Sample returns data for demo (in production, this comes from API)
const sampleReturns = [
  0.012, -0.005, 0.008, -0.003, 0.015, -0.007, 0.011, 0.006, -0.004, 0.009,
  -0.002, 0.013, 0.007, -0.008, 0.010, -0.006, 0.014, 0.003, -0.009, 0.011,
  0.005, -0.004, 0.008, 0.002, -0.007, 0.012, -0.003, 0.009, 0.006, -0.005,
];

export default function DashboardPage() {
  // Initialize data fetching
  useEngineHealth();
  useFunds();
  useRiskMetrics(sampleReturns);

  return (
    <div className="p-6 space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          Welcome back! Here's an overview of your trading activity.
        </p>
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

        {/* Right Column - Quick Actions & Signals */}
        <div className="space-y-6">
          <QuickTradeCard />
          <SignalsCard />
        </div>
      </div>
    </div>
  );
}

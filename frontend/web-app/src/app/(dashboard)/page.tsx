'use client';

import { EngineStatusCards } from '@/components/dashboard/engine-status';
import { PortfolioSummary } from '@/components/dashboard/portfolio-summary';
import { RiskMetricsCard } from '@/components/dashboard/risk-metrics';
import { SignalsCard } from '@/components/dashboard/signals-card';
import { QuickTradeCard } from '@/components/dashboard/quick-trade';
import { RecentOrdersCard } from '@/components/dashboard/recent-orders';
import { AutoTradingCard } from '@/components/dashboard/auto-trading';
import { GeminiChat } from '@/components/dashboard/gemini-chat';
import { ActivityDashboard } from '@/components/activity';
import { useEngineHealth, useUserAccount, useRiskMetrics, usePositions, usePageActivityLogger } from '@/hooks/useApi';
import { useAppStore } from '@/lib/store';
import { useMemo, useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Sparkles, RefreshCw, Activity, LayoutDashboard } from 'lucide-react';
import Link from 'next/link';

export default function DashboardPage() {
  const userProfile = useAppStore((s) => s.userProfile);
  const [activeTab, setActiveTab] = useState('overview');

  // Log page visit
  usePageActivityLogger(userProfile?.clientId, 'Dashboard');

  // Initialize data fetching
  useEngineHealth();

  // Fetch complete user account data (funds, positions, holdings, orders)
  const { data: accountData, isLoading: isAccountLoading, refetch: refetchAccount } = useUserAccount();

  // Fetch positions for real-time P&L updates
  const { data: positionsData } = usePositions();

  // Calculate real returns from user's positions
  const userReturns = useMemo(() => {
    const positions = positionsData?.data || accountData?.positions?.data || [];

    if (!Array.isArray(positions) || positions.length === 0) {
      return [];
    }

    // Calculate returns from each position's PnL
    return positions.slice(0, 30).map((p: any) => {
      const buyAvg = p.buyAvg || p.costPrice || 0;
      const currentValue = p.dayBuyValue || p.currentValue || buyAvg;
      return buyAvg > 0 ? (currentValue - buyAvg) / buyAvg : 0;
    }).filter((r: number) => !isNaN(r) && isFinite(r));
  }, [positionsData, accountData]);

  // Only fetch risk metrics if we have actual returns data
  useRiskMetrics(userReturns.length > 0 ? userReturns : []);

  return (
    <div className="p-6 space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">
            {userProfile?.isConnected
              ? `Welcome back, ${userProfile.clientId}! Here's your live trading data.`
              : 'Connect your Dhan account in Settings to see live data.'}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => refetchAccount()} disabled={isAccountLoading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${isAccountLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Link href="/ai">
            <Button className="gap-2">
              <Sparkles className="h-4 w-4" />
              Ask Gemini AI
            </Button>
          </Link>
        </div>
      </div>

      {/* Tab Navigation */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full max-w-md grid-cols-2">
          <TabsTrigger value="overview" className="gap-2">
            <LayoutDashboard className="h-4 w-4" />
            Overview
          </TabsTrigger>
          <TabsTrigger value="activity" className="gap-2">
            <Activity className="h-4 w-4" />
            Activity & Trading
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6 mt-6">
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
        </TabsContent>

        <TabsContent value="activity" className="mt-6">
          {userProfile?.clientId ? (
            <ActivityDashboard userId={userProfile.clientId} />
          ) : (
            <div className="text-center py-12">
              <Activity className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
              <h3 className="text-lg font-semibold mb-2">Connect Your Account</h3>
              <p className="text-muted-foreground mb-4">
                Connect your Dhan account in Settings to view activity and enable background trading.
              </p>
              <Link href="/settings">
                <Button>Go to Settings</Button>
              </Link>
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
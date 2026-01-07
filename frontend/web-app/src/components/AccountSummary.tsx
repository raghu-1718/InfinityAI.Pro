"use client";

import { useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useUserData } from "@/hooks/useUserData";
import {
  Wallet,
  TrendingUp,
  Activity,
  RefreshCw,
  AlertCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";

interface AccountSummaryProps {
  userId: string;
}

export function AccountSummary({ userId }: AccountSummaryProps) {
  const { accountData, loading, error, fetchAccountData, hasCredentials } =
    useUserData(userId);

  if (!hasCredentials) {
    return (
      <Card className="border-amber-500/20 bg-amber-500/5">
        <CardContent className="p-6">
          <div className="flex items-center gap-4">
            <AlertCircle className="h-10 w-10 text-amber-500" />
            <div>
              <h3 className="font-semibold text-lg">Credentials Required</h3>
              <p className="text-sm text-muted-foreground">
                Please add your DhanHQ credentials in Settings to view account
                data
              </p>
              <Button variant="link" className="px-0 mt-2" asChild>
                <a href="/settings">Go to Settings →</a>
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (loading && !accountData) {
    return (
      <div className="grid md:grid-cols-4 gap-6">
        <Skeleton className="h-32" />
        <Skeleton className="h-32" />
        <Skeleton className="h-32" />
        <Skeleton className="h-32" />
      </div>
    );
  }

  if (error) {
    return (
      <Card className="border-red-500/20 bg-red-500/5">
        <CardContent className="p-6">
          <div className="flex items-center gap-4">
            <AlertCircle className="h-10 w-10 text-red-500" />
            <div>
              <h3 className="font-semibold text-lg">
                Error Loading Account Data
              </h3>
              <p className="text-sm text-muted-foreground">{error}</p>
              <Button
                variant="link"
                className="px-0 mt-2"
                onClick={() => fetchAccountData(true)}
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Retry
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!accountData) {
    return null;
  }

  const { account_summary, funds, positions, orders } = accountData;

  return (
    <div className="space-y-6">
      {/* Account Overview Cards */}
      <div className="grid md:grid-cols-4 gap-6">
        <Card className="border-cyan-500/20 bg-gradient-to-br from-cyan-500/5 to-transparent">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Wallet className="h-4 w-4 text-cyan-400" />
              Available Balance
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-white">
              ₹{funds.availabelBalance.toFixed(2)}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Withdrawable: ₹{funds.withdrawableBalance.toFixed(2)}
            </p>
          </CardContent>
        </Card>

        <Card className="border-violet-500/20 bg-gradient-to-br from-violet-500/5 to-transparent">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-violet-400" />
              Holdings Value
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-white">
              ₹{account_summary.total_holdings_value.toFixed(2)}
            </div>
            <p
              className={`text-xs mt-1 ${
                account_summary.total_holdings_pnl >= 0
                  ? "text-green-400"
                  : "text-red-400"
              }`}
            >
              P&L: ₹{account_summary.total_holdings_pnl.toFixed(2)}
            </p>
          </CardContent>
        </Card>

        <Card className="border-amber-500/20 bg-gradient-to-br from-amber-500/5 to-transparent">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Activity className="h-4 w-4 text-amber-400" />
              Positions P&L
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div
              className={`text-3xl font-bold ${
                account_summary.total_positions_pnl >= 0
                  ? "text-green-400"
                  : "text-red-400"
              }`}
            >
              ₹{account_summary.total_positions_pnl.toFixed(2)}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Open: {positions.count}
            </p>
          </CardContent>
        </Card>

        <Card
          className={`border-${
            account_summary.net_pnl >= 0 ? "green" : "red"
          }-500/20 bg-gradient-to-br from-${
            account_summary.net_pnl >= 0 ? "green" : "red"
          }-500/5 to-transparent`}
        >
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <TrendingUp
                className={`h-4 w-4 text-${
                  account_summary.net_pnl >= 0 ? "green" : "red"
                }-400`}
              />
              Net P&L
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div
              className={`text-3xl font-bold ${
                account_summary.net_pnl >= 0 ? "text-green-400" : "text-red-400"
              }`}
            >
              ₹{account_summary.net_pnl.toFixed(2)}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Realized + Unrealized
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Info */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">Account Details</CardTitle>
            <Button
              variant="outline"
              size="sm"
              onClick={() => fetchAccountData(true)}
              disabled={loading}
            >
              <RefreshCw
                className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`}
              />
              Refresh
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-2 gap-6">
            <div className="space-y-3">
              <h4 className="font-semibold text-sm text-muted-foreground">
                Funds
              </h4>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>SOD Limit</span>
                  <span className="font-mono">
                    ₹{funds.sodLimit.toFixed(2)}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Utilized Amount</span>
                  <span className="font-mono">
                    ₹{funds.utilizedAmount.toFixed(2)}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Collateral</span>
                  <span className="font-mono">
                    ₹{funds.collateralAmount.toFixed(2)}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Blocked Payout</span>
                  <span className="font-mono">
                    ₹{funds.blockedPayoutAmount.toFixed(2)}
                  </span>
                </div>
              </div>
            </div>

            <div className="space-y-3">
              <h4 className="font-semibold text-sm text-muted-foreground">
                Activity
              </h4>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Holdings</span>
                  <Badge variant="secondary">
                    {accountData.holdings.count}
                  </Badge>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Open Positions</span>
                  <Badge variant="secondary">{positions.count}</Badge>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Active Orders</span>
                  <Badge variant="secondary">{orders.count}</Badge>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Client ID</span>
                  <span className="font-mono text-xs">
                    {funds.dhanClientId}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-4 border-t">
            <p className="text-xs text-muted-foreground">
              Last updated: {new Date(accountData.timestamp).toLocaleString()}
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

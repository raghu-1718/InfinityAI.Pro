'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Activity,
  Clock,
  TrendingUp,
  Play,
  Pause,
  BarChart3,
  History,
  Zap,
  RefreshCw,
} from 'lucide-react';
import {
  useActivityLogs,
  useActivitySummary,
  useBackgroundTradingStatus,
  useStartBackgroundTrading,
  useStopBackgroundTrading,
} from '@/hooks/useApi';

interface ActivityDashboardProps {
  userId: string;
}

export function ActivityDashboard({ userId }: ActivityDashboardProps) {
  const { data: logs, isLoading: logsLoading, refetch: refetchLogs } = useActivityLogs(userId, {
    limit: 50,
  });

  const { data: summary, isLoading: summaryLoading } = useActivitySummary(userId, 7);

  const {
    data: tradingStatus,
    isLoading: statusLoading,
    refetch: refetchStatus,
  } = useBackgroundTradingStatus(userId);

  const startTrading = useStartBackgroundTrading();
  const stopTrading = useStopBackgroundTrading();

  const handleToggleTrading = async () => {
    if (tradingStatus?.is_active) {
      await stopTrading.mutateAsync(userId);
    } else {
      await startTrading.mutateAsync({
        userId,
        strategy: 'auto_options',
        config: {
          max_positions: 5,
          risk_per_trade: 0.02,
          stop_loss_percent: 5,
          take_profit_percent: 10,
        },
      });
    }
    refetchStatus();
  };

  const getActionIcon = (action: string) => {
    if (action.includes('TRADE')) return <TrendingUp className="h-4 w-4" />;
    if (action.includes('PAGE')) return <Activity className="h-4 w-4" />;
    if (action.includes('LOGIN')) return <Zap className="h-4 w-4" />;
    return <Clock className="h-4 w-4" />;
  };

  const getActionColor = (action: string) => {
    if (action.includes('ERROR')) return 'destructive';
    if (action.includes('SUCCESS') || action.includes('STARTED')) return 'default';
    if (action.includes('STOPPED')) return 'secondary';
    return 'outline';
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return date.toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="space-y-6">
      {/* Background Trading Control */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg flex items-center gap-2">
                <Zap className="h-5 w-5 text-yellow-500" />
                Background Trading
              </CardTitle>
              <CardDescription>
                Automated trading runs even when browser is closed
              </CardDescription>
            </div>
            <Button
              onClick={handleToggleTrading}
              variant={tradingStatus?.is_active ? 'destructive' : 'default'}
              disabled={startTrading.isPending || stopTrading.isPending || statusLoading}
              className="min-w-[140px]"
            >
              {startTrading.isPending || stopTrading.isPending ? (
                <RefreshCw className="h-4 w-4 animate-spin mr-2" />
              ) : tradingStatus?.is_active ? (
                <Pause className="h-4 w-4 mr-2" />
              ) : (
                <Play className="h-4 w-4 mr-2" />
              )}
              {tradingStatus?.is_active ? 'Stop Trading' : 'Start Trading'}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {statusLoading ? (
            <div className="space-y-2">
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-4 w-1/2" />
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center p-3 bg-secondary/50 rounded-lg">
                <div className="text-2xl font-bold">
                  {tradingStatus?.is_active ? (
                    <span className="text-green-500">Active</span>
                  ) : (
                    <span className="text-gray-400">Inactive</span>
                  )}
                </div>
                <div className="text-xs text-muted-foreground">Status</div>
              </div>
              <div className="text-center p-3 bg-secondary/50 rounded-lg">
                <div className="text-2xl font-bold">
                  {tradingStatus?.strategy || 'N/A'}
                </div>
                <div className="text-xs text-muted-foreground">Strategy</div>
              </div>
              <div className="text-center p-3 bg-secondary/50 rounded-lg">
                <div className="text-2xl font-bold">
                  {tradingStatus?.last_execution?.trades_executed || 0}
                </div>
                <div className="text-xs text-muted-foreground">Trades Today</div>
              </div>
              <div className="text-center p-3 bg-secondary/50 rounded-lg">
                <div className="text-sm font-medium">
                  {tradingStatus?.started_at
                    ? formatTimestamp(tradingStatus.started_at)
                    : 'Not started'}
                </div>
                <div className="text-xs text-muted-foreground">Since</div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Activity Summary */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-lg flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-blue-500" />
            Activity Summary (Last 7 Days)
          </CardTitle>
        </CardHeader>
        <CardContent>
          {summaryLoading ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[...Array(4)].map((_, i) => (
                <Skeleton key={i} className="h-20" />
              ))}
            </div>
          ) : summary ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center p-3 bg-blue-500/10 rounded-lg">
                <div className="text-2xl font-bold text-blue-500">
                  {summary.total_actions}
                </div>
                <div className="text-xs text-muted-foreground">Total Actions</div>
              </div>
              <div className="text-center p-3 bg-green-500/10 rounded-lg">
                <div className="text-2xl font-bold text-green-500">
                  {summary.daily_average}
                </div>
                <div className="text-xs text-muted-foreground">Daily Average</div>
              </div>
              <div className="text-center p-3 bg-purple-500/10 rounded-lg">
                <div className="text-lg font-bold text-purple-500">
                  {summary.most_common_action?.replace(/_/g, ' ') || 'N/A'}
                </div>
                <div className="text-xs text-muted-foreground">Most Common</div>
              </div>
              <div className="text-center p-3 bg-orange-500/10 rounded-lg">
                <div className="text-2xl font-bold text-orange-500">
                  {summary.peak_activity_hour}:00
                </div>
                <div className="text-xs text-muted-foreground">Peak Hour</div>
              </div>
            </div>
          ) : (
            <p className="text-muted-foreground text-center py-4">
              No activity data available
            </p>
          )}

          {/* Action Breakdown */}
          {summary?.actions_by_type && Object.keys(summary.actions_by_type).length > 0 && (
            <div className="mt-4 pt-4 border-t">
              <h4 className="text-sm font-medium mb-2">Actions Breakdown</h4>
              <div className="flex flex-wrap gap-2">
                {Object.entries(summary.actions_by_type)
                  .sort((a, b) => b[1] - a[1])
                  .slice(0, 8)
                  .map(([action, count]) => (
                    <Badge key={action} variant="secondary" className="text-xs">
                      {action.replace(/_/g, ' ')}: {count}
                    </Badge>
                  ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Recent Activity Log */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg flex items-center gap-2">
              <History className="h-5 w-5 text-purple-500" />
              Recent Activity (Last 24 Hours)
            </CardTitle>
            <Button variant="ghost" size="sm" onClick={() => refetchLogs()}>
              <RefreshCw className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {logsLoading ? (
            <div className="space-y-3">
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} className="h-12" />
              ))}
            </div>
          ) : ((logs as any)?.logs || (logs as any)?.activities)?.length > 0 ? (
            <ScrollArea className="h-[400px]">
              <div className="space-y-2">
                {((logs as any)?.logs || (logs as any)?.activities || []).map((log: any, index: number) => (
                  <div
                    key={log.id || index}
                    className="flex items-center justify-between p-3 bg-secondary/30 rounded-lg hover:bg-secondary/50 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-secondary rounded-full">
                        {getActionIcon(log.action || log.type || '')}
                      </div>
                      <div>
                        <p className="font-medium text-sm">
                          {(log.action || log.type || 'Unknown').replace(/_/g, ' ')}
                        </p>
                        {log.details && Object.keys(log.details).length > 0 && (
                          <p className="text-xs text-muted-foreground">
                            {String(log.details.page || log.details.symbol || log.details.strategy || JSON.stringify(log.details).slice(0, 50))}
                          </p>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant={getActionColor(log.action || log.type || '')} className="text-xs">
                        {formatTimestamp(log.timestamp)}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              <Activity className="h-12 w-12 mx-auto mb-2 opacity-50" />
              <p>No activity logged yet</p>
              <p className="text-xs">Your actions will appear here</p>
            </div>
          )}

          {logs?.total_count && logs.total_count > 50 && (
            <div className="mt-4 text-center text-sm text-muted-foreground">
              Showing 50 of {logs.total_count} activities
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default ActivityDashboard;

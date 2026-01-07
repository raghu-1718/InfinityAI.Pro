/**
 * Real-Time Trading Dashboard Component
 *
 * Displays live trading updates using Server-Sent Events (SSE)
 * Shows order status, position updates, and trade confirmations in real-time
 */

"use client";

import { useRealtimeTrading } from "@/hooks/useRealtimeTrading";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import {
  AlertCircle,
  CheckCircle,
  Clock,
  Radio,
  RefreshCw,
} from "lucide-react";
import { Button } from "@/components/ui/button";

interface RealtimeDashboardProps {
  userId: string;
  className?: string;
}

export function RealtimeDashboard({
  userId,
  className,
}: RealtimeDashboardProps) {
  const {
    connected,
    connecting,
    error,
    latestUpdate,
    events,
    eventCount,
    lastHeartbeat,
    reconnect,
    clearEvents,
  } = useRealtimeTrading(userId);

  const getStatusBadge = (status: string) => {
    const statusMap: Record<string, { variant: any; label: string }> = {
      PENDING: { variant: "secondary", label: "Pending" },
      FILLED: { variant: "default", label: "Filled" },
      PARTIAL: { variant: "secondary", label: "Partial" },
      REJECTED: { variant: "destructive", label: "Rejected" },
      CANCELLED: { variant: "outline", label: "Cancelled" },
    };

    const statusInfo = statusMap[status] || {
      variant: "outline",
      label: status,
    };
    return <Badge variant={statusInfo.variant}>{statusInfo.label}</Badge>;
  };

  const getSideBadge = (side: string) => {
    return side === "BUY" ? (
      <Badge variant="default" className="bg-green-600">
        BUY
      </Badge>
    ) : (
      <Badge variant="destructive">SELL</Badge>
    );
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  };

  return (
    <div className={className}>
      {/* Connection Status */}
      <Card className="mb-4">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium">
              Real-Time Connection
            </CardTitle>
            <div className="flex items-center gap-2">
              {connecting && (
                <div className="flex items-center gap-2 text-yellow-600">
                  <Clock className="h-4 w-4 animate-spin" />
                  <span className="text-xs">Connecting...</span>
                </div>
              )}
              {connected && (
                <div className="flex items-center gap-2 text-green-600">
                  <Radio className="h-4 w-4 animate-pulse" />
                  <span className="text-xs font-medium">Live</span>
                </div>
              )}
              {error && (
                <div className="flex items-center gap-2 text-red-600">
                  <AlertCircle className="h-4 w-4" />
                  <span className="text-xs">Offline</span>
                </div>
              )}
              {!connected && !connecting && !error && (
                <div className="flex items-center gap-2 text-gray-400">
                  <Radio className="h-4 w-4" />
                  <span className="text-xs">Idle</span>
                </div>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent className="pb-3">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>
              {eventCount} {eventCount === 1 ? "event" : "events"} received
            </span>
            {lastHeartbeat && (
              <span>
                Last heartbeat: {formatTimestamp(lastHeartbeat.toISOString())}
              </span>
            )}
          </div>
          {error && (
            <div className="mt-2 flex items-center gap-2">
              <p className="text-xs text-red-600">{error}</p>
              <Button size="sm" variant="outline" onClick={reconnect}>
                <RefreshCw className="h-3 w-3 mr-1" />
                Reconnect
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Latest Update */}
      {latestUpdate && latestUpdate.event !== "connected" && (
        <Card className="mb-4">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <CheckCircle className="h-4 w-4 text-green-600" />
              Latest Update
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">
                  Event Type
                </span>
                <Badge variant="outline">
                  {latestUpdate.event.replace("_", " ").toUpperCase()}
                </Badge>
              </div>
              {latestUpdate.data.order_id && (
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">
                    Order ID
                  </span>
                  <span className="text-xs font-mono">
                    {latestUpdate.data.order_id}
                  </span>
                </div>
              )}
              {latestUpdate.data.symbol && (
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">Symbol</span>
                  <span className="text-xs font-medium">
                    {latestUpdate.data.symbol}
                  </span>
                </div>
              )}
              {latestUpdate.data.status && (
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">Status</span>
                  {getStatusBadge(latestUpdate.data.status)}
                </div>
              )}
              {latestUpdate.data.side && (
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">Side</span>
                  {getSideBadge(latestUpdate.data.side)}
                </div>
              )}
              {latestUpdate.data.price && (
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">Price</span>
                  <span className="text-xs font-medium">
                    ₹{latestUpdate.data.price.toFixed(2)}
                  </span>
                </div>
              )}
              {latestUpdate.data.quantity && (
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">
                    Quantity
                  </span>
                  <span className="text-xs">{latestUpdate.data.quantity}</span>
                </div>
              )}
              {latestUpdate.data.filled_qty !== undefined && (
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">Filled</span>
                  <span className="text-xs">
                    {latestUpdate.data.filled_qty} /{" "}
                    {latestUpdate.data.quantity}
                  </span>
                </div>
              )}
              <div className="flex items-center justify-between pt-2 border-t">
                <span className="text-xs text-muted-foreground">Time</span>
                <span className="text-xs">
                  {formatTimestamp(latestUpdate.timestamp)}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Event History */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium">Event History</CardTitle>
            {eventCount > 0 && (
              <Button size="sm" variant="ghost" onClick={clearEvents}>
                Clear
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[400px]">
            {events.length === 0 ? (
              <div className="text-center py-8 text-sm text-muted-foreground">
                No events yet. Waiting for real-time updates...
              </div>
            ) : (
              <div className="space-y-2">
                {events.map((event, index) => (
                  <div key={index}>
                    <div className="p-3 rounded-lg bg-muted/50">
                      <div className="flex items-center justify-between mb-2">
                        <Badge variant="outline" className="text-xs">
                          {event.event.replace("_", " ").toUpperCase()}
                        </Badge>
                        <span className="text-xs text-muted-foreground">
                          {formatTimestamp(event.timestamp)}
                        </span>
                      </div>
                      <div className="space-y-1">
                        {event.data.order_id && (
                          <div className="text-xs">
                            <span className="text-muted-foreground">
                              Order:
                            </span>{" "}
                            <span className="font-mono">
                              {event.data.order_id}
                            </span>
                          </div>
                        )}
                        {event.data.symbol && (
                          <div className="text-xs">
                            <span className="text-muted-foreground">
                              Symbol:
                            </span>{" "}
                            <span className="font-medium">
                              {event.data.symbol}
                            </span>
                          </div>
                        )}
                        {event.data.status && (
                          <div className="text-xs flex items-center gap-2">
                            <span className="text-muted-foreground">
                              Status:
                            </span>
                            {getStatusBadge(event.data.status)}
                          </div>
                        )}
                        {event.data.side && (
                          <div className="text-xs flex items-center gap-2">
                            <span className="text-muted-foreground">Side:</span>
                            {getSideBadge(event.data.side)}
                          </div>
                        )}
                      </div>
                    </div>
                    {index < events.length - 1 && (
                      <Separator className="my-2" />
                    )}
                  </div>
                ))}
              </div>
            )}
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}

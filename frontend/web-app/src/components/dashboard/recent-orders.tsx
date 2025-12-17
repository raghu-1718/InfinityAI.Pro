'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useOrders } from '@/hooks/useApi';
import { Clock, CheckCircle, XCircle, AlertCircle, ChevronRight } from 'lucide-react';
import { formatCurrency, formatRelativeTime } from '@/lib/format';
import Link from 'next/link';

type Order = { orderId?: string; tradingSymbol?: string; securityId?: string; transactionType?: string; quantity?: number; price?: number; orderStatus?: string; createTime?: string };

export function RecentOrdersCard() {
  const { data, isLoading, error } = useOrders();

  if (isLoading) {
    return <RecentOrdersSkeleton />;
  }

  const orders: Order[] = Array.isArray(data?.data) ? data.data : [];

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Recent Orders</CardTitle>
          <Link href="/history">
            <Button variant="ghost" size="sm">
              View All
              <ChevronRight className="ml-1 h-4 w-4" />
            </Button>
          </Link>
        </div>
      </CardHeader>
      <CardContent>
        {orders.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <Clock className="h-12 w-12 text-muted-foreground/50" />
            <p className="mt-2 text-sm text-muted-foreground">No recent orders</p>
            <Link href="/trading">
              <Button variant="outline" size="sm" className="mt-4">
                Place an Order
              </Button>
            </Link>
          </div>
        ) : (
          <ScrollArea className="h-[300px]">
            <div className="space-y-2">
              {orders.slice(0, 10).map((order: Order, idx: number) => (
                <OrderRow key={order.orderId || idx} order={order} />
              ))}
            </div>
          </ScrollArea>
        )}
      </CardContent>
    </Card>
  );
}

function OrderRow({ order }: { order: Order }) {
  const statusConfig: Record<string, { icon: React.ComponentType<{ className?: string }>; color: string; bgColor: string }> = {
    TRADED: { icon: CheckCircle, color: 'text-green-600', bgColor: 'bg-green-100 dark:bg-green-900/30' },
    PENDING: { icon: Clock, color: 'text-yellow-600', bgColor: 'bg-yellow-100 dark:bg-yellow-900/30' },
    REJECTED: { icon: XCircle, color: 'text-red-600', bgColor: 'bg-red-100 dark:bg-red-900/30' },
    CANCELLED: { icon: XCircle, color: 'text-gray-600', bgColor: 'bg-gray-100 dark:bg-gray-800' },
  };

  const status = order.orderStatus || 'PENDING';
  const config = statusConfig[status] || statusConfig.PENDING;
  const Icon = config.icon;

  return (
    <div className="flex items-center justify-between rounded-lg border p-3 transition-colors hover:bg-muted/50">
      <div className="flex items-center gap-3">
        <div className={`rounded-lg p-2 ${config.bgColor}`}>
          <Icon className={`h-4 w-4 ${config.color}`} />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <p className="font-medium">{order.tradingSymbol || order.securityId}</p>
            <Badge
              variant="outline"
              className={
                order.transactionType === 'BUY'
                  ? 'border-green-500 text-green-600'
                  : 'border-red-500 text-red-600'
              }
            >
              {order.transactionType}
            </Badge>
          </div>
          <p className="text-xs text-muted-foreground">
            {order.quantity} qty @ {formatCurrency(order.price || 0)}
          </p>
        </div>
      </div>
      <div className="text-right">
        <Badge variant={status === 'TRADED' ? 'default' : 'secondary'} className="text-xs">
          {status}
        </Badge>
        {order.createTime && (
          <p className="mt-1 text-xs text-muted-foreground">
            {formatRelativeTime(order.createTime)}
          </p>
        )}
      </div>
    </div>
  );
}

function RecentOrdersSkeleton() {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Recent Orders</CardTitle>
          <Skeleton className="h-8 w-20" />
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="flex items-center justify-between rounded-lg border p-3">
              <div className="flex items-center gap-3">
                <Skeleton className="h-10 w-10 rounded-lg" />
                <div className="space-y-1">
                  <Skeleton className="h-4 w-24" />
                  <Skeleton className="h-3 w-20" />
                </div>
              </div>
              <Skeleton className="h-5 w-16" />
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useOrders } from '@/hooks/useApi';
import { formatCurrency, formatDateTime } from '@/lib/format';
import {
  History,
  Search,
  Filter,
  CheckCircle,
  XCircle,
  Clock,
  AlertCircle,
  ArrowUpCircle,
  ArrowDownCircle,
  RefreshCw,
} from 'lucide-react';
import { cn } from '@/lib/utils';

// Order type definition
interface Order {
  orderId?: string;
  symbol: string;
  transactionType: 'BUY' | 'SELL';
  orderType: 'LIMIT' | 'MARKET' | 'SL' | 'SL-M';
  quantity: number;
  price?: number;
  status: 'PENDING' | 'OPEN' | 'FILLED' | 'CANCELLED' | 'REJECTED';
  timestamp: string;
  filledQty?: number;
  avgPrice?: number;
}

export default function HistoryPage() {
  const { data: ordersData, isLoading, refetch, isFetching } = useOrders();
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');

  const orders = ordersData?.data || [];

  // Filter orders
  const filteredOrders = orders.filter((order: any) => {
    const matchesSearch =
      !searchQuery ||
      order.tradingSymbol?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      order.orderId?.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesStatus =
      statusFilter === 'all' || order.orderStatus?.toLowerCase() === statusFilter.toLowerCase();

    const matchesType =
      typeFilter === 'all' || order.transactionType?.toLowerCase() === typeFilter.toLowerCase();

    return matchesSearch && matchesStatus && matchesType;
  });

  // Group orders by date
  const ordersByDate = filteredOrders.reduce((acc: Record<string, any[]>, order: any) => {
    const date = order.createTime
      ? new Date(order.createTime).toLocaleDateString('en-IN', {
          day: '2-digit',
          month: 'short',
          year: 'numeric',
        })
      : 'Unknown Date';
    if (!acc[date]) acc[date] = [];
    acc[date].push(order);
    return acc;
  }, {});

  return (
    <div className="p-6 space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Order History</h1>
          <p className="text-muted-foreground">
            View and track all your past orders
          </p>
        </div>
        <Button onClick={() => refetch()} variant="outline" disabled={isFetching}>
          <RefreshCw className={cn('mr-2 h-4 w-4', isFetching && 'animate-spin')} />
          Refresh
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col gap-4 md:flex-row md:items-center">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search by symbol or order ID..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9"
              />
            </div>
            <div className="flex gap-2">
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-[130px]">
                  <Filter className="mr-2 h-4 w-4" />
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="traded">Traded</SelectItem>
                  <SelectItem value="pending">Pending</SelectItem>
                  <SelectItem value="rejected">Rejected</SelectItem>
                  <SelectItem value="cancelled">Cancelled</SelectItem>
                </SelectContent>
              </Select>
              <Select value={typeFilter} onValueChange={setTypeFilter}>
                <SelectTrigger className="w-[130px]">
                  <SelectValue placeholder="Type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  <SelectItem value="buy">Buy</SelectItem>
                  <SelectItem value="sell">Sell</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Orders Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg">Orders</CardTitle>
              <CardDescription>
                {filteredOrders.length} orders found
              </CardDescription>
            </div>
            <OrderStats orders={orders} />
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3, 4, 5].map((i) => (
                <Skeleton key={i} className="h-16 w-full" />
              ))}
            </div>
          ) : filteredOrders.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <History className="h-12 w-12 text-muted-foreground/50" />
              <p className="mt-2 text-muted-foreground">No orders found</p>
              <p className="text-xs text-muted-foreground">
                {orders.length === 0
                  ? 'Start trading to see your order history'
                  : 'Try adjusting your filters'}
              </p>
            </div>
          ) : (
            <ScrollArea className="h-[500px]">
              {Object.entries(ordersByDate).map(([date, dateOrders]) => {
                const orders = dateOrders as Order[];
                return (
                  <div key={date} className="mb-6">
                    <div className="mb-3 flex items-center gap-2">
                      <Badge variant="secondary">{date}</Badge>
                      <span className="text-xs text-muted-foreground">
                        {orders.length} orders
                      </span>
                    </div>
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Symbol</TableHead>
                          <TableHead>Type</TableHead>
                          <TableHead>Qty</TableHead>
                          <TableHead>Price</TableHead>
                          <TableHead>Status</TableHead>
                          <TableHead>Time</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {orders.map((order: Order, idx: number) => (
                          <OrderRow key={order.orderId || idx} order={order} />
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                );
              })}
            </ScrollArea>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function OrderStats({ orders }: { orders: any[] }) {
  const stats = orders.reduce(
    (acc, order) => {
      if (order.orderStatus === 'TRADED') acc.traded++;
      if (order.orderStatus === 'PENDING') acc.pending++;
      if (order.orderStatus === 'REJECTED') acc.rejected++;
      if (order.transactionType === 'BUY') acc.buys++;
      if (order.transactionType === 'SELL') acc.sells++;
      return acc;
    },
    { traded: 0, pending: 0, rejected: 0, buys: 0, sells: 0 }
  );

  return (
    <div className="flex gap-3">
      <Badge variant="outline" className="border-green-500 text-green-600">
        <CheckCircle className="mr-1 h-3 w-3" />
        {stats.traded} Traded
      </Badge>
      <Badge variant="outline" className="border-yellow-500 text-yellow-600">
        <Clock className="mr-1 h-3 w-3" />
        {stats.pending} Pending
      </Badge>
      <Badge variant="outline" className="border-red-500 text-red-600">
        <XCircle className="mr-1 h-3 w-3" />
        {stats.rejected} Rejected
      </Badge>
    </div>
  );
}

function OrderRow({ order }: { order: any }) {
  const status = order.orderStatus || 'PENDING';
  const isBuy = order.transactionType === 'BUY';

  const statusConfig: Record<string, { icon: any; color: string; bgColor: string }> = {
    TRADED: {
      icon: CheckCircle,
      color: 'text-green-600',
      bgColor: 'bg-green-100 dark:bg-green-900/30',
    },
    PENDING: {
      icon: Clock,
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-100 dark:bg-yellow-900/30',
    },
    REJECTED: {
      icon: XCircle,
      color: 'text-red-600',
      bgColor: 'bg-red-100 dark:bg-red-900/30',
    },
    CANCELLED: {
      icon: XCircle,
      color: 'text-gray-600',
      bgColor: 'bg-gray-100 dark:bg-gray-800',
    },
  };

  const config = statusConfig[status] || statusConfig.PENDING;
  const StatusIcon = config.icon;

  return (
    <TableRow>
      <TableCell>
        <div className="flex items-center gap-2">
          <div className={cn('rounded p-1', isBuy ? 'bg-green-100 dark:bg-green-900/30' : 'bg-red-100 dark:bg-red-900/30')}>
            {isBuy ? (
              <ArrowUpCircle className="h-4 w-4 text-green-600" />
            ) : (
              <ArrowDownCircle className="h-4 w-4 text-red-600" />
            )}
          </div>
          <div>
            <p className="font-medium">{order.tradingSymbol || order.securityId}</p>
            <p className="text-xs text-muted-foreground font-mono">{order.orderId?.slice(0, 8)}...</p>
          </div>
        </div>
      </TableCell>
      <TableCell>
        <Badge
          variant="outline"
          className={isBuy ? 'border-green-500 text-green-600' : 'border-red-500 text-red-600'}
        >
          {order.transactionType}
        </Badge>
      </TableCell>
      <TableCell className="font-mono">{order.quantity}</TableCell>
      <TableCell className="font-mono">{formatCurrency(order.price || 0)}</TableCell>
      <TableCell>
        <div className="flex items-center gap-2">
          <div className={cn('rounded p-1', config.bgColor)}>
            <StatusIcon className={cn('h-3 w-3', config.color)} />
          </div>
          <span className={cn('text-sm', config.color)}>{status}</span>
        </div>
      </TableCell>
      <TableCell className="text-muted-foreground text-sm">
        {order.createTime
          ? new Date(order.createTime).toLocaleTimeString('en-IN', {
              hour: '2-digit',
              minute: '2-digit',
            })
          : '--'}
      </TableCell>
    </TableRow>
  );
}

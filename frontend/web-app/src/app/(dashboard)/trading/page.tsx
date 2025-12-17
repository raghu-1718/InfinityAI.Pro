'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Separator } from '@/components/ui/separator';
import { usePositions, useHoldings, usePlaceOrder, useCalculateRiskScore, Holding } from '@/hooks/useApi';

// Minimal Position type for this page
type Position = {
  securityId?: string;
  tradingSymbol?: string;
  realizedProfit?: number;
  netQty?: number;
  averagePrice?: number;
  productType?: string;
  ltp?: number;
  avgCostPrice?: number;
  totalQty?: number;
};
import { useAppStore } from '@/lib/store';
import { formatCurrency, formatPercent } from '@/lib/format';
import {
  TrendingUp,
  TrendingDown,
  ArrowUpCircle,
  ArrowDownCircle,
  Calculator,
  AlertTriangle,
  Loader2,
  CheckCircle
} from 'lucide-react';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';

const symbols = [
  { value: '1333', label: 'RELIANCE', name: 'Reliance Industries' },
  { value: '2968', label: 'TCS', name: 'Tata Consultancy Services' },
  { value: '1394', label: 'HDFCBANK', name: 'HDFC Bank' },
  { value: '1594', label: 'INFY', name: 'Infosys' },
  { value: '1270', label: 'ICICIBANK', name: 'ICICI Bank' },
];

const productTypes = [
  { value: 'INTRADAY', label: 'Intraday' },
  { value: 'CNC', label: 'Delivery (CNC)' },
  { value: 'MARGIN', label: 'Margin' },
];

const orderTypes = [
  { value: 'MARKET', label: 'Market' },
  { value: 'LIMIT', label: 'Limit' },
  { value: 'SL', label: 'Stop Loss' },
  { value: 'SL-M', label: 'SL-Market' },
];

export default function TradingPage() {
  const funds = useAppStore((s) => s.funds);
  const [orderType, setOrderType] = useState<'BUY' | 'SELL'>('BUY');
  const [securityId, setSecurityId] = useState('1333');
  const [quantity, setQuantity] = useState('1');
  const [price, setPrice] = useState('0');
  const [productType, setProductType] = useState('INTRADAY');
  const [orderTypeValue, setOrderTypeValue] = useState('MARKET');
  const [useAIRisk, setUseAIRisk] = useState(true);

  const { mutate: placeOrder, isPending: isPlacing } = usePlaceOrder();
  const { mutateAsync: calculateRisk, isPending: isCalculatingRisk } = useCalculateRiskScore();
  const { data: positionsData } = usePositions();
  const { data: holdingsData } = useHoldings();

  // Safely handle positions data - ensure it's always an array
  const positionsRaw = positionsData?.data;
  const positions = Array.isArray(positionsRaw) ? positionsRaw : [];

  // Safely handle holdings data - ensure it's always an array
  const holdingsRaw = holdingsData?.data;
  const holdings = Array.isArray(holdingsRaw) ? holdingsRaw : [];

  const handlePlaceOrder = async () => {
    // Optional risk check
    if (useAIRisk) {
      try {
        const riskResult = await calculateRisk({
          position_size: parseFloat(quantity) * parseFloat(price || '1000'),
          volatility: 0.2,
          max_drawdown: 0.05,
        });

        if (riskResult.risk_level === 'HIGH') {
          toast.warning('High Risk Trade', {
            description: `Risk score: ${riskResult.risk_score.toFixed(2)}. Proceed with caution.`,
          });
        }
      } catch (e) {
        console.error('Risk check failed:', e);
      }
    }

    placeOrder(
      {
        transaction_type: orderType,
        exchange_segment: 'NSE_EQ',
        product_type: productType,
        order_type: orderTypeValue,
        validity: 'DAY',
        security_id: securityId,
        quantity: parseInt(quantity) || 1,
        price: parseFloat(price) || 0,
      },
      {
        onSuccess: (data) => {
          if (data.status === 'success') {
            toast.success('Order Placed', {
              description: `${orderType} order for ${quantity} qty submitted successfully`,
            });
          } else {
            toast.error('Order Failed', {
              description: data.message || 'Unknown error',
            });
          }
        },
        onError: (error) => {
          toast.error('Order Error', {
            description: error.message || 'Failed to place order',
          });
        },
      }
    );
  };

  const selectedSymbol = symbols.find(s => s.value === securityId);

  return (
    <div className="p-6 space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Trading</h1>
          <p className="text-muted-foreground">
            Place orders and manage your positions
          </p>
        </div>
        {funds && (
          <Card className="w-fit">
            <CardContent className="flex items-center gap-4 p-4">
              <div>
                <p className="text-xs text-muted-foreground">Available Balance</p>
                <p className="text-xl font-bold text-green-600">
                  {formatCurrency(funds.availableBalance)}
                </p>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Order Form */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle>Place Order</CardTitle>
              <CardDescription>
                {selectedSymbol?.name || 'Select a symbol'}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Buy/Sell Toggle */}
              <div className="grid grid-cols-2 gap-2">
                <Button
                  variant={orderType === 'BUY' ? 'default' : 'outline'}
                  className={cn(
                    'h-12',
                    orderType === 'BUY' && 'bg-green-600 hover:bg-green-700'
                  )}
                  onClick={() => setOrderType('BUY')}
                >
                  <ArrowUpCircle className="mr-2 h-5 w-5" />
                  BUY
                </Button>
                <Button
                  variant={orderType === 'SELL' ? 'default' : 'outline'}
                  className={cn(
                    'h-12',
                    orderType === 'SELL' && 'bg-red-600 hover:bg-red-700'
                  )}
                  onClick={() => setOrderType('SELL')}
                >
                  <ArrowDownCircle className="mr-2 h-5 w-5" />
                  SELL
                </Button>
              </div>

              {/* Symbol Select */}
              <div className="space-y-2">
                <Label>Symbol</Label>
                <Select value={securityId} onValueChange={setSecurityId}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select symbol" />
                  </SelectTrigger>
                  <SelectContent>
                    {symbols.map((s) => (
                      <SelectItem key={s.value} value={s.value}>
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{s.label}</span>
                          <span className="text-xs text-muted-foreground">({s.name})</span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Quantity */}
              <div className="space-y-2">
                <Label>Quantity</Label>
                <Input
                  type="number"
                  value={quantity}
                  onChange={(e) => setQuantity(e.target.value)}
                  min="1"
                  placeholder="Enter quantity"
                />
              </div>

              {/* Product Type */}
              <div className="space-y-2">
                <Label>Product Type</Label>
                <Select value={productType} onValueChange={setProductType}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {productTypes.map((p) => (
                      <SelectItem key={p.value} value={p.value}>
                        {p.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Order Type */}
              <div className="space-y-2">
                <Label>Order Type</Label>
                <Select value={orderTypeValue} onValueChange={setOrderTypeValue}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {orderTypes.map((o) => (
                      <SelectItem key={o.value} value={o.value}>
                        {o.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Price (for Limit orders) */}
              {orderTypeValue !== 'MARKET' && (
                <div className="space-y-2">
                  <Label>Price</Label>
                  <Input
                    type="number"
                    value={price}
                    onChange={(e) => setPrice(e.target.value)}
                    placeholder="Enter price"
                  />
                </div>
              )}

              <Separator />

              {/* AI Risk Check */}
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>AI Risk Check</Label>
                  <p className="text-xs text-muted-foreground">
                    Analyze risk before placing order
                  </p>
                </div>
                <Switch checked={useAIRisk} onCheckedChange={setUseAIRisk} />
              </div>

              {/* Place Order Button */}
              <Button
                className={cn(
                  'w-full h-12',
                  orderType === 'BUY' ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'
                )}
                onClick={handlePlaceOrder}
                disabled={isPlacing || isCalculatingRisk}
              >
                {isPlacing || isCalculatingRisk ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    {isCalculatingRisk ? 'Checking Risk...' : 'Placing Order...'}
                  </>
                ) : (
                  <>
                    {orderType === 'BUY' ? (
                      <ArrowUpCircle className="mr-2 h-5 w-5" />
                    ) : (
                      <ArrowDownCircle className="mr-2 h-5 w-5" />
                    )}
                    {orderType} {selectedSymbol?.label}
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Positions & Holdings */}
        <div className="lg:col-span-2">
          <Tabs defaultValue="positions" className="w-full">
            <TabsList className="w-full">
              <TabsTrigger value="positions" className="flex-1">
                Positions
                {positions.length > 0 && (
                  <Badge variant="secondary" className="ml-2">
                    {positions.length}
                  </Badge>
                )}
              </TabsTrigger>
              <TabsTrigger value="holdings" className="flex-1">
                Holdings
                {holdings.length > 0 && (
                  <Badge variant="secondary" className="ml-2">
                    {holdings.length}
                  </Badge>
                )}
              </TabsTrigger>
            </TabsList>

            <TabsContent value="positions" className="mt-4">
              <Card>
                <CardContent className="p-4">
                  {positions.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-12 text-center">
                      <TrendingUp className="h-12 w-12 text-muted-foreground/50" />
                      <p className="mt-2 text-muted-foreground">No open positions</p>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {positions.map((pos: Position, idx: number) => (
                        <PositionRow key={pos.securityId || idx} position={pos} />
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="holdings" className="mt-4">
              <Card>
                <CardContent className="p-4">
                  {holdings.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-12 text-center">
                      <TrendingUp className="h-12 w-12 text-muted-foreground/50" />
                      <p className="mt-2 text-muted-foreground">No holdings</p>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {holdings.map((holding: Holding, idx: number) => (
                        <HoldingRow key={holding.securityId || idx} holding={holding} />
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}

function PositionRow({ position }: { position: Position }) {
  const pnl = position.realizedProfit || 0;
  const isProfit = pnl >= 0;

  return (
    <div className="flex items-center justify-between rounded-lg border p-4 transition-colors hover:bg-muted/50">
      <div className="flex items-center gap-3">
        <div className={cn(
          'rounded-lg p-2',
          isProfit ? 'bg-green-100 dark:bg-green-900/30' : 'bg-red-100 dark:bg-red-900/30'
        )}>
          {isProfit ? (
            <TrendingUp className="h-4 w-4 text-green-600 dark:text-green-400" />
          ) : (
            <TrendingDown className="h-4 w-4 text-red-600 dark:text-red-400" />
          )}
        </div>
        <div>
          <p className="font-medium">{position.tradingSymbol || position.securityId}</p>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <span>{position.netQty} qty</span>
            <span>@</span>
            <span>{formatCurrency(position.averagePrice || 0)}</span>
          </div>
        </div>
      </div>
      <div className="text-right">
        <p className={cn(
          'font-mono font-semibold',
          isProfit ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
        )}>
          {formatCurrency(pnl)}
        </p>
        <Badge variant={isProfit ? 'default' : 'destructive'} className="text-xs">
          {position.productType}
        </Badge>
      </div>
    </div>
  );
}

function HoldingRow({ holding }: { holding: Holding }) {
  const pnl = (holding.ltp - holding.avgCostPrice) * holding.totalQty;
  const pnlPercent = ((holding.ltp - holding.avgCostPrice) / holding.avgCostPrice) * 100;
  const isProfit = pnl >= 0;

  return (
    <div className="flex items-center justify-between rounded-lg border p-4 transition-colors hover:bg-muted/50">
      <div className="flex items-center gap-3">
        <div className={cn(
          'rounded-lg p-2',
          isProfit ? 'bg-green-100 dark:bg-green-900/30' : 'bg-red-100 dark:bg-red-900/30'
        )}>
          {isProfit ? (
            <TrendingUp className="h-4 w-4 text-green-600 dark:text-green-400" />
          ) : (
            <TrendingDown className="h-4 w-4 text-red-600 dark:text-red-400" />
          )}
        </div>
        <div>
          <p className="font-medium">{holding.tradingSymbol || holding.securityId}</p>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <span>{holding.totalQty} qty</span>
            <span>@</span>
            <span>{formatCurrency(holding.avgCostPrice || 0)}</span>
          </div>
        </div>
      </div>
      <div className="text-right">
        <p className={cn(
          'font-mono font-semibold',
          isProfit ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
        )}>
          {formatCurrency(pnl)} ({formatPercent(pnlPercent)})
        </p>
        <p className="text-xs text-muted-foreground">
          LTP: {formatCurrency(holding.ltp || 0)}
        </p>
      </div>
    </div>
  );
}

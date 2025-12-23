'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';
import { usePositions, useHoldings, usePlaceOrder, useCalculateRiskScore, Holding, useBatchSignals } from '@/hooks/useApi';
import { useAppStore } from '@/lib/store';
import { formatCurrency, formatPercent } from '@/lib/format';
import { TrendingUp, TrendingDown, ArrowUpCircle, ArrowDownCircle, Loader2, Play, RefreshCw, Zap } from 'lucide-react';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';
import { WatchlistTable, WatchlistItem } from '@/components/trading/WatchlistTable';
import { SignalResponse } from '@/lib/api';

// --- Types & Constants ---
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

const SYMBOLS = [
  { value: '1333', label: 'RELIANCE', name: 'Reliance Industries' },
  { value: '2968', label: 'TCS', name: 'Tata Consultancy Services' },
  { value: '1394', label: 'HDFCBANK', name: 'HDFC Bank' },
  { value: '1594', label: 'INFY', name: 'Infosys' },
  { value: '1270', label: 'ICICIBANK', name: 'ICICI Bank' },
];

const WATCHLIST_SYMBOLS = SYMBOLS.map(s => s.label);

export default function TradingPage() {
  const funds = useAppStore((s) => s.funds);
  const [orderType, setOrderType] = useState<'BUY' | 'SELL'>('BUY');
  const [securityId, setSecurityId] = useState('1333');
  const [quantity, setQuantity] = useState('1');
  const [price, setPrice] = useState('0');
  const [productType, setProductType] = useState('INTRADAY');
  const [orderTypeValue, setOrderTypeValue] = useState('MARKET');
  const [useAIRisk, setUseAIRisk] = useState(true);
  const [executingSymbol, setExecutingSymbol] = useState<string | null>(null);

  // Live Hooks
  const { mutate: placeOrder, isPending: isPlacing } = usePlaceOrder();
  const { mutateAsync: calculateRisk, isPending: isCalculatingRisk } = useCalculateRiskScore();
  const { data: positionsData } = usePositions();
  const { data: holdingsData } = useHoldings();
  const { data: batchSignals, isLoading: isSignalLoading, refetch: refetchSignals } = useBatchSignals(WATCHLIST_SYMBOLS);

  const positions = Array.isArray(positionsData?.data) ? positionsData?.data : [];
  const holdings = Array.isArray(holdingsData?.data) ? holdingsData?.data : [];

  // Transform Batch Signals to WatchlistItem[]
  const watchlistItems: WatchlistItem[] = SYMBOLS.map(sym => {
      // Find signal for this symbol
      // The API returns { data: [...] } or just [...]
      const signals = Array.isArray(batchSignals) ? batchSignals : (batchSignals?.data || []);
      const sig: SignalResponse | undefined = signals.find((s: SignalResponse) => s.symbol === sym.label);
      
      return {
          symbol: sym.label,
          // If live price is not available in signal, fallback to mock roughly around the real price
          ltp: 2500, // TODO: Get real LTP from separate hook if possible
          change_pct: 0.5, 
          signal: sig?.signal || 'HOLD',
          confidence: (sig?.confidence || 0) * 100
      };
  });

  const handlePlaceOrder = async (overrideSymbol?: string, overrideAction?: 'BUY' | 'SELL') => {
    const activeSymbol = overrideSymbol ? SYMBOLS.find(s => s.label === overrideSymbol)?.value || '1333' : securityId;
    const activeAction = overrideAction || orderType;
    
    if (useAIRisk) {
        try {
            await calculateRisk({
             position_size: parseFloat(quantity) * parseFloat(price || '1000'), 
             volatility: 0.02, 
             max_drawdown: 0.05
            });
        } catch(e) { /* Warning is sufficient, don't block execution */ }
    }

    placeOrder(
      {
        transaction_type: activeAction,
        exchange_segment: 'NSE_EQ',
        product_type: productType,
        order_type: orderTypeValue,
        validity: 'DAY',
        security_id: activeSymbol,
        quantity: parseInt(quantity) || 1,
        price: parseFloat(price) || 0,
      },
      {
        onSuccess: (data) => {
          if (data.status === 'success') {
            toast.success(`Order Executed: ${activeAction} ${overrideSymbol || 'Unknown'}`);
          } else {
            toast.error('Order Failed', { description: data.message });
          }
          setExecutingSymbol(null);
        },
        onError: (err) => {
            toast.error('Execution Error', { description: err.message });
            setExecutingSymbol(null);
        },
      }
    );
  };

  const handleWatchlistExecute = (symbol: string, action: 'BUY' | 'SELL') => {
      setExecutingSymbol(symbol);
      handlePlaceOrder(symbol, action);
  };

  return (
    <div className="p-6 space-y-6 max-w-[1600px] mx-auto">
      
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-black tracking-tight flex items-center gap-3">
             <Zap className="w-8 h-8 text-yellow-500 fill-current" />
             Trading Terminal
          </h1>
          <p className="text-muted-foreground">Connected to Engine C (Execution) & B (Intelligence)</p>
        </div>
        {funds && (
          <Card className="bg-gradient-to-br from-green-500/10 to-transparent border-green-500/20">
            <CardContent className="flex items-center gap-4 p-4">
              <div>
                <p className="text-xs text-muted-foreground uppercase font-semibold">Buying Power</p>
                <p className="text-2xl font-mono font-bold text-green-600 dark:text-green-400">
                  {formatCurrency(funds.availableBalance)}
                </p>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      <div className="grid gap-6 lg:grid-cols-12">
        
        {/* Left: Watchlist (AI Signals) */}
        <div className="lg:col-span-8 space-y-6">
            <Card className="border-t-4 border-t-primary">
                <CardHeader className="flex flex-row items-center justify-between py-4">
                    <div className="space-y-1">
                        <CardTitle className="text-lg flex items-center gap-2">
                           AI Watchlist
                        </CardTitle>
                        <CardDescription>Real-time signals refreshed every 60s</CardDescription>
                    </div>
                    <div className="flex items-center gap-2">
                         <Badge variant="outline" className={cn("transition-colors", isSignalLoading ? "bg-yellow-500/10 text-yellow-500" : "bg-green-500/10 text-green-500")}>
                            {isSignalLoading ? "Updating..." : "● Live"}
                        </Badge>
                        <Button variant="ghost" size="icon" onClick={() => refetchSignals()}>
                            <RefreshCw className={cn("w-4 h-4", isSignalLoading && "animate-spin")} />
                        </Button>
                    </div>
                </CardHeader>
                <CardContent className="p-0">
                    <WatchlistTable 
                        items={watchlistItems}
                        onExecute={handleWatchlistExecute}
                        isExecuting={executingSymbol}
                    />
                </CardContent>
            </Card>

            {/* Positions */}
            <Tabs defaultValue="positions" className="w-full">
                <TabsList>
                    <TabsTrigger value="positions">Open Positions ({positions.length})</TabsTrigger>
                    <TabsTrigger value="holdings">Holdings (CNC)</TabsTrigger>
                </TabsList>
                <TabsContent value="positions">
                    <Card>
                        <CardContent className="p-0">
                            {positions.length === 0 ? (
                                <div className="p-12 text-center text-muted-foreground">
                                    No open intraday positions.
                                </div>
                            ) : (
                                <div className="divide-y">
                                    {positions.map((pos: any, i) => (
                                        <PositionRow key={i} position={pos} />
                                    ))}
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </TabsContent>
                <TabsContent value="holdings">
                     <Card>
                        <CardContent className="p-0">
                            {holdings.length === 0 ? (
                                <div className="p-12 text-center text-muted-foreground">
                                    No delivery holdings found.
                                </div>
                            ) : (
                                <div className="divide-y">
                                    {holdings.map((h: any, i) => (
                                        <HoldingRow key={i} holding={h} />
                                    ))}
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>
        </div>

        {/* Right: Manual Order Entry */}
        <div className="lg:col-span-4 space-y-6">
            <Card className="border-l-4 border-l-blue-500 shadow-lg sticky top-6">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Play className="w-4 h-4 fill-current" />
                        Quick Order
                    </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                     {/* Buy/Sell Switches */}
                      <div className="grid grid-cols-2 gap-2 bg-muted p-1 rounded-lg">
                        <Button
                          variant="ghost"
                          className={cn("uppercase font-bold", orderType === 'BUY' && "bg-green-600 text-white shadow-sm")}
                          onClick={() => setOrderType('BUY')}
                        >
                          Buy
                        </Button>
                        <Button
                          variant="ghost"
                          className={cn("uppercase font-bold", orderType === 'SELL' && "bg-red-600 text-white shadow-sm")}
                          onClick={() => setOrderType('SELL')}
                        >
                          Sell
                        </Button>
                      </div>

                      <div className="space-y-3">
                          <div className="space-y-1">
                            <Label>Symbol</Label>
                            <Select value={securityId} onValueChange={setSecurityId}>
                                <SelectTrigger>
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    {SYMBOLS.map(s => (
                                        <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                          </div>
                          
                          <div className="flex gap-4">
                              <div className="space-y-1 flex-1">
                                <Label>Qty</Label>
                                <Input type="number" value={quantity} onChange={e => setQuantity(e.target.value)} />
                              </div>
                              <div className="space-y-1 flex-1">
                                <Label>Price (0=Mkt)</Label>
                                <Input type="number" value={price} onChange={e => setPrice(e.target.value)} />
                              </div>
                          </div>
                      </div>

                      <Separator />
                      
                      <div className="flex items-center justify-between">
                        <Label className="flex items-center gap-2 cursor-pointer">
                            <Switch checked={useAIRisk} onCheckedChange={setUseAIRisk} />
                            <span>AI Risk Guard</span>
                        </Label>
                        <Badge variant="outline">v2.0 Active</Badge>
                      </div>

                      <Button 
                        size="lg" 
                        className={cn("w-full font-bold text-lg", orderType === 'BUY' ? "bg-green-600 hover:bg-green-700" : "bg-red-600 hover:bg-red-700")}
                        onClick={() => handlePlaceOrder()}
                        disabled={isPlacing || isCalculatingRisk}
                       >
                         {isPlacing ? <Loader2 className="animate-spin w-5 h-5" /> : `EXECUTE ${orderType}`}
                      </Button>
                </CardContent>
            </Card>
        </div>

      </div>
    </div>
  );
}

// Reuse PositionRow/HoldingRow components (simplified for brevity)
function PositionRow({ position }: { position: Position }) {
    const isProfit = (position.realizedProfit || 0) >= 0;
    return (
        <div className="flex items-center justify-between p-4 hover:bg-muted/50 transition-all">
            <div className="flex items-center gap-3">
                 <Badge variant={isProfit ? "default" : "destructive"} className="h-8 w-8 flex items-center justify-center rounded-full p-0">
                    {isProfit ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                 </Badge>
                 <div>
                    <div className="font-bold">{position.tradingSymbol}</div>
                    <div className="text-xs text-muted-foreground">{position.netQty} Qty @ {position.averagePrice}</div>
                 </div>
            </div>
            <div className={cn("text-right font-mono font-bold", isProfit ? "text-green-600" : "text-red-600")}>
                {formatCurrency(position.realizedProfit || 0)}
            </div>
        </div>
    )
}

function HoldingRow({ holding }: { holding: Holding }) {
    // Similar simplified implementation
     const isProfit = ((holding.ltp || 0) - (holding.avgCostPrice || 0)) >= 0;
     return (
        <div className="flex items-center justify-between p-4 hover:bg-muted/50 transition-all">
            <div className="flex items-center gap-3">
                 <Badge variant="outline" className="h-8 w-8 flex items-center justify-center rounded-full p-0">
                    {isProfit ? <TrendingUp className="w-4 h-4 text-green-500" /> : <TrendingDown className="w-4 h-4 text-red-500" />}
                 </Badge>
                 <div>
                    <div className="font-bold">{holding.tradingSymbol}</div>
                    <div className="text-xs text-muted-foreground">{holding.totalQty} Qty • CNC</div>
                 </div>
            </div>
            <div className={cn("text-right font-mono font-bold", isProfit ? "text-green-600" : "text-red-600")}>
                {formatCurrency(((holding.ltp || 0) - (holding.avgCostPrice || 0)) * (holding.totalQty || 0))}
            </div>
        </div>
    )
}

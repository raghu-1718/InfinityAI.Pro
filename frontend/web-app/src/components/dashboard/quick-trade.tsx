'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useStartTrade } from '@/hooks/useApi';
import { useState } from 'react';
import { Zap, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

const symbols = [
  { value: 'NIFTY', label: 'NIFTY 50' },
  { value: 'BANKNIFTY', label: 'BANK NIFTY' },
  { value: 'RELIANCE', label: 'Reliance Industries' },
  { value: 'TCS', label: 'TCS' },
  { value: 'HDFCBANK', label: 'HDFC Bank' },
  { value: 'INFY', label: 'Infosys' },
  { value: 'ICICIBANK', label: 'ICICI Bank' },
];

export function QuickTradeCard() {
  const [symbol, setSymbol] = useState('NIFTY');
  const [quantity, setQuantity] = useState('1');
  const { mutate: startTrade, isPending } = useStartTrade();

  const handleTrade = () => {
    startTrade(
      { symbol, qty: parseFloat(quantity) || 1 },
      {
        onSuccess: (data) => {
          if (data.status === 'execution_scheduled') {
            toast.success('Trade Scheduled', {
              description: `${data.signal?.signal} signal for ${symbol} - Execution in progress`,
            });
          } else if (data.status === 'no_action') {
            toast.info('No Action', {
              description: `HOLD signal for ${symbol} - No trade executed`,
            });
          } else {
            toast.error('Trade Failed', {
              description: data.message || 'Unknown error',
            });
          }
        },
        onError: (error) => {
          toast.error('Trade Error', {
            description: error.message || 'Failed to execute trade',
          });
        },
      }
    );
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-lg">
            <Zap className="h-5 w-5 text-yellow-500" />
            Quick Trade
          </CardTitle>
          <Badge variant="secondary">AI-Powered</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="symbol">Symbol</Label>
          <Select value={symbol} onValueChange={setSymbol}>
            <SelectTrigger>
              <SelectValue placeholder="Select symbol" />
            </SelectTrigger>
            <SelectContent>
              {symbols.map((s) => (
                <SelectItem key={s.value} value={s.value}>
                  {s.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="quantity">Quantity</Label>
          <Input
            id="quantity"
            type="number"
            value={quantity}
            onChange={(e) => setQuantity(e.target.value)}
            min="1"
            placeholder="Enter quantity"
          />
        </div>

        <div className="rounded-lg bg-muted p-3">
          <p className="text-xs text-muted-foreground">
            This will analyze {symbol} using AI and execute a trade based on the signal.
            The system will automatically determine BUY/SELL/HOLD action.
          </p>
        </div>

        <Button
          className="w-full"
          onClick={handleTrade}
          disabled={isPending}
        >
          {isPending ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Analyzing...
            </>
          ) : (
            <>
              <Zap className="mr-2 h-4 w-4" />
              Execute AI Trade
            </>
          )}
        </Button>
      </CardContent>
    </Card>
  );
}

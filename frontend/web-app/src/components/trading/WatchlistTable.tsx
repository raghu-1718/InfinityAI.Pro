import React from 'react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ArrowUp, ArrowDown, Play, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

export interface WatchlistItem {
  symbol: string;
  ltp: number;
  change_pct: number;
  signal: 'BUY' | 'SELL' | 'HOLD';
  confidence: number;
}

interface WatchlistTableProps {
  items: WatchlistItem[];
  onExecute: (symbol: string, action: 'BUY' | 'SELL') => void;
  isExecuting?: string | null; // Symbol currently being executed
}

export function WatchlistTable({ items, onExecute, isExecuting }: WatchlistTableProps) {
  return (
    <div className="rounded-md border bg-card">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-[100px]">Symbol</TableHead>
            <TableHead>Price</TableHead>
            <TableHead>24h %</TableHead>
            <TableHead>AI Signal</TableHead>
            <TableHead className="text-right">Action</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {items.map((item) => (
            <TableRow key={item.symbol}>
              <TableCell className="font-medium font-mono">{item.symbol}</TableCell>
              <TableCell className="font-mono">
                ₹{item.ltp.toLocaleString('en-IN')}
              </TableCell>
              <TableCell>
                <div className={cn("flex items-center gap-1", item.change_pct >= 0 ? "text-chart-1" : "text-destructive")}>
                    {item.change_pct >= 0 ? <ArrowUp className="w-3 h-3" /> : <ArrowDown className="w-3 h-3" />}
                    {Math.abs(item.change_pct).toFixed(2)}%
                </div>
              </TableCell>
              <TableCell>
                {item.signal === 'BUY' && (
                    <Badge variant="default" className="bg-chart-1/20 text-chart-1 hover:bg-chart-1/30">
                        BUY {item.confidence}%
                    </Badge>
                )}
                {item.signal === 'SELL' && (
                    <Badge variant="destructive" className="bg-destructive/20 text-destructive hover:bg-destructive/30">
                        SELL {item.confidence}%
                    </Badge>
                )}
                {item.signal === 'HOLD' && (
                    <Badge variant="secondary" className="opacity-50">HOLD</Badge>
                )}
              </TableCell>
              <TableCell className="text-right">
                {item.signal !== 'HOLD' && (
                    <Button 
                        size="sm" 
                        variant={item.signal === 'BUY' ? "default" : "destructive"}
                        className={cn("h-7 text-xs", item.signal === 'BUY' ? "bg-chart-1 hover:bg-chart-1/90" : "")}
                        disabled={!!isExecuting}
                        onClick={() => onExecute(item.symbol, item.signal)}
                    >
                        {isExecuting === item.symbol ? (
                            <Loader2 className="w-3 h-3 animate-spin mr-1" />
                        ) : (
                            <Play className="w-3 h-3 mr-1" />
                        )}
                        Execute
                    </Button>
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

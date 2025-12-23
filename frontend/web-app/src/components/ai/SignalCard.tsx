import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { SignalResponse } from "@/lib/api";
import { ArrowUpIcon, ArrowDownIcon, MinusIcon, TrendingUp, Zap, Newspaper, Activity } from "lucide-react";
import { cn } from "@/lib/utils";

interface SignalCardProps {
  data: SignalResponse;
  mini?: boolean;
}

export function SignalCard({ data, mini = false }: SignalCardProps) {
  const { signal, confidence, symbol, analysis, timestamp } = data;

  const isBuy = signal === 'BUY';
  const isSell = signal === 'SELL';
  const isHold = signal === 'HOLD';

  const colorClass = isBuy ? "text-chart-1" : isSell ? "text-destructive" : "text-muted-foreground";
  const bgClass = isBuy ? "bg-chart-1/10" : isSell ? "bg-destructive/10" : "bg-muted";
  const borderClass = isBuy ? "border-chart-1/20" : isSell ? "border-destructive/20" : "border-border";

  if (mini) {
     return (
        <Card className={cn("flex items-center justify-between p-4", borderClass)}>
             <div className="flex items-center gap-3">
                <div className={cn("p-2 rounded-full", bgClass)}>
                    {isBuy && <ArrowUpIcon className={cn("w-4 h-4", colorClass)} />}
                    {isSell && <ArrowDownIcon className={cn("w-4 h-4", colorClass)} />}
                    {isHold && <MinusIcon className={cn("w-4 h-4", colorClass)} />}
                </div>
                <div>
                    <h4 className="font-bold text-sm">{symbol}</h4>
                    <span className={cn("text-xs font-mono", colorClass)}>{signal}</span>
                </div>
             </div>
             <div className="text-right">
                <div className="text-xs text-muted-foreground">Confidence</div>
                <div className="font-bold text-sm">{confidence.toFixed(0)}%</div>
             </div>
        </Card>
     )
  }

  return (
    <Card className={cn("overflow-hidden border-l-4 shadow-lg", borderClass)}>
      <CardHeader className="pb-2">
        <div className="flex justify-between items-start">
            <div>
                <CardTitle className="text-2xl font-black tracking-tight flex items-center gap-2">
                    {symbol}
                    {isBuy && <Badge variant="default" className="bg-chart-1 hover:bg-chart-1/80 text-white ml-2">BUY</Badge>}
                    {isSell && <Badge variant="destructive" className="ml-2">SELL</Badge>}
                    {isHold && <Badge variant="secondary" className="ml-2">HOLD</Badge>}
                </CardTitle>
                <CardDescription className="font-mono text-xs opacity-70 mt-1">
                    {new Date(timestamp || Date.now()).toLocaleTimeString()} • AI-Model v4.0
                </CardDescription>
            </div>
            <div className={cn("flex flex-col items-end")}>
                <span className="text-xs uppercase text-muted-foreground font-semibold">AI Confidence</span>
                <span className={cn("text-3xl font-black", colorClass)}>{confidence.toFixed(1)}%</span>
            </div>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-6 pt-4">
        {/* Component Scores */}
        <div className="grid grid-cols-3 gap-2">
            <div className="flex flex-col items-center p-2 rounded-lg bg-secondary/50">
                <Activity className="w-4 h-4 text-primary mb-1" />
                <span className="text-[10px] uppercase text-muted-foreground">Tech</span>
                <span className="font-mono font-bold">{analysis.technical_score.toFixed(0)}</span>
            </div>
            <div className="flex flex-col items-center p-2 rounded-lg bg-secondary/50">
                <Zap className="w-4 h-4 text-yellow-500 mb-1" />
                <span className="text-[10px] uppercase text-muted-foreground">ML</span>
                <span className="font-mono font-bold">{analysis.ml_prediction.toFixed(2)}</span>
            </div>
             <div className="flex flex-col items-center p-2 rounded-lg bg-secondary/50">
                <Newspaper className="w-4 h-4 text-blue-400 mb-1" />
                <span className="text-[10px] uppercase text-muted-foreground">News</span>
                <span className="font-mono font-bold">{analysis.sentiment_score.toFixed(2)}</span>
            </div>
        </div>

        {/* Visual Bar */}
        <div className="space-y-1">
            <div className="flex justify-between text-xs">
                <span>Bearish</span>
                <span>Neutral</span>
                <span>Bullish</span>
            </div>
            <Progress value={isBuy ? 80 : isSell ? 20 : 50} className={cn("h-2", isBuy ? "bg-chart-1/20" : "")} />
        </div>
        
      </CardContent>
    </Card>
  );
}

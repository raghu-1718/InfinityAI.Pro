"use client";

import { useState, useEffect } from "react";
import { useAppStore } from "@/lib/store";
import { useOptionChain, useCalculateGreeks, useAnalyzeOptionStrategy } from "@/hooks/useApi";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Play, Activity, TrendingUp, TrendingDown, AlertTriangle, ArrowRight, BarChart2 } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';

const STRATEGIES = [
  {
    name: "Iron Condor",
    description: "Profit from low volatility. Sell OTM Call & Put, Buy further OTM protection.",
    risk: "Limited",
    reward: "Limited",
    sentiment: "Neutral",
    icon: <Activity className="h-6 w-6 text-blue-400" />,
    popular: true
  },
  {
    name: "Long Straddle",
    description: "Profit from high volatility. Buy ATM Call & Put.",
    risk: "Limited",
    reward: "Unlimited",
    sentiment: "Volatile",
    icon: <AlertTriangle className="h-6 w-6 text-amber-400" />,
    popular: false
  },
  {
    name: "Bull Call Spread",
    description: "Profit from moderate rise. Buy ATM Call, Sell OTM Call.",
    risk: "Limited",
    reward: "Limited",
    sentiment: "Bullish",
    icon: <TrendingUp className="h-6 w-6 text-green-400" />,
    popular: true
  },
  {
    name: "Bear Put Spread",
    description: "Profit from moderate fall. Buy ATM Put, Sell OTM Put.",
    risk: "Limited",
    reward: "Limited",
    sentiment: "Bearish",
    icon: <TrendingDown className="h-6 w-6 text-red-400" />,
    popular: false
  },
  {
    name: "Butterfly",
    description: "Profit if price stays exactly at ATM. 3-leg strategy.",
    risk: "Limited",
    reward: "High",
    sentiment: "Neutral",
    icon: <BarChart2 className="h-6 w-6 text-purple-400" />,
    popular: false
  }
];

export default function OptionsPage() {
  const { userProfile } = useAppStore();
  const [expiryDate, setExpiryDate] = useState<string>(getNextExpiry());
  
  // NIFTY 50 defaults
  const underlyingSecurityId = 13; 
  const underlyingExchange = "IDX_I";

  const { data: chainRes, isLoading: isChainLoading } = useOptionChain({
    under_security_id: underlyingSecurityId,
    under_exchange_segment: underlyingExchange,
    expiry: expiryDate
  });

  const { mutate: analyzeStrategy, isPending: isAnalyzing } = useAnalyzeOptionStrategy();
  
  // State
  const [calcSpot, setCalcSpot] = useState("23450");
  const [analysisResult, setAnalysisResult] = useState<any>(null);
  const [isResultOpen, setIsResultOpen] = useState(false);

  const optionChain = Array.isArray(chainRes?.data) ? chainRes.data : [];

  // Auto-sync Spot Price from Data
  useEffect(() => {
    if (chainRes?.data?.[0]?.underlying_price) {
      setCalcSpot(chainRes.data[0].underlying_price.toString());
    }
  }, [chainRes]);

  function getNextExpiry() {
     const d = new Date();
     // Logic for next Thursday (Simple approx)
     const day = d.getDay();
     const diff = (4 - day + 7) % 7; 
     const nextThursday = new Date(d);
     nextThursday.setDate(d.getDate() + (diff === 0 ? 0 : diff)); 
     return nextThursday.toISOString().split('T')[0];
  }

  const handleAnalyzeStrategy = (strategyName: string) => {
    const spot = parseFloat(calcSpot) || 23500;
    const atm = Math.round(spot / 50) * 50;

    // Helper to find real-time premium
    const findLTP = (strike: number, type: 'call' | 'put') => {
       const row = optionChain.find((r: any) => (r.strike_price || r.strike) == strike);
       const val = row ? (type === 'call' ? (row.call_ltp || row.call_close) : (row.put_ltp || row.put_close)) : 0;
       return parseFloat(val) || 0;
    };
    
    let params: any = { quantity: 50 }; // Default 1 lot Nifty
    
    // Auto-generate strikes based on Strategy logic using LIVE DATA
    if (strategyName === "Bear Put Spread") {
       params.buy_strike = atm;        
       params.sell_strike = atm - 100;
       params.buy_premium = findLTP(params.buy_strike, 'put') || 100;
       params.sell_premium = findLTP(params.sell_strike, 'put') || 60;
    } else if (strategyName === "Bull Call Spread") {
       params.buy_strike = atm;        
       params.sell_strike = atm + 100; 
       params.buy_premium = findLTP(params.buy_strike, 'call') || 120;
       params.sell_premium = findLTP(params.sell_strike, 'call') || 70;
    } else if (strategyName === "Long Straddle") {
       params.strike = atm;
       params.call_premium = findLTP(atm, 'call') || 120;
       params.put_premium = findLTP(atm, 'put') || 100;
    } else if (strategyName === "Butterfly") {
       params.lower_strike = atm - 100;
       params.middle_strike = atm;
       params.upper_strike = atm + 100;
       params.lower_premium = findLTP(atm - 100, 'call') || 150;
       params.middle_premium = findLTP(atm, 'call') || 80;
       params.upper_premium = findLTP(atm + 100, 'call') || 30;
    } else if (strategyName === "Iron Condor") {
       params.put_long_strike = atm - 200;
       params.put_short_strike = atm - 100;
       params.call_short_strike = atm + 100;
       params.call_long_strike = atm + 200;
       params.put_long_premium = findLTP(params.put_long_strike, 'put') || 20;
       params.put_short_premium = findLTP(params.put_short_strike, 'put') || 40;
       params.call_short_premium = findLTP(params.call_short_strike, 'call') || 45;
       params.call_long_premium = findLTP(params.call_long_strike, 'call') || 25;
    } else {
       params.buy_strike = atm;
       params.sell_strike = atm + 100;
       params.buy_premium = 50;
       params.sell_premium = 20;
    }

    analyzeStrategy({
      strategy_name: strategyName,
      spot_price: spot,
      params: params
    }, {
      onSuccess: (data) => {
        setAnalysisResult(data);
        setIsResultOpen(true);
      },
      onError: (err) => {
        console.error("Analysis failed", err);
        alert("Strategy analysis failed. Ensure Engine C is healthy.");
      }
    });
  };

  return (
    <div className="space-y-6 p-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-400 to-pink-600 bg-clip-text text-transparent">
            Options Analytics
          </h1>
          <p className="text-white/60">Real-time Strategy Analysis & Option Chain</p>
        </div>
      </div>

      <div className="glass-card p-6 border-white/10">
        <div className="flex flex-wrap items-center gap-6">
           <div className="space-y-1">
              <label className="text-xs text-white/40">Underlying</label>
              <div className="text-xl font-bold text-white">NIFTY 50</div>
           </div>
           
           <div className="space-y-1">
              <label className="text-xs text-white/40">Spot Price</label>
              <Input 
                 type="number" 
                 value={calcSpot}
                 onChange={(e) => setCalcSpot(e.target.value)}
                 className="w-32 bg-white/5 border-white/10 text-white font-mono"
              />
           </div>

           <div className="space-y-1">
              <label className="text-xs text-white/40">Expiry</label>
              <div className="text-sm font-mono text-white/80 border border-white/10 px-3 py-2 rounded">
                 {expiryDate}
              </div>
           </div>
        </div>
      </div>

      <Tabs defaultValue="strategies" className="w-full">
        <TabsList className="glass-card p-1 border-white/10 mb-6 w-full md:w-auto">
          <TabsTrigger value="strategies" className="data-[state=active]:bg-purple-500/20 data-[state=active]:text-purple-300">
             Strategies
          </TabsTrigger>
          <TabsTrigger value="chain" className="data-[state=active]:bg-purple-500/20 data-[state=active]:text-purple-300">
             Option Chain
          </TabsTrigger>
        </TabsList>

        <TabsContent value="strategies" className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {STRATEGIES.map((strategy, idx) => (
              <div 
                key={idx} 
                className="glass-card p-4 hover:neon-glow-purple cursor-pointer group border-white/5 hover:border-purple-500/30 transition-all"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="p-2 bg-white/5 rounded-lg text-purple-400 group-hover:text-purple-300 transition-colors">
                    {strategy.icon}
                  </div>
                  {strategy.popular && (
                    <Badge className="bg-amber-500/10 text-amber-400 border-amber-500/20 text-[10px] uppercase tracking-wider">
                      Popular
                    </Badge>
                  )}
                </div>
                
                <h3 className="text-lg font-semibold text-white mb-2 group-hover:text-purple-400 transition-colors">
                  {strategy.name}
                </h3>
                
                <p className="text-sm text-white/60 mb-4 h-10 line-clamp-2">
                  {strategy.description}
                </p>

                <div className="space-y-2 text-xs border-t border-white/5 pt-4">
                  <div className="flex justify-between">
                    <span className="text-white/40">Sentiment</span>
                    <span className="text-white font-medium">{strategy.sentiment}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-white/40">Risk/Reward</span>
                    <span className="text-white font-medium">{strategy.risk} / {strategy.reward}</span>
                  </div>
                </div>

                <Button 
                  variant="secondary" 
                  className="w-full mt-4 bg-white/5 hover:bg-purple-500/20 text-white hover:text-purple-300 border border-white/5"
                  onClick={() => handleAnalyzeStrategy(strategy.name)}
                  disabled={isAnalyzing}
                >
                  {isAnalyzing ? (
                     <span className="flex items-center gap-2"><Activity className="h-4 w-4 animate-spin"/> Analyzing...</span>
                  ) : (
                     <span className="flex items-center gap-2"><Play className="h-4 w-4 fill-current"/> Analyze Strategy</span>
                  )}
                </Button>
              </div>
            ))}
          </div>
        </TabsContent>
        
        <TabsContent value="chain">
            <div className="glass-card p-6 text-center text-white/60">
                 {isChainLoading ? "Loading Chain..." : (
                     optionChain.length > 0 ? (
                         <div className="overflow-x-auto">
                            <table className="w-full text-sm text-left">
                                <thead>
                                    <tr className="border-b border-white/10">
                                        <th className="p-2">Call LTP</th>
                                        <th className="p-2 text-center">Strike</th>
                                        <th className="p-2 text-right">Put LTP</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {optionChain.slice(0, 10).map((row: any, i: number) => (
                                       <tr key={i} className="border-b border-white/5 hover:bg-white/5">
                                           <td className="p-2 text-green-400">{row.call_ltp || '-'}</td>
                                           <td className="p-2 text-center font-mono">{row.strike_price || row.strike}</td>
                                           <td className="p-2 text-right text-red-400">{row.put_ltp || '-'}</td>
                                       </tr>
                                    ))}
                                </tbody>
                            </table>
                            <div className="mt-4 text-xs text-center">Showing top 10 strikes (Demo)</div>
                         </div>
                     ) : "No Option Chain Data Available"
                 )}
            </div>
        </TabsContent>
      </Tabs>

      {/* Analysis UI Dialog */}
      <Dialog open={isResultOpen} onOpenChange={setIsResultOpen}>
        <DialogContent className="glass-card border-white/10 text-white max-w-3xl">
          <DialogHeader>
            <DialogTitle className="text-xl">Strategy Analysis: {analysisResult?.strategy}</DialogTitle>
            <DialogDescription className="text-white/60">
              Projected Performance based on LIVE Market Data
            </DialogDescription>
          </DialogHeader>
          
          {analysisResult && (
            <div className="space-y-6 mt-4">
               <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="p-3 bg-white/5 rounded border border-white/5">
                      <div className="text-xs text-white/40">Max Profit</div>
                      <div className="text-lg font-bold text-green-400">{analysisResult.summary.max_profit}</div>
                  </div>
                  <div className="p-3 bg-white/5 rounded border border-white/5">
                      <div className="text-xs text-white/40">Max Loss</div>
                      <div className="text-lg font-bold text-red-400">{analysisResult.summary.max_loss}</div>
                  </div>
                  <div className="p-3 bg-white/5 rounded border border-white/5">
                      <div className="text-xs text-white/40">Breakeven</div>
                      <div className="text-lg font-bold text-white">
                         {analysisResult.summary.breakeven || `${analysisResult.summary.breakeven_lower} - ${analysisResult.summary.breakeven_upper}`}
                      </div>
                  </div>
                  <div className="p-3 bg-white/5 rounded border border-white/5">
                      <div className="text-xs text-white/40">Net Premium</div>
                      <div className="text-lg font-bold text-blue-400">{analysisResult.summary.net_premium}</div>
                  </div>
               </div>

               {/* Payoff Chart */}
               {analysisResult.payoff_chart && (
                   <div className="h-64 w-full mt-4">
                       <ResponsiveContainer width="100%" height="100%">
                           <BarChart data={analysisResult.payoff_chart}>
                               <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                               <XAxis dataKey="spot" stroke="#666" fontSize={12} tickFormatter={(val) => Math.round(val).toString()}/>
                               <YAxis stroke="#666" fontSize={12}/>
                               <Tooltip 
                                  contentStyle={{backgroundColor: '#111', borderColor: '#333'}}
                                  itemStyle={{color: '#fff'}}
                               />
                               <ReferenceLine y={0} stroke="#666" />
                               <Bar dataKey="pnl" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                           </BarChart>
                       </ResponsiveContainer>
                   </div>
               )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

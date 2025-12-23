'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Sparkles, Activity, Target, Search, Loader2 } from 'lucide-react';
import { SignalCard } from '@/components/ai/SignalCard';
import { engineB, SignalResponse } from '@/lib/api';
import { useToast } from 'sonner';

const POPULAR_STOCKS = ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK', 'SBIN', 'CRUDEOIL', 'GOLDM'];

export default function AIAnalysisPage() {
  const [symbol, setSymbol] = useState('RELIANCE');
  const [timeframe, setTimeframe] = useState('INTRADAY');
  const [loading, setLoading] = useState(false);
  const [signalData, setSignalData] = useState<SignalResponse | null>(null);
  const { toast } = useToast();

  const handleAnalyze = async () => {
    setLoading(true);
    try {
        // We use the "AI Signal" endpoint from engineB (which calls Gemini 2.5)
        // In a real app, 'current_price' would be fetched from Dhan/Engine A first
        const res = await engineB.getEnhancedSignal({
            symbol: symbol,
            timeframe: timeframe,
            user_analysis_type: "comprehensive",
            use_pro_model: true // Use the smart model
        });
        
        // Transform backend response to UI format if needed, but strict typing helps
        // The API returns the exact structure SignalCard expects mostly
        setSignalData(res);
        toast.success("AI Analysis Complete");
    } catch (e) {
        toast.error("Analysis Failed", { description: String(e) });
    } finally {
        setLoading(false);
    }
  };

  return (
    <div className="p-6 space-y-8 max-w-7xl mx-auto">
      
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
            <h1 className="text-3xl font-black tracking-tight flex items-center gap-3">
                <Sparkles className="h-8 w-8 text-chart-1" />
                <span className="bg-clip-text text-transparent bg-gradient-to-r from-chart-1 to-purple-500">
                    Infinity AI Brain
                </span>
            </h1>
            <p className="text-muted-foreground mt-1 text-lg">
                Real-time multi-model market analysis powered by Gemini 2.5 Pro.
            </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left Control Panel */}
        <div className="lg:col-span-4 space-y-6">
            <Card className="border-l-4 border-l-primary shadow-md">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Search className="w-5 h-5" />
                        Analysis Parameters
                    </CardTitle>
                    <CardDescription>Configure the AI model inputs.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="space-y-2">
                        <Label>Symbol</Label>
                        <div className="flex gap-2">
                            <Input 
                                value={symbol} 
                                onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                                placeholder="e.g. NIFTY" 
                                className="font-mono uppercase font-bold"
                            />
                        </div>
                        <div className="flex flex-wrap gap-2 mt-2">
                            {POPULAR_STOCKS.slice(0, 5).map(s => (
                                <div 
                                    key={s} 
                                    onClick={() => setSymbol(s)}
                                    className="text-xs cursor-pointer px-2 py-1 rounded bg-secondary hover:bg-primary/20 transition-colors"
                                >
                                    {s}
                                </div>
                            ))}
                        </div>
                    </div>

                    <div className="space-y-2">
                        <Label>Time Horizon</Label>
                        <Select value={timeframe} onValueChange={setTimeframe}>
                            <SelectTrigger>
                                <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="SCALP">Scalp (1-5m)</SelectItem>
                                <SelectItem value="INTRADAY">Intraday (15m-1h)</SelectItem>
                                <SelectItem value="SWING">Swing (1d-1w)</SelectItem>
                                <SelectItem value="POSITIONAL">Positional (1m+)</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>

                    <Button 
                        onClick={handleAnalyze} 
                        disabled={loading} 
                        className="w-full h-12 text-lg font-bold shadow-lg shadow-primary/20"
                    >
                        {loading ? (
                            <>
                                <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                                Analyzing...
                            </>
                        ) : (
                            <>
                                <Sparkles className="mr-2 h-5 w-5" />
                                Run AI Analysis
                            </>
                        )}
                    </Button>
                </CardContent>
            </Card>

            {/* AI Stats / Quota */}
            <Card>
                <CardHeader>
                    <CardTitle className="text-sm">Model Status</CardTitle>
                </CardHeader>
                <CardContent className="text-sm space-y-2">
                    <div className="flex justify-between">
                        <span className="text-muted-foreground">Engine B</span>
                        <span className="text-green-500 font-bold">Online</span>
                    </div>
                    <div className="flex justify-between">
                        <span className="text-muted-foreground">Model</span>
                        <span className="font-mono">Gemini 2.5 Pro</span>
                    </div>
                     <div className="flex justify-between">
                        <span className="text-muted-foreground">Latency</span>
                        <span className="font-mono">~1.2s</span>
                    </div>
                </CardContent>
            </Card>
        </div>

        {/* Right Result Area */}
        <div className="lg:col-span-8 space-y-6">
            {signalData ? (
                <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                    <SignalCard data={signalData} />
                    
                    <Tabs defaultValue="reasoning">
                        <TabsList className="w-full justify-start">
                            <TabsTrigger value="reasoning">Brain Reasoning</TabsTrigger>
                            <TabsTrigger value="technical">Technical Data</TabsTrigger>
                            <TabsTrigger value="context">Market Context</TabsTrigger>
                        </TabsList>
                        
                        <TabsContent value="reasoning" className="mt-4">
                            <Card>
                                <CardHeader>
                                    <CardTitle>Why did the AI choose {signalData.signal}?</CardTitle>
                                </CardHeader>
                                <CardContent className="space-y-4">
                                    <div className="p-4 bg-secondary/50 rounded-lg border border-border">
                                        <p className="leading-relaxed whitespace-pre-wrap">
                                            {signalData.market_context.reasoning || "No detailed reasoning provided by the model."}
                                        </p>
                                    </div>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        <div>
                                            <h4 className="font-semibold mb-2 flex items-center gap-2">
                                                <Target className="w-4 h-4 text-green-500" />
                                                Bullish Factors
                                            </h4>
                                            <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1">
                                                {/* Mock data until API provides explicit lists */}
                                                <li>Strong momentum on 15m timeframe</li>
                                                <li>RSI showing hidden divergence</li>
                                                <li>Sector tailwinds form global markets</li>
                                            </ul>
                                        </div>
                                        <div>
                                            <h4 className="font-semibold mb-2 flex items-center gap-2">
                                                <Activity className="w-4 h-4 text-red-500" />
                                                Risk Factors
                                            </h4>
                                             <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1">
                                                <li>Near major resistance level</li>
                                                <li>Volume fading on recent highs</li>
                                            </ul>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        </TabsContent>

                        <TabsContent value="technical">
                             <Card>
                                 <CardContent className="pt-6">
                                    <p className="text-muted-foreground">Raw technical indicators would be here.</p>
                                 </CardContent>
                             </Card>
                        </TabsContent>
                    </Tabs>
                </div>
            ) : (
                <div className="h-full flex flex-col items-center justify-center p-12 text-center border-2 border-dashed rounded-xl bg-secondary/10">
                    <div className="w-20 h-20 rounded-full bg-secondary/50 flex items-center justify-center mb-4">
                        <Activity className="w-10 h-10 text-muted-foreground/50" />
                    </div>
                    <h3 className="text-xl font-bold mb-2">Ready to Analyze</h3>
                    <p className="text-muted-foreground max-w-sm">
                        Select a symbol and horizon to generate real-time trading signals powered by our Hybrid AI Engine.
                    </p>
                </div>
            )}
        </div>

      </div>
    </div>
  );
}

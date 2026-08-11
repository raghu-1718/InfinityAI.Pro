"use client";

import { useMarketPrediction, useGeminiAnalysis, useSentimentAnalysis } from "@/hooks/useApi";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Brain, Globe, Activity, TrendingUp, Sparkles, Newspaper } from "lucide-react";
import { cn } from "@/lib/utils";

export default function IntelligencePage() {
  const { data: marketPrediction, isLoading: isPredicting } = useMarketPrediction("day");
  // Using NIFTY as the base index for the macro market view
  const { data: geminiAnalysis, isLoading: isAnalyzing } = useGeminiAnalysis("NIFTY");
  const { data: sentiment, isLoading: isSentimentLoading } = useSentimentAnalysis("NIFTY");

  return (
    <div className="p-6 space-y-8 max-w-7xl mx-auto w-full">
      <div className="flex flex-col gap-2">
        <h1 className="text-4xl font-bold tracking-tighter flex items-center gap-3">
          <Brain className="w-10 h-10 text-purple-500" />
          AI Intelligence <span className="text-white/50">& News Hub</span>
        </h1>
        <p className="text-slate-400">Live macroeconomic synthesis powered by Vertex AI Search Grounding.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Narrative - 2 cols */}
        <div className="lg:col-span-2 space-y-6">
          <Card className="glass-card border-t-4 border-t-purple-500">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Sparkles className="h-5 w-5 text-purple-400" />
                  <CardTitle>Market Narrative</CardTitle>
                </div>
                {isAnalyzing ? (
                  <Badge variant="outline" className="animate-pulse">Analyzing...</Badge>
                ) : (
                  <Badge className="bg-purple-500/20 text-purple-300">Live AI Synthesis</Badge>
                )}
              </div>
              <CardDescription>Synthesized from global live news and tick data</CardDescription>
            </CardHeader>
            <CardContent>
              {isAnalyzing ? (
                <div className="space-y-4">
                  <div className="h-4 bg-white/5 rounded animate-pulse w-full" />
                  <div className="h-4 bg-white/5 rounded animate-pulse w-5/6" />
                  <div className="h-4 bg-white/5 rounded animate-pulse w-4/6" />
                </div>
              ) : (
                <div className="space-y-4 text-slate-300 leading-relaxed">
                  <p>{geminiAnalysis?.analysis || "AI narrative generation is currently unavailable. Waiting for tick data."}</p>
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="glass-card border-t-4 border-t-blue-500">
            <CardHeader>
              <div className="flex items-center gap-2">
                <Globe className="h-5 w-5 text-blue-400" />
                <CardTitle>Real-Time Global Sentiment</CardTitle>
              </div>
              <CardDescription>Live Web Search Grounded</CardDescription>
            </CardHeader>
            <CardContent>
               {isSentimentLoading ? (
                 <div className="flex items-center justify-center p-8"><Globe className="w-8 h-8 text-blue-500 animate-spin" /></div>
               ) : (
                 <div className="flex items-center justify-between p-6 bg-blue-500/10 rounded-xl border border-blue-500/20">
                    <div>
                      <p className="text-sm text-blue-300 uppercase tracking-widest font-bold">Overall Sentiment</p>
                      <p className="text-3xl font-black text-white capitalize mt-1">{sentiment?.overall_sentiment || "Neutral"}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-slate-400">Confidence Score</p>
                      <p className="text-3xl font-mono text-emerald-400 font-bold">{sentiment?.confidence ? `${(sentiment.confidence * 100).toFixed(0)}%` : "N/A"}</p>
                    </div>
                 </div>
               )}
            </CardContent>
          </Card>
        </div>

        {/* Sidebar - 1 col */}
        <div className="space-y-6">
          <Card className="glass-card border-t-4 border-t-emerald-500">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5 text-emerald-400" />
                  <CardTitle>ML Trend Signals</CardTitle>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {isPredicting ? (
                 <div className="h-20 bg-white/5 rounded animate-pulse w-full" />
              ) : (
                <div className="space-y-4">
                  <div className="p-4 rounded-xl bg-black/40 border border-white/5">
                    <p className="text-sm text-slate-400 mb-1">Predicted Day Trend</p>
                    <p className="text-xl font-bold text-white capitalize">{marketPrediction?.prediction || "Ranging"}</p>
                  </div>
                  <div className="p-4 rounded-xl bg-black/40 border border-white/5">
                    <p className="text-sm text-slate-400 mb-1">Model Accuracy</p>
                    <p className="text-xl font-mono text-emerald-400">{marketPrediction?.confidence ? `${(marketPrediction.confidence * 100).toFixed(1)}%` : "--"}</p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="glass-card">
            <CardHeader>
              <div className="flex items-center gap-2">
                <Newspaper className="h-5 w-5 text-slate-400" />
                <CardTitle>Key Catalysts</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
               <div className="space-y-3">
                 {sentiment?.catalysts && sentiment.catalysts.length > 0 ? (
                   sentiment.catalysts.slice(0, 3).map((catalyst: string, index: number) => (
                     <div key={index} className="p-3 rounded-lg bg-white/5 border border-white/10 text-sm">
                       <p className="text-slate-300">{catalyst}</p>
                       <Badge className="mt-2 bg-blue-500/20 text-blue-400">Live Insight</Badge>
                     </div>
                   ))
                 ) : (
                   <div className="p-3 rounded-lg bg-white/5 border border-white/10 text-sm">
                     <p className="text-slate-500 italic">No live catalysts available right now.</p>
                   </div>
                 )}
               </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

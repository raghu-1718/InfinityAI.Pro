'use client';

import { useAppStore } from '@/lib/store';
import { useSystemState } from '@/hooks/useApi';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Shield, Brain, TrendingUp, Zap, Activity, ChevronRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import Link from 'next/link';
import { Badge } from '@/components/ui/badge';

export default function DashboardPage() {
  const { userProfile } = useAppStore();
  const { data: systemState } = useSystemState();
  const engineActive = systemState?.engine_active;

  return (
    <div className="flex flex-col min-h-[calc(100vh-4rem)] space-y-8 p-8 max-w-7xl mx-auto">
      
      {/* Hero Section */}
      <div className="relative rounded-3xl overflow-hidden bg-gradient-to-br from-indigo-900 via-slate-900 to-slate-950 p-12 border border-slate-800 shadow-2xl">
        <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20"></div>
        <div className="relative z-10 flex flex-col md:flex-row items-center justify-between gap-8">
          <div className="space-y-6 max-w-2xl">
            <Badge variant="secondary" className="bg-indigo-500/10 text-indigo-400 border-indigo-500/20 backdrop-blur-sm px-4 py-1">
              <Sparkles className="h-3 w-3 mr-2 inline" />
              v4.0 Live System
            </Badge>
            <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight text-white leading-tight">
              Infinity<span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-cyan-400">AI</span>
            </h1>
            <p className="text-lg text-slate-300 leading-relaxed max-w-xl">
              Automated High-Frequency Trading System. 
              Engineered for precision, risk management, and speed.
              Control your capital with AI-driven execution.
            </p>
            <div className="flex gap-4 pt-4">
              <Link href="/trading">
                <Button size="lg" className="bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 border-0 shadow-lg">
                  <Zap className="h-4 w-4 mr-2 group-hover:fill-current" />
                  {engineActive ? "Monitor Active Session" : "Launch Engine"}
                </Button>
              </Link>
              <Link href="/settings">
                  <Button size="lg" variant="outline" className="border-slate-600 text-slate-200 hover:bg-slate-800 backdrop-blur-sm">
                    Configure
                  </Button>
              </Link>
            </div>
          </div>
          
          {/* Status Widget */}
          <div className="w-full md:w-80 glass-panel rounded-2xl p-6 border border-white/10 bg-white/5 backdrop-blur-md">
            <div className="flex items-center gap-4 mb-4">
              <div className="h-12 w-12 rounded-full bg-indigo-500/20 flex items-center justify-center">
                <Activity className="h-6 w-6 text-indigo-400" />
              </div>
              <div>
                <h3 className="font-semibold text-white">System Status</h3>
                <p className="text-xs text-green-400 font-medium flex items-center gap-1">
                  <span className="h-1.5 w-1.5 rounded-full bg-green-500 animate-pulse" />
                  All Engines Online
                </p>
              </div>
            </div>
            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-slate-400">Risk Engine</span>
                <span className="text-cyan-400 font-mono">ACTIVE</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-400">AI Model</span>
                <span className="text-cyan-400 font-mono">v3.8</span>
              </div>
              <div className="h-px bg-white/10 my-2" />
              <div className="flex justify-between text-sm">
                <span className="text-slate-400">User</span>
                <span className="text-white font-medium">{userProfile?.clientId || 'Trader'}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Feature Grid */}
      <div className="grid md:grid-cols-3 gap-6">
        <FeatureCard 
          icon={<Shield className="h-8 w-8 text-emerald-400" />}
          title="Risk Management"
          description="Real-time margin monitoring, auto-kill switch, and capital protection protocols."
          delay={100}
        />
        <FeatureCard 
          icon={<Brain className="h-8 w-8 text-violet-400" />}
          title="AI-Powered"
          description="Deep learning models analyze market microstructure for optimal entry and exit."
          delay={200}
        />
        <FeatureCard 
          icon={<TrendingUp className="h-8 w-8 text-amber-400" />}
          title="Multi-Asset"
          description="Seamless execution across Equity, F&O, and Commodities with unified capital."
          delay={300}
        />
      </div>

    </div>
  );
}

function FeatureCard({ icon, title, description, delay }: { icon: any, title: string, description: string, delay: number }) {
  return (
    <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-sm hover:bg-slate-800/80 transition-all duration-300 hover:-translate-y-1">
      <CardHeader>
        <div className="mb-4 inline-block p-3 rounded-2xl bg-slate-950 border border-slate-800">
          {icon}
        </div>
        <CardTitle className="text-xl text-white">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-slate-400 leading-relaxed">
          {description}
        </p>
      </CardContent>
    </Card>
  );
}

function Sparkles({ className }: { className?: string }) {
  return (
    <svg className={className} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/>
    </svg>
  )
}
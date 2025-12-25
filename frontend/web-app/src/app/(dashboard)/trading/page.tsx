'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { Slider } from "@/components/ui/slider";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Power, ShieldAlert, Activity, DollarSign, Wallet, TrendingUp, Infinity as InfinityIcon, FileClock } from 'lucide-react';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';
import { useAppStore } from '@/lib/store';
import { useCouponAuth } from "@/contexts/DualAuthContext";
import { useUserAccount } from '@/hooks/useApi';
import { engineA } from '@/lib/api';

// Phase 6 Components
import { useAuditTimeline } from "@/hooks/useAuditTimeline";
import { useSessionState } from "@/hooks/useSessionState";
import { SessionStatus } from "@/components/dashboard/session-status";
import { AuditTimeline } from "@/components/dashboard/audit-timeline";

export default function TradingPage() {
  const { userProfile } = useAppStore();
  const { session } = useCouponAuth();
  const { data: accountData } = useUserAccount();
  
  // Phase 6: Live Data Streams
  const uid = session?.userId;
  const auditEvents = useAuditTimeline(uid);
  const sessionState = useSessionState(uid);

  // Configuration State
  const [tradingCapital, setTradingCapital] = useState('50000');
  const [assetClass, setAssetClass] = useState('NIFTY'); 
  const [riskPerTrade, setRiskPerTrade] = useState(1.0); 
  const [targetProfit, setTargetProfit] = useState(5.0); 
  const [isTrailing, setIsTrailing] = useState(true);
  const [isContinuous, setIsContinuous] = useState(false); 
  
  // System State
  const [isEngineRunning, setIsEngineRunning] = useState(false);
  const [isKillSwitchActive, setIsKillSwitchActive] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // Poll for status (Engine A Availability)
  useEffect(() => {
    const checkStatus = async () => {
        try {
            const state = await engineA.getSystemState();
            setIsEngineRunning(state.engine_active);
        } catch (e) { console.error("Status Poll Failed", e); }
    };
    checkStatus();
    const interval = setInterval(checkStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleStartStop = async () => {
    if (!userProfile?.isConnected) {
      toast.error("Account Not Connected", { description: "Please connect Dhan in Settings first." });
      return;
    }
    
    if (isKillSwitchActive && !isEngineRunning) {
        toast.error("Kill Switch Active", { description: "Disable Kill Switch to start engine." });
        return;
    }

    setIsLoading(true);

    try {
        if (!isEngineRunning) {
             // START LOGIC
             const payload = {
                 instruments: [assetClass],
                 tradingAmount: parseFloat(tradingCapital),
                 riskLevel: riskPerTrade < 1 ? 'conservative' : riskPerTrade < 3 ? 'moderate' : 'aggressive',
                 stopLossPercent: riskPerTrade, 
                 takeProfitPercent: targetProfit,
                 maxTradesPerDay: isContinuous ? 1000 : 5, 
                 useAISignals: true,
                 user_id: session?.userId || 'unknown',
                 _metadata: {
                     isTrailing,
                     isContinuous,
                     assetClass
                 }
             };

             await engineA.startAutoTrading(payload as any);
             setIsEngineRunning(true);
             toast.success("Engine Started", { 
                 description: `Trading ${assetClass} with ${isContinuous ? 'Continuous Loop' : 'Standard Targets'}` 
             });

        } else {
            // STOP LOGIC
            const uid = session?.userId || 'unknown';
            await engineA.stopAutoTrading(uid); 
            setIsEngineRunning(false);
            toast.success("Engine Stopped", { description: "Trading halted. Positions may still be open." });
        }
    } catch (error: any) {
        toast.error(isEngineRunning ? 'Stop Failed' : 'Start Failed', { description: error.message });
    } finally {
        setIsLoading(false);
    }
  };

  const handleKillSwitch = async (checked: boolean) => {
      setIsKillSwitchActive(checked);
      if (checked) {
          setIsEngineRunning(false);
          toast.warning("KILL SWITCH ACTIVATED", { description: "Sending emergency stop command..." });
          try {
             // Use consistent method
             const uid = session?.userId || 'unknown';
             await engineA.stopAutoTrading(uid);
          } catch(e) { console.error(e); }
      }
  };

  const funds = accountData?.funds?.availableBalance || 0;

  return (
    <div className="flex flex-col items-center min-h-[calc(100vh-6rem)] p-6 gap-8 max-w-5xl mx-auto">
      
      {/* Header */}
      <div className="text-center space-y-2 w-full">
        <h1 className="text-4xl font-black text-white tracking-tight flex items-center justify-center gap-3">
           <Activity className={cn("w-10 h-10", isEngineRunning ? "text-green-500 animate-pulse" : "text-slate-600")} />
           Execution Engine
        </h1>
        <p className="text-slate-400">
           Configure & Launch High-Frequency Trading
        </p>

        {/* Phase 6: Session Status Banner */}
        <div className="max-w-3xl mx-auto mt-4">
             <SessionStatus state={sessionState} />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 w-full">
          
          {/* LEFT: Configuration Panel */}
          <Card className={cn("lg:col-span-2 border-slate-800 bg-slate-900/50 transition-all", isEngineRunning && "opacity-50 pointer-events-none grayscale")}>
             <CardHeader>
                 <CardTitle className="flex items-center gap-2">
                     <TrendingUp className="w-5 h-5 text-primary" />
                     Strategy Configuration
                 </CardTitle>
                 <CardDescription>Set your asset class, risk parameters, and profit targets.</CardDescription>
             </CardHeader>
             <CardContent className="space-y-6">
                 
                 {/* Asset & Capital */}
                 <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                     <div className="space-y-2">
                         <Label>Asset Class</Label>
                         <Select value={assetClass} onValueChange={setAssetClass} disabled={isEngineRunning}>
                             <SelectTrigger>
                                 <SelectValue placeholder="Select Asset" />
                             </SelectTrigger>
                             <SelectContent>
                                 <SelectItem value="NIFTY">NIFTY 50</SelectItem>
                                 <SelectItem value="BANKNIFTY">BANK NIFTY</SelectItem>
                                 <SelectItem value="FINNIFTY">FIN NIFTY</SelectItem>
                                 <SelectItem value="CRUDEOIL">CRUDE OIL (Comm)</SelectItem>
                                 <SelectItem value="GOLD">GOLD (Comm)</SelectItem>
                             </SelectContent>
                         </Select>
                     </div>
                     <div className="space-y-2">
                         <Label>Deploy Capital (₹)</Label>
                         <div className="relative">
                            <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                            <Input 
                                type="number" 
                                value={tradingCapital}
                                onChange={(e) => setTradingCapital(e.target.value)}
                                className="pl-9 font-mono"
                                disabled={isEngineRunning}
                            />
                         </div>
                         <p className="text-xs text-muted-foreground flex items-center gap-1">
                             <Wallet className="w-3 h-3" /> Available: ₹{funds.toLocaleString()}
                         </p>
                     </div>
                 </div>

                 {/* Risk & Profit Sliders */}
                 <div className="space-y-6 pt-4 border-t border-slate-800">
                     <div className="space-y-4">
                         <div className="flex justify-between">
                             <Label>Stop Loss / Max Risk (%)</Label>
                             <span className="font-mono text-red-400">{riskPerTrade.toFixed(1)}%</span>
                         </div>
                         <Slider 
                            value={[riskPerTrade]} 
                            min={0.5} max={5} step={0.1} 
                            onValueChange={(val) => setRiskPerTrade(val[0])}
                            disabled={isEngineRunning}
                            className="[&>.absolute]:bg-red-500"
                         />
                     </div>

                     <div className="space-y-4">
                         <div className="flex justify-between">
                             <Label>Min Profit Target (%)</Label>
                             <span className="font-mono text-green-400">{targetProfit.toFixed(1)}%</span>
                         </div>
                         <Slider 
                            value={[targetProfit]} 
                            min={1} max={20} step={0.5} 
                            onValueChange={(val) => setTargetProfit(val[0])}
                            disabled={isEngineRunning}
                            className="[&>.absolute]:bg-green-500"
                         />
                     </div>
                 </div>

                 {/* Advanced Modes */}
                 <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-slate-800">
                    <div className="flex items-center justify-between p-3 border border-slate-800 rounded-lg bg-slate-950/30">
                        <div className="space-y-1">
                            <Label>Trailing Stop</Label>
                            <p className="text-xs text-muted-foreground">Move SL to Break-Even</p>
                        </div>
                        <Switch checked={isTrailing} onCheckedChange={setIsTrailing} disabled={isEngineRunning}/>
                    </div>
                    
                    <div className={cn("flex items-center justify-between p-3 border rounded-lg transition-colors", isContinuous ? "border-indigo-500/50 bg-indigo-500/10" : "border-slate-800 bg-slate-950/30")}>
                        <div className="space-y-1">
                            <div className="flex items-center gap-2">
                                <Label className={isContinuous ? "text-indigo-400" : ""}>Continuous Mode</Label>
                                {isContinuous && <InfinityIcon className="w-3 h-3 text-indigo-400 animate-pulse" />}
                            </div>
                            <p className="text-xs text-muted-foreground">Trade until manual stop</p>
                        </div>
                        <Switch checked={isContinuous} onCheckedChange={setIsContinuous} disabled={isEngineRunning}/>
                    </div>
                 </div>

             </CardContent>
          </Card>

          {/* RIGHT: Execution Panel */}
          <div className="space-y-6">
              
              {/* Start/Stop Button */}
              <Card className={cn("border-2 shadow-2xl overflow-hidden", isEngineRunning ? "border-green-500/50 bg-green-950/20" : "border-slate-700 bg-slate-900")}>
                 <CardContent className="p-6">
                    <Button 
                        onClick={handleStartStop}
                        disabled={isLoading || isKillSwitchActive}
                        className={cn("w-full h-32 text-4xl font-black tracking-widest transition-all duration-300 relative overflow-hidden group",
                            isEngineRunning 
                              ? "bg-red-600 hover:bg-red-700 shadow-[0_0_40px_-5px_theme(colors.red.600)]" 
                              : "bg-green-600 hover:bg-green-500 shadow-[0_0_40px_-5px_theme(colors.green.600)]"
                        )}
                    >
                        <div className="relative z-10 flex flex-col items-center gap-2">
                            <Power className="w-12 h-12" />
                            {isEngineRunning ? "STOP" : "START"}
                            <span className="text-xs font-normal tracking-normal opacity-80">
                                {isEngineRunning ? "HALT EXECUTION" : "INITIATE ENGINE"}
                            </span>
                        </div>
                        {isEngineRunning && <div className="absolute inset-0 bg-red-500/20 animate-pulse" />}
                    </Button>
                 </CardContent>
              </Card>

              {/* Status Display (When Running) */}
              {isEngineRunning && (
                   <Card className="border-indigo-500/30 bg-indigo-950/10 animate-in fade-in slide-in-from-right-4">
                       <CardHeader className="pb-2">
                           <CardTitle className="text-sm uppercase text-muted-foreground">Active Configuration</CardTitle>
                       </CardHeader>
                       <CardContent className="space-y-3">
                           <div className="flex justify-between text-sm">
                               <span>Asset:</span>
                               <span className="font-bold text-white">{assetClass}</span>
                           </div>
                           <div className="flex justify-between text-sm">
                               <span>Target Profit:</span>
                               <span className="font-bold text-green-400">{targetProfit}%</span>
                           </div>
                           <div className="flex justify-between text-sm">
                               <span>Mode:</span>
                               <Badge variant={isContinuous ? "default" : "secondary"}>
                                   {isContinuous ? "CONTINUOUS" : "STANDARD"}
                               </Badge>
                           </div>
                       </CardContent>
                   </Card>
              )}

              {/* Kill Switch */}
             <Card className="border-red-900/30 bg-red-950/10">
                 <CardContent className="p-4 flex items-center justify-between gap-4">
                     <div className="flex items-center gap-3">
                         <ShieldAlert className={cn("w-8 h-8", isKillSwitchActive ? "text-red-500 animate-pulse" : "text-slate-600")} />
                         <div>
                             <h3 className="font-bold text-slate-200">Kill Switch</h3>
                             <p className="text-xs text-slate-400">Emergency Halt</p>
                         </div>
                     </div>
                     <Switch 
                         checked={isKillSwitchActive}
                         onCheckedChange={handleKillSwitch}
                         className="data-[state=checked]:bg-red-600"
                     />
                 </CardContent>
             </Card>
          </div>

      </div>

      {/* Phase 6: Live Audit Timeline */}
      <div className="w-full">
            <Card className="border-slate-800 bg-slate-900/30">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <FileClock className="w-5 h-5 text-slate-400" />
                        Live Audit Trail
                    </CardTitle>
                    <CardDescription>Real-time log of all Engine decisions, risk checks, and executions.</CardDescription>
                </CardHeader>
                <CardContent>
                    <AuditTimeline events={auditEvents} />
                </CardContent>
            </Card>
      </div>

    </div>
  );
}

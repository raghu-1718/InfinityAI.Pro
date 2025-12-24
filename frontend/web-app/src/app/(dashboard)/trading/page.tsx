'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { Power, ShieldAlert, Activity, DollarSign, Wallet } from 'lucide-react';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';
import { useAppStore } from '@/lib/store';
import { useUserAccount } from '@/hooks/useApi';
import { engineA } from '@/lib/api';

const ENGINE_A_URL = process.env.NEXT_PUBLIC_ENGINE_A_URL || 'https://engine-a-429140669077.us-central1.run.app';

export default function TradingPage() {
  const { userProfile } = useAppStore();
  const { data: accountData } = useUserAccount();
  
  const [tradingCapital, setTradingCapital] = useState('50000');
  const [isEngineRunning, setIsEngineRunning] = useState(false); // Should sync with backend
  const [isKillSwitchActive, setIsKillSwitchActive] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  
  // Load initial state (mock for now, ideally fetch from /api/trading/status)
  useEffect(() => {
    // Poll for status or load
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

    // Logic: If NOT running, user should go to /start page to configure parameters.
    if (!isEngineRunning) {
        window.location.href = "/start";
        return;
    }

    // If RUNNING, user wants to STOP.
    setIsLoading(true);
    try {
      await engineA.stopSession(); // Use API client
      
      // Verification: Check state after stop
      const state = await engineA.getSystemState();
      
      if (!state.engine_active) {
         setIsEngineRunning(false);
         toast.success("Engine Stopped", { description: "Trading halted." });
      } else {
         throw new Error("Engine reported active state after stop command.");
      }

    } catch (error: any) {
      toast.error('Stop Failed', { description: error.message });
    } finally {
      setIsLoading(false);
    }
  };

  const handleKillSwitch = async (checked: boolean) => {
      // Immediate frontend update for responsiveness
      setIsKillSwitchActive(checked);
      
      if (checked) {
          // If turning ON kill switch, halt everything
          setIsEngineRunning(false);
          toast.warning("KILL SWITCH ACTIVATED", { description: "Sending emergency stop command..." });
          
          try {
             await engineA.stopSession();
             setIsEngineRunning(false); // Force state update
          } catch(e) { 
              console.error(e);
              toast.error("Kill Switch Error", { description: "Check console / connection." });
          }
      } else {
          toast.info("Kill Switch Deactivated", { description: "You can now launch the engine." });
      }
  };

  const funds = accountData?.funds?.availableBalance || 0;

  return (
    <div className="flex items-center justify-center min-h-[calc(100vh-6rem)] p-6">
      
      <div className="w-full max-w-2xl space-y-8">
        
        {/* Header */}
        <div className="text-center space-y-2">
          <h1 className="text-4xl font-black text-white tracking-tight flex items-center justify-center gap-3">
             <Activity className={cn("w-10 h-10", isEngineRunning ? "text-green-500 animate-pulse" : "text-slate-600")} />
             Execution Engine
          </h1>
          <p className="text-slate-400">
             High-Frequency AI Trading Control Center
          </p>
        </div>

        {/* Main Control Card */}
        <Card className={cn("border-2 shadow-2xl transition-all duration-500", 
             isEngineRunning ? "border-green-500/50 bg-green-500/5 shadow-green-500/20" : "border-slate-800 bg-slate-900/50"
        )}>
           <CardContent className="p-8 space-y-8">
               
               {/* Capital Input */}
               <div className="space-y-4">
                   <div className="flex items-center justify-between">
                       <Label className="text-lg font-medium text-slate-200">Deployed Capital</Label>
                       <div className="flex items-center gap-2 text-sm text-slate-400">
                           <Wallet className="w-4 h-4" />
                           Available: ₹{funds.toLocaleString()}
                       </div>
                   </div>
                   <div className="relative">
                       <DollarSign className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                       <Input 
                          type="number" 
                          value={tradingCapital}
                          onChange={(e) => setTradingCapital(e.target.value)}
                          className="pl-12 h-14 text-2xl font-mono bg-slate-950 border-slate-700 focus-visible:ring-indigo-500"
                          disabled={isEngineRunning}
                       />
                   </div>
               </div>

               {/* Start/Stop Button */}
               <Button 
                  onClick={handleStartStop}
                  disabled={isLoading || isKillSwitchActive}
                  className={cn("w-full h-24 text-3xl font-black tracking-widest transition-all duration-300 relative overflow-hidden group",
                      isEngineRunning 
                        ? "bg-red-600 hover:bg-red-700 shadow-lg shadow-red-900/20" 
                        : "bg-green-600 hover:bg-green-500 shadow-lg shadow-green-900/20"
                  )}
               >
                   <div className="relative z-10 flex items-center gap-4">
                       <Power className="w-8 h-8" />
                       {isEngineRunning ? "STOP ENGINE" : "START ENGINE"}
                   </div>
                   {isEngineRunning && (
                       <div className="absolute inset-0 bg-red-500/20 animate-pulse" />
                   )}
               </Button>
               
               {/* Status Metrics (PnL placeholder) */}
               {isEngineRunning && (
                   <div className="grid grid-cols-2 gap-4 pt-4 animate-in fade-in slide-in-from-top-4">
                       <div className="bg-slate-950/50 p-4 rounded-xl border border-slate-800 text-center">
                           <p className="text-xs text-slate-500 uppercase font-bold">Session P&L</p>
                           <p className="text-2xl font-mono text-green-400">+₹0.00</p>
                       </div>
                       <div className="bg-slate-950/50 p-4 rounded-xl border border-slate-800 text-center">
                           <p className="text-xs text-slate-500 uppercase font-bold">Trades Executed</p>
                           <p className="text-2xl font-mono text-white">0</p>
                       </div>
                   </div>
               )}

           </CardContent>
        </Card>

        {/* Kill Switch Area */}
        <Card className="border-red-900/30 bg-red-950/10">
            <CardContent className="p-6 flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <div className={cn("p-3 rounded-full", isKillSwitchActive ? "bg-red-500/20 text-red-500" : "bg-slate-800 text-slate-500")}>
                        <ShieldAlert className="w-6 h-6" />
                    </div>
                    <div>
                        <h3 className="font-bold text-slate-200">Global Kill Switch</h3>
                        <p className="text-sm text-slate-400">Instantly halt all activity and cancel orders.</p>
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
  );
}

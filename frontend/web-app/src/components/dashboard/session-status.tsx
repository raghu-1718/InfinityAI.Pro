'use client';

import { SessionState } from "@/hooks/useSessionState";
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";
import { ShieldCheck, ShieldAlert } from "lucide-react";

export function SessionStatus({ state }: { state: SessionState | null }) {
  if (!state) return null;

  if (state.halted) {
    return (
      <Alert variant="destructive" className="border-red-500/50 bg-red-900/20 text-red-200">
        <ShieldAlert className="h-5 w-5" />
        <AlertTitle className="text-lg font-bold">TRADING HALTED</AlertTitle>
        <AlertDescription>
          Safety Circuit Breaker Tripped. Reason: <span className="font-mono font-bold">{state.halt_reason || "UNKNOWN"}</span>
          <div className="mt-2 text-sm flex gap-4">
             <span>PnL: ₹{state.session_pnl.toFixed(2)}</span>
             <span>Consecutive Losses: {state.consecutive_losses}</span>
          </div>
        </AlertDescription>
      </Alert>
    );
  }

  // Active State (could be informative or just PnL)
  // Logic: Show if session_pnl is significantly active or losses > 0
  return (
      <Alert className="border-green-500/50 bg-green-900/10 text-green-200">
        <ShieldCheck className="h-5 w-5 text-green-500" />
        <AlertTitle className="text-green-400 font-bold flex items-center gap-2">
            Safety Systems Nominal
            <span className="text-xs font-normal text-muted-foreground ml-auto">Updated Live</span>
        </AlertTitle>
        <AlertDescription className="grid grid-cols-2 gap-4 mt-2">
           <div>
              <span className="text-muted-foreground text-xs block">Session PnL</span>
              <div className={`font-mono font-bold text-lg ${state.session_pnl >= 0 ? "text-green-400" : "text-red-400"}`}>
                {state.session_pnl >= 0 ? "+" : ""}₹{state.session_pnl.toFixed(2)}
              </div>
           </div>
           <div>
              <span className="text-muted-foreground text-xs block">Streak</span>
              <div className="font-mono text-lg">
                {state.consecutive_losses > 0 ? (
                    <span className="text-red-400">{state.consecutive_losses} Loss(es)</span>
                ) : (
                    <span className="text-green-500">Clean</span>
                )}
              </div>
           </div>
        </AlertDescription>
      </Alert>
  );
}

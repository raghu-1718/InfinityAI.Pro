'use client';

import { AuditEvent } from "@/hooks/useAuditTimeline";
import { ScrollArea } from "@/components/ui/scroll-area";
import { CheckCircle2, XCircle, AlertTriangle, Power, StopCircle, Info } from "lucide-react";
import { cn } from "@/lib/utils";

export function AuditTimeline({ events }: { events: AuditEvent[] }) {
  if (!events || events.length === 0) {
      return (
          <div className="text-center py-8 text-muted-foreground text-sm border border-dashed border-slate-800 rounded-lg">
              No audit logs available for this session.
          </div>
      );
  }

  return (
    <ScrollArea className="h-[400px] pr-4">
      <div className="space-y-4">
        {events.map((e, i) => {
            const date = new Date(e.timestamp);
            const timeStr = date.toLocaleTimeString(); 

            let Icon = Info;
            let iconColor = "text-slate-400";
            let borderColor = "border-slate-800";
            
            // Icon Logic based on Event Type
            if (e.event === "TRADE_APPROVED") { Icon = CheckCircle2; iconColor = "text-green-500"; borderColor = "border-green-900/30"; }
            else if (e.event === "TRADE_REJECTED") { Icon = XCircle; iconColor = "text-orange-500"; borderColor = "border-orange-900/30"; }
            else if (e.event.includes("KILL_SWITCH")) { Icon = AlertTriangle; iconColor = "text-red-500"; borderColor = "border-red-500/50"; }
            else if (e.event === "SESSION_START") { Icon = Power; iconColor = "text-blue-500"; }
            else if (e.event === "SESSION_STOP") { Icon = StopCircle; iconColor = "text-slate-400"; }

            return (
                <div key={i} className={cn("p-3 rounded-lg border bg-slate-950/50 relative overflow-hidden", borderColor)}>
                    <div className="flex gap-3 items-start relative z-10">
                        <Icon className={cn("w-5 h-5 mt-0.5", iconColor)} />
                        <div className="flex-1 space-y-1">
                            <div className="flex justify-between items-center">
                                <span className={cn("font-medium text-sm", iconColor)}>{e.event.replace(/_/g, " ")}</span>
                                <span className="text-xs text-muted-foreground font-mono">{timeStr}</span>
                            </div>
                            
                            {/* Render Details Generically but nicely */}
                            <div className="text-xs text-slate-300 font-mono space-y-1">
                                {Object.entries(e.details).map(([k, v]) => (
                                    <div key={k} className="flex gap-2">
                                        <span className="text-slate-500">{k}:</span>
                                        <span>
                                            {typeof v === 'object' ? JSON.stringify(v) : String(v)}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            );
        })}
      </div>
    </ScrollArea>
  );
}

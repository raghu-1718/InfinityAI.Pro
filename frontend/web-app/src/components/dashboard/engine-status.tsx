'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { useAppStore } from '@/lib/store';
import { Activity, Brain, Zap, Server, CheckCircle, XCircle, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

const engineInfo = {
  engineA: {
    name: 'Engine A',
    description: 'Orchestration & Risk Management',
    icon: Activity,
    color: 'text-blue-500',
  },
  engineB: {
    name: 'Engine B',
    description: 'AI/ML Intelligence',
    icon: Brain,
    color: 'text-purple-500',
  },
  engineC: {
    name: 'Engine C',
    description: 'DhanHQ Execution',
    icon: Zap,
    color: 'text-green-500',
  },
};

export function EngineStatusCards() {
  const engines = useAppStore((s) => s.engines);

  // Defensive fallback for engines
  const safeEngines = engines || {
    engineA: { status: 'loading', version: null, lastChecked: null, capabilities: [] },
    engineB: { status: 'loading', version: null, lastChecked: null, capabilities: [] },
    engineC: { status: 'loading', version: null, lastChecked: null, capabilities: [] },
  };

  const onlineCount = Object.values(safeEngines).filter((e) => e?.status === 'online').length;
  const healthPercent = (onlineCount / 3) * 100;

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium">System Health</CardTitle>
            <Badge variant={healthPercent === 100 ? 'default' : 'destructive'}>
              {onlineCount}/3 Online
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <Progress value={healthPercent} className="h-2" />
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-3">
        {(Object.keys(safeEngines) as Array<keyof typeof safeEngines>).map((key) => {
          const engine = safeEngines[key] || { status: 'loading', version: null, capabilities: [] };
          const info = engineInfo[key];
          if (!info) return null;
          const Icon = info.icon;

          return (
            <Card key={key} className="relative overflow-hidden">
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className={cn('rounded-lg bg-muted p-2', info.color)}>
                      <Icon className="h-4 w-4" />
                    </div>
                    <div>
                      <CardTitle className="text-sm font-medium">{info.name}</CardTitle>
                      <p className="text-xs text-muted-foreground">{info.description}</p>
                    </div>
                  </div>
                  <StatusIcon status={engine.status} />
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-muted-foreground">Version</span>
                  <span className="font-mono">{engine.version || 'N/A'}</span>
                </div>
                {engine.capabilities && Array.isArray(engine.capabilities) && engine.capabilities.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {engine.capabilities.slice(0, 3).map((cap) => (
                      <Badge key={cap} variant="secondary" className="text-[10px]">
                        {cap}
                      </Badge>
                    ))}
                    {engine.capabilities.length > 3 && (
                      <Badge variant="secondary" className="text-[10px]">
                        +{engine.capabilities.length - 3}
                      </Badge>
                    )}
                  </div>
                )}
              </CardContent>
              {/* Status indicator bar */}
              <div
                className={cn(
                  'absolute bottom-0 left-0 h-1 w-full',
                  engine.status === 'online' && 'bg-green-500',
                  engine.status === 'offline' && 'bg-red-500',
                  engine.status === 'loading' && 'bg-yellow-500'
                )}
              />
            </Card>
          );
        })}
      </div>
    </div>
  );
}

function StatusIcon({ status }: { status: string }) {
  if (status === 'online') {
    return <CheckCircle className="h-5 w-5 text-green-500" />;
  }
  if (status === 'offline') {
    return <XCircle className="h-5 w-5 text-red-500" />;
  }
  return <Loader2 className="h-5 w-5 animate-spin text-yellow-500" />;
}

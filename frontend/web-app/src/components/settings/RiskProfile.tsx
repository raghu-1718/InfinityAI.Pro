import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { Slider } from "@/components/ui/slider";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ShieldCheck, AlertTriangle, Save } from "lucide-react";
import { TradingSettings } from "@/lib/api";

interface RiskProfileProps {
  initialSettings: TradingSettings;
  onSave: (settings: TradingSettings) => void;
}

export function RiskProfile({ initialSettings, onSave }: RiskProfileProps) {
  const [settings, setSettings] = useState<TradingSettings>(initialSettings);
  const [hasChanges, setHasChanges] = useState(false);

  const handleChange = (key: keyof TradingSettings, value: any) => {
    setSettings(prev => ({ ...prev, [key]: value }));
    setHasChanges(true);
  };

  const riskScore = (settings.max_risk_per_trade * 100) * (settings.max_trades_per_day / 2);
  const riskLevel = riskScore < 5 ? "CONSERVATIVE" : riskScore < 15 ? "MODERATE" : "AGGRESSIVE";

  return (
    <Card className="w-full max-w-2xl border-sidebar-border">
      <CardHeader>
        <div className="flex justify-between items-center">
            <div>
                <CardTitle className="flex items-center gap-2">
                    <ShieldCheck className="w-5 h-5 text-primary" />
                    Risk Management Profile
                </CardTitle>
                <CardDescription>
                    Configure the automated risk guardrails for the AI.
                </CardDescription>
            </div>
            <Badge variant={riskLevel === "CONSERVATIVE" ? "secondary" : riskLevel === "MODERATE" ? "default" : "destructive"}>
                {riskLevel}
            </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-8">
        
        {/* Max Risk Per Trade */}
        <div className="space-y-4">
            <div className="flex justify-between">
                <Label className="text-base font-semibold">Max Risk Per Trade</Label>
                <span className="font-mono text-primary font-bold">{(settings.max_risk_per_trade * 100).toFixed(1)}%</span>
            </div>
            <Slider 
                value={[settings.max_risk_per_trade * 100]} 
                min={0.1} 
                max={5.0} 
                step={0.1}
                onValueChange={(val) => handleChange('max_risk_per_trade', val[0] / 100)}
            />
            <p className="text-xs text-muted-foreground">
                The AI will size positions such that you never lose more than this % of capital in a single trade if the Stop Loss is hit.
            </p>
        </div>

        {/* Max Trades Per Day */}
        <div className="space-y-4">
            <div className="flex justify-between">
                <Label className="text-base font-semibold">Max Trades / Day</Label>
                <span className="font-mono text-primary font-bold">{settings.max_trades_per_day}</span>
            </div>
            <Slider 
                value={[settings.max_trades_per_day]} 
                min={1} 
                max={20} 
                step={1}
                onValueChange={(val) => handleChange('max_trades_per_day', val[0])}
            />
        </div>

        {/* Trailing Stop Loss */}
        <div className="flex items-center justify-between p-4 border rounded-lg bg-secondary/20">
            <div className="space-y-0.5">
                <Label className="text-base">Trailing Stop Loss</Label>
                <p className="text-xs text-muted-foreground">Automatically move SL to break-even after 1% profit.</p>
            </div>
            <Switch 
                checked={settings.trailing_stop_loss}
                onCheckedChange={(val) => handleChange('trailing_stop_loss', val)}
            />
        </div>

         {/* Emergency Stop */}
         <div className="p-4 border border-destructive/30 bg-destructive/5 rounded-lg flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-destructive mt-0.5" />
            <div className="space-y-1">
                <Label className="text-destructive font-bold">Kill Switch Logic</Label>
                <p className="text-xs text-muted-foreground">
                    If Drawdown exceeds <span className="font-mono font-bold text-foreground">{(settings.max_capital * 0.1).toLocaleString()}</span> (10%), all trading will halt immediately.
                </p>
            </div>
         </div>

      </CardContent>
      <CardFooter className="flex justify-end border-t bg-secondary/10 p-4">
        <Button onClick={() => onSave(settings)} disabled={!hasChanges} className="gap-2">
            <Save className="w-4 h-4" />
            Save Profile
        </Button>
      </CardFooter>
    </Card>
  );
}

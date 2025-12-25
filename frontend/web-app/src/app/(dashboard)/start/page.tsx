"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { useSystemState } from "@/hooks/useApi";
import { engineA } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Rocket, ShieldAlert, BadgeIndianRupee, Activity } from "lucide-react";
import { toast } from "sonner";
import { getUserId } from "@/lib/user";

export default function StartEnginePage() {
  const router = useRouter();
  const { data: systemState } = useSystemState();
  
  const [capital, setCapital] = useState("100000");
  const [riskMode, setRiskMode] = useState("conservative");
  const [assetClass, setAssetClass] = useState("equities");
  const [isStarting, setIsStarting] = useState(false);

  // If engine is already active, redirect to dashboard
  React.useEffect(() => {
    if (systemState?.engine_active) {
      router.push("/dashboard");
    }
  }, [systemState, router]);

  const handleStart = async () => {
    const userId = getUserId(); // Or get from auth context
    if (!userId) {
        toast.error("User ID not found. Please login.");
        return;
    }

    if (!capital || parseFloat(capital) <= 0) {
        toast.error("Please enter valid capital.");
        return;
    }

    setIsStarting(true);
    try {
        await engineA.startSession({
            capital: parseFloat(capital),
            risk_mode: riskMode,
            asset_class: assetClass,
            user_id: userId
        });
        toast.success("Engine Started Successfully!", {
            description: "Redirecting to Command Center..."
        });
        
        // Wait a moment for state to propagate then redirect
        setTimeout(() => router.push("/dashboard"), 1500);

    } catch (error: any) {
        toast.error("Failed to start engine", {
            description: error.message || "Unknown error"
        });
        setIsStarting(false);
    }
  };

  return (
    <div className="container mx-auto max-w-2xl min-h-screen flex flex-col justify-center p-6">
      <div className="mb-8 text-center space-y-2">
        <h1 className="text-4xl font-bold tracking-tight">System Launch</h1>
        <p className="text-muted-foreground">Configure immutable session parameters for autonomous trading.</p>
      </div>

      <Card className="border-2 shadow-lg">
        <CardHeader className="bg-muted/50 pb-8">
            <div className="flex items-center gap-2 mb-2">
                <Rocket className="w-5 h-5 text-primary" />
                <CardTitle>Session Configuration</CardTitle>
            </div>
            <CardDescription>
                These parameters are locked for the duration of the session.
            </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6 pt-6">
            
            {/* Capital Input */}
            <div className="space-y-2">
                <Label className="flex items-center gap-2">
                    <BadgeIndianRupee className="w-4 h-4" />
                    Capital Allocation
                </Label>
                <Input 
                    type="number" 
                    value={capital} 
                    onChange={(e) => setCapital(e.target.value)}
                    className="text-lg font-mono"
                />
                <p className="text-xs text-muted-foreground">Virtual capital limit for risk sizing.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Risk Mode */}
                <div className="space-y-2">
                    <Label className="flex items-center gap-2">
                        <ShieldAlert className="w-4 h-4" />
                        Risk Profile
                    </Label>
                    <Select value={riskMode} onValueChange={setRiskMode}>
                        <SelectTrigger>
                            <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="conservative">Conservative (Low Risk)</SelectItem>
                            <SelectItem value="moderate">Moderate (Balanced)</SelectItem>
                            <SelectItem value="aggressive">Aggressive (High Risk)</SelectItem>
                        </SelectContent>
                    </Select>
                </div>

                {/* Asset Class */}
                <div className="space-y-2">
                    <Label className="flex items-center gap-2">
                        <Activity className="w-4 h-4" />
                        Asset Class
                    </Label>
                    <Select value={assetClass} onValueChange={setAssetClass}>
                        <SelectTrigger>
                            <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="equities">Equities (Intraday)</SelectItem>
                            <SelectItem value="fno">F&O (Derivatives)</SelectItem>
                            <SelectItem value="commodities">Commodities</SelectItem>
                        </SelectContent>
                    </Select>
                </div>
            </div>

            <div className="pt-6">
                <Button 
                    className="w-full h-12 text-lg font-semibold bg-green-600 hover:bg-green-700 text-white"
                    onClick={handleStart}
                    disabled={isStarting}
                >
                    {isStarting ? "Initializing System..." : "INITIATE LAUNCH SEQUENCE"}
                </Button>
                <p className="text-center text-xs text-muted-foreground mt-4">
                    By starting, you acknowledge the risk of autonomous trading logic.
                </p>
            </div>

        </CardContent>
      </Card>
    </div>
  );
}

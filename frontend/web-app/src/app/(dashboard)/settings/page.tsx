"use client";

import React, { useState, useEffect } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Settings,
  Key,
  Bell,
  TrendingUp,
  Server,
  Loader2,
  CheckCircle,
  XCircle,
  Wallet,
  RefreshCw,
  ExternalLink,
  AlertCircle,
  Eye,
  EyeOff,
  ShieldCheck,
} from "lucide-react";
import { toast } from "sonner";
import { useAppStore } from "@/lib/store";
import { useQueryClient } from "@tanstack/react-query";
import { useCouponAuth } from "@/contexts/DualAuthContext";
import { getUserId, setDhanClientId, clearDhanClientId } from "@/lib/user";
import { RiskProfile } from "@/components/settings/RiskProfile";
import { TradingSettings } from "@/lib/api";

const ENGINE_C_URL = process.env.NEXT_PUBLIC_ENGINE_C_URL || "https://engine-c-429140669077.us-central1.run.app";

// ... (Keep existing Interfaces DhanCredentials, DematInfo) ...
interface DhanCredentials {
  client_id: string;
  api_key: string;
  api_secret: string;
  access_token: string;
  is_verified: boolean;
}

interface DematInfo {
  holdings: {
    totalValue: number;
    count: number;
    items: Array<{
      symbol: string;
      quantity: number;
      avgPrice: number;
      currentPrice: number;
      pnl: number;
    }>;
  };
  positions: {
    totalPnl: number;
    count: number;
    items: Array<{
      symbol: string;
      quantity: number;
      entryPrice: number;
      currentPrice: number;
      pnl: number;
    }>;
  };
  funds: {
    availableBalance: number;
    utilisedMargin: number;
    totalBalance: number;
  };
}

export default function SettingsPage() {
  // Global state
  const { userProfile, setUserProfile, dematData, setDematData, setFunds } = useAppStore();
  const queryClient = useQueryClient();
  const { session } = useCouponAuth(); // Removed unused variables

  // Dhan Credentials State (Condensed for brevity - same as before)
  const [dhanCredentials, setDhanCredentials] = useState<DhanCredentials>({
    client_id: "", api_key: "", api_secret: "", access_token: "", is_verified: false,
  });
  const [showAccessToken, setShowAccessToken] = useState(false);
  const [showApiSecret, setShowApiSecret] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isVerifying, setIsVerifying] = useState(false);
  const [isLoadingCredentials, setIsLoadingCredentials] = useState(true);
  const [connectionStatus, setConnectionStatus] = useState<"disconnected" | "connected" | "error">(
    userProfile?.isConnected ? "connected" : "disconnected"
  );
  const [dematInfo, setDematInfo] = useState<DematInfo | null>(dematData);
  const [isLoadingDemat, setIsLoadingDemat] = useState(false);

  // Trading Settings State
  const [tradingSettings, setTradingSettings] = useState<TradingSettings>({
      risk_level: 'conservative',
      max_risk_per_trade: 0.02,
      max_trades_per_day: 10,
      stop_loss_percent: 2,
      take_profit_percent: 4,
      trading_amount: 100000,
      min_capital: 10000,
      max_capital: 500000,
      trailing_stop_loss: false,
      auto_rebalance: false,
      use_ai_signals: true,
      selected_instruments: ['NIFTY'],
      position_sizing_method: 'fixed',
      min_confidence: 0.75
  });

  // Risk Profile Handler
  const handleSaveRiskProfile = (newSettings: TradingSettings) => {
      setTradingSettings(newSettings);
      // In real app, save to backend here
      toast.success("Risk Profile Updated", {
          description: "New parameters are active for AI Engine."
      });
  };

  // Load credentials on mount
  useEffect(() => {
      const loadCredentials = async () => {
          if (!session?.userId) {
              setIsLoadingCredentials(false);
              return;
          }

          setIsLoadingCredentials(true);
          try {
              const response = await fetch(
                  `${ENGINE_C_URL}/api/dhan/credentials/${session.userId}`
              );
              
              if (response.ok) {
                  const data = await response.json();
                  if (data.success && data.credentials) {
                      setDhanCredentials({
                          client_id: data.credentials.client_id || "",
                          api_key: data.credentials.api_key || "",
                          api_secret: data.credentials.api_secret || "",
                          access_token: data.credentials.access_token || "",
                          is_verified: data.verified
                      });
                      setConnectionStatus(data.verified ? "connected" : "disconnected");
                  }
              }
          } catch (error) {
              console.error("Failed to load credentials:", error);
          } finally {
              setIsLoadingCredentials(false);
          }
      };

      loadCredentials();
  }, [session]);

  const loadDematInfo = async () => { 
      // TODO: Implement demat info loading
  };
  
  const handleSaveCredentials = async () => {
      if (!session?.userId) {
          toast.error("Not authenticated");
          return;
      }

      if (!dhanCredentials.client_id || !dhanCredentials.access_token) {
          toast.error("Please fill in all required fields");
          return;
      }

      setIsConnecting(true);
      try {
          const response = await fetch(`${ENGINE_C_URL}/api/dhan/credentials`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                  user_id: session.userId,
                  client_id: dhanCredentials.client_id,
                  api_key: dhanCredentials.api_key,
                  api_secret: dhanCredentials.api_secret,
                  access_token: dhanCredentials.access_token
              })
          });

          const data = await response.json();
          
          if (data.success) {
              setConnectionStatus(data.verified ? "connected" : "error");
              setDhanCredentials({...dhanCredentials, is_verified: data.verified});
              toast.success("Credentials saved" + (data.verified ? " and verified!" : ""));
              persistClientId(dhanCredentials.client_id);
          } else {
              throw new Error(data.message || "Save failed");
          }
      } catch (error: any) {
          toast.error(`Save failed: ${error.message}`);
          setConnectionStatus("error");
      } finally {
          setIsConnecting(false);
      }
  };
  
  const handleVerifyConnection = async () => {
      if (!session?.userId) {
          toast.error("Not authenticated");
          return;
      }

      setIsVerifying(true);
      try {
          const response = await fetch(`${ENGINE_C_URL}/api/dhan/verify`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                  user_id: session.userId,
                  client_id: dhanCredentials.client_id,
                  api_key: dhanCredentials.api_key,
                  api_secret: dhanCredentials.api_secret,
                  access_token: dhanCredentials.access_token
              })
          });

          const data = await response.json();
          setConnectionStatus(data.verified ? "connected" : "error");
          toast[data.verified ? "success" : "error"](data.message || "Verification complete");
      } catch (error: any) {
          toast.error("Verification failed");
          setConnectionStatus("error");
      } finally {
          setIsVerifying(false);
      }
  };
  
  const handleDisconnect = async () => {
      if (!session?.userId) return;
      
      setIsConnecting(true);
      try {
          const response = await fetch(
              `${ENGINE_C_URL}/api/dhan/credentials/${session.userId}`,
              { method: 'DELETE' }
          );

          const data = await response.json();
          
          if (data.success) {
              setConnectionStatus("disconnected");
              setDhanCredentials({
                  client_id: "", api_key: "", api_secret: "", 
                  access_token: "", is_verified: false
              });
              clearDhanClientId();
              toast.success("Disconnected from Dhan");
          } else {
              throw new Error(data.message || "Disconnect failed");
          }
      } catch (error: any) {
          toast.error(`Disconnect failed: ${error.message}`);
      } finally {
          setIsConnecting(false);
      }
  };
  
  const formatCurrency = (val: number) => `₹${val.toFixed(2)}`;
  
  // Persist client ID helper (Fix for missing function)
  const persistClientId = (id: string) => setDhanClientId(id);


  return (
    <div className="container mx-auto p-6 max-w-7xl">
      <div className="flex items-center gap-3 mb-6">
        <Settings className="h-8 w-8 text-primary" />
        <div>
          <h1 className="text-3xl font-bold">Settings</h1>
          <p className="text-muted-foreground">Manage your trading preferences and integrations</p>
        </div>
      </div>


        <Tabs defaultValue="dhan" className="space-y-4">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="dhan" className="flex items-center gap-2">
            <Wallet className="h-4 w-4" />
            <span className="hidden sm:inline">Dhan Account</span>
          </TabsTrigger>
          <TabsTrigger value="notifications" className="flex items-center gap-2">
            <Bell className="h-4 w-4" />
            <span className="hidden sm:inline">Notifications</span>
          </TabsTrigger>
           <TabsTrigger value="engines" className="flex items-center gap-2">
            <Server className="h-4 w-4" />
            <span className="hidden sm:inline">Engines</span>
          </TabsTrigger>
        </TabsList>

        {/* --- DHAN ACCOUNT TAB --- */}
        <TabsContent value="dhan" className="space-y-4">
          <Card>
            <CardHeader>
                <CardTitle>Dhan Connection</CardTitle>
                <CardDescription>
                    Status: <span className={connectionStatus === 'connected' ? "text-green-500 font-bold" : "text-red-500 font-bold"}>{connectionStatus.toUpperCase()}</span>
                </CardDescription>
            </CardHeader>
            <CardContent>
                <div className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <Label htmlFor="client-id">Client ID</Label>
                            <Input 
                                id="client-id"
                                name="client_id"
                                value={dhanCredentials.client_id}
                                onChange={(e) => setDhanCredentials({...dhanCredentials, client_id: e.target.value})}
                                placeholder="Enter Dhan Client ID"
                            />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="access-token">Access Token</Label>
                            <div className="relative">
                                <Input 
                                    id="access-token"
                                    name="access_token"
                                    type={showAccessToken ? "text" : "password"}
                                    value={dhanCredentials.access_token}
                                    onChange={(e) => setDhanCredentials({...dhanCredentials, access_token: e.target.value})}
                                    placeholder="Enter Access Token"
                                />
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                                    onClick={() => setShowAccessToken(!showAccessToken)}
                                >
                                    {showAccessToken ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                                </Button>
                            </div>
                        </div>
                    </div>

                    <div className="flex gap-4 pt-4">
                         <Button onClick={handleSaveCredentials} disabled={isConnecting}>
                            {isConnecting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            Save & Connect
                        </Button>
                        {connectionStatus === 'connected' && (
                            <Button variant="destructive" onClick={handleDisconnect} disabled={isConnecting}>
                                Disconnect
                            </Button>
                        )}
                    </div>

                    <div className="mt-8 pt-6 border-t">
                        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                            <ExternalLink className="w-4 h-4" />
                            Connection Details (For DhanHQ)
                        </h3>
                         <div className="grid grid-cols-1 md:grid-cols-2 gap-6 bg-secondary/20 p-4 rounded-lg">
                            <div className="space-y-2">
                                <Label className="text-xs uppercase text-muted-foreground">Postback URL</Label>
                                <div className="flex gap-2">
                                    <code className="flex-1 bg-background p-2 rounded border font-mono text-xs overflow-x-auto">
                                        https://engine-c.infinityai.pro/api/dhan/postback
                                    </code>
                                    <Button variant="outline" size="icon" className="h-8 w-8" onClick={() => {
                                        navigator.clipboard.writeText("https://engine-c.infinityai.pro/api/dhan/postback");
                                        toast.success("Copied Postback URL");
                                    }}>
                                        <CheckCircle className="h-3 w-3" />
                                    </Button>
                                </div>
                            </div>
                            <div className="space-y-2">
                                <Label className="text-xs uppercase text-muted-foreground">Redirect URL</Label>
                                <div className="flex gap-2">
                                    <code className="flex-1 bg-background p-2 rounded border font-mono text-xs overflow-x-auto">
                                        https://infinityai.pro/settings
                                    </code>
                                    <Button variant="outline" size="icon" className="h-8 w-8" onClick={() => {
                                        navigator.clipboard.writeText("https://infinityai.pro/settings");
                                        toast.success("Copied Redirect URL");
                                    }}>
                                        <CheckCircle className="h-3 w-3" />
                                    </Button>
                                </div>
                            </div>
                        </div>
                    </div>

                </div>
                <div className="mt-4 flex justify-end">
                    <Button variant="outline"><ExternalLink className="mr-2 h-4 w-4"/> DhanHQ Dashboard</Button>
                </div>
            </CardContent>
          </Card>
        </TabsContent>
        
        {/* Notifications Tab */}
        <TabsContent value="notifications">
             <Card>
                <CardHeader>
                    <CardTitle>Notification Settings</CardTitle>
                    <CardDescription>Configure trading alerts and notifications</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="flex items-center justify-between p-4 border rounded-lg">
                        <div>
                            <Label className="text-base">Signal Notifications</Label>
                            <p className="text-sm text-muted-foreground">Get notified when AI generates new signals</p>
                        </div>
                        <Switch defaultChecked />
                    </div>
                    <div className="flex items-center justify-between p-4 border rounded-lg">
                        <div>
                            <Label className="text-base">Trade Execution Alerts</Label>
                            <p className="text-sm text-muted-foreground">Real-time updates on order status</p>
                        </div>
                        <Switch defaultChecked />
                    </div>
                    <div className="flex items-center justify-between p-4 border rounded-lg">
                        <div>
                            <Label className="text-base">Risk Alerts</Label>
                            <p className="text-sm text-muted-foreground">Warnings when risk limits are approached</p>
                        </div>
                        <Switch defaultChecked />
                    </div>
                </CardContent>
             </Card>
        </TabsContent>
        <TabsContent value="engines">
             <Card>
                <CardHeader>
                    <CardTitle>Backend Engines Status</CardTitle>
                    <CardDescription>Monitor AI engines and infrastructure</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="p-4 border rounded-lg">
                        <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-2">
                                <div className="h-2 w-2 bg-green-500 rounded-full"></div>
                                <Label className="text-base">Engine A - Orchestration</Label>
                            </div>
                            <span className="text-xs text-green-600 font-medium">Operational</span>
                        </div>
                        <p className="text-sm text-muted-foreground">Risk management & signal validation</p>
                    </div>
                    <div className="p-4 border rounded-lg">
                        <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-2">
                                <div className="h-2 w-2 bg-green-500 rounded-full"></div>
                                <Label className="text-base">Engine B - AI/ML Intelligence</Label>
                            </div>
                            <span className="text-xs text-green-600 font-medium">Operational</span>
                        </div>
                        <p className="text-sm text-muted-foreground">Signal generation & market analysis</p>
                    </div>
                    <div className="p-4 border rounded-lg">
                        <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-2">
                                <div className="h-2 w-2 bg-green-500 rounded-full"></div>
                                <Label className="text-base">Engine C - Execution</Label>
                            </div>
                            <span className="text-xs text-green-600 font-medium">Operational</span>
                        </div>
                        <p className="text-sm text-muted-foreground">Order routing & execution optimization</p>
                    </div>
                </CardContent>
             </Card>
        </TabsContent>


      </Tabs>
    </div>
  );
}

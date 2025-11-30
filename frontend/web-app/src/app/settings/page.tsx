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
  Save,
  Loader2,
  CheckCircle,
  XCircle,
  Wallet,
  RefreshCw,
  ExternalLink,
  AlertCircle,
  Eye,
  EyeOff,
} from "lucide-react";
import { toast } from "sonner";

// Engine C API URL
const ENGINE_C_URL = process.env.NEXT_PUBLIC_ENGINE_C_URL || "https://engine-c-573866363639.us-central1.run.app";

interface DhanCredentials {
  client_id: string;
  api_key: string;
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
  // Dhan Credentials State
  const [dhanCredentials, setDhanCredentials] = useState<DhanCredentials>({
    client_id: "",
    api_key: "",
    access_token: "",
    is_verified: false,
  });
  const [showAccessToken, setShowAccessToken] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isVerifying, setIsVerifying] = useState(false);
  const [isLoadingCredentials, setIsLoadingCredentials] = useState(true);
  const [connectionStatus, setConnectionStatus] = useState<"disconnected" | "connected" | "error">("disconnected");
  const [dematInfo, setDematInfo] = useState<DematInfo | null>(null);
  const [isLoadingDemat, setIsLoadingDemat] = useState(false);

  // Other Settings State
  const [emailNotifications, setEmailNotifications] = useState(true);
  const [pushNotifications, setPushNotifications] = useState(true);
  const [tradeAlerts, setTradeAlerts] = useState(true);
  const [dailyReports, setDailyReports] = useState(false);
  const [riskLevel, setRiskLevel] = useState("medium");
  const [maxPositionSize, setMaxPositionSize] = useState("25000");
  const [stopLossPercent, setStopLossPercent] = useState("2");
  const [autoTrading, setAutoTrading] = useState(false);

  // Get user ID (for now using a placeholder - integrate with your auth system)
  const getUserId = () => {
    // TODO: Replace with actual user ID from authentication
    return localStorage.getItem("userId") || "default_user";
  };

  // Load existing credentials on mount
  useEffect(() => {
    const loadCreds = async () => {
      setIsLoadingCredentials(true);
      try {
        const userId = getUserId();
        const response = await fetch(`${ENGINE_C_URL}/api/user/credentials?user_id=${userId}`);

        if (response.ok) {
          const data = await response.json();
          setDhanCredentials({
            client_id: data.client_id || "",
            api_key: data.api_key || "",
            access_token: data.access_token ? "********" : "",
            is_verified: data.is_verified || false,
          });
          if (data.is_verified) {
            setConnectionStatus("connected");
          }
        }
      } catch (error) {
        console.error("Failed to load credentials:", error);
      } finally {
        setIsLoadingCredentials(false);
      }
    };
    loadCreds();
  }, []);

  const loadDematInfo = async () => {
    setIsLoadingDemat(true);
    try {
      const userId = getUserId();
      const response = await fetch(`${ENGINE_C_URL}/api/user/demat?user_id=${userId}`);

      if (response.ok) {
        const data = await response.json();
        setDematInfo(data);
      }
    } catch (error) {
      console.error("Failed to load demat info:", error);
    } finally {
      setIsLoadingDemat(false);
    }
  };

  const handleSaveCredentials = async () => {
    if (!dhanCredentials.client_id || !dhanCredentials.access_token) {
      toast.error("Missing Required Fields", {
        description: "Client ID and Access Token are required to connect your Dhan account.",
      });
      return;
    }

    setIsConnecting(true);
    try {
      const userId = getUserId();
      const response = await fetch(`${ENGINE_C_URL}/api/user/credentials`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          user_id: userId,
          client_id: dhanCredentials.client_id,
          api_key: dhanCredentials.api_key || undefined,
          access_token: dhanCredentials.access_token.includes("*") ? undefined : dhanCredentials.access_token,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setConnectionStatus(data.is_verified ? "connected" : "error");

        if (data.is_verified) {
          toast.success("Dhan Connected Successfully", {
            description: "Your Dhan account has been linked. Loading your portfolio...",
          });
          // Mask the access token after successful save
          setDhanCredentials(prev => ({
            ...prev,
            access_token: "********",
            is_verified: true,
          }));
          loadDematInfo();
        } else {
          toast.warning("Credentials Saved", {
            description: "Credentials saved but verification pending. Please verify your connection.",
          });
        }
      } else {
        const error = await response.json();
        toast.error("Connection Failed", {
          description: error.detail || "Failed to save credentials. Please check your details.",
        });
        setConnectionStatus("error");
      }
    } catch (error) {
      console.error("Failed to save credentials:", error);
      toast.error("Connection Error", {
        description: "Network error. Please check your internet connection and try again.",
      });
      setConnectionStatus("error");
    } finally {
      setIsConnecting(false);
    }
  };

  const handleVerifyConnection = async () => {
    setIsVerifying(true);
    try {
      const userId = getUserId();
      const response = await fetch(`${ENGINE_C_URL}/api/user/credentials/verify?user_id=${userId}`);

      if (response.ok) {
        const data = await response.json();
        if (data.is_verified) {
          setConnectionStatus("connected");
          toast.success("Connection Verified", {
            description: "Your Dhan account is connected and working properly.",
          });
          loadDematInfo();
        } else {
          setConnectionStatus("error");
          toast.error("Verification Failed", {
            description: data.message || "Could not verify Dhan connection. Please update your access token.",
          });
        }
      }
    } catch (error) {
      console.error("Verification failed:", error);
      setConnectionStatus("error");
      toast.error("Verification Error", {
        description: "Failed to verify connection. Please try again.",
      });
    } finally {
      setIsVerifying(false);
    }
  };

  const handleDisconnect = async () => {
    if (!confirm("Are you sure you want to disconnect your Dhan account?")) return;

    try {
      const userId = getUserId();
      const response = await fetch(`${ENGINE_C_URL}/api/user/credentials?user_id=${userId}`, {
        method: "DELETE",
      });

      if (response.ok) {
        setDhanCredentials({
          client_id: "",
          api_key: "",
          access_token: "",
          is_verified: false,
        });
        setConnectionStatus("disconnected");
        setDematInfo(null);
        toast.info("Disconnected", {
          description: "Your Dhan account has been disconnected.",
        });
      }
    } catch (error) {
      console.error("Failed to disconnect:", error);
      toast.error("Error", {
        description: "Failed to disconnect. Please try again.",
      });
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 2,
    }).format(value);
  };

  return (
    <div className="container mx-auto p-6">
      <div className="flex items-center gap-3 mb-6">
        <Settings className="h-8 w-8 text-primary" />
        <div>
          <h1 className="text-3xl font-bold">Settings</h1>
          <p className="text-muted-foreground">Manage your trading preferences and integrations</p>
        </div>
      </div>

      <Tabs defaultValue="dhan" className="space-y-4">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="dhan" className="flex items-center gap-2">
            <Wallet className="h-4 w-4" />
            <span className="hidden sm:inline">Dhan Account</span>
          </TabsTrigger>
          <TabsTrigger value="general" className="flex items-center gap-2">
            <Settings className="h-4 w-4" />
            <span className="hidden sm:inline">General</span>
          </TabsTrigger>
          <TabsTrigger value="notifications" className="flex items-center gap-2">
            <Bell className="h-4 w-4" />
            <span className="hidden sm:inline">Notifications</span>
          </TabsTrigger>
          <TabsTrigger value="trading" className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            <span className="hidden sm:inline">Trading</span>
          </TabsTrigger>
          <TabsTrigger value="engines" className="flex items-center gap-2">
            <Server className="h-4 w-4" />
            <span className="hidden sm:inline">Engines</span>
          </TabsTrigger>
        </TabsList>

        {/* Dhan Account Tab */}
        <TabsContent value="dhan" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <Wallet className="h-5 w-5" />
                    Connect Your Dhan Account
                  </CardTitle>
                  <CardDescription>
                    Link your Dhan demat account to enable live trading and portfolio tracking
                  </CardDescription>
                </div>
                <div className="flex items-center gap-2">
                  {connectionStatus === "connected" && (
                    <span className="flex items-center gap-1 text-sm text-green-600 bg-green-100 px-3 py-1 rounded-full">
                      <CheckCircle className="h-4 w-4" />
                      Connected
                    </span>
                  )}
                  {connectionStatus === "error" && (
                    <span className="flex items-center gap-1 text-sm text-red-600 bg-red-100 px-3 py-1 rounded-full">
                      <XCircle className="h-4 w-4" />
                      Error
                    </span>
                  )}
                  {connectionStatus === "disconnected" && (
                    <span className="flex items-center gap-1 text-sm text-gray-600 bg-gray-100 px-3 py-1 rounded-full">
                      <AlertCircle className="h-4 w-4" />
                      Not Connected
                    </span>
                  )}
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              {isLoadingCredentials ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                </div>
              ) : (
                <>
                  {/* Credential Input Form */}
                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="space-y-2">
                      <Label htmlFor="client_id">Client ID *</Label>
                      <Input
                        id="client_id"
                        placeholder="Enter your Dhan Client ID"
                        value={dhanCredentials.client_id}
                        onChange={(e) => setDhanCredentials(prev => ({ ...prev, client_id: e.target.value }))}
                        disabled={connectionStatus === "connected"}
                      />
                      <p className="text-xs text-muted-foreground">
                        Your unique Dhan trading account ID
                      </p>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="api_key">API Key (Optional)</Label>
                      <Input
                        id="api_key"
                        placeholder="Enter your Dhan API Key"
                        value={dhanCredentials.api_key}
                        onChange={(e) => setDhanCredentials(prev => ({ ...prev, api_key: e.target.value }))}
                        disabled={connectionStatus === "connected"}
                      />
                      <p className="text-xs text-muted-foreground">
                        Leave blank to use system market data API
                      </p>
                    </div>

                    <div className="space-y-2 md:col-span-2">
                      <Label htmlFor="access_token">Access Token *</Label>
                      <div className="relative">
                        <Input
                          id="access_token"
                          type={showAccessToken ? "text" : "password"}
                          placeholder="Enter your Dhan Access Token"
                          value={dhanCredentials.access_token}
                          onChange={(e) => setDhanCredentials(prev => ({ ...prev, access_token: e.target.value }))}
                          disabled={connectionStatus === "connected"}
                          className="pr-10"
                        />
                        <button
                          type="button"
                          onClick={() => setShowAccessToken(!showAccessToken)}
                          className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                        >
                          {showAccessToken ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                        </button>
                      </div>
                      <p className="text-xs text-muted-foreground">
                        Generate from{" "}
                        <a
                          href="https://dhanhq.co/dashboard"
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-primary hover:underline inline-flex items-center gap-1"
                        >
                          Dhan Dashboard <ExternalLink className="h-3 w-3" />
                        </a>
                        . Token expires daily - update as needed.
                      </p>
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex flex-wrap gap-3">
                    {connectionStatus !== "connected" ? (
                      <Button
                        onClick={handleSaveCredentials}
                        disabled={isConnecting || !dhanCredentials.client_id || !dhanCredentials.access_token}
                      >
                        {isConnecting ? (
                          <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            Connecting...
                          </>
                        ) : (
                          <>
                            <Wallet className="mr-2 h-4 w-4" />
                            Connect Dhan Account
                          </>
                        )}
                      </Button>
                    ) : (
                      <>
                        <Button
                          variant="outline"
                          onClick={handleVerifyConnection}
                          disabled={isVerifying}
                        >
                          {isVerifying ? (
                            <>
                              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                              Verifying...
                            </>
                          ) : (
                            <>
                              <RefreshCw className="mr-2 h-4 w-4" />
                              Verify Connection
                            </>
                          )}
                        </Button>
                        <Button
                          variant="outline"
                          onClick={() => {
                            setConnectionStatus("disconnected");
                            setDhanCredentials(prev => ({ ...prev, access_token: "" }));
                          }}
                        >
                          <Key className="mr-2 h-4 w-4" />
                          Update Token
                        </Button>
                        <Button variant="destructive" onClick={handleDisconnect}>
                          <XCircle className="mr-2 h-4 w-4" />
                          Disconnect
                        </Button>
                      </>
                    )}
                  </div>
                </>
              )}
            </CardContent>
          </Card>

          {/* Portfolio Summary Card - Only show when connected */}
          {connectionStatus === "connected" && (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Your Portfolio</CardTitle>
                    <CardDescription>Real-time view of your Dhan demat account</CardDescription>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={loadDematInfo}
                    disabled={isLoadingDemat}
                  >
                    {isLoadingDemat ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <RefreshCw className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {isLoadingDemat ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                  </div>
                ) : dematInfo ? (
                  <div className="grid gap-4 md:grid-cols-3">
                    {/* Funds */}
                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-muted-foreground">
                          Available Funds
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold text-green-600">
                          {formatCurrency(dematInfo.funds?.availableBalance || 0)}
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">
                          Margin Used: {formatCurrency(dematInfo.funds?.utilisedMargin || 0)}
                        </p>
                      </CardContent>
                    </Card>

                    {/* Holdings */}
                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-muted-foreground">
                          Holdings Value
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold">
                          {formatCurrency(dematInfo.holdings?.totalValue || 0)}
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">
                          {dematInfo.holdings?.count || 0} stocks
                        </p>
                      </CardContent>
                    </Card>

                    {/* Positions P&L */}
                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-muted-foreground">
                          Today&apos;s P&amp;L
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className={`text-2xl font-bold ${(dematInfo.positions?.totalPnl || 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {formatCurrency(dematInfo.positions?.totalPnl || 0)}
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">
                          {dematInfo.positions?.count || 0} open positions
                        </p>
                      </CardContent>
                    </Card>
                  </div>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    <Wallet className="h-12 w-12 mx-auto mb-3 opacity-50" />
                    <p>No portfolio data available</p>
                    <p className="text-sm">Click refresh to load your portfolio</p>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* General Settings Tab */}
        <TabsContent value="general">
          <Card>
            <CardHeader>
              <CardTitle>General Settings</CardTitle>
              <CardDescription>Configure your basic preferences</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="timezone">Timezone</Label>
                <Select defaultValue="ist">
                  <SelectTrigger>
                    <SelectValue placeholder="Select timezone" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ist">India Standard Time (IST)</SelectItem>
                    <SelectItem value="utc">UTC</SelectItem>
                    <SelectItem value="est">Eastern Time (EST)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="language">Language</Label>
                <Select defaultValue="en">
                  <SelectTrigger>
                    <SelectValue placeholder="Select language" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="en">English</SelectItem>
                    <SelectItem value="hi">Hindi</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Dark Mode</Label>
                  <p className="text-sm text-muted-foreground">Toggle dark theme</p>
                </div>
                <Switch defaultChecked />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Notifications Tab */}
        <TabsContent value="notifications">
          <Card>
            <CardHeader>
              <CardTitle>Notification Preferences</CardTitle>
              <CardDescription>Manage how you receive alerts and updates</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Email Notifications</Label>
                  <p className="text-sm text-muted-foreground">Receive email updates</p>
                </div>
                <Switch
                  checked={emailNotifications}
                  onCheckedChange={setEmailNotifications}
                />
              </div>
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Push Notifications</Label>
                  <p className="text-sm text-muted-foreground">Receive push notifications</p>
                </div>
                <Switch
                  checked={pushNotifications}
                  onCheckedChange={setPushNotifications}
                />
              </div>
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Trade Alerts</Label>
                  <p className="text-sm text-muted-foreground">Get notified on trade executions</p>
                </div>
                <Switch
                  checked={tradeAlerts}
                  onCheckedChange={setTradeAlerts}
                />
              </div>
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Daily Reports</Label>
                  <p className="text-sm text-muted-foreground">Receive daily P&L summary</p>
                </div>
                <Switch
                  checked={dailyReports}
                  onCheckedChange={setDailyReports}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Trading Settings Tab */}
        <TabsContent value="trading">
          <Card>
            <CardHeader>
              <CardTitle>Trading Preferences</CardTitle>
              <CardDescription>Configure risk management and trading parameters</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="risk">Risk Level</Label>
                <Select value={riskLevel} onValueChange={setRiskLevel}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select risk level" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="low">Conservative (Low Risk)</SelectItem>
                    <SelectItem value="medium">Balanced (Medium Risk)</SelectItem>
                    <SelectItem value="high">Aggressive (High Risk)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="maxPosition">Max Position Size (₹)</Label>
                <Input
                  id="maxPosition"
                  type="number"
                  value={maxPositionSize}
                  onChange={(e) => setMaxPositionSize(e.target.value)}
                  placeholder="25000"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="stopLoss">Default Stop Loss (%)</Label>
                <Input
                  id="stopLoss"
                  type="number"
                  value={stopLossPercent}
                  onChange={(e) => setStopLossPercent(e.target.value)}
                  placeholder="2"
                />
              </div>
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Auto Trading</Label>
                  <p className="text-sm text-muted-foreground">Enable automated trade execution</p>
                </div>
                <Switch
                  checked={autoTrading}
                  onCheckedChange={setAutoTrading}
                />
              </div>
              <Button className="w-full">
                <Save className="mr-2 h-4 w-4" />
                Save Trading Preferences
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Engines Tab */}
        <TabsContent value="engines">
          <Card>
            <CardHeader>
              <CardTitle>AI Engines Status</CardTitle>
              <CardDescription>Monitor your trading engine connections</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-3">
                <Card>
                  <CardContent className="pt-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">Engine A</p>
                        <p className="text-sm text-muted-foreground">Data Analysis</p>
                      </div>
                      <div className="flex items-center gap-1 text-green-600">
                        <CheckCircle className="h-4 w-4" />
                        <span className="text-sm">Online</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">Engine B</p>
                        <p className="text-sm text-muted-foreground">AI Prediction</p>
                      </div>
                      <div className="flex items-center gap-1 text-green-600">
                        <CheckCircle className="h-4 w-4" />
                        <span className="text-sm">Online</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">Engine C</p>
                        <p className="text-sm text-muted-foreground">Execution</p>
                      </div>
                      <div className="flex items-center gap-1 text-green-600">
                        <CheckCircle className="h-4 w-4" />
                        <span className="text-sm">Online</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
              <div className="text-sm text-muted-foreground text-center pt-2">
                All engines operational • Last checked: just now
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

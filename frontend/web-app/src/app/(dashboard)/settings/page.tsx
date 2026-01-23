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
  Settings,
  Bell,
  Server,
  Loader2,
  CheckCircle,
  Wallet,
  ExternalLink,
  Eye,
  EyeOff,
} from "lucide-react";
import { toast } from "sonner";
import { useAppStore } from "@/lib/store";
import { useCouponAuth } from "@/contexts/DualAuthContext";
import { setDhanClientId, clearDhanClientId } from "@/lib/user";
import { storeCredentialsAPI } from "@/lib/cloudFunctions";
import { EngineStatusCards } from "@/components/dashboard/engine-status";

import { cn } from "@/lib/utils";
import { getEngineCUrl } from "@/lib/api";

const ENGINE_C_URL = getEngineCUrl();

interface DhanCredentials {
  client_id: string;
  api_key: string;
  api_secret: string;
  access_token: string;
  is_verified: boolean;
}

export default function SettingsPage() {
  // Global state
  const {
    userProfile,
    dhanConnected,
    setDhanConnected,
    disconnectDhan,
    setUserProfile,
  } = useAppStore();
  const { session, refreshSession } = useCouponAuth();

  // Dhan Credentials State
  const [dhanCredentials, setDhanCredentials] = useState<DhanCredentials>({
    client_id: "",
    api_key: "",
    api_secret: "",
    access_token: "",
    is_verified: false,
  });
  const [showAccessToken, setShowAccessToken] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);

  // Load credentials on mount
  useEffect(() => {
    const loadCredentials = async () => {
      if (!session?.userId) {
        return;
      }

      try {
        const response = await fetch(
          `${ENGINE_C_URL}/api/user/credentials?user_id=${session.userId}`,
        );

        if (response.ok) {
          const data = await response.json();
          if (data.configured) {
            setDhanCredentials({
              client_id: data.client_id || "",
              api_key: data.api_key || "",
              api_secret: data.api_secret || "",
              access_token: "", // masked on server; keep empty locally
              is_verified: Boolean(data.is_verified),
            });
            // Update global state with connection status
            setDhanConnected(Boolean(data.is_verified));
          }
        }
      } catch (error) {
        console.error("Failed to load credentials:", error);
      }
    };

    loadCredentials();
  }, [session, setDhanConnected]);

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
      const response = await fetch(`${ENGINE_C_URL}/api/user/credentials`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: session.userId,
          client_id: dhanCredentials.client_id,
          api_key: dhanCredentials.api_key || "",
          api_secret: dhanCredentials.api_secret || "",
          access_token: dhanCredentials.access_token,
        }),
      });

      const data = await response.json();

      const isSuccess = data.status === "success" || response.ok;
      const isVerified = Boolean(data.is_verified);

      if (!isSuccess) {
        throw new Error(data.message || "Save failed");
      }

      // Update global state FIRST
      setDhanConnected(isVerified);
      if (userProfile) {
        setUserProfile({
          ...userProfile,
          isConnected: isVerified,
          isVerified: isVerified,
        });
      }

      setDhanCredentials({
        ...dhanCredentials,
        is_verified: isVerified,
      });

      if (isVerified) {
        toast.success(
          `✅ Credentials saved & verified!\nClient ID: ${dhanCredentials.client_id}`,
        );
        // REFRESH GLOBAL SESSION STATE
        await refreshSession();
      } else {
        // Show detailed reason from backend if available
        const errorDetail = data.error || data.message || "Verification failed";
        toast.warning(
          `⚠️ Credentials saved but not verified\n${errorDetail}\n\nPlease check your DhanHQ access token.`,
          { duration: 6000 },
        );
      }

      setDhanClientId(dhanCredentials.client_id);
    } catch (error: any) {
      toast.error(`❌ Save failed: ${error.message}`);
      setDhanConnected(false);
    } finally {
      setIsConnecting(false);
    }
  };

  const handleVerifyConnection = async () => {
    if (!session?.userId) return;

    setIsConnecting(true);
    try {
      const response = await fetch(
        `${ENGINE_C_URL}/api/user/credentials/verify?user_id=${session.userId}`,
      );

      const data = await response.json();

      if (data.is_verified) {
        // Update global state
        setDhanConnected(true);
        if (userProfile) {
          setUserProfile({
            ...userProfile,
            isConnected: true,
            isVerified: true,
          });
        }

        setDhanCredentials({ ...dhanCredentials, is_verified: true });
        toast.success(
          `✅ Connection verified successfully!\nDhanHQ API responding normally.`,
        );
        // REFRESH GLOBAL SESSION STATE
        await refreshSession();
      } else {
        setDhanConnected(false);
        setDhanCredentials({ ...dhanCredentials, is_verified: false });
        
        // Extract detailed error message
        const errorMsg = data.error || data.message || "Unknown error";
        toast.error(
          `❌ Verification failed\n${errorMsg}\n\nPlease regenerate your access token in DhanHQ.`,
          { duration: 7000 },
        );
      }
    } catch (error: any) {
      toast.error(
        `❌ Verification error: ${error.message}\n\nCheck your network connection.`,
      );
      setDhanConnected(false);
    } finally {
      setIsConnecting(false);
    }
  };

  const handleDisconnect = async () => {
    if (!session?.userId) return;

    setIsConnecting(true);
    try {
      // Call backend to delete credentials
      const response = await fetch(
        `${ENGINE_C_URL}/api/user/credentials?user_id=${session.userId}`,
        { method: "DELETE" },
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to disconnect");
      }

      // Clear local state FIRST
      setDhanCredentials({
        client_id: "",
        api_key: "",
        api_secret: "",
        access_token: "",
        is_verified: false,
      });
      
      // Clear global state
      setDhanConnected(false);
      if (userProfile) {
        setUserProfile({
          ...userProfile,
          isConnected: false,
          isVerified: false,
        });
      }
      
      clearDhanClientId();

      // REFRESH SESSION to update NavBar and other components
      await refreshSession();

      toast.success("✅ Disconnected from DhanHQ\nCredentials removed from Secret Manager");
    } catch (error: any) {
      toast.error(`❌ Disconnect failed: ${error.message}`);
      // Still clear local state even if API fails
      setDhanConnected(false);
      setDhanCredentials({
        client_id: "",
        api_key: "",
        api_secret: "",
        access_token: "",
        is_verified: false,
      });
    } finally {
      setIsConnecting(false);
    }
  };

  return (
    <div className="container mx-auto p-6 max-w-7xl">
      <div className="flex items-center gap-3 mb-6">
        <Settings className="h-8 w-8 text-primary" />
        <div>
          <h1 className="text-3xl font-bold">Settings</h1>
          <p className="text-muted-foreground">
            Manage your trading preferences and integrations
          </p>
        </div>
      </div>

      <Tabs defaultValue="dhan" className="space-y-4">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="dhan" className="flex items-center gap-2">
            <Wallet className="h-4 w-4" />
            <span className="hidden sm:inline">Dhan Account</span>
          </TabsTrigger>
          <TabsTrigger
            value="notifications"
            className="flex items-center gap-2"
          >
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
              <CardDescription className="flex items-center gap-2">
                Status:
                <span
                  className={cn(
                    "px-2 py-0.5 rounded text-xs font-bold uppercase",
                    dhanConnected
                      ? "bg-green-500/20 text-green-500"
                      : "bg-slate-500/20 text-slate-400",
                  )}
                >
                  {dhanConnected ? "connected" : "disconnected"}
                </span>
                {dhanConnected && (
                  <span className="flex items-center gap-1 text-[10px] text-green-400">
                    <CheckCircle className="w-3 h-3" /> Verified
                  </span>
                )}
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
                      onChange={(e) =>
                        setDhanCredentials({
                          ...dhanCredentials,
                          client_id: e.target.value,
                        })
                      }
                      placeholder="Enter Dhan Client ID"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="api-key">API Key</Label>
                    <Input
                      id="api-key"
                      name="api_key"
                      value={dhanCredentials.api_key}
                      onChange={(e) =>
                        setDhanCredentials({
                          ...dhanCredentials,
                          api_key: e.target.value,
                        })
                      }
                      placeholder="Enter API Key (for Data APIs)"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="api-secret">API Secret</Label>
                    <div className="relative">
                      <Input
                        id="api-secret"
                        name="api_secret"
                        type={showAccessToken ? "text" : "password"}
                        value={dhanCredentials.api_secret}
                        onChange={(e) =>
                          setDhanCredentials({
                            ...dhanCredentials,
                            api_secret: e.target.value,
                          })
                        }
                        placeholder="Enter API Secret"
                      />
                      <Button
                        variant="ghost"
                        size="sm"
                        className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                        onClick={() => setShowAccessToken(!showAccessToken)}
                      >
                        {showAccessToken ? (
                          <EyeOff className="h-4 w-4" />
                        ) : (
                          <Eye className="h-4 w-4" />
                        )}
                      </Button>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="access-token">Access Token</Label>
                    <div className="relative">
                      <Input
                        id="access-token"
                        name="access_token"
                        type={showAccessToken ? "text" : "password"}
                        value={dhanCredentials.access_token}
                        onChange={(e) =>
                          setDhanCredentials({
                            ...dhanCredentials,
                            access_token: e.target.value,
                          })
                        }
                        placeholder="Enter Access Token"
                      />
                      <Button
                        variant="ghost"
                        size="sm"
                        className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                        onClick={() => setShowAccessToken(!showAccessToken)}
                      >
                        {showAccessToken ? (
                          <EyeOff className="h-4 w-4" />
                        ) : (
                          <Eye className="h-4 w-4" />
                        )}
                      </Button>
                    </div>
                  </div>
                </div>

                <div className="flex flex-wrap gap-4 pt-4">
                  <Button
                    onClick={handleSaveCredentials}
                    disabled={isConnecting}
                  >
                    {isConnecting && (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    )}
                    Save Credentials
                  </Button>
                  <Button
                    variant="outline"
                    onClick={handleVerifyConnection}
                    disabled={isConnecting || !dhanCredentials.client_id}
                  >
                    {isConnecting && (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    )}
                    Verify Connection
                  </Button>
                  {dhanConnected && (
                    <Button
                      variant="destructive"
                      onClick={handleDisconnect}
                      disabled={isConnecting}
                    >
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
                      <Label className="text-xs uppercase text-muted-foreground">
                        Postback URL (DhanHQ Webhook)
                      </Label>
                      <div className="flex gap-2">
                        <code className="flex-1 bg-background p-2 rounded border font-mono text-xs overflow-x-auto">
                          {ENGINE_C_URL}/api/dhan/postback
                        </code>
                        <Button
                          variant="outline"
                          size="icon"
                          className="h-8 w-8"
                          onClick={() => {
                            navigator.clipboard.writeText(
                              `${ENGINE_C_URL}/api/dhan/postback`,
                            );
                            toast.success("Copied Postback URL");
                          }}
                        >
                          <CheckCircle className="h-3 w-3" />
                        </Button>
                      </div>
                      <p className="text-xs text-muted-foreground">
                        Configure this URL in DhanHQ Developer Dashboard for
                        order/trade webhooks
                      </p>
                    </div>
                    <div className="space-y-2">
                      <Label className="text-xs uppercase text-muted-foreground">
                        OAuth Redirect URL
                      </Label>
                      <div className="flex gap-2">
                        <code className="flex-1 bg-background p-2 rounded border font-mono text-xs overflow-x-auto">
                          {ENGINE_C_URL}/auth/dhan/success
                        </code>
                        <Button
                          variant="outline"
                          size="icon"
                          className="h-8 w-8"
                          onClick={() => {
                            navigator.clipboard.writeText(
                              `${ENGINE_C_URL}/auth/dhan/success`,
                            );
                            toast.success("Copied Redirect URL");
                          }}
                        >
                          <CheckCircle className="h-3 w-3" />
                        </Button>
                      </div>
                      <p className="text-xs text-muted-foreground">
                        Configure this URL in DhanHQ Developer Dashboard for
                        OAuth callback
                      </p>
                    </div>
                  </div>
                </div>

                {/* Removed duplicate Credentials Input Section to avoid confusion */}
              </div>
              <div className="mt-4 flex justify-end">
                <Button variant="outline">
                  <ExternalLink className="mr-2 h-4 w-4" /> DhanHQ Dashboard
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Notifications Tab */}
        <TabsContent value="notifications">
          <Card>
            <CardHeader>
              <CardTitle>Notification Settings</CardTitle>
              <CardDescription>
                Configure trading alerts and notifications
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div>
                  <Label className="text-base">Signal Notifications</Label>
                  <p className="text-sm text-muted-foreground">
                    Get notified when AI generates new signals
                  </p>
                </div>
                <Switch defaultChecked />
              </div>
              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div>
                  <Label className="text-base">Trade Execution Alerts</Label>
                  <p className="text-sm text-muted-foreground">
                    Real-time updates on order status
                  </p>
                </div>
                <Switch defaultChecked />
              </div>
              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div>
                  <Label className="text-base">Risk Alerts</Label>
                  <p className="text-sm text-muted-foreground">
                    Warnings when risk limits are approached
                  </p>
                </div>
                <Switch defaultChecked />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* --- ENGINES TAB (Dynamic) --- */}
        <TabsContent value="engines">
          <EngineStatusCards />
        </TabsContent>
      </Tabs>
    </div>
  );
}

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
import { EngineStatusCards } from "@/components/dashboard/engine-status";

import { cn } from "@/lib/utils";

const ENGINE_C_URL = process.env.NEXT_PUBLIC_ENGINE_C_URL || "";

interface DhanCredentials {
  client_id: string;
  api_key: string;
  api_secret: string;
  access_token: string;
  is_verified: boolean;
}

export default function SettingsPage() {
  // Global state
  const { userProfile } = useAppStore();
  const { session } = useCouponAuth();

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
  const [connectionStatus, setConnectionStatus] = useState<
    "disconnected" | "connected" | "error"
  >(userProfile?.isConnected ? "connected" : "disconnected");

  // Trading Settings State Wrapper
  // Risk Profile moved to /trading page

  // Load credentials on mount
  useEffect(() => {
    const loadCredentials = async () => {
      if (!session?.userId) {
        return;
      }

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
              is_verified: data.verified,
            });
            setConnectionStatus(data.verified ? "connected" : "disconnected");
          }
        }
      } catch (error) {
        console.error("Failed to load credentials:", error);
      }
    };

    loadCredentials();
  }, [session]);

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
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: session.userId,
          client_id: dhanCredentials.client_id,
          api_key: dhanCredentials.api_key || "ignored", // API might require key but we use token mainly
          api_secret: dhanCredentials.api_secret || "ignored",
          access_token: dhanCredentials.access_token,
        }),
      });

      const data = await response.json();

      if (data.success) {
        const isActuallyVerified = data.verified;
        setConnectionStatus(isActuallyVerified ? "connected" : "error");
        setDhanCredentials({
          ...dhanCredentials,
          is_verified: isActuallyVerified,
        });

        if (isActuallyVerified) {
          toast.success("Credentials saved and verified!");
        } else {
          toast.warning(
            "Credentials saved but verification failed. Check your token."
          );
        }

        setDhanClientId(dhanCredentials.client_id);
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
    if (!session?.userId) return;

    setIsConnecting(true);
    try {
      const response = await fetch(`${ENGINE_C_URL}/api/dhan/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: session.userId,
          client_id: dhanCredentials.client_id,
          access_token: dhanCredentials.access_token,
        }),
      });

      const data = await response.json();

      if (data.verified) {
        setConnectionStatus("connected");
        setDhanCredentials({ ...dhanCredentials, is_verified: true });
        toast.success("Connection verified successfully!");
      } else {
        setConnectionStatus("error");
        setDhanCredentials({ ...dhanCredentials, is_verified: false });
        toast.error(`Verification failed: ${data.message}`);
      }
    } catch (error: any) {
      toast.error(`Verification error: ${error.message}`);
      setConnectionStatus("error");
    } finally {
      setIsConnecting(false);
    }
  };

  const handleDisconnect = async () => {
    if (!session?.userId) return;

    setIsConnecting(true);
    try {
      const response = await fetch(
        `${ENGINE_C_URL}/api/dhan/credentials/${session.userId}`,
        { method: "DELETE" }
      );

      const data = await response.json();

      if (data.success) {
        setConnectionStatus("disconnected");
        setDhanCredentials({
          client_id: "",
          api_key: "",
          api_secret: "",
          access_token: "",
          is_verified: false,
        });
        clearDhanClientId();

        // Clear global store immediately
        if (userProfile) {
          useAppStore.getState().setUserProfile({
            ...userProfile,
            isConnected: false,
            isVerified: false,
            clientId: "",
          });
        }

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
                    connectionStatus === "connected"
                      ? "bg-green-500/20 text-green-500"
                      : connectionStatus === "error"
                        ? "bg-red-500/20 text-red-500"
                        : "bg-slate-500/20 text-slate-400"
                  )}
                >
                  {connectionStatus}
                </span>
                {connectionStatus === "connected" && (
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
                  {connectionStatus !== "disconnected" && (
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
                        Postback URL
                      </Label>
                      <div className="flex gap-2">
                        <code className="flex-1 bg-background p-2 rounded border font-mono text-xs overflow-x-auto">
                          https://engine-c.infinityai.pro/api/dhan/postback
                        </code>
                        <Button
                          variant="outline"
                          size="icon"
                          className="h-8 w-8"
                          onClick={() => {
                            navigator.clipboard.writeText(
                              "https://engine-c.infinityai.pro/api/dhan/postback"
                            );
                            toast.success("Copied Postback URL");
                          }}
                        >
                          <CheckCircle className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label className="text-xs uppercase text-muted-foreground">
                        Redirect URL
                      </Label>
                      <div className="flex gap-2">
                        <code className="flex-1 bg-background p-2 rounded border font-mono text-xs overflow-x-auto">
                          https://infinityai.pro/settings
                        </code>
                        <Button
                          variant="outline"
                          size="icon"
                          className="h-8 w-8"
                          onClick={() => {
                            navigator.clipboard.writeText(
                              "https://infinityai.pro/settings"
                            );
                            toast.success("Copied Redirect URL");
                          }}
                        >
                          <CheckCircle className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
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

'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useAppStore } from '@/lib/store';
import {
  Settings,
  User,
  Key,
  Bell,
  Shield,
  Palette,
  Monitor,
  Moon,
  Sun,
  Server,
  RefreshCw,
  Save,
  ExternalLink,
} from 'lucide-react';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';

export default function SettingsPage() {
  const { theme, toggleTheme, engines } = useAppStore();
  const [notifications, setNotifications] = useState(true);
  const [emailAlerts, setEmailAlerts] = useState(false);
  const [riskAlerts, setRiskAlerts] = useState(true);
  const [autoTrade, setAutoTrade] = useState(false);

  const handleSave = () => {
    toast.success('Settings saved successfully');
  };

  return (
    <div className="p-6 space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground">
          Manage your account and application preferences
        </p>
      </div>

      <Tabs defaultValue="general" className="w-full">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="general">General</TabsTrigger>
          <TabsTrigger value="api">API Keys</TabsTrigger>
          <TabsTrigger value="notifications">Notifications</TabsTrigger>
          <TabsTrigger value="trading">Trading</TabsTrigger>
          <TabsTrigger value="engines">Engines</TabsTrigger>
        </TabsList>

        {/* General Settings */}
        <TabsContent value="general" className="mt-6 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="h-5 w-5" />
                Profile
              </CardTitle>
              <CardDescription>Your account information</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="name">Display Name</Label>
                  <Input id="name" defaultValue="Raghu" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <Input id="email" type="email" defaultValue="raghu@infinityai.pro" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Palette className="h-5 w-5" />
                Appearance
              </CardTitle>
              <CardDescription>Customize the look and feel</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Theme</Label>
                  <p className="text-sm text-muted-foreground">
                    Switch between light and dark mode
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant={theme === 'light' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => theme === 'dark' && toggleTheme()}
                  >
                    <Sun className="mr-2 h-4 w-4" />
                    Light
                  </Button>
                  <Button
                    variant={theme === 'dark' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => theme === 'light' && toggleTheme()}
                  >
                    <Moon className="mr-2 h-4 w-4" />
                    Dark
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* API Keys */}
        <TabsContent value="api" className="mt-6 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Key className="h-5 w-5" />
                DhanHQ API Configuration
              </CardTitle>
              <CardDescription>
                Manage your DhanHQ broker API credentials
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="rounded-lg border border-green-500/30 bg-green-50 dark:bg-green-900/20 p-4">
                <div className="flex items-center gap-2">
                  <Badge className="bg-green-600">Connected</Badge>
                  <span className="text-sm">DhanHQ API is configured and active</span>
                </div>
              </div>

              <Separator />

              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="client-id">Client ID</Label>
                  <Input id="client-id" defaultValue="1101302170" disabled />
                  <p className="text-xs text-muted-foreground">
                    Stored securely in Google Secret Manager
                  </p>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="api-key">API Key</Label>
                  <Input id="api-key" type="password" defaultValue="••••••••••••" disabled />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="access-token">Access Token</Label>
                  <Input id="access-token" type="password" defaultValue="••••••••••••" disabled />
                </div>
              </div>

              <Button variant="outline" className="w-full" asChild>
                <a href="https://console.cloud.google.com/security/secret-manager" target="_blank" rel="noopener noreferrer">
                  <ExternalLink className="mr-2 h-4 w-4" />
                  Manage Secrets in GCP
                </a>
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Notifications */}
        <TabsContent value="notifications" className="mt-6 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bell className="h-5 w-5" />
                Notification Preferences
              </CardTitle>
              <CardDescription>
                Control how you receive alerts and updates
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Push Notifications</Label>
                  <p className="text-sm text-muted-foreground">
                    Receive real-time alerts in browser
                  </p>
                </div>
                <Switch checked={notifications} onCheckedChange={setNotifications} />
              </div>

              <Separator />

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Email Alerts</Label>
                  <p className="text-sm text-muted-foreground">
                    Receive important updates via email
                  </p>
                </div>
                <Switch checked={emailAlerts} onCheckedChange={setEmailAlerts} />
              </div>

              <Separator />

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Risk Alerts</Label>
                  <p className="text-sm text-muted-foreground">
                    Get notified when trades exceed risk thresholds
                  </p>
                </div>
                <Switch checked={riskAlerts} onCheckedChange={setRiskAlerts} />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Trading */}
        <TabsContent value="trading" className="mt-6 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="h-5 w-5" />
                Trading Preferences
              </CardTitle>
              <CardDescription>
                Configure trading behavior and risk management
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Auto Trading</Label>
                  <p className="text-sm text-muted-foreground">
                    Automatically execute AI-generated signals
                  </p>
                </div>
                <Switch checked={autoTrade} onCheckedChange={setAutoTrade} />
              </div>

              <Separator />

              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="max-position">Max Position Size (%)</Label>
                  <Input id="max-position" type="number" defaultValue="10" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="stop-loss">Default Stop Loss (%)</Label>
                  <Input id="stop-loss" type="number" defaultValue="2" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="risk-per-trade">Risk Per Trade (%)</Label>
                  <Input id="risk-per-trade" type="number" defaultValue="1" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="max-daily-loss">Max Daily Loss (%)</Label>
                  <Input id="max-daily-loss" type="number" defaultValue="5" />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Engines */}
        <TabsContent value="engines" className="mt-6 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Server className="h-5 w-5" />
                Engine Configuration
              </CardTitle>
              <CardDescription>
                View and configure the 3-engine architecture
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <EngineConfig
                name="Engine A"
                description="Orchestration & Risk Management"
                url="https://engine-a.infinityai.pro"
                fallbackUrl="https://engine-a-573866363639.us-central1.run.app"
                status={engines.engineA.status}
                version={engines.engineA.version}
              />

              <Separator />

              <EngineConfig
                name="Engine B"
                description="AI/ML Intelligence"
                url="https://engine-b.infinityai.pro"
                fallbackUrl="https://engine-b-573866363639.us-central1.run.app"
                status={engines.engineB.status}
                version={engines.engineB.version}
              />

              <Separator />

              <EngineConfig
                name="Engine C"
                description="DhanHQ Execution"
                url="https://engine-c.infinityai.pro"
                fallbackUrl="https://engine-c-573866363639.us-central1.run.app"
                status={engines.engineC.status}
                version={engines.engineC.version}
              />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Save Button */}
      <div className="flex justify-end">
        <Button onClick={handleSave}>
          <Save className="mr-2 h-4 w-4" />
          Save Settings
        </Button>
      </div>
    </div>
  );
}

function EngineConfig({
  name,
  description,
  url,
  fallbackUrl,
  status,
  version,
}: {
  name: string;
  description: string;
  url: string;
  fallbackUrl: string;
  status: string;
  version: string | null;
}) {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <p className="font-semibold">{name}</p>
          <p className="text-sm text-muted-foreground">{description}</p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={status === 'online' ? 'default' : 'destructive'}>
            {status}
          </Badge>
          {version && (
            <Badge variant="secondary" className="font-mono">
              {version}
            </Badge>
          )}
        </div>
      </div>
      <div className="rounded-lg bg-muted p-3 space-y-1">
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">Primary URL:</span>
          <code className="text-xs">{url}</code>
        </div>
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">Fallback:</span>
          <code className="text-xs">{fallbackUrl}</code>
        </div>
      </div>
    </div>
  );
}

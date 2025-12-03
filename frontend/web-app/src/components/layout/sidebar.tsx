'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { useAppStore } from '@/lib/store';
import {
  LayoutDashboard,
  TrendingUp,
  BarChart3,
  Brain,
  Wallet,
  History,
  Settings,
  ChevronLeft,
  Activity,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Trading', href: '/trading', icon: TrendingUp },
  { name: 'Analytics', href: '/analytics', icon: BarChart3 },
  { name: 'AI Signals', href: '/signals', icon: Brain },
  { name: 'Portfolio', href: '/portfolio', icon: Wallet },
  { name: 'History', href: '/history', icon: History },
];

const secondaryNavigation = [
  { name: 'Settings', href: '/settings', icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const { sidebarOpen, setSidebarOpen, engines, wsConnected } = useAppStore();

  // Safe access to engine status with defaults
  const engineA = engines?.engineA || { status: 'loading', version: null, lastChecked: null };
  const engineB = engines?.engineB || { status: 'loading', version: null, lastChecked: null };
  const engineC = engines?.engineC || { status: 'loading', version: null, lastChecked: null };

  const allOnline =
    engineA.status === 'online' &&
    engineB.status === 'online' &&
    engineC.status === 'online';

  return (
    <aside
      className={cn(
        'fixed left-0 top-0 z-40 h-screen border-r bg-background transition-all duration-300',
        sidebarOpen ? 'w-64' : 'w-16'
      )}
    >
      <div className="flex h-full flex-col">
        {/* Logo */}
        <div className="flex h-16 items-center justify-between border-b px-4">
          {sidebarOpen && (
            <Link href="/" className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                <Activity className="h-5 w-5" />
              </div>
              <span className="text-lg font-bold">InfinityAI</span>
            </Link>
          )}
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className={cn(!sidebarOpen && 'mx-auto')}
          >
            <ChevronLeft
              className={cn('h-4 w-4 transition-transform', !sidebarOpen && 'rotate-180')}
            />
          </Button>
        </div>

        {/* Status Indicators */}
        {sidebarOpen && (
          <div className="border-b p-4">
            <div className="flex items-center justify-between">
              <span className="text-xs text-muted-foreground">System Status</span>
              <Badge variant={allOnline ? 'default' : 'destructive'} className="text-xs">
                {allOnline ? 'All Online' : 'Degraded'}
              </Badge>
            </div>
            <div className="mt-2 flex gap-2">
              <EngineIndicator name="A" status={engineA.status} />
              <EngineIndicator name="B" status={engineB.status} />
              <EngineIndicator name="C" status={engineC.status} />
              <div className="ml-auto flex items-center gap-1">
                <div
                  className={cn(
                    'h-2 w-2 rounded-full',
                    wsConnected ? 'bg-green-500' : 'bg-gray-400'
                  )}
                />
                <span className="text-xs text-muted-foreground">WS</span>
              </div>
            </div>
          </div>
        )}

        {/* Navigation */}
        <ScrollArea className="flex-1 px-2 py-4">
          <nav className="flex flex-col gap-1">
            {navigation.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={cn(
                    'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-primary text-primary-foreground'
                      : 'text-muted-foreground hover:bg-muted hover:text-foreground',
                    !sidebarOpen && 'justify-center px-2'
                  )}
                >
                  <item.icon className="h-5 w-5 flex-shrink-0" />
                  {sidebarOpen && <span>{item.name}</span>}
                </Link>
              );
            })}
          </nav>

          <Separator className="my-4" />

          <nav className="flex flex-col gap-1">
            {secondaryNavigation.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={cn(
                    'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-primary text-primary-foreground'
                      : 'text-muted-foreground hover:bg-muted hover:text-foreground',
                    !sidebarOpen && 'justify-center px-2'
                  )}
                >
                  <item.icon className="h-5 w-5 flex-shrink-0" />
                  {sidebarOpen && <span>{item.name}</span>}
                </Link>
              );
            })}
          </nav>
        </ScrollArea>

        {/* Version */}
        {sidebarOpen && (
          <div className="border-t p-4">
            <p className="text-xs text-muted-foreground">InfinityAI.Pro v3.5</p>
            <p className="text-xs text-muted-foreground">3-Engine Architecture</p>
          </div>
        )}
      </div>
    </aside>
  );
}

function EngineIndicator({ name, status }: { name: string; status: string }) {
  return (
    <div className="flex items-center gap-1">
      <div
        className={cn(
          'h-2 w-2 rounded-full',
          status === 'online' && 'bg-green-500',
          status === 'offline' && 'bg-red-500',
          status === 'loading' && 'bg-yellow-500 animate-pulse'
        )}
      />
      <span className="text-xs text-muted-foreground">{name}</span>
    </div>
  );
}

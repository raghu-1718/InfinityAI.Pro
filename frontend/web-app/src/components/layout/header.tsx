'use client';

import { useAppStore } from '@/lib/store';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Moon, Sun, Bell, RefreshCw, User, LogOut, Settings } from 'lucide-react';
import { useFunds, useEngineHealth } from '@/hooks/useApi';
import { formatCurrency } from '@/lib/format';

export function Header() {
  const { theme, toggleTheme, funds, engines } = useAppStore();
  const { refetch: refetchEngines, isFetching: isRefreshing } = useEngineHealth();
  const { refetch: refetchFunds } = useFunds();

  const handleRefresh = () => {
    refetchEngines();
    refetchFunds();
  };

  const allOnline =
    engines.engineA.status === 'online' &&
    engines.engineB.status === 'online' &&
    engines.engineC.status === 'online';

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b bg-background/95 px-6 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex items-center gap-4">
        <h1 className="text-xl font-semibold">Dashboard</h1>
        <Badge variant={allOnline ? 'outline' : 'destructive'} className="hidden sm:flex">
          {allOnline ? '3 Engines Online' : 'System Degraded'}
        </Badge>
      </div>

      <div className="flex items-center gap-2">
        {/* Balance Display */}
        {funds && (
          <div className="hidden md:flex items-center gap-2 rounded-lg bg-muted px-3 py-1.5">
            <span className="text-xs text-muted-foreground">Balance:</span>
            <span className="font-mono font-semibold text-green-600 dark:text-green-400">
              {formatCurrency(funds.availableBalance)}
            </span>
          </div>
        )}

        {/* Refresh Button */}
        <Button variant="ghost" size="icon" onClick={handleRefresh} disabled={isRefreshing}>
          <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
        </Button>

        {/* Notifications */}
        <Button variant="ghost" size="icon" className="relative">
          <Bell className="h-4 w-4" />
          <span className="absolute -right-0.5 -top-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] text-white">
            3
          </span>
        </Button>

        {/* Theme Toggle */}
        <Button variant="ghost" size="icon" onClick={toggleTheme}>
          {theme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
        </Button>

        {/* User Menu */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="relative h-8 w-8 rounded-full">
              <Avatar className="h-8 w-8">
                <AvatarFallback>RA</AvatarFallback>
              </Avatar>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent className="w-56" align="end" forceMount>
            <DropdownMenuLabel className="font-normal">
              <div className="flex flex-col space-y-1">
                <p className="text-sm font-medium leading-none">Raghu</p>
                <p className="text-xs leading-none text-muted-foreground">
                  raghu@infinityai.pro
                </p>
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem>
              <User className="mr-2 h-4 w-4" />
              Profile
            </DropdownMenuItem>
            <DropdownMenuItem>
              <Settings className="mr-2 h-4 w-4" />
              Settings
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem className="text-red-600">
              <LogOut className="mr-2 h-4 w-4" />
              Log out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}

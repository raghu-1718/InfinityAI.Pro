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
import { Moon, Sun, Bell, RefreshCw, User, LogOut, Settings, Wallet } from 'lucide-react';
import { useFunds, useEngineHealth, useUserProfile } from '@/hooks/useApi';
import { formatCurrency } from '@/lib/format';
import { useQueryClient } from '@tanstack/react-query';
import { engineC } from '@/lib/api';
import { toast } from 'sonner';
import Link from 'next/link';

export function Header() {
  const { theme, toggleTheme, funds, engines, userProfile, dematData, clearUserData } = useAppStore();
  const { refetch: refetchEngines, isFetching: isRefreshing } = useEngineHealth();
  const { refetch: refetchFunds } = useFunds();
  const { refetch: refetchProfile } = useUserProfile();
  const queryClient = useQueryClient();

  const handleRefresh = () => {
    refetchEngines();
    refetchFunds();
    refetchProfile();
  };

  const handleLogout = async () => {
    try {
      // Get userId before clearing
      const userId = typeof window !== 'undefined' ? localStorage.getItem('userId') : null;

      if (userId) {
        // Delete credentials from backend
        await engineC.deleteUserCredentials(userId);
      }

      // Clear local store
      clearUserData();

      // Invalidate all queries
      queryClient.clear();

      toast.success('Logged Out', {
        description: 'You have been logged out successfully.',
      });

      // Redirect to home/settings
      window.location.href = '/settings';
    } catch (error) {
      console.error('Logout failed:', error);
      // Still clear local data even if API fails
      clearUserData();
      queryClient.clear();
      window.location.href = '/settings';
    }
  };

  const allOnline =
    engines.engineA.status === 'online' &&
    engines.engineB.status === 'online' &&
    engines.engineC.status === 'online';

  // Get balance from user's connected demat or fallback to admin funds
  const displayBalance = dematData?.funds?.availableBalance ?? funds?.availableBalance ?? 0;

  // Get user initials for avatar
  const getUserInitials = () => {
    if (userProfile?.isConnected && userProfile?.clientId) {
      // Use first 2 chars of client ID
      return userProfile.clientId.substring(0, 2).toUpperCase();
    }
    return 'G'; // Guest
  };

  const getUserName = () => {
    if (userProfile?.isConnected) {
      return userProfile.name || `Dhan User`;
    }
    return 'Guest User';
  };

  const getUserEmail = () => {
    if (userProfile?.isConnected && userProfile?.clientId) {
      return `Client ID: ${userProfile.clientId}`;
    }
    return 'Connect Dhan to trade';
  };

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
        <div className="hidden md:flex items-center gap-2 rounded-lg bg-muted px-3 py-1.5">
          <span className="text-xs text-muted-foreground">Balance:</span>
          {userProfile?.isConnected ? (
            <span className="font-mono font-semibold text-green-600 dark:text-green-400">
              {formatCurrency(displayBalance)}
            </span>
          ) : (
            <Link href="/settings" className="text-xs text-yellow-600 dark:text-yellow-400 hover:underline flex items-center gap-1">
              <Wallet className="h-3 w-3" />
              Connect Dhan
            </Link>
          )}
        </div>

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
                <AvatarFallback className={userProfile?.isConnected ? 'bg-green-600 text-white' : 'bg-muted'}>
                  {getUserInitials()}
                </AvatarFallback>
              </Avatar>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent className="w-56" align="end" forceMount>
            <DropdownMenuLabel className="font-normal">
              <div className="flex flex-col space-y-1">
                <p className="text-sm font-medium leading-none">{getUserName()}</p>
                <p className="text-xs leading-none text-muted-foreground">
                  {getUserEmail()}
                </p>
                {userProfile?.isConnected && (
                  <Badge variant="outline" className="w-fit mt-1 text-xs text-green-600">
                    Dhan Connected
                  </Badge>
                )}
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem asChild>
              <Link href="/settings" className="flex items-center cursor-pointer">
                <User className="mr-2 h-4 w-4" />
                Profile
              </Link>
            </DropdownMenuItem>
            <DropdownMenuItem asChild>
              <Link href="/settings" className="flex items-center cursor-pointer">
                <Settings className="mr-2 h-4 w-4" />
                Settings
              </Link>
            </DropdownMenuItem>
            {!userProfile?.isConnected && (
              <DropdownMenuItem asChild>
                <Link href="/settings" className="flex items-center cursor-pointer text-yellow-600">
                  <Wallet className="mr-2 h-4 w-4" />
                  Connect Dhan Account
                </Link>
              </DropdownMenuItem>
            )}
            <DropdownMenuSeparator />
            <DropdownMenuItem
              className="text-red-600 cursor-pointer"
              onClick={handleLogout}
            >
              <LogOut className="mr-2 h-4 w-4" />
              Log out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}

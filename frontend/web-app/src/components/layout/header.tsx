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
import { Moon, Sun, Bell, RefreshCw, User, LogOut, Settings, Wallet, LogIn, Loader2 } from 'lucide-react';

import { useFunds, useEngineHealth, useUserProfile, useSystemState } from '@/hooks/useApi';
import { formatCurrency } from '@/lib/format';
import { useQueryClient } from '@tanstack/react-query';
import { useCouponAuth } from '@/contexts/DualAuthContext';
import { toast } from 'sonner';
import Link from 'next/link';
import { useHydration } from '@/hooks/useHydration';
import { useRouter } from 'next/navigation';

export function Header() {
  const router = useRouter();
  const { theme, toggleTheme, funds, engines, userProfile, dematData, clearUserData } = useAppStore();
  const { session, user, logout, isAuthenticated, loading: authLoading } = useCouponAuth();
  const { refetch: refetchEngines, isFetching: isRefreshing } = useEngineHealth();
  const { data: systemState, refetch: refetchSystem } = useSystemState();
  const { refetch: refetchFunds } = useFunds();
  const { refetch: refetchProfile, isLoading: isProfileLoading } = useUserProfile();
  const queryClient = useQueryClient();
  const hydrated = useHydration();

  // Defensive fallback for engines state
  const enginesState = engines || {
    engineA: { status: 'loading', version: null, lastChecked: null },
    engineB: { status: 'loading', version: null, lastChecked: null },
    engineC: { status: 'loading', version: null, lastChecked: null },
  };

  const handleRefresh = () => {
    refetchEngines();
    refetchSystem();
    refetchFunds();
    refetchProfile();
  };

  const handleLogin = () => {
    router.push('/login');
  };

  const handleLogout = async () => {
    try {
      await logout();
      queryClient.clear();

      toast.success('Logged Out', {
        description: 'You have been logged out successfully.',
      });

      router.push('/login');
    } catch (error) {
      console.error('Logout failed:', error);
      clearUserData();
      queryClient.clear();
      router.push('/login');
    }
  };

  const allOnline =
    enginesState.engineA.status === 'online' &&
    enginesState.engineB.status === 'online' &&
    enginesState.engineC.status === 'online';

  // Get balance from user's connected demat or fallback to admin funds
  const displayBalance = dematData?.funds?.availableBalance ?? funds?.availableBalance ?? 0;

  // In Single-Tenant mode, Dhan connection is always active
  const isDhanConnected = true;

  // Get user initials for avatar
  const getUserInitials = () => {
    return 'RG';
  };

  const getUserName = () => {
    return 'Raghu (1101302170)';
  };

  const getUserEmail = () => {
    return 'DhanHQ Vault Connected';
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
        {/* Balance Display (Removed for cleaner look) */}
        {/* <div className="hidden md:flex items-center gap-2 rounded-lg bg-muted px-3 py-1.5"> ... </div> */}

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
                <AvatarFallback className={isAuthenticated ? 'bg-green-600 text-white' : 'bg-muted'}>
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
                {hydrated && isDhanConnected && (
                  <Badge variant="outline" className="w-fit mt-1 text-xs text-green-600">
                    Dhan Connected
                  </Badge>
                )}
                {hydrated && isAuthenticated && !isDhanConnected && (
                  <Badge variant="outline" className="w-fit mt-1 text-xs text-blue-600">
                    Coupon Verified
                  </Badge>
                )}
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />

            {!hydrated || authLoading ? (
              // Loading state
              <DropdownMenuItem disabled>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Loading...
              </DropdownMenuItem>
            ) : !isAuthenticated ? (
              // Not logged in - show login option
              <DropdownMenuItem
                className="text-blue-600 cursor-pointer"
                onClick={handleLogin}
              >
                <LogIn className="mr-2 h-4 w-4" />
                Enter Coupon Code
              </DropdownMenuItem>
            ) : (
              // Logged in - show profile and settings
              <>
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
                {hydrated && !isDhanConnected && (
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
              </>
            )}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}

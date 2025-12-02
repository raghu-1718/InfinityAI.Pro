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
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Moon, Sun, Bell, RefreshCw, User, LogOut, Settings, Wallet, LogIn, Loader2 } from 'lucide-react';
import { useFunds, useEngineHealth, useUserProfile } from '@/hooks/useApi';
import { formatCurrency } from '@/lib/format';
import { useQueryClient } from '@tanstack/react-query';
import { engineC } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { toast } from 'sonner';
import Link from 'next/link';
import { useHydration } from '@/hooks/useHydration';

export function Header() {
  const { theme, toggleTheme, funds, engines, userProfile, dematData, clearUserData } = useAppStore();
  const { user, userProfile: firebaseProfile, signIn, signOut: firebaseSignOut, loading: authLoading } = useAuth();
  const { refetch: refetchEngines, isFetching: isRefreshing } = useEngineHealth();
  const { refetch: refetchFunds } = useFunds();
  const { refetch: refetchProfile, isLoading: isProfileLoading } = useUserProfile();
  const queryClient = useQueryClient();
  const hydrated = useHydration();

  const handleRefresh = () => {
    refetchEngines();
    refetchFunds();
    refetchProfile();
  };

  const handleLogin = async () => {
    const result = await signIn();
    if (result.success) {
      toast.success('Signed In', {
        description: 'Welcome to InfinityAI.Pro!',
      });
    } else {
      toast.error('Sign In Failed', {
        description: result.error || 'Please try again.',
      });
    }
  };

  const handleLogout = async () => {
    try {
      // If using Firebase Auth
      if (user) {
        await firebaseSignOut();
      } else {
        // Fallback to old localStorage-based logout
        const userId = typeof window !== 'undefined' ? localStorage.getItem('userId') : null;

        if (userId) {
          await engineC.deleteUserCredentials(userId);
        }

        clearUserData();
      }

      // Invalidate all queries
      queryClient.clear();

      toast.success('Logged Out', {
        description: 'You have been logged out successfully.',
      });

      // Redirect to home/settings
      window.location.href = '/settings';
    } catch (error) {
      console.error('Logout failed:', error);
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

  // Check if user is authenticated (Firebase or Dhan connected)
  // Only use persisted state after hydration to prevent mismatch
  const isAuthenticated = hydrated && (!!user || userProfile?.isConnected);

  // Get user initials for avatar
  const getUserInitials = () => {
    if (!hydrated) return '?'; // Show placeholder during hydration
    if (user?.displayName) {
      // Use Firebase display name initials
      const names = user.displayName.split(' ');
      return names.length >= 2
        ? `${names[0][0]}${names[1][0]}`.toUpperCase()
        : user.displayName.substring(0, 2).toUpperCase();
    }
    if (userProfile?.isConnected && userProfile?.clientId) {
      return userProfile.clientId.substring(0, 2).toUpperCase();
    }
    return 'G'; // Guest
  };

  const getUserName = () => {
    if (!hydrated) return 'Loading...';
    if (user?.displayName) {
      return user.displayName;
    }
    if (userProfile?.isConnected) {
      return userProfile.name || `Dhan User`;
    }
    return 'Guest User';
  };

  const getUserEmail = () => {
    if (!hydrated) return 'Loading...';
    if (user?.email) {
      return user.email;
    }
    if (userProfile?.isConnected && userProfile?.clientId) {
      return `Client ID: ${userProfile.clientId}`;
    }
    return 'Sign in to get started';
  };

  const getUserPhoto = () => {
    return user?.photoURL || null;
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
          {!hydrated || isProfileLoading || authLoading ? (
            <Loader2 className="h-3 w-3 animate-spin text-muted-foreground" />
          ) : userProfile?.isConnected ? (
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
                {getUserPhoto() && (
                  <AvatarImage src={getUserPhoto()!} alt={getUserName()} />
                )}
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
                {hydrated && userProfile?.isConnected && (
                  <Badge variant="outline" className="w-fit mt-1 text-xs text-green-600">
                    Dhan Connected
                  </Badge>
                )}
                {hydrated && user && !userProfile?.isConnected && (
                  <Badge variant="outline" className="w-fit mt-1 text-xs text-blue-600">
                    Google Connected
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
            ) : !user && !userProfile?.isConnected ? (
              // Not logged in - show login option
              <DropdownMenuItem
                className="text-blue-600 cursor-pointer"
                onClick={handleLogin}
                disabled={authLoading}
              >
                <LogIn className="mr-2 h-4 w-4" />
                Sign in with Google
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
                {hydrated && !userProfile?.isConnected && (
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

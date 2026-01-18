'use client';

import { useCouponAuth } from '@/contexts/DualAuthContext';
import { AppSidebar, TopBar } from '@/components/layout/AppSidebar';
import { GlobalDataPoller } from '@/components/layout/global-data-poller';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { Loader2, TrendingUp } from 'lucide-react';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { isAuthenticated, loading } = useCouponAuth();
  const router = useRouter();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Redirect to login if not authenticated
  useEffect(() => {
    if (mounted && !loading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, loading, mounted, router]);

  // Show beautiful loading screen while checking auth
  if (!mounted || loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="text-center space-y-6">
          <div className="w-20 h-20 mx-auto rounded-2xl bg-gradient-to-br from-purple-600 to-cyan-500 flex items-center justify-center shadow-2xl neon-glow-purple animate-pulse">
            <TrendingUp className="h-10 w-10 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Infinity<span className="gradient-text">AI</span></h1>
            <p className="text-white/40 text-sm mt-1">Initializing Trading System...</p>
          </div>
          <div className="flex justify-center gap-1">
            <div className="w-2 h-2 rounded-full bg-purple-500 animate-bounce" style={{ animationDelay: '0ms' }} />
            <div className="w-2 h-2 rounded-full bg-purple-500 animate-bounce" style={{ animationDelay: '150ms' }} />
            <div className="w-2 h-2 rounded-full bg-purple-500 animate-bounce" style={{ animationDelay: '300ms' }} />
          </div>
        </div>
      </div>
    );
  }

  // Not authenticated - will redirect
  if (!isAuthenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="text-center space-y-4">
          <Loader2 className="h-8 w-8 animate-spin text-purple-500 mx-auto" />
          <p className="text-white/60">Redirecting to login...</p>
        </div>
      </div>
    );
  }

  // Authenticated - show dashboard layout with new design
  return (
    <ErrorBoundary>
      <div className="flex min-h-screen bg-background">
        {/* Sidebar */}
        <AppSidebar />
        <GlobalDataPoller />
        
        {/* Main Content */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <TopBar />
          <main className="flex-1 overflow-y-auto">
            {children}
          </main>
        </div>
      </div>
    </ErrorBoundary>
  );
}


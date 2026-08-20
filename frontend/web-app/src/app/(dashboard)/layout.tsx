'use client';

import { useCouponAuth } from '@/contexts/DualAuthContext';
import { AppSidebar, TopBar } from '@/components/layout/AppSidebar';
import { GlobalDataPoller } from '@/components/layout/global-data-poller';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { InfinityAICopilotFloating } from '@/components/ai-agent';
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

  // Authenticated - show dashboard layout with new design
  return (
    <ErrorBoundary>
      <div className="flex min-h-screen bg-background relative">
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

        {/* Global Institutional Copilot Drawer */}
        <InfinityAICopilotFloating />
      </div>
    </ErrorBoundary>
  );
}



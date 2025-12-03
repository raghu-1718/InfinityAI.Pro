'use client';

import { useCouponAuth } from '@/contexts/DualAuthContext';
import { Sidebar } from '@/components/layout/sidebar';
import { Header } from '@/components/layout/header';
import { usePathname, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { Loader2 } from 'lucide-react';

interface AuthLayoutWrapperProps {
  children: React.ReactNode;
}

// Pages that don't require authentication
const PUBLIC_PATHS = ['/login', '/login/'];

export function AuthLayoutWrapper({ children }: AuthLayoutWrapperProps) {
  const { isAuthenticated, loading } = useCouponAuth();
  const pathname = usePathname();
  const router = useRouter();
  const [mounted, setMounted] = useState(false);

  // Check if current path is public (handle trailing slash and SSR)
  const isPublicPath = pathname ? PUBLIC_PATHS.some(p =>
    pathname === p || pathname.startsWith(p.replace(/\/$/, '') + '/')
  ) : false;

  // Mark as mounted after first render
  useEffect(() => {
    setMounted(true);
  }, []);

  // CRITICAL: For public pages (login), ALWAYS render children immediately
  // This must come BEFORE any loading checks
  if (isPublicPath) {
    return <>{children}</>;
  }

  // Handle auth redirects (only after mounted and not loading)
  useEffect(() => {
    if (!mounted || loading || isPublicPath) return;

    // If not authenticated and trying to access protected route, redirect to login
    if (!isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, loading, isPublicPath, router, mounted]);

  // For protected pages, show loading only after mount
  if (!mounted || loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-900">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary mx-auto mb-4" />
          <p className="text-slate-400">Loading...</p>
        </div>
      </div>
    );
  }

  // For protected pages, require authentication
  if (!isAuthenticated) {
    // Will be redirected by useEffect above
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-900">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary mx-auto mb-4" />
          <p className="text-slate-400">Redirecting to login...</p>
        </div>
      </div>
    );
  }

  // Render with full dashboard layout
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex flex-1 flex-col pl-64 transition-all duration-300 data-[sidebar-collapsed=true]:pl-16">
        <Header />
        <main className="flex-1 bg-muted/30">
          {children}
        </main>
      </div>
    </div>
  );
}

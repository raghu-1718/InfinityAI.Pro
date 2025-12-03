'use client';

import { useCouponAuth } from '@/contexts/CouponAuthContext';
import { Sidebar } from '@/components/layout/sidebar';
import { Header } from '@/components/layout/header';
import { usePathname, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { Loader2 } from 'lucide-react';

interface AuthLayoutWrapperProps {
  children: React.ReactNode;
}

// Pages that don't require authentication
const PUBLIC_PATHS = ['/login'];

export function AuthLayoutWrapper({ children }: AuthLayoutWrapperProps) {
  const { isAuthenticated, loading } = useCouponAuth();
  const pathname = usePathname();
  const router = useRouter();
  const [mounted, setMounted] = useState(false);

  // Mark as mounted after first render
  useEffect(() => {
    setMounted(true);
  }, []);

  const isPublicPath = PUBLIC_PATHS.includes(pathname);

  // Handle auth redirects
  useEffect(() => {
    if (!mounted || loading) return;

    // If not authenticated and trying to access protected route, redirect to login
    if (!isAuthenticated && !isPublicPath) {
      router.push('/login');
    }

    // If authenticated and on login page, redirect to dashboard
    if (isAuthenticated && isPublicPath) {
      router.push('/');
    }
  }, [isAuthenticated, loading, isPublicPath, router, mounted]);

  // Don't render anything during SSR to avoid hydration mismatch
  // Show loading only after mount if still loading
  if (!mounted) {
    return null;
  }

  // Show loading spinner while checking auth (client-side only)
  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  // For public pages (login), render without layout
  if (isPublicPath) {
    return <>{children}</>;
  }

  // For protected pages, require authentication and show full layout
  if (!isAuthenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
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

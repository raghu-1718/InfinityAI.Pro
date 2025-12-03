'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useCouponAuth } from '@/contexts/CouponAuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Loader2, Key, Sparkles, TrendingUp, Shield, Brain } from 'lucide-react';
import { toast } from 'sonner';

export default function LoginPage() {
  const router = useRouter();
  const { verifyCoupon, isAuthenticated, loading } = useCouponAuth();
  const [couponCode, setCouponCode] = useState('');
  const [isVerifying, setIsVerifying] = useState(false);
  const [error, setError] = useState('');
  const [mounted, setMounted] = useState(false);

  // Mark as mounted
  useEffect(() => {
    setMounted(true);
  }, []);

  // Redirect if already authenticated (only after mounted)
  useEffect(() => {
    if (mounted && !loading && isAuthenticated) {
      router.push('/');
    }
  }, [isAuthenticated, loading, router, mounted]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!couponCode.trim()) {
      setError('Please enter a coupon code');
      return;
    }
    setError('');
    setIsVerifying(true);

    try {
      const result = await verifyCoupon(couponCode.trim().toUpperCase());

      if (result.success) {
        toast.success('Welcome to InfinityAI.Pro!', {
          description: 'Coupon verified successfully. Redirecting to dashboard...',
        });
        router.push('/');
      } else {
        setError(result.error || 'Invalid coupon code');
        toast.error('Verification Failed', {
          description: result.error || 'Please check your coupon code and try again.',
        });
      }
    } catch (err) {
      setError('Network error. Please try again.');
      toast.error('Error', { description: 'Network error. Please try again.' });
    }

    setIsVerifying(false);
  };

  // ALWAYS show the login form - never show loading spinner
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-4">
      <div className="w-full max-w-md space-y-8">
        {/* Logo and Title */}
        <div className="text-center">
          <div className="inline-flex items-center gap-2 mb-4">
            <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-primary to-primary/50 flex items-center justify-center">
              <Sparkles className="h-7 w-7 text-white" />
            </div>
          </div>
          <h1 className="text-3xl font-bold text-white">InfinityAI.Pro</h1>
          <p className="text-slate-400 mt-2">AI-Powered Trading Platform</p>
        </div>

        {/* Login Card */}
        <Card className="border-slate-700 bg-slate-900/50 backdrop-blur">
          <CardHeader className="space-y-1">
            <CardTitle className="text-2xl text-center text-white">Enter Access Code</CardTitle>
            <CardDescription className="text-center text-slate-400">
              Enter your coupon code to access the trading dashboard
            </CardDescription>
          </CardHeader>
          <form onSubmit={handleSubmit}>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="coupon" className="text-slate-200">Coupon Code</Label>
                <div className="relative">
                  <Key className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                  <Input
                    id="coupon"
                    type="text"
                    placeholder="INFINITY2025"
                    value={couponCode}
                    onChange={(e) => {
                      setCouponCode(e.target.value.toUpperCase());
                      setError('');
                    }}
                    className="pl-10 bg-slate-800 border-slate-600 text-white placeholder:text-slate-500 uppercase font-mono tracking-wider"
                    autoComplete="off"
                    autoFocus
                  />
                </div>
                {error && (
                  <p className="text-sm text-red-400">{error}</p>
                )}
              </div>
            </CardContent>
            <CardFooter>
              <Button
                type="submit"
                className="w-full bg-primary hover:bg-primary/90"
                disabled={isVerifying || !couponCode.trim()}
              >
                {isVerifying ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Verifying...
                  </>
                ) : (
                  'Access Dashboard'
                )}
              </Button>
            </CardFooter>
          </form>
        </Card>

        {/* Features */}
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center p-3 rounded-lg bg-slate-800/50 border border-slate-700">
            <TrendingUp className="h-5 w-5 mx-auto mb-2 text-green-400" />
            <p className="text-xs text-slate-400">AI Trading</p>
          </div>
          <div className="text-center p-3 rounded-lg bg-slate-800/50 border border-slate-700">
            <Brain className="h-5 w-5 mx-auto mb-2 text-blue-400" />
            <p className="text-xs text-slate-400">ML Signals</p>
          </div>
          <div className="text-center p-3 rounded-lg bg-slate-800/50 border border-slate-700">
            <Shield className="h-5 w-5 mx-auto mb-2 text-purple-400" />
            <p className="text-xs text-slate-400">Risk Analysis</p>
          </div>
        </div>

        {/* Help Text */}
        <p className="text-center text-sm text-slate-500">
          Don&apos;t have a coupon? Contact{' '}
          <a href="mailto:support@infinityai.pro" className="text-primary hover:underline">
            support@infinityai.pro
          </a>
        </p>
      </div>
    </div>
  );
}

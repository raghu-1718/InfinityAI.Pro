'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useCouponAuth } from '@/contexts/CouponAuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { Loader2, Key, Sparkles, TrendingUp, Shield, Brain } from 'lucide-react';
import { toast } from 'sonner';

// Google icon component
function GoogleIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
      <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
      <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
      <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
    </svg>
  );
}

export default function LoginPage() {
  const router = useRouter();
  const { verifyCoupon, signInWithGoogle, isAuthenticated, loading } = useCouponAuth();
  const [couponCode, setCouponCode] = useState('');
  const [isVerifying, setIsVerifying] = useState(false);
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);
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

  const handleGoogleSignIn = async () => {
    setIsGoogleLoading(true);
    setError('');

    try {
      const result = await signInWithGoogle();

      if (result.success) {
        toast.success('Welcome to InfinityAI.Pro!', {
          description: 'Signed in with Google. Redirecting to dashboard...',
        });
        router.push('/');
      } else {
        setError(result.error || 'Failed to sign in with Google');
        toast.error('Sign In Failed', {
          description: result.error || 'Please try again.',
        });
      }
    } catch (err) {
      setError('Sign in failed. Please try again.');
      toast.error('Error', { description: 'Sign in failed. Please try again.' });
    }

    setIsGoogleLoading(false);
  };

  const handleCouponSubmit = async (e: React.FormEvent) => {
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
            <CardTitle className="text-2xl text-center text-white">Sign In</CardTitle>
            <CardDescription className="text-center text-slate-400">
              Sign in with Google or enter your access code
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Google Sign In Button */}
            <Button
              type="button"
              variant="outline"
              className="w-full bg-white hover:bg-gray-100 text-gray-900 border-gray-300"
              onClick={handleGoogleSignIn}
              disabled={isGoogleLoading || isVerifying}
            >
              {isGoogleLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Signing in...
                </>
              ) : (
                <>
                  <GoogleIcon className="mr-2 h-5 w-5" />
                  Continue with Google
                </>
              )}
            </Button>

            {/* Divider */}
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <Separator className="w-full bg-slate-700" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-slate-900 px-2 text-slate-500">Or use access code</span>
              </div>
            </div>

            {/* Coupon Code Form */}
            <form onSubmit={handleCouponSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="coupon" className="text-slate-200">Access Code</Label>
                <div className="relative">
                  <Key className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                  <Input
                    id="coupon"
                    type="text"
                    placeholder="Enter your access code"
                    value={couponCode}
                    onChange={(e) => {
                      setCouponCode(e.target.value.toUpperCase());
                      setError('');
                    }}
                    className="pl-10 bg-slate-800 border-slate-600 text-white placeholder:text-slate-500 uppercase font-mono tracking-wider"
                    autoComplete="off"
                  />
                </div>
                {error && (
                  <p className="text-sm text-red-400">{error}</p>
                )}
              </div>
              <Button
                type="submit"
                className="w-full bg-primary hover:bg-primary/90"
                disabled={isVerifying || isGoogleLoading || !couponCode.trim()}
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
            </form>
          </CardContent>
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
          Don&apos;t have an account? Contact{' '}
          <a href="mailto:support@infinityai.pro" className="text-primary hover:underline">
            support@infinityai.pro
          </a>
        </p>
      </div>
    </div>
  );
}

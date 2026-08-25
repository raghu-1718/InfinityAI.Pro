"use client";

import { useEffect, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { Loader2, Key, Sparkles, TrendingUp, Shield, Brain, CheckCircle2, Circle, LockKeyhole } from "lucide-react";
import { toast } from "sonner";

import { useCouponAuth } from "@/contexts/DualAuthContext";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

function GoogleIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" />
      <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
      <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
      <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
    </svg>
  );
}

export default function LoginPage() {
  const router = useRouter();
  const {
    verifyCoupon,
    signInWithGoogle,
    isAuthenticated,
    isGoogleSignedIn,
    isCouponVerified,
    authUser: firebaseUser,
    loading,
  } = useCouponAuth();

  const singleUserMode = process.env.NEXT_PUBLIC_SINGLE_USER_MODE === "true";
  const [couponCode, setCouponCode] = useState("");
  const [isVerifying, setIsVerifying] = useState(false);
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);
  const [error, setError] = useState("");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (mounted && !loading && isAuthenticated) {
      router.push("/");
    }
  }, [mounted, loading, isAuthenticated, router]);

  const handleGoogleSignIn = async () => {
    setIsGoogleLoading(true);
    setError("");

    try {
      const result = await signInWithGoogle();
      if (result.success) {
        toast.success("Google sign-in successful", {
          description: singleUserMode ? "Owner access enabled." : "Now verify access to continue.",
        });
        if (singleUserMode) {
          router.push("/");
        }
      } else {
        setError(result.error || "Failed to sign in with Google");
        toast.error("Sign-in failed", { description: result.error || "Please try again." });
      }
    } catch {
      setError("Sign in failed. Please try again.");
      toast.error("Error", { description: "Sign in failed. Please try again." });
    }

    setIsGoogleLoading(false);
  };

  const handleCouponSubmit = async (e: FormEvent) => {
    e.preventDefault();

    if (!isGoogleSignedIn) {
      setError("Please sign in with Google first.");
      toast.error("Step required", { description: "Please sign in with Google first." });
      return;
    }

    if (singleUserMode) {
      const result = await verifyCoupon("OWNER_ACCESS");
      if (result.success) {
        router.push("/");
      } else {
        setError(result.error || "Access validation failed.");
      }
      return;
    }

    if (!couponCode.trim()) {
      setError("Please enter your access code.");
      return;
    }

    setError("");
    setIsVerifying(true);

    try {
      const result = await verifyCoupon(couponCode.trim().toUpperCase());
      if (result.success) {
        toast.success("Welcome to InfinityAI.Pro", {
          description: "Verification complete. Redirecting to dashboard...",
        });
        router.push("/");
      } else {
        setError(result.error || "Invalid access code.");
        toast.error("Verification failed", { description: result.error || "Please check your access code and try again." });
      }
    } catch {
      setError("Network error. Please try again.");
      toast.error("Error", { description: "Network error. Please try again." });
    }

    setIsVerifying(false);
  };

  return (
    <div className="relative min-h-screen overflow-hidden bg-[radial-gradient(circle_at_top,_rgba(99,102,241,0.25),_transparent_30%),linear-gradient(135deg,_#020817_0%,_#0f172a_45%,_#111827_100%)] px-4 py-12 text-slate-100">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute left-1/2 top-10 h-72 w-72 -translate-x-1/2 rounded-full bg-violet-500/20 blur-3xl" />
        <div className="absolute bottom-0 right-0 h-64 w-64 rounded-full bg-cyan-500/10 blur-3xl" />
      </div>

      <div className="relative mx-auto flex w-full max-w-5xl items-center justify-center">
        <div className="w-full max-w-xl">
          <div className="mb-8 text-center">
            <div className="mb-4 inline-flex h-16 w-16 items-center justify-center rounded-2xl border border-violet-400/40 bg-gradient-to-br from-violet-500/80 to-cyan-500/70 shadow-[0_0_40px_rgba(99,102,241,0.45)]">
              <Sparkles className="h-8 w-8 text-white" />
            </div>
            <h1 className="text-4xl font-black tracking-tight text-white">InfinityAI.Pro</h1>
            <p className="mt-2 text-sm uppercase tracking-[0.3em] text-slate-400">AI-powered execution intelligence</p>
          </div>

          <Card className="border border-slate-700/80 bg-slate-950/70 shadow-[0_30px_80px_rgba(15,23,42,0.8)] backdrop-blur-xl">
            <CardHeader className="space-y-2 pb-4 text-center">
              <CardTitle className="text-2xl font-bold text-white">Secure access</CardTitle>
              <CardDescription className="text-slate-400">
                {singleUserMode
                  ? "Owner mode is enabled for this single-user deployment."
                  : "Sign in with Google and verify your access code to continue."}
              </CardDescription>
            </CardHeader>

            <CardContent className="space-y-6">
              <div className="flex items-center justify-center gap-4 rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
                <div className="flex items-center gap-2">
                  {isGoogleSignedIn ? <CheckCircle2 className="h-5 w-5 text-emerald-400" /> : <Circle className="h-5 w-5 text-slate-500" />}
                  <span className={isGoogleSignedIn ? "text-emerald-400" : "text-slate-400"}>Google</span>
                </div>
                <div className="h-px w-10 bg-slate-700" />
                <div className="flex items-center gap-2">
                  {isCouponVerified || singleUserMode ? <CheckCircle2 className="h-5 w-5 text-emerald-400" /> : <Circle className="h-5 w-5 text-slate-500" />}
                  <span className={isCouponVerified || singleUserMode ? "text-emerald-400" : "text-slate-400"}>{singleUserMode ? "Owner" : "Access"}</span>
                </div>
              </div>

              <div className={`rounded-2xl border p-4 ${isGoogleSignedIn ? "border-emerald-500/40 bg-emerald-500/5" : "border-slate-700 bg-slate-900/50"}`}>
                <div className="mb-3 flex items-center justify-between">
                  <Label className="text-base font-medium text-slate-200">1. Google account</Label>
                  {isGoogleSignedIn && (
                    <Badge variant="outline" className="border-emerald-500/50 bg-emerald-500/10 text-emerald-400">
                      Verified
                    </Badge>
                  )}
                </div>

                {isGoogleSignedIn ? (
                  <div className="flex items-center gap-3 rounded-xl border border-slate-700 bg-slate-800/80 p-3">
                    {firebaseUser?.photoURL ? <img src={firebaseUser.photoURL} alt="Profile" className="h-10 w-10 rounded-full object-cover" /> : <div className="flex h-10 w-10 items-center justify-center rounded-full bg-violet-500/20 text-sm font-bold text-violet-300">{firebaseUser?.displayName?.charAt(0) || "U"}</div>}
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium text-white">{firebaseUser?.displayName || "InfinityAI User"}</p>
                      <p className="truncate text-xs text-slate-400">{firebaseUser?.email || "No email"}</p>
                    </div>
                  </div>
                ) : (
                  <Button type="button" onClick={handleGoogleSignIn} disabled={isGoogleLoading || isVerifying} className="w-full bg-white text-slate-900 hover:bg-slate-200">
                    {isGoogleLoading ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Signing in...</> : <><GoogleIcon className="mr-2 h-5 w-5" />Sign in with Google</>}
                  </Button>
                )}
              </div>

              <div className={`rounded-2xl border p-4 ${!isGoogleSignedIn && !singleUserMode ? "cursor-not-allowed border-slate-800 bg-slate-900/30 opacity-60" : "border-slate-700 bg-slate-900/50"}`}>
                <div className="mb-3 flex items-center justify-between">
                  <Label className="text-base font-medium text-slate-200">{singleUserMode ? "2. Owner verification" : "2. Access code"}</Label>
                  {(isCouponVerified || singleUserMode) && (
                    <Badge variant="outline" className="border-emerald-500/50 bg-emerald-500/10 text-emerald-400">
                      Verified
                    </Badge>
                  )}
                </div>

                <form onSubmit={handleCouponSubmit} className="space-y-3">
                  {!singleUserMode && (
                    <div className="relative">
                      <Key className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
                      <Input
                        id="coupon"
                        type="text"
                        value={couponCode}
                        onChange={(e) => {
                          setCouponCode(e.target.value.toUpperCase());
                          setError("");
                        }}
                        placeholder="ENTER ACCESS CODE"
                        className="border-slate-700 bg-slate-950 pl-10 font-mono uppercase tracking-[0.25em] text-white placeholder:text-slate-500"
                        autoComplete="off"
                        disabled={!isGoogleSignedIn || isCouponVerified}
                      />
                    </div>
                  )}

                  {singleUserMode && (
                    <div className="flex items-center gap-3 rounded-xl border border-violet-500/30 bg-violet-500/5 p-3 text-sm text-violet-200">
                      <LockKeyhole className="h-4 w-4" />
                      <span>Single-user owner access is enabled with Firebase Auth.</span>
                    </div>
                  )}

                  {error && <p className="text-sm text-red-400">{error}</p>}

                  <Button type="submit" className="w-full bg-gradient-to-r from-violet-600 to-cyan-500 hover:from-violet-500 hover:to-cyan-400" disabled={(!isGoogleSignedIn && !singleUserMode) || isVerifying || isGoogleLoading || (!singleUserMode && !couponCode.trim()) || isCouponVerified}>
                    {isVerifying ? (
                      <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Verifying...</>
                    ) : (isCouponVerified || singleUserMode) ? (
                      <><CheckCircle2 className="mr-2 h-4 w-4" />Verified</>
                    ) : (
                      singleUserMode ? "Continue to dashboard" : "Verify access code"
                    )}
                  </Button>
                </form>
              </div>
            </CardContent>
          </Card>

          <div className="mt-6 grid grid-cols-3 gap-3">
            <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-3 text-center">
              <TrendingUp className="mx-auto mb-2 h-5 w-5 text-emerald-400" />
              <p className="text-[11px] uppercase tracking-[0.2em] text-slate-400">AI Trading</p>
            </div>
            <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-3 text-center">
              <Brain className="mx-auto mb-2 h-5 w-5 text-cyan-400" />
              <p className="text-[11px] uppercase tracking-[0.2em] text-slate-400">ML Signals</p>
            </div>
            <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-3 text-center">
              <Shield className="mx-auto mb-2 h-5 w-5 text-violet-400" />
              <p className="text-[11px] uppercase tracking-[0.2em] text-slate-400">Risk Control</p>
            </div>
          </div>

          <p className="mt-6 text-center text-sm text-slate-500">
            Need help? <a href="mailto:support@infinityai.pro" className="text-violet-300 hover:text-violet-200">support@infinityai.pro</a>
          </p>
        </div>
      </div>
    </div>
  );
}

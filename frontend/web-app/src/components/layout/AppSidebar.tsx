"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  Zap,
  BarChart3,
  Activity,
  Target,
  History,
  Settings,
  Brain,
  TrendingUp,
  LineChart,
  PieChart,
  Wallet,
  LogOut,
  ChevronLeft,
  ChevronRight,
  Sun,
  Moon,
} from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { useTheme } from "next-themes";
import { useIndices, useFunds } from "@/hooks/useApi";
import { useAppStore } from "@/lib/store";

const NAVIGATION = [
  { name: "Dashboard", href: "/", icon: LayoutDashboard },
  { name: "Trading", href: "/trading", icon: Zap },
  { name: "Options", href: "/options", icon: Target },
  { name: "Portfolio", href: "/portfolio", icon: PieChart },
  { name: "Signals", href: "/signals", icon: Brain },
  { name: "Analytics", href: "/analytics", icon: BarChart3 },
  { name: "Backtest", href: "/backtest", icon: History },
  { name: "History", href: "/history", icon: Activity },
];

const BOTTOM_NAV = [
  { name: "Settings", href: "/settings", icon: Settings },
];

export function AppSidebar() {
  const pathname = usePathname();
  const { userProfile } = useAppStore();
  const [collapsed, setCollapsed] = useState(false);
  const { theme, setTheme } = useTheme();

  return (
    <aside className={cn(
      "glass-sidebar h-screen flex flex-col transition-all duration-300 relative",
      collapsed ? "w-20" : "w-64"
    )}>
      {/* Logo */}
      <div className="p-6 border-b border-white/5">
        <Link href="/" className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-600 to-cyan-500 flex items-center justify-center shadow-lg neon-glow-purple">
            <TrendingUp className="h-5 w-5 text-white" />
          </div>
          {!collapsed && (
            <div>
              <h1 className="text-xl font-bold text-white">Infinity<span className="gradient-text">AI</span></h1>
              <p className="text-[10px] text-white/40 -mt-1">Automated Trading</p>
            </div>
          )}
        </Link>
      </div>

      {/* Collapse Button */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="absolute -right-3 top-20 w-6 h-6 rounded-full bg-purple-600 flex items-center justify-center text-white shadow-lg hover:bg-purple-500 transition-colors z-50"
      >
        {collapsed ? <ChevronRight className="h-3 w-3" /> : <ChevronLeft className="h-3 w-3" />}
      </button>

      {/* Main Navigation */}
      <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
        {NAVIGATION.map((item) => {
          const isActive = pathname === item.href || 
            (item.href !== "/" && pathname.startsWith(item.href));
          
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group",
                isActive 
                  ? "bg-gradient-to-r from-purple-600/20 to-cyan-600/20 text-white border border-purple-500/30" 
                  : "text-white/60 hover:text-white hover:bg-white/5"
              )}
            >
              <item.icon className={cn(
                "h-5 w-5 transition-colors",
                isActive ? "text-purple-400" : "text-white/60 group-hover:text-purple-400"
              )} />
              {!collapsed && (
                <span className="font-medium">{item.name}</span>
              )}
              {isActive && !collapsed && (
                <div className="ml-auto w-1.5 h-1.5 rounded-full bg-purple-400 animate-pulse" />
              )}
            </Link>
          );
        })}
      </nav>

      {/* Bottom Section */}
      <div className="p-4 border-t border-white/5 space-y-2">
        {BOTTOM_NAV.map((item) => (
          <Link
            key={item.name}
            href={item.href}
            className={cn(
              "flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 text-white/60 hover:text-white hover:bg-white/5"
            )}
          >
            <item.icon className="h-5 w-5" />
            {!collapsed && <span className="font-medium">{item.name}</span>}
          </Link>
        ))}

        {/* Theme Toggle */}
        <button
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          className="flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 text-white/60 hover:text-white hover:bg-white/5 w-full"
        >
          {theme === "dark" ? (
            <Sun className="h-5 w-5" />
          ) : (
            <Moon className="h-5 w-5" />
          )}
          {!collapsed && <span className="font-medium">Toggle Theme</span>}
        </button>

        {/* User Profile */}
        {!collapsed && (
          <div className="mt-4 p-4 rounded-xl bg-white/5 border border-white/10">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-cyan-500 flex items-center justify-center text-white font-bold">
                {/* Initials */}
                {(userProfile?.name || "User").substring(0, 2).toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-white truncate">{userProfile?.name || "Trader"}</p>
                <p className="text-xs text-white/40 truncate">{userProfile?.isConnected ? "Connected" : "Guest Mode"}</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}

export function TopBar() {
  const { data: indicesRes } = useIndices();
  const { data: fundsRes } = useFunds();
  
  const indices = indicesRes?.data?.data?.IDX_I || {};
  const nifty = indices['13'];
  const bankNifty = indices['25'];
  
  // Helper to calculate change
  const getChange = (quote: any) => {
    if (!quote || !quote.last_price || !quote.ohlc?.open) return { val: 0, pct: 0 };
    // Using Open as proxy for prev close if prev close missing for Intraday change
    const base = quote.ohlc.open; 
    const diff = quote.last_price - base;
    const pct = (diff / base) * 100;
    return { val: diff, pct };
  };

  const niftyChange = getChange(nifty);
  const bankChange = getChange(bankNifty);
  
  // Safe formatting
  const fmt = (n: number) => n?.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || "--";

  const totalFunds = fundsRes?.data?.availableBalance || 0;

  return (
    <header className="glass h-16 px-6 flex items-center justify-between border-b border-white/5">
      <div className="flex items-center gap-4">
        <div className="badge-live">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          LIVE
        </div>
        <div className="text-sm text-white/60">
          <span className="text-white font-medium">NSE</span> • Market Open
        </div>
      </div>

      <div className="flex items-center gap-6">
        {/* Market Ticker */}
        <div className="hidden lg:flex items-center gap-6 text-sm">
          {/* NIFTY 50 */}
          <div className="flex items-center gap-2">
            <span className="text-white/60">NIFTY</span>
            <span className="text-white font-mono font-medium">{fmt(nifty?.last_price)}</span>
            <span className={cn("text-xs", niftyChange.pct >= 0 ? "text-emerald-400" : "text-red-400")}>
              {niftyChange.pct >= 0 ? "+" : ""}{niftyChange.pct.toFixed(2)}%
            </span>
          </div>
          <div className="w-px h-4 bg-white/20" />
          
          {/* BANKNIFTY */}
          <div className="flex items-center gap-2">
            <span className="text-white/60">BANKNIFTY</span>
            <span className="text-white font-mono font-medium">{fmt(bankNifty?.last_price)}</span>
            <span className={cn("text-xs", bankChange.pct >= 0 ? "text-emerald-400" : "text-red-400")}>
               {bankChange.pct >= 0 ? "+" : ""}{bankChange.pct.toFixed(2)}%
            </span>
          </div>
          <div className="w-px h-4 bg-white/20" />
          
          {/* VIX (Static for now if ID unknown or use fallback) */}
          <div className="flex items-center gap-2">
            <span className="text-white/60">VIX</span>
            <span className="text-white font-mono font-medium">12.45</span>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" className="text-white/60 hover:text-white">
            <Wallet className="h-4 w-4 mr-2" />
            ₹{totalFunds.toLocaleString('en-IN')}
          </Button>
        </div>
      </div>
    </header>
  );
}

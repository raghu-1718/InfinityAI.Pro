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
  { name: "Portfolio", href: "/portfolio", icon: PieChart },
  { name: "Trading", href: "/trading", icon: Zap },
  { name: "AI Signals", href: "/signals", icon: Activity },
  { name: "Intelligence", href: "/intelligence", icon: Brain },
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
  
  // Recursively extract quotes from DhanHQ response
  const extractSegment = (raw: any, seg: string) => {
    if (!raw) return {};
    let curr = raw.data || raw;
    let depth = 0;
    while (curr && curr.data && typeof curr.data === 'object' && !curr[seg] && depth < 5) {
      curr = curr.data;
      depth++;
    }
    return curr?.[seg] || curr || {};
  };

  const indices = extractSegment(indicesRes, "IDX_I");
  const nifty = indices['13'] || {};
  const bankNifty = indices['25'] || {};
  const vix = indices['26'] || {};
  
  // Live IST Market Hours Calculation (09:15 to 15:30 IST, Mon-Fri)
  const getMarketStatus = () => {
    try {
      const now = new Date();
      const istString = now.toLocaleString("en-US", { timeZone: "Asia/Kolkata" });
      const istDate = new Date(istString);
      const day = istDate.getDay(); // 0 is Sunday, 6 is Saturday
      const hours = istDate.getHours();
      const minutes = istDate.getMinutes();
      const currentMinutes = hours * 60 + minutes;

      const marketOpenMinutes = 9 * 60 + 15;   // 09:15 IST
      const marketCloseMinutes = 15 * 60 + 30; // 15:30 IST

      const isWeekday = day >= 1 && day <= 5;
      const isTradingHours = currentMinutes >= marketOpenMinutes && currentMinutes <= marketCloseMinutes;

      if (isWeekday && isTradingHours) {
        return { isOpen: true, badge: "LIVE", text: "NSE • Market Open", badgeClass: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" };
      } else {
        const reason = !isWeekday ? "Weekend" : "Off-Hours";
        return { isOpen: false, badge: "CLOSED", text: `NSE • Market Closed (${reason})`, badgeClass: "bg-zinc-800 text-zinc-400 border-zinc-700" };
      }
    } catch {
      return { isOpen: false, badge: "CLOSED", text: "NSE • Market Closed", badgeClass: "bg-zinc-800 text-zinc-400 border-zinc-700" };
    }
  };

  const marketStatus = getMarketStatus();

  // Helper to calculate change
  const getChange = (quote: any, defaultLtp: number, defaultPct: number) => {
    const ltp = Number(quote?.last_price || quote?.ltp || quote?.ohlc?.close || defaultLtp);
    if (!quote?.ohlc?.open) return { ltp, val: 0, pct: defaultPct };
    const base = Number(quote.ohlc.open); 
    const diff = ltp - base;
    const pct = (diff / base) * 100;
    return { ltp, val: diff, pct };
  };

  const niftyMetric = getChange(nifty, 24366.00, -0.12);
  const bankMetric = getChange(bankNifty, 57491.10, -0.25);
  const vixLtp = Number(vix?.last_price || vix?.ltp || 12.45);
  
  // Safe formatting
  const fmt = (n: number) => n?.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || "--";

  const totalFunds = fundsRes?.funds?.availableBalance ?? fundsRes?.data?.availableBalance ?? 11.18;

  return (
    <header className="glass h-16 px-6 flex items-center justify-between border-b border-white/5">
      <div className="flex items-center gap-4">
        <div className={cn("px-2.5 py-1 rounded-full text-xs font-bold font-mono flex items-center gap-1.5 border", marketStatus.badgeClass)}>
          <span className={cn("w-2 h-2 rounded-full", marketStatus.isOpen ? "bg-emerald-400 animate-pulse" : "bg-zinc-400")} />
          {marketStatus.badge}
        </div>
        <div className="text-sm text-white/60">
          <span className="text-white font-medium">NSE</span> • {marketStatus.text.replace("NSE • ", "")}
        </div>
      </div>

      <div className="flex items-center gap-6">
        {/* Market Ticker */}
        <div className="hidden lg:flex items-center gap-6 text-sm">
          {/* NIFTY 50 */}
          <div className="flex items-center gap-2">
            <span className="text-white/60 font-semibold">NIFTY</span>
            <span className="text-white font-mono font-bold">₹{fmt(niftyMetric.ltp)}</span>
            <span className={cn("text-xs font-mono font-medium", niftyMetric.pct >= 0 ? "text-emerald-400" : "text-rose-400")}>
              {niftyMetric.pct >= 0 ? "+" : ""}{niftyMetric.pct.toFixed(2)}%
            </span>
          </div>
          <div className="w-px h-4 bg-white/20" />
          
          {/* BANKNIFTY */}
          <div className="flex items-center gap-2">
            <span className="text-white/60 font-semibold">BANKNIFTY</span>
            <span className="text-white font-mono font-bold">₹{fmt(bankMetric.ltp)}</span>
            <span className={cn("text-xs font-mono font-medium", bankMetric.pct >= 0 ? "text-emerald-400" : "text-rose-400")}>
               {bankMetric.pct >= 0 ? "+" : ""}{bankMetric.pct.toFixed(2)}%
            </span>
          </div>
          <div className="w-px h-4 bg-white/20" />
          
          {/* VIX */}
          <div className="flex items-center gap-2">
            <span className="text-white/60 font-semibold">INDIA VIX</span>
            <span className="text-amber-400 font-mono font-bold">{vixLtp.toFixed(2)}</span>
          </div>
        </div>

        {/* Available Cash Margin Action */}
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" className="text-emerald-400 hover:text-emerald-300 font-mono font-bold bg-emerald-500/10 border border-emerald-500/20">
            <Wallet className="h-4 w-4 mr-2" />
            ₹{totalFunds.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </Button>
        </div>
      </div>
    </header>
  );
}

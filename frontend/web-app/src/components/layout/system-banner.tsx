"use client";

import { useEffect, useState } from "react";
import { AlertCircle, Terminal, ShieldAlert } from "lucide-react";

// Simple types for banner state
type SystemState = {
  status: "NORMAL" | "DEGRADED" | "MAINTENANCE" | "KILL_SWITCH_ACTIVE";
  message?: string;
  engine_version?: string;
};

// Fallback logic if API fails
const DEFAULT_STATE: SystemState = {
  status: "NORMAL",
  engine_version: "v4.0",
};

import { getEngineAUrl } from "@/lib/api";

const ENGINE_A_URL = getEngineAUrl();

export function SystemBanner() {
  const [state, setState] = useState<SystemState | null>(DEFAULT_STATE);

  useEffect(() => {
    const fetchState = async () => {
      try {
        // Ideally fetch from Engine A which orchestrates everything
        // Using a short timeout to not block UI rendering if slow
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 2000);

        const res = await fetch(`${ENGINE_A_URL}/api/system/state`, {
          signal: controller.signal,
          next: { revalidate: 60 },
        });
        clearTimeout(timeoutId);

        if (res.ok) {
          const data = await res.json();
          setState(data);
        } else {
          setState(DEFAULT_STATE);
        }
      } catch (e) {
        // Silent fail to default
        setState(DEFAULT_STATE);
      }
    };

    fetchState();
    // Poll every 30s
    const interval = setInterval(fetchState, 30000);
    return () => clearInterval(interval);
  }, []);

  if (!state || state.status === "NORMAL") return null;

  const isKillSwitch = state.status === "KILL_SWITCH_ACTIVE";

  return (
    <div
      className={`w-full px-4 py-2 flex items-center justify-center gap-3 text-sm font-bold tracking-wide
        ${isKillSwitch ? "bg-red-600 text-white animate-pulse" : "bg-yellow-500 text-black"}
    `}
    >
      {isKillSwitch ? (
        <ShieldAlert className="h-4 w-4" />
      ) : (
        <AlertCircle className="h-4 w-4" />
      )}
      <span>
        SYSTEM STATUS: {(state.status || "").replace(/_/g, " ")}
        {state.message && (
          <span className="mx-2 opacity-80 font-normal border-l border-white/20 pl-2">
            {state.message}
          </span>
        )}
      </span>
    </div>
  );
}

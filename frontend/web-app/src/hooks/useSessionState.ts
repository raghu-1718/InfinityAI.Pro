import { useState, useEffect } from 'react';
import { getEngineAUrl } from '@/lib/api';

export interface SessionState {
  consecutive_losses: number;
  session_pnl: number;
  halted: boolean;
  halt_reason?: string | null;
  updated_at?: string;
}

export function useSessionState(uid: string | null | undefined) {
  const [state, setState] = useState<SessionState | null>(null);

  useEffect(() => {
    if (!uid) return;

    // Fetch system and session state from Engine-A
    const fetchState = async () => {
      try {
        const engineAUrl = getEngineAUrl();
        const res = await fetch(`${engineAUrl}/api/system/state`, {
          headers: { 'X-User-ID': uid },
        });
        if (res.ok) {
          const data = await res.json();
          setState({
            consecutive_losses: 0,
            session_pnl: 0,
            halted: data.system_status === 'KILL_SWITCH',
            halt_reason: data.system_status !== 'NORMAL' ? data.system_status : null,
            updated_at: data.timestamp,
          });
        }
      } catch (err) {
        // Safe non-blocking fallback
      }
    };

    // Initial fetch
    fetchState();

    // Poll every 15 seconds
    const interval = setInterval(fetchState, 15000);

    return () => clearInterval(interval);
  }, [uid]);

  return state;
}


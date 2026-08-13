import { useState, useEffect } from 'react';
import { supabase, isSupabaseConfigured } from '@/lib/supabase';

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
    if (!uid || !isSupabaseConfigured()) return;

    // Fetch circuit breaker state (when Supabase is configured)
    const fetchState = async () => {
      try {
        const { data, error } = await supabase
          .from('circuit_breaker_state')
          .select('*')
          .eq('user_id', uid)
          .maybeSingle();

        if (data && !error) {
          setState({
            consecutive_losses: data.consecutive_losses || 0,
            session_pnl: data.session_pnl || 0,
            halted: data.halted || false,
            halt_reason: data.halt_reason,
            updated_at: data.updated_at,
          });
        } else {
          setState(null);
        }
      } catch (err) {
        console.error("Session State Fetch Error:", err);
      }
    };

    // Initial fetch
    fetchState();

    // Poll every 5 seconds for near-real-time updates
    const interval = setInterval(fetchState, 5000);

    return () => clearInterval(interval);
  }, [uid]);

  return state;
}

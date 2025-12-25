import { useState, useEffect } from 'react';
import { doc, onSnapshot } from "firebase/firestore";
import { db } from "@/lib/firebase";

export interface SessionState {
  consecutive_losses: number;
  session_pnl: number;
  halted: boolean;
  halt_reason?: string | null;
  updated_at?: any;
}

export function useSessionState(uid: string | null | undefined) {
  const [state, setState] = useState<SessionState | null>(null);

  useEffect(() => {
    if (!uid || !db) return;

    const docRef = doc(db, "trading_sessions", uid, "state", "circuit_breaker"); // Path matches Backend CircuitBreaker

    const unsubscribe = onSnapshot(docRef, (snap) => {
      if (snap.exists()) {
          setState(snap.data() as SessionState);
      } else {
          setState(null);
      }
    }, (err) => {
        console.error("Session State Stream Error:", err);
    });

    return () => unsubscribe();
  }, [uid]);

  return state;
}

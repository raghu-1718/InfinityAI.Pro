import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

interface SessionState {
  sessionId: string | null;
  userId: string | null;
  features: string[];
  isAuthenticated: boolean;
  expiresAt: string | null;
  setSession: (session: { sessionId: string; userId: string; features: string[]; expiresAt: string }) => void;
  clearSession: () => void;
  validateSession: () => boolean; // Basic expiry check
}

export const useSessionStore = create<SessionState>()(
  persist(
    (set, get) => ({
      sessionId: null,
      userId: null,
      features: [],
      isAuthenticated: false,
      expiresAt: null,

      setSession: (session) => {
        set({
          sessionId: session.sessionId,
          userId: session.userId,
          features: session.features,
          expiresAt: session.expiresAt,
          isAuthenticated: true,
        });
      },

      clearSession: () => {
        set({
          sessionId: null,
          userId: null,
          features: [],
          isAuthenticated: false,
          expiresAt: null,
        });
      },

      validateSession: () => {
        const { expiresAt, isAuthenticated } = get();
        if (!isAuthenticated || !expiresAt) return false;
        return new Date(expiresAt) > new Date();
      }
    }),
    {
      name: 'infinity-session-storage', // unique name
      storage: createJSONStorage(() => localStorage),
    }
  )
);

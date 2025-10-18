import { create, StateCreator } from 'zustand'

type AuthState = {
  token: string | null
  setToken: (t: string | null) => void
  getAuthHeader: () => Record<string, string>
}

const creator: StateCreator<AuthState, [], []> = (set, get) => ({
  token: null,
  setToken: (t) => set({ token: t }),
  getAuthHeader: () => {
    const t = get().token
    if (!t) return {} as Record<string, string>
    return { Authorization: `Bearer ${t}` }
  }
})

export const useAuthStore = create<AuthState>(creator)

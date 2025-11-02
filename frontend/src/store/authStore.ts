import { create } from 'zustand'
import axios from 'axios'

const ENGINE_D_URL = import.meta.env.VITE_ENGINE_D_URL

interface AuthState {
  token: string | null
  expiresAt: number | null
  isAuthenticated: boolean
  fetchToken: () => Promise<void>
  getAuthHeader: () => Record<string, string>
  ensureTokenValid: () => Promise<void>
  logout: () => void
}

export const useAuthStore = create<AuthState>((set, get) => ({
  token: null,
  expiresAt: null,
  isAuthenticated: false,

  async fetchToken() {
    try {
      // For now, use a simple token fetch from Engine D
      // In production, this would be a proper OAuth flow
  await axios.get(`${ENGINE_D_URL}/health`)
      
      // Generate a session token (in production, Engine D would provide this)
      const token = `session_${Date.now()}_${Math.random().toString(36).substring(7)}`
      const expiry = Date.now() + 110 * 60 * 1000 // 110 minutes
      
      set({ 
        token, 
        expiresAt: expiry,
        isAuthenticated: true
      })
      
      console.log('✅ Auth token generated')
    } catch (error) {
      console.error('❌ Token fetch failed:', error)
      set({ token: null, expiresAt: null, isAuthenticated: false })
    }
  },

  getAuthHeader(): Record<string, string> {
    const { token } = get()
    return token ? { Authorization: `Bearer ${token}` } : { Authorization: '' }
  },

  async ensureTokenValid() {
    const { expiresAt, fetchToken } = get()
    if (!expiresAt || Date.now() > expiresAt - 5 * 60 * 1000) {
      await fetchToken()
    }
  },

  logout() {
    set({ token: null, expiresAt: null, isAuthenticated: false })
  },
}))

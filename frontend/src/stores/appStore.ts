import { create } from 'zustand'
import { subscribeWithSelector } from 'zustand/middleware'

interface User {
  uid: string
  email: string
  displayName?: string
}

interface AppState {
  // User state
  user: User | null
  isAuthenticated: boolean

  // Engine status
  engines: {
    'engine-a': { status: 'online' | 'offline' | 'error', lastChecked: Date | null }
    'engine-b': { status: 'online' | 'offline' | 'error', lastChecked: Date | null }
    'engine-c': { status: 'online' | 'offline' | 'error', lastChecked: Date | null }
    'engine-d': { status: 'online' | 'offline' | 'error', lastChecked: Date | null }
  }

  // AI Analysis data
  aiAnalysis: {
    gemini: any | null
    vertex: any | null
    signals: any[] | null
    lastUpdated: Date | null
    isLoading: boolean
    error: string | null
  }

  // Real-time data
  realTimeData: {
    marketData: any | null
    websocketConnected: boolean
    lastUpdate: Date | null
  }

  // Actions
  setUser: (user: User | null) => void
  updateEngineStatus: (engine: string, status: any) => void
  setAiAnalysis: (type: string, data: any) => void
  setAiAnalysisLoading: (loading: boolean) => void
  setAiAnalysisError: (error: string | null) => void
  setRealTimeData: (data: any) => void
  setWebSocketStatus: (connected: boolean) => void
}

export const useAppStore = create<AppState>()(
  subscribeWithSelector((set) => ({
    // Initial state
    user: null,
    isAuthenticated: false,

    engines: {
      'engine-a': { status: 'offline', lastChecked: null },
      'engine-b': { status: 'offline', lastChecked: null },
      'engine-c': { status: 'offline', lastChecked: null },
      'engine-d': { status: 'offline', lastChecked: null },
    },

    aiAnalysis: {
      gemini: null,
      vertex: null,
      signals: null,
      lastUpdated: null,
      isLoading: false,
      error: null,
    },

    realTimeData: {
      marketData: null,
      websocketConnected: false,
      lastUpdate: null,
    },

    // Actions
    setUser: (user) => set({ user, isAuthenticated: !!user }),

    updateEngineStatus: (engine, status) => set((state) => ({
      engines: {
        ...state.engines,
        [engine]: { ...status, lastChecked: new Date() }
      }
    })),

    setAiAnalysis: (type, data) => set((state) => ({
      aiAnalysis: {
        ...state.aiAnalysis,
        [type]: data,
        lastUpdated: new Date(),
        error: null,
      }
    })),

    setAiAnalysisLoading: (loading) => set((state) => ({
      aiAnalysis: { ...state.aiAnalysis, isLoading: loading }
    })),

    setAiAnalysisError: (error) => set((state) => ({
      aiAnalysis: { ...state.aiAnalysis, error, isLoading: false }
    })),

    setRealTimeData: (data) => set((state) => ({
      realTimeData: {
        ...state.realTimeData,
        marketData: data,
        lastUpdate: new Date(),
      }
    })),

    setWebSocketStatus: (connected) => set((state) => ({
      realTimeData: { ...state.realTimeData, websocketConnected: connected }
    })),
  }))
)

// Selectors for optimized subscriptions
export const useUser = () => useAppStore((state) => state.user)
export const useEngines = () => useAppStore((state) => state.engines)
export const useAiAnalysis = () => useAppStore((state) => state.aiAnalysis)
export const useRealTimeData = () => useAppStore((state) => state.realTimeData)

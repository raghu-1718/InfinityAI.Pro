import { create } from 'zustand'

interface Trade {
  id: string
  timestamp: string
  symbol: string
  type: 'BUY' | 'SELL'
  quantity: number
  price: number
  status: 'pending' | 'executed' | 'failed'
  strategy: string
}

interface TradeState {
  trades: Trade[]
  activeStrategy: string | null
  isExecuting: boolean
  addTrade: (trade: Trade) => void
  updateTrade: (id: string, updates: Partial<Trade>) => void
  clearTrades: () => void
  setActiveStrategy: (strategy: string | null) => void
  setExecuting: (executing: boolean) => void
}

export const useTradeStore = create<TradeState>((set) => ({
  trades: [],
  activeStrategy: null,
  isExecuting: false,

  addTrade: (trade) =>
    set((state) => ({
      trades: [...state.trades, trade],
    })),

  updateTrade: (id, updates) =>
    set((state) => ({
      trades: state.trades.map((trade) =>
        trade.id === id ? { ...trade, ...updates } : trade
      ),
    })),

  clearTrades: () => set({ trades: [] }),

  setActiveStrategy: (strategy) => set({ activeStrategy: strategy }),

  setExecuting: (executing) => set({ isExecuting: executing }),
}))

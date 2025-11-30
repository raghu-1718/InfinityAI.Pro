import { create } from 'zustand';
import { subscribeWithSelector, persist } from 'zustand/middleware';

// Types
export interface EngineStatus {
  status: 'online' | 'offline' | 'loading';
  version: string | null;
  lastChecked: Date | null;
  capabilities?: string[];
}

export interface FundsData {
  availableBalance: number;
  sodLimit: number;
  collateralAmount: number;
  dhanClientId: string;
}

export interface UserProfile {
  userId: string;
  clientId: string;
  name: string;
  email: string;
  isConnected: boolean;
  isVerified: boolean;
}

export interface DematData {
  holdings: {
    totalValue: number;
    count: number;
    items: Array<{
      symbol: string;
      quantity: number;
      avgPrice: number;
      currentPrice: number;
      pnl: number;
    }>;
  };
  positions: {
    totalPnl: number;
    count: number;
    items: Array<{
      symbol: string;
      quantity: number;
      entryPrice: number;
      currentPrice: number;
      pnl: number;
    }>;
  };
  funds: {
    availableBalance: number;
    utilisedMargin: number;
    totalBalance: number;
  };
}

export interface Position {
  symbol: string;
  quantity: number;
  avgPrice: number;
  ltp: number;
  pnl: number;
  pnlPercent: number;
}

export interface Signal {
  symbol: string;
  signal: 'BUY' | 'SELL' | 'HOLD';
  confidence: number;
  timestamp: string;
}

export interface RiskMetrics {
  sharpe_ratio: number;
  sortino_ratio: number;
  var_95: number;
  cvar_95: number;
  max_drawdown_pct: number;
  annualized_return: number;
  annualized_volatility: number;
}

interface AppState {
  // Theme
  theme: 'light' | 'dark';
  toggleTheme: () => void;

  // User Profile
  userProfile: UserProfile | null;
  setUserProfile: (profile: UserProfile | null) => void;

  // Demat Data (from connected user's account)
  dematData: DematData | null;
  setDematData: (data: DematData | null) => void;

  // Engine Status
  engines: {
    engineA: EngineStatus;
    engineB: EngineStatus;
    engineC: EngineStatus;
  };
  updateEngineStatus: (engine: 'engineA' | 'engineB' | 'engineC', status: Partial<EngineStatus>) => void;

  // Funds & Portfolio
  funds: FundsData | null;
  positions: Position[];
  setFunds: (funds: FundsData) => void;
  setPositions: (positions: Position[]) => void;

  // Signals
  signals: Signal[];
  addSignal: (signal: Signal) => void;
  setSignals: (signals: Signal[]) => void;

  // Risk Metrics
  riskMetrics: RiskMetrics | null;
  setRiskMetrics: (metrics: RiskMetrics) => void;

  // UI State
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
  selectedSymbol: string;
  setSelectedSymbol: (symbol: string) => void;

  // WebSocket
  wsConnected: boolean;
  setWsConnected: (connected: boolean) => void;
}

export const useAppStore = create<AppState>()(
  subscribeWithSelector(
    persist(
      (set) => ({
        // Theme
        theme: 'dark',
        toggleTheme: () => set((state) => ({ theme: state.theme === 'dark' ? 'light' : 'dark' })),

        // User Profile
        userProfile: null,
        setUserProfile: (userProfile) => set({ userProfile }),

        // Demat Data
        dematData: null,
        setDematData: (dematData) => set({ dematData }),

        // Engine Status
        engines: {
          engineA: { status: 'loading', version: null, lastChecked: null },
          engineB: { status: 'loading', version: null, lastChecked: null },
          engineC: { status: 'loading', version: null, lastChecked: null },
        },
        updateEngineStatus: (engine, status) =>
          set((state) => ({
            engines: {
              ...state.engines,
              [engine]: {
                ...state.engines[engine],
                ...status,
                lastChecked: new Date(),
              },
            },
          })),

        // Funds & Portfolio
        funds: null,
        positions: [],
        setFunds: (funds) => set({ funds }),
        setPositions: (positions) => set({ positions }),

        // Signals
        signals: [],
        addSignal: (signal) =>
          set((state) => ({
            signals: [signal, ...state.signals].slice(0, 50), // Keep last 50
          })),
        setSignals: (signals) => set({ signals }),

        // Risk Metrics
        riskMetrics: null,
        setRiskMetrics: (riskMetrics) => set({ riskMetrics }),

        // UI State
        sidebarOpen: true,
        setSidebarOpen: (sidebarOpen) => set({ sidebarOpen }),
        selectedSymbol: 'NIFTY',
        setSelectedSymbol: (selectedSymbol) => set({ selectedSymbol }),

        // WebSocket
        wsConnected: false,
        setWsConnected: (wsConnected) => set({ wsConnected }),
      }),
      {
        name: 'infinityai-storage',
        partialize: (state) => ({
          theme: state.theme,
          userProfile: state.userProfile,
        }),
      }
    )
  )
);

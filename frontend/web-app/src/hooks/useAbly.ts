// Mock hooks to replace Ably functionality temporarily to allow the build to pass.
// TODO: Implement with Supabase Realtime

export function useTradingSignals(engineId?: string, callback?: (signal: any) => void) {
  return {
    connectionState: "disconnected",
    error: null,
  };
}

export function usePortfolioUpdates(userId: string, callback?: (update: any) => void) {
  return {
    connectionState: "disconnected",
    error: null,
  };
}

export function useMarketData(symbols: string[], callback?: (data: any) => void) {
  return {
    connectionState: "disconnected",
    error: null,
  };
}

export function useTradeExecution(callback?: (execution: any) => void) {
  return {
    connectionState: "disconnected",
    error: null,
  };
}

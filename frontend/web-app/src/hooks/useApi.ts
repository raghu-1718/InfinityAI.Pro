'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api, engineA, engineB, engineC } from '@/lib/api';
import { useAppStore } from '@/lib/store';
import { useEffect, useCallback } from 'react';
import { getUserId } from '@/lib/user';

// Engine Health Hooks
export function useEngineHealth() {
  const updateEngineStatus = useAppStore((s) => s.updateEngineStatus);

  const query = useQuery({
    queryKey: ['engines', 'health'],
    queryFn: () => api.checkAllEngines(),
    refetchInterval: 30000, // 30 seconds
    staleTime: 10000,
    retry: 1, // Only retry once
    retryDelay: 2000,
  });

  useEffect(() => {
    if (query.data) {
      const { engineA, engineB, engineC } = query.data;

      updateEngineStatus('engineA', {
        status: engineA ? 'online' : 'offline',
        version: engineA?.version || null,
        capabilities: Array.isArray(engineA?.ml_capabilities) ? engineA.ml_capabilities : [],
        lastChecked: new Date(),
      });

      updateEngineStatus('engineB', {
        status: engineB ? 'online' : 'offline',
        version: engineB?.version || null,
        capabilities: engineB?.capabilities ? Object.keys(engineB.capabilities) : (Array.isArray(engineB?.ml_capabilities) ? engineB.ml_capabilities : []),
        lastChecked: new Date(),
      });

      updateEngineStatus('engineC', {
        status: engineC ? 'online' : 'offline',
        version: engineC?.version || null,
        capabilities: Array.isArray(engineC?.ml_capabilities) ? engineC.ml_capabilities : [],
        lastChecked: new Date(),
      });
    }
  }, [query.data, updateEngineStatus]);

  return query;
}

// User Profile Hook - Fetches user's Dhan credentials status
export function useUserProfile() {
  const { setUserProfile, setDematData, setFunds, userProfile: currentProfile } = useAppStore();

  return useQuery({
    queryKey: ['userProfile', getUserId()],
    queryFn: async () => {
      const userId = getUserId();

      try {
        const res = await engineC.getUserCredentials(userId);

        if (res.configured && res.is_verified) {
          // User is connected, fetch their demat data
          try {
            const dematRes = await engineC.getUserDemat(userId);
            if (dematRes && dematRes.funds) {
              setDematData(dematRes);
              setFunds({
                availableBalance: dematRes.funds.availableBalance || 0,
                sodLimit: 0,
                collateralAmount: dematRes.funds.utilisedMargin || 0,
                dhanClientId: res.client_id,
              });
            }
          } catch (e) {
            console.error('Failed to fetch demat data:', e);
          }

          // Set the user profile as connected
          const newProfile = {
            userId,
            clientId: res.client_id,
            name: `User ${res.client_id}`,
            email: '',
            isConnected: true,
            isVerified: true,
          };

          setUserProfile(newProfile);
          return { ...res, userProfile: newProfile };
        } else {
          // If there's already a profile from Settings page, don't overwrite it
          // This prevents race conditions where Settings page set the profile
          // but this hook runs before the query cache is invalidated
          if (currentProfile?.isConnected) {
            console.log('Keeping existing connected profile from Settings');
            return { ...res, userProfile: currentProfile };
          }

          return res;
        }
      } catch (error) {
        console.error('Failed to fetch user credentials:', error);
        // On error, keep existing profile if it exists
        if (currentProfile?.isConnected) {
          return { configured: true, is_verified: true, userProfile: currentProfile };
        }
        throw error;
      }
    },
    refetchInterval: 60000, // 1 minute
    staleTime: 30000,
    // Don't retry on 404 (user not found)
    retry: (failureCount, error: unknown) => {
      if (error && typeof error === 'object' && 'status' in error && error.status === 404) {
        return false;
      }
      return failureCount < 2;
    },
  });
}

// Helper to get user ID from localStorage
const getStoredUserId = () => {
  if (typeof window === 'undefined') return null;
  // First check for stored Dhan client ID (most reliable)
  const dhanClientId = localStorage.getItem('dhan_client_id');
  if (dhanClientId) return dhanClientId;
  // Fallback to generated user ID
  return localStorage.getItem('infinityai_user_id');
};

// Complete User Account Hook - Fetches funds, positions, holdings, orders in one call
export function useUserAccount() {
  const { userProfile, setFunds, setUserProfile, setDematData } = useAppStore();
  const userId = userProfile?.userId || getStoredUserId();

  return useQuery({
    queryKey: ['userAccount', userId],
    queryFn: async () => {
      if (!userId) {
        throw new Error('No user ID available');
      }

      const res = await engineC.getUserAccount(userId);

      if (res.status === 'success') {
        // Update funds in store
        if (res.funds) {
          setFunds({
            availableBalance: res.funds.availabelBalance || res.funds.availableBalance || 0,
            sodLimit: res.funds.sodLimit || 0,
            collateralAmount: res.funds.collateralAmount || res.funds.utilizedAmount || 0,
            dhanClientId: res.funds.dhanClientId || userId,
          });
        }

        // Update user profile if needed
        if (!userProfile?.isConnected) {
          setUserProfile({
            userId: userId,
            clientId: res.user_id || userId,
            name: `User ${res.user_id || userId}`,
            email: '',
            isConnected: true,
            isVerified: true,
          });
        }

        // Update demat data
        setDematData({
          holdings: {
            totalValue: res.holdings?.total_value || 0,
            count: res.holdings?.count || 0,
            items: Array.isArray(res.holdings?.data) ? res.holdings.data : [],
          },
          positions: {
            totalPnl: res.positions?.total_pnl || res.account_summary?.total_positions_pnl || 0,
            count: res.positions?.count || 0,
            items: Array.isArray(res.positions?.data) ? res.positions.data : [],
          },
          funds: {
            availableBalance: res.funds?.availabelBalance || res.funds?.availableBalance || 0,
            utilisedMargin: res.funds?.utilizedAmount || 0,
            totalBalance: (res.funds?.availabelBalance || 0) + (res.funds?.collateralAmount || 0),
          },
        });

        return res;
      }

      throw new Error(res.detail || 'Failed to fetch user account');
    },
    refetchInterval: 15000, // 15 seconds for real-time updates
    staleTime: 10000,
    enabled: !!userId,
    retry: 2,
  });
}

// Funds Hook - Now uses user's connected account
export function useFunds() {
  const { userProfile, setFunds, setUserProfile } = useAppStore();

  return useQuery({
    queryKey: ['funds', userProfile?.userId || getStoredUserId()],
    queryFn: async () => {
      // Determine the user ID to use
      const userId = userProfile?.userId || getStoredUserId();

      // If user has connected their account, fetch their funds directly
      if (userId) {
        try {
          // Use the user-specific funds endpoint
          const res = await engineC.getFunds(userId);
          if (res.status === 'success' && res.data) {
            const fundsData = res.data as {
              dhanClientId?: string;
              availabelBalance?: number;
              availableBalance?: number;
              sodLimit?: number;
              collateralAmount?: number;
              utilizedAmount?: number;
            };

            // Update userProfile if not already set
            if (!userProfile?.isConnected && fundsData.dhanClientId) {
              setUserProfile({
                userId: fundsData.dhanClientId,
                clientId: fundsData.dhanClientId,
                name: `User ${fundsData.dhanClientId}`,
                email: '',
                isConnected: true,
                isVerified: true,
              });
            }

            setFunds({
              availableBalance: fundsData.availabelBalance || fundsData.availableBalance || 0,
              sodLimit: fundsData.sodLimit || 0,
              collateralAmount: fundsData.collateralAmount || fundsData.utilizedAmount || 0,
              dhanClientId: fundsData.dhanClientId || userId,
            });
            return res;
          }
        } catch (e) {
          console.error('Failed to fetch user funds:', e);
        }
      }

      // Fallback to default funds (no user_id)
      const res = await engineC.getFunds();
      if (res.status === 'success' && res.data) {
        setFunds({
          availableBalance: res.data.availabelBalance || 0,
          sodLimit: res.data.sodLimit || 0,
          collateralAmount: res.data.collateralAmount || 0,
          dhanClientId: res.data.dhanClientId || 'default',
        });
      }
      return res;
    },
    refetchInterval: 30000, // 30 seconds for real-time updates
    staleTime: 15000,
    enabled: true,
  });
}

// Positions Hook - Fetches positions using user's credentials if connected
export function usePositions() {
  const { userProfile } = useAppStore();
  const userId = userProfile?.userId || getStoredUserId();

  return useQuery({
    queryKey: ['positions', userId],
    queryFn: async () => {
      // Pass user_id to get user-specific positions
      const res = await engineC.getPositions(userId || undefined);

      // Ensure data is always an array
      if (res && res.data && !Array.isArray(res.data)) {
        return { ...res, data: [] };
      }
      return res;
    },
    refetchInterval: 10000, // 10 seconds for real-time position updates
    staleTime: 5000,
    enabled: !!userId, // Only fetch if we have a user ID
  });
}

// Holdings Hook - Fetches holdings using user's credentials if connected
export function useHoldings() {
  const { userProfile } = useAppStore();
  const userId = userProfile?.userId || getStoredUserId();

  return useQuery({
    queryKey: ['holdings', userId],
    queryFn: async () => {
      // Pass user_id to get user-specific holdings
      const res = await engineC.getHoldings(userId || undefined);

      // Ensure data is always an array
      if (res && res.data && !Array.isArray(res.data)) {
        return { ...res, data: [] };
      }
      return res;
    },
    refetchInterval: 60000,
    staleTime: 30000,
    enabled: !!userId, // Only fetch if we have a user ID
  });
}

// Orders Hook
export function useOrders() {
  const { userProfile } = useAppStore();
  const userId = userProfile?.userId || getStoredUserId();

  return useQuery({
    queryKey: ['orders', userId],
    queryFn: () => engineC.getOrders(userId || undefined),
    refetchInterval: 5000,
    staleTime: 2000,
    enabled: !!userId, // Only fetch if we have a user ID
  });
}

// Signal Hook
export function useSignal(symbol: string, enabled = true) {
  const addSignal = useAppStore((s) => s.addSignal);

  return useQuery({
    queryKey: ['signal', symbol],
    queryFn: async () => {
      const res = await engineB.getSignal({ symbol, use_gemini: true });
      addSignal({
        symbol: res.symbol,
        signal: res.signal,
        confidence: res.confidence,
        timestamp: res.timestamp,
      });
      return res;
    },
    enabled,
    staleTime: 60000,
  });
}

// All Signals Hook (for auto-trading)
export function useSignals() {
  const defaultSymbols = ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK', 'SBIN', 'BHARTIARTL', 'ITC', 'KOTAKBANK', 'LT'];

  return useQuery({
    queryKey: ['signals', 'all'],
    queryFn: () => engineB.getBatchSignals(defaultSymbols),
    staleTime: 30000,
    refetchInterval: 60000, // Refresh every minute
  });
}

// Batch Signals Hook
export function useBatchSignals(symbols: string[]) {
  return useQuery({
    queryKey: ['signals', 'batch', symbols],
    queryFn: () => engineB.getBatchSignals(symbols),
    enabled: symbols.length > 0,
    staleTime: 30000,
  });
}

// Gemini Analysis Hook
export function useGeminiAnalysis(symbol: string, context?: string) {
  return useQuery({
    queryKey: ['gemini', symbol, context],
    queryFn: () => engineB.getGeminiAnalysis({ symbol, context }),
    staleTime: 300000, // 5 minutes
  });
}

// Risk Metrics Hook
export function useRiskMetrics(returns: number[]) {
  const setRiskMetrics = useAppStore((s) => s.setRiskMetrics);

  return useQuery({
    queryKey: ['risk', 'comprehensive', returns.length],
    queryFn: async () => {
      const res = await engineA.getComprehensiveRisk({ returns });
      setRiskMetrics(res);
      return res;
    },
    enabled: returns.length > 0,
    staleTime: 60000,
  });
}

// VaR Hook
export function useVaR(returns: number[], confidence = 0.95, method = 'historical') {
  return useQuery({
    queryKey: ['risk', 'var', returns.length, confidence, method],
    queryFn: () => engineA.calculateVaR({ returns, confidence, method: method as any }),
    enabled: returns.length > 0,
    staleTime: 60000,
  });
}

// Kelly Criterion Hook
export function useKellyCriterion(winRate: number, avgWin: number, avgLoss: number) {
  return useQuery({
    queryKey: ['risk', 'kelly', winRate, avgWin, avgLoss],
    queryFn: () => engineA.calculateKelly({ win_rate: winRate, avg_win: avgWin, avg_loss: avgLoss }),
    enabled: winRate > 0 && avgWin > 0 && avgLoss !== 0,
    staleTime: 60000,
  });
}

// Position Size Hook
export function usePositionSize(capital: number, riskPerTrade = 0.02, stopLossPct = 0.05) {
  return useQuery({
    queryKey: ['risk', 'position-size', capital, riskPerTrade, stopLossPct],
    queryFn: () =>
      engineA.calculatePositionSize({
        capital,
        risk_per_trade: riskPerTrade,
        stop_loss_pct: stopLossPct,
      }),
    enabled: capital > 0,
    staleTime: 60000,
  });
}

// Execution Analytics Hook
export function useExecutionAnalytics() {
  return useQuery({
    queryKey: ['execution', 'analytics'],
    queryFn: () => engineC.getExecutionAnalytics(),
    staleTime: 30000,
  });
}

// Model Status Hook
export function useModelStatus() {
  return useQuery({
    queryKey: ['models', 'status'],
    queryFn: () => engineB.getModelStatus(),
    staleTime: 60000,
  });
}

// Mutations
export function usePlaceOrder() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: engineC.placeOrder,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orders'] });
      queryClient.invalidateQueries({ queryKey: ['positions'] });
      queryClient.invalidateQueries({ queryKey: ['funds'] });
    },
  });
}

export function useCancelOrder() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: engineC.cancelOrder,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orders'] });
    },
  });
}

export function useStartTrade() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: engineA.startTrade,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orders'] });
      queryClient.invalidateQueries({ queryKey: ['positions'] });
    },
  });
}

// Instrument-specific auto trading hook
export function useStartInstrumentTrade() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: engineA.startInstrumentTrade,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orders'] });
      queryClient.invalidateQueries({ queryKey: ['positions'] });
      queryClient.invalidateQueries({ queryKey: ['signals'] });
    },
  });
}

// Start auto-trading with full configuration
export function useStartAutoTrading() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: engineA.startAutoTrading,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orders'] });
      queryClient.invalidateQueries({ queryKey: ['positions'] });
      queryClient.invalidateQueries({ queryKey: ['signals'] });
      queryClient.invalidateQueries({ queryKey: ['auto-trade-status'] });
    },
  });
}

// Stop auto-trading
export function useStopAutoTrading() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: engineA.stopAutoTrading,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['auto-trade-status'] });
    },
  });
}

// Get auto-trading status
export function useAutoTradingStatus() {
  return useQuery({
    queryKey: ['auto-trade-status'],
    queryFn: engineA.getAutoTradingStatus,
    refetchInterval: 10000, // Refresh every 10 seconds
  });
}

export function useCalculateRiskScore() {
  return useMutation({
    mutationFn: engineA.calculateRiskScore,
  });
}

// Portfolio Analysis Hook - Analyze user's holdings with AI
export function usePortfolioAnalysis(holdings: any[], enabled = true) {
  return useQuery({
    queryKey: ['portfolio', 'analysis', holdings.map((h: any) => h.tradingSymbol || h.securityId).join(',')],
    queryFn: () => engineB.analyzePortfolio(holdings),
    enabled: enabled && holdings.length > 0,
    staleTime: 300000, // 5 minutes
  });
}

// Holding-specific AI recommendation
export function useHoldingRecommendation(symbol: string, holding: any, enabled = true) {
  return useQuery({
    queryKey: ['holding', 'recommendation', symbol],
    queryFn: () => engineB.getHoldingRecommendation(symbol, holding),
    enabled: enabled && !!symbol,
    staleTime: 300000,
  });
}

// User's portfolio signals - get signals for all holdings
export function usePortfolioSignals() {
  const { data: holdingsData } = useHoldings();
  const holdings = Array.isArray(holdingsData?.data) ? holdingsData.data : [];
  const symbols = holdings.map((h: any) => h.tradingSymbol || h.securityId).filter(Boolean);

  return useQuery({
    queryKey: ['portfolio', 'signals', symbols.join(',')],
    queryFn: () => engineB.getBatchSignals(symbols),
    enabled: symbols.length > 0,
    staleTime: 60000,
    refetchInterval: 120000, // Refresh every 2 minutes
  });
}

// Portfolio Optimization Hook
export function usePortfolioOptimization(holdings: any[], riskTolerance: 'low' | 'medium' | 'high' = 'medium') {
  return useQuery({
    queryKey: ['portfolio', 'optimize', riskTolerance, holdings.length],
    queryFn: () => engineB.optimizePortfolio(holdings, riskTolerance),
    enabled: holdings.length > 0,
    staleTime: 300000, // 5 minutes
  });
}

// Market Prediction Hook
export function useMarketPrediction(timeframe: 'day' | 'week' | 'month' = 'day') {
  return useQuery({
    queryKey: ['market', 'prediction', timeframe],
    queryFn: () => engineB.getMarketPrediction(timeframe),
    staleTime: 300000,
    refetchInterval: 600000, // 10 minutes
  });
}

// Sector Analysis Hook
export function useSectorAnalysis() {
  return useQuery({
    queryKey: ['sector', 'analysis'],
    queryFn: () => engineB.getSectorAnalysis(),
    staleTime: 300000,
  });
}

// Stock Screener Hook
export function useStockScreener(criteria: {
  minMarketCap?: number;
  sector?: string;
  signalType?: 'BUY' | 'SELL' | 'HOLD';
  minConfidence?: number;
}) {
  return useQuery({
    queryKey: ['screener', JSON.stringify(criteria)],
    queryFn: () => engineB.screenStocks(criteria),
    staleTime: 120000,
  });
}

// Technical Indicators Hook
export function useTechnicalIndicators(symbol: string, enabled = true) {
  return useQuery({
    queryKey: ['technical', symbol],
    queryFn: () => engineB.getTechnicalIndicators(symbol),
    enabled: enabled && !!symbol,
    staleTime: 60000,
  });
}

// Sentiment Analysis Hook
export function useSentimentAnalysis(symbol: string, enabled = true) {
  return useQuery({
    queryKey: ['sentiment', symbol],
    queryFn: () => engineB.getSentimentAnalysis(symbol),
    enabled: enabled && !!symbol,
    staleTime: 300000,
  });
}

// Correlation Analysis Hook
export function useCorrelationAnalysis(symbols: string[]) {
  return useQuery({
    queryKey: ['correlation', symbols.join(',')],
    queryFn: () => engineB.getCorrelationAnalysis(symbols),
    enabled: symbols.length >= 2,
    staleTime: 300000,
  });
}

// Trade Ideas Hook
export function useTradeIdeas(budget?: number, riskLevel?: 'conservative' | 'moderate' | 'aggressive') {
  return useQuery({
    queryKey: ['trade-ideas', budget, riskLevel],
    queryFn: () => engineB.getTradeIdeas(budget, riskLevel),
    staleTime: 300000,
    refetchInterval: 600000,
  });
}

// =====================================================
// Position Analysis Hooks - AI/ML Analysis of Positions
// =====================================================

import type { PositionAnalysisRequest, PositionAnalysisResponse } from '@/lib/api';

// Single Position Analysis Hook
export function usePositionAnalysis(position: PositionAnalysisRequest | null, enabled = true) {
  return useQuery<PositionAnalysisResponse | null>({
    queryKey: ['position', 'analysis', position?.symbol],
    queryFn: () => (position ? engineB.analyzePosition(position) : Promise.resolve(null)),
    enabled: enabled && !!position,
    staleTime: 60000, // 1 minute
    refetchInterval: 120000, // Refresh every 2 minutes
  });
}

// All Positions Analysis Hook - Analyzes all current positions
export function useAllPositionsAnalysis(enabled = true) {
  const { data: positionsData, isLoading: positionsLoading } = usePositions();

  // Extract positions array from response
  const positions = Array.isArray(positionsData?.data) ? positionsData.data : [];

  // Transform Dhan positions to PositionAnalysisRequest format
  // Note: Dhan API uses camelCase with 'drv' prefix for derivative fields
  const positionDataList: PositionAnalysisRequest[] = positions.map((p: any) => ({
    symbol: p.tradingSymbol?.split('-')[0] || p.securityId,
    trading_symbol: p.tradingSymbol || '',
    security_id: p.securityId || '',
    position_type: (p.netQty || 0) > 0 ? 'LONG' : 'SHORT',
    exchange_segment: p.exchangeSegment || 'NSE_EQ',
    product_type: p.productType || 'CNC',
    buy_avg: p.buyAvg || 0,
    cost_price: p.costPrice || p.buyAvg || 0,
    buy_qty: p.buyQty || 0,
    sell_qty: p.sellQty || 0,
    net_qty: p.netQty || p.buyQty - (p.sellQty || 0),
    realized_profit: p.realizedProfit || 0,
    unrealized_profit: p.unrealizedProfit || 0,
    // Dhan uses drvExpiryDate, drvOptionType, drvStrikePrice for derivatives
    expiry_date: p.drvExpiryDate || p.expiryDate,
    option_type: p.drvOptionType === 'PUT' ? 'PUT' : p.drvOptionType === 'CALL' ? 'CALL' : p.optionType,
    strike_price: p.drvStrikePrice || p.strikePrice,
    current_price: p.dayClosePrice || p.lastTradedPrice,
  }));

  return useQuery<PositionAnalysisResponse[]>({
    queryKey: ['positions', 'analysis', 'all', positionDataList.map((p) => p.symbol).join(',')],
    queryFn: async () => {
      const response = await engineB.analyzePortfolioPositions(positionDataList);
      // Ensure we always return an array (API might wrap in {data: [...]})
      if (Array.isArray(response)) return response;
      if (response?.data && Array.isArray(response.data)) return response.data;
      if (response?.results && Array.isArray(response.results)) return response.results;
      return [];
    },
    enabled: enabled && !positionsLoading && positionDataList.length > 0,
    staleTime: 60000,
    refetchInterval: 120000,
  });
}

// Position Risk Summary Hook - Aggregates risk across all positions
export function usePositionRiskSummary() {
  const { data: analysisData, isLoading, error } = useAllPositionsAnalysis();

  // Ensure analysisData is always an array for safe operations
  const safeAnalysisData = Array.isArray(analysisData) ? analysisData : [];
  
  const summary = safeAnalysisData.length > 0 ? {
    totalPositions: safeAnalysisData.length,
    totalUnrealizedPnL: safeAnalysisData.reduce((sum, a) => sum + (a.risk_metrics?.unrealized_pnl || 0), 0),
    averageRiskScore: safeAnalysisData.reduce((sum, a) => sum + (a.ai_recommendation?.score || 50), 0) / safeAnalysisData.length,
    highRiskCount: safeAnalysisData.filter((a) => (a.ai_recommendation?.score || 50) > 70).length,
    buyRecommendations: safeAnalysisData.filter((a) => a.ai_recommendation?.action === 'HOLD').length,
    sellRecommendations: safeAnalysisData.filter((a) => a.ai_recommendation?.action === 'EXIT_CONSIDERATION').length,
    holdRecommendations: safeAnalysisData.filter((a) => a.ai_recommendation?.action === 'MONITOR').length,
    totalMaxLoss: safeAnalysisData.reduce((sum, a) => {
      const maxLoss = a.risk_metrics?.max_loss;
      return sum + (typeof maxLoss === 'number' ? maxLoss : 0);
    }, 0),
    positionsByConfidence: {
      high: safeAnalysisData.filter((a) => a.ai_recommendation?.confidence === 'HIGH').length,
      medium: safeAnalysisData.filter((a) => a.ai_recommendation?.confidence === 'MEDIUM').length,
      low: safeAnalysisData.filter((a) => a.ai_recommendation?.confidence === 'LOW').length,
    },
  } : null;

  return { summary, analysisData: safeAnalysisData, isLoading, error };
}

// ==========================================
// Background Trading Hooks
// ==========================================

// Background Trading Status Interface
interface BackgroundTradingStatus {
  user_id: string;
  is_active: boolean;
  strategy: string;
  started_at?: string;
  config?: Record<string, unknown>;
  last_execution?: {
    timestamp: string;
    trades_executed: number;
    status: string;
  };
  execution_history?: Array<{
    timestamp: string;
    action: string;
    result: string;
  }>;
}

// Get Background Trading Status
export function useBackgroundTradingStatus(userId: string | undefined) {
  return useQuery<BackgroundTradingStatus>({
    queryKey: ['background-trading', 'status', userId],
    queryFn: () => engineC.getBackgroundTradingStatus(userId!),
    enabled: !!userId,
    refetchInterval: 30000, // Refresh every 30 seconds
    staleTime: 10000,
    retry: 2,
  });
}

// Start Background Trading Mutation
export function useStartBackgroundTrading() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      userId,
      strategy = 'auto_options',
      config = {},
    }: {
      userId: string;
      strategy?: string;
      config?: Record<string, unknown>;
    }) => engineC.startBackgroundTrading({
      user_id: userId,
      strategy,
      ...config,
    }),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['background-trading', 'status', variables.userId],
      });
      // Log activity
      engineC.logActivity({
        user_id: variables.userId,
        type: 'BACKGROUND_TRADING_STARTED',
        details: { strategy: variables.strategy },
      });
    },
  });
}

// Stop Background Trading Mutation
export function useStopBackgroundTrading() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (userId: string) => engineC.stopBackgroundTrading(userId),
    onSuccess: (_data, userId) => {
      queryClient.invalidateQueries({
        queryKey: ['background-trading', 'status', userId],
      });
      // Log activity
      engineC.logActivity({
        user_id: userId,
        type: 'BACKGROUND_TRADING_STOPPED',
        details: {},
      });
    },
  });
}

// ==========================================
// Activity Tracking Hooks
// ==========================================

// Activity Log Interface
interface ActivityLog {
  id: string;
  user_id: string;
  action: string;
  details: Record<string, unknown>;
  timestamp: string;
  ip_address?: string;
  user_agent?: string;
}

interface ActivityLogsResponse {
  user_id: string;
  logs: ActivityLog[];
  total_count: number;
  period: {
    start: string;
    end: string;
  };
}

interface ActivitySummary {
  user_id: string;
  total_actions: number;
  actions_by_type: Record<string, number>;
  first_activity: string;
  last_activity: string;
  most_common_action: string;
  active_hours: number[];
  peak_activity_hour: number;
  daily_average: number;
}

// Get Activity Logs
export function useActivityLogs(
  userId: string | undefined,
  options?: {
    limit?: number;
    date?: string;
    activityType?: string;
  }
) {
  return useQuery<ActivityLogsResponse>({
    queryKey: ['activity', 'logs', userId, options],
    queryFn: () =>
      engineC.getActivityLog(userId!, {
        limit: options?.limit,
        date: options?.date,
        activity_type: options?.activityType,
      }),
    enabled: !!userId,
    staleTime: 30000,
    refetchInterval: 60000, // Refresh every minute
  });
}

// Get Activity Summary
export function useActivitySummary(userId: string | undefined, days = 7) {
  return useQuery<ActivitySummary>({
    queryKey: ['activity', 'summary', userId, days],
    queryFn: async () => {
      // Fetch logs for the period and compute summary
      const response = await engineC.getActivityLog(userId!, { limit: 1000 });
      const logs = response.logs || response.activities || [];

      const actionCounts: Record<string, number> = {};
      const hourCounts: Record<number, number> = {};

      logs.forEach((log: ActivityLog) => {
        // Count by action type
        actionCounts[log.action] = (actionCounts[log.action] || 0) + 1;

        // Count by hour
        const hour = new Date(log.timestamp).getHours();
        hourCounts[hour] = (hourCounts[hour] || 0) + 1;
      });

      const mostCommonAction = Object.entries(actionCounts).sort(
        (a, b) => b[1] - a[1]
      )[0]?.[0] || 'NONE';

      const peakActivityHour = Object.entries(hourCounts).sort(
        (a, b) => b[1] - a[1]
      )[0]?.[0] || 0;

      return {
        user_id: userId!,
        total_actions: logs.length,
        actions_by_type: actionCounts,
        first_activity: logs[logs.length - 1]?.timestamp || '',
        last_activity: logs[0]?.timestamp || '',
        most_common_action: mostCommonAction,
        active_hours: Object.keys(hourCounts).map(Number),
        peak_activity_hour: Number(peakActivityHour),
        daily_average: Math.round(logs.length / days),
      };
    },
    enabled: !!userId,
    staleTime: 300000, // Cache for 5 minutes
  });
}

// Log Activity Mutation
export function useLogActivity() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      userId,
      action,
      details = {},
    }: {
      userId: string;
      action: string;
      details?: Record<string, unknown>;
    }) => engineC.logActivity({
      user_id: userId,
      type: action,
      details,
    }),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['activity', 'logs', variables.userId],
      });
    },
  });
}

// Hook to automatically log page visits
export function usePageActivityLogger(userId: string | undefined, pageName: string) {
  const logActivity = useLogActivity();

  useEffect(() => {
    if (userId) {
      logActivity.mutate({
        userId,
        action: 'PAGE_VISIT',
        details: {
          page: pageName,
          timestamp: new Date().toISOString(),
          url: typeof window !== 'undefined' ? window.location.href : '',
        },
      });
    }
  }, [userId, pageName]); // Only log once when page loads
}

// Hook to log trading actions
export function useTradingActivityLogger(userId: string | undefined) {
  const logActivity = useLogActivity();

  const logTrade = useCallback(
    (action: string, details: Record<string, unknown>) => {
      if (userId) {
        logActivity.mutate({
          userId,
          action: `TRADE_${action.toUpperCase()}`,
          details: {
            ...details,
            timestamp: new Date().toISOString(),
          },
        });
      }
    },
    [userId, logActivity]
  );

  return { logTrade };
}
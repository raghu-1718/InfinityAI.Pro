'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api, engineA, engineB, engineC } from '@/lib/api';
import { useAppStore } from '@/lib/store';
import { useEffect } from 'react';

// Engine Health Hooks
export function useEngineHealth() {
  const updateEngineStatus = useAppStore((s) => s.updateEngineStatus);

  const query = useQuery({
    queryKey: ['engines', 'health'],
    queryFn: () => api.checkAllEngines(),
    refetchInterval: 30000, // 30 seconds
    staleTime: 10000,
  });

  useEffect(() => {
    if (query.data) {
      const { engineA, engineB, engineC } = query.data;

      updateEngineStatus('engineA', {
        status: engineA ? 'online' : 'offline',
        version: engineA?.version || null,
        capabilities: engineA?.ml_capabilities,
      });

      updateEngineStatus('engineB', {
        status: engineB ? 'online' : 'offline',
        version: engineB?.version || null,
        capabilities: Object.keys(engineB?.capabilities || {}),
      });

      updateEngineStatus('engineC', {
        status: engineC ? 'online' : 'offline',
        version: engineC?.version || null,
        capabilities: engineC?.ml_capabilities,
      });
    }
  }, [query.data, updateEngineStatus]);

  return query;
}

// Funds Hook
export function useFunds() {
  const setFunds = useAppStore((s) => s.setFunds);

  return useQuery({
    queryKey: ['funds'],
    queryFn: async () => {
      const res = await engineC.getFunds();
      if (res.status === 'success' && res.data) {
        setFunds({
          availableBalance: res.data.availabelBalance,
          sodLimit: res.data.sodLimit,
          collateralAmount: res.data.collateralAmount,
          dhanClientId: res.data.dhanClientId,
        });
      }
      return res;
    },
    refetchInterval: 60000, // 1 minute
    staleTime: 30000,
  });
}

// Positions Hook
export function usePositions() {
  return useQuery({
    queryKey: ['positions'],
    queryFn: () => engineC.getPositions(),
    refetchInterval: 10000,
    staleTime: 5000,
  });
}

// Holdings Hook
export function useHoldings() {
  return useQuery({
    queryKey: ['holdings'],
    queryFn: () => engineC.getHoldings(),
    refetchInterval: 60000,
    staleTime: 30000,
  });
}

// Orders Hook
export function useOrders() {
  return useQuery({
    queryKey: ['orders'],
    queryFn: () => engineC.getOrders(),
    refetchInterval: 5000,
    staleTime: 2000,
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
  const positionDataList: PositionAnalysisRequest[] = positions.map((p: any) => ({
    symbol: p.tradingSymbol || p.securityId,
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
    expiry_date: p.expiryDate,
    option_type: p.optionType,
    strike_price: p.strikePrice,
    current_price: p.dayClosePrice || p.lastTradedPrice,
  }));

  return useQuery<PositionAnalysisResponse[]>({
    queryKey: ['positions', 'analysis', 'all', positionDataList.map((p) => p.symbol).join(',')],
    queryFn: () => engineB.analyzePortfolioPositions(positionDataList),
    enabled: enabled && !positionsLoading && positionDataList.length > 0,
    staleTime: 60000,
    refetchInterval: 120000,
  });
}

// Position Risk Summary Hook - Aggregates risk across all positions
export function usePositionRiskSummary() {
  const { data: analysisData, isLoading, error } = useAllPositionsAnalysis();

  const summary = analysisData ? {
    totalPositions: analysisData.length,
    totalUnrealizedPnL: analysisData.reduce((sum, a) => sum + (a.risk_metrics?.unrealized_pnl || 0), 0),
    averageRiskScore: analysisData.reduce((sum, a) => sum + (a.ai_recommendation?.score || 50), 0) / analysisData.length,
    highRiskCount: analysisData.filter((a) => (a.ai_recommendation?.score || 50) > 70).length,
    buyRecommendations: analysisData.filter((a) => a.ai_recommendation?.action === 'HOLD').length,
    sellRecommendations: analysisData.filter((a) => a.ai_recommendation?.action === 'EXIT_CONSIDERATION').length,
    holdRecommendations: analysisData.filter((a) => a.ai_recommendation?.action === 'MONITOR').length,
    totalMaxLoss: analysisData.reduce((sum, a) => {
      const maxLoss = a.risk_metrics?.max_loss;
      return sum + (typeof maxLoss === 'number' ? maxLoss : 0);
    }, 0),
    positionsByConfidence: {
      high: analysisData.filter((a) => a.ai_recommendation?.confidence === 'HIGH').length,
      medium: analysisData.filter((a) => a.ai_recommendation?.confidence === 'MEDIUM').length,
      low: analysisData.filter((a) => a.ai_recommendation?.confidence === 'LOW').length,
    },
  } : null;

  return { summary, analysisData, isLoading, error };
}
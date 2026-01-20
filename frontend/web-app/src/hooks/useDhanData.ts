/**
 * Dhan Market Data Hooks (Phase 3)
 * 
 * React Query hooks for consuming Dhan Data API endpoints
 */

import { useQuery } from '@tanstack/react-query';
import { engineC } from '@/lib/api';
import { getUserId } from '@/lib/user';

// Type definitions
export interface MarketQuote {
  symbol: string;
  ltp: number;
  open: number;
  high: number;
  low: number;
  volume: number;
  change: number;
  changePercent: number;
}

export interface HistoricalCandle {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface MarketDepthLevel {
  price: number;
  quantity: number;
  orders: number;
}

export interface OptionData {
  strikePrice: number;
  callOI: number;
  putOI: number;
  callLTP: number;
  putLTP: number;
  callVolume: number;
  putVolume: number;
}

/**
 * Hook to fetch real-time market quotes
 */
export function useMarketQuotes(symbols: string[], enabled: boolean = true) {
  const userId = getUserId();
  
  return useQuery({
    queryKey: ['market', 'quotes', symbols.join(','), userId],
    queryFn: async () => {
      if (!userId) throw new Error('User ID not available');
      const response = await engineC.getMarketQuotes(
        userId,
        symbols,
        'NSE_EQ'
      );
      return response;
    },
    enabled: enabled && symbols.length > 0 && !!userId,
    refetchInterval: 5000, // Refresh every 5 seconds for real-time data
    staleTime: 3000,
  });
}

/**
 * Hook to fetch historical data for charting
 */
export function useHistoricalData(
  symbol: string,
  fromDate: string,
  toDate: string,
  interval: string = '1D',
  enabled: boolean = true
) {
  return useQuery({
    queryKey: ['market', 'historical', symbol, fromDate, toDate, interval],
    queryFn: async () => {
      const response = await engineC.getHistoricalData(symbol, fromDate, toDate, interval);
      return response;
    },
    enabled: enabled && !!symbol,
    staleTime: 60000, // 1 minute - historical data doesn't change frequently
  });
}

/**
 * Hook to fetch market depth (order book)
 */
export function useMarketDepth(symbol: string, levels: number = 20, enabled: boolean = true) {
  return useQuery({
    queryKey: ['market', 'depth', symbol, levels],
    queryFn: async () => {
      const response = await engineC.getMarketDepth(symbol, levels);
      return response;
    },
    enabled: enabled && !!symbol,
    refetchInterval: 2000, // Refresh every 2 seconds
    staleTime: 1000,
  });
}

/**
 * Hook to fetch option chain data
 */
export function useOptionChain(symbol: string, expiry: string, enabled: boolean = true) {
  return useQuery({
    queryKey: ['market', 'options', 'chain', symbol, expiry],
    queryFn: async () => {
      const response = await engineC.getOptionChain(symbol, expiry);
      return response;
    },
    enabled: enabled && !!symbol && !!expiry,
    refetchInterval: 10000, // Refresh every 10 seconds
    staleTime: 5000,
  });
}

/**
 * Hook to fetch expired options data
 */
export function useExpiredOptions(symbol: string, date: string, enabled: boolean = true) {
  return useQuery({
    queryKey: ['market', 'options', 'expired', symbol, date],
    queryFn: async () => {
      const response = await engineC.getExpiredOptions(symbol, date);
      return response;
    },
    enabled: enabled && !!symbol && !!date,
    staleTime: 300000, // 5 minutes - expired data is static
  });
}

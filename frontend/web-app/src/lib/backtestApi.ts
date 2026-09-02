/**
 * InfinityAI.Pro - Backtest & Market Data Service API Client
 * Provides market quotes, price history, signals, and backtesting endpoints.
 */

import { API_CONFIG } from './api';

export interface LivePrice {
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
  change_percent?: number;
  open?: number;
  high: number;
  low: number;
  volume: number;
  timestamp: string;
}

export interface LivePricesResponse {
  status: string;
  prices: Record<string, LivePrice>;
  timestamp: string;
}

export interface PriceTick {
  timestamp: string;
  price?: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface PriceHistoryResponse {
  status: string;
  symbol: string;
  timeframe: string;
  ticks: PriceTick[];
  data?: PriceTick[];
  error?: string;
}

export interface TradingSignal {
  id: string;
  symbol: string;
  signal: 'BUY' | 'SELL' | 'HOLD';
  signal_type?: 'BUY' | 'SELL' | 'HOLD';
  confidence: number;
  entryPrice?: number;
  targetPrice?: number;
  stopLoss?: number;
  price?: number;
  strategy?: string;
  indicators?: Record<string, any>;
  reasoning: string;
  timestamp: string;
}

export interface SignalsResponse {
  status: string;
  signals: TradingSignal[];
  error?: string;
}

export interface BacktestRequest {
  symbol: string;
  strategy: string;
  initialCapital: number;
  fromDate: string;
  toDate: string;
}

export interface BacktestResponse {
  status: string;
  metrics: {
    totalTrades: number;
    winRate: number;
    totalReturnPercent: number;
    sharpeRatio: number;
    maxDrawdownPercent: number;
    profitFactor: number;
  };
  trades: Array<{
    date: string;
    type: 'BUY' | 'SELL';
    price: number;
    pnl: number;
  }>;
}

/**
 * Fetch live market prices for key symbols
 */
export async function getLivePrices(): Promise<LivePricesResponse> {
  try {
    const res = await fetch(`${API_CONFIG.ENGINE_C}/api/dhan/market/quotes`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return await res.json();
  } catch (error) {
    console.warn("Live market prices unavailable from broker gateway:", error);
    return {
      status: 'error',
      prices: {},
      timestamp: new Date().toISOString(),
    };
  }
}

/**
 * Fetch price history (OHLC ticks) for charting
 */
export async function getPriceHistory(
  symbol: string,
  timeframe: string = '1D'
): Promise<PriceHistoryResponse> {
  try {
    const res = await fetch(
      `${API_CONFIG.ENGINE_C}/api/dhan/market/historical?symbol=${encodeURIComponent(symbol)}&interval=${timeframe}`
    );
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    const json = await res.json();
    return {
      ...json,
      data: json.ticks || json.data || [],
    };
  } catch (error) {
    console.warn(`Price history unavailable for ${symbol}:`, error);
    return {
      status: 'error',
      symbol,
      timeframe,
      ticks: [],
      data: [],
    };
  }
}

/**
 * Fetch latest AI/ML generated trading signals
 */
export async function getLatestSignals(limit: number = 10): Promise<SignalsResponse> {
  try {
    const res = await fetch(`${API_CONFIG.ENGINE_B}/api/v1/signals?limit=${limit}`);
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return await res.json();
  } catch (error) {
    console.warn("Real-time signals unavailable from Engine B:", error);
    return {
      status: 'error',
      signals: [],
    };
  }
}

/**
 * Run strategy backtest
 */
export async function runBacktest(req: BacktestRequest): Promise<BacktestResponse> {
  const res = await fetch(`${API_CONFIG.ENGINE_A}/api/v1/backtest`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });
  if (!res.ok) throw new Error(`HTTP error ${res.status}`);
  return await res.json();
}

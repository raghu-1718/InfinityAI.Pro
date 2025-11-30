// API Client for InfinityAI.Pro 3-Engine Architecture

const API_CONFIG = {
  ENGINE_A: process.env.NEXT_PUBLIC_ENGINE_A_URL || 'https://engine-a.infinityai.pro',
  ENGINE_B: process.env.NEXT_PUBLIC_ENGINE_B_URL || 'https://engine-b.infinityai.pro',
  ENGINE_C: process.env.NEXT_PUBLIC_ENGINE_C_URL || 'https://engine-c.infinityai.pro',
};

// Fallback to Cloud Run URLs if custom domains aren't ready
const FALLBACK_URLS = {
  ENGINE_A: 'https://engine-a-573866363639.us-central1.run.app',
  ENGINE_B: 'https://engine-b-573866363639.us-central1.run.app',
  ENGINE_C: 'https://engine-c-573866363639.us-central1.run.app',
};

async function fetchWithFallback(primaryUrl: string, fallbackUrl: string, options?: RequestInit) {
  try {
    const response = await fetch(primaryUrl, { ...options, signal: AbortSignal.timeout(5000) });
    if (response.ok) return response;
    throw new Error(`HTTP ${response.status}`);
  } catch {
    // Try fallback URL
    return fetch(fallbackUrl, options);
  }
}

// Types
export interface EngineHealth {
  status: string;
  service: string;
  version: string;
  ml_capabilities?: string[];
  capabilities?: Record<string, boolean>;
  dhan_connected?: boolean;
  timestamp: string;
}

export interface RiskScoreRequest {
  position_size: number;
  volatility?: number;
  max_drawdown?: number;
}

export interface RiskScoreResponse {
  risk_score: number;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
  components: {
    position_size_risk: number;
    volatility_risk: number;
    drawdown_risk: number;
  };
  recommendation: string;
}

export interface VaRRequest {
  returns: number[];
  confidence?: number;
  method?: 'historical' | 'parametric' | 'cornish-fisher';
}

export interface CVaRRequest {
  returns: number[];
  confidence?: number;
}

export interface KellyRequest {
  win_rate: number;
  avg_win: number;
  avg_loss: number;
}

export interface PositionSizeRequest {
  capital: number;
  risk_per_trade?: number;
  stop_loss_pct?: number;
}

export interface SignalRequest {
  symbol: string;
  use_gemini?: boolean;
}

export interface SignalResponse {
  signal: 'BUY' | 'SELL' | 'HOLD';
  confidence: number;
  symbol: string;
  analysis: {
    technical_score: number;
    sentiment_score: number;
    ml_prediction: number;
  };
  timestamp: string;
}

export interface OrderRequest {
  transaction_type: 'BUY' | 'SELL';
  exchange_segment: string;
  product_type: string;
  order_type: string;
  validity: string;
  security_id: string;
  quantity: number;
  price?: number;
}

export interface FundsResponse {
  status: string;
  data: {
    dhanClientId: string;
    availabelBalance: number;
    sodLimit: number;
    collateralAmount: number;
  };
}

// Engine A - Orchestration & Risk Management
export const engineA = {
  async health(): Promise<EngineHealth> {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_A}/health`,
      `${FALLBACK_URLS.ENGINE_A}/health`
    );
    return res.json();
  },

  async calculateRiskScore(data: RiskScoreRequest): Promise<RiskScoreResponse> {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_A}/api/v1/risk/score`,
      `${FALLBACK_URLS.ENGINE_A}/api/v1/risk/score`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      }
    );
    return res.json();
  },

  async calculateVaR(data: VaRRequest) {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_A}/api/v1/risk/var`,
      `${FALLBACK_URLS.ENGINE_A}/api/v1/risk/var`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      }
    );
    return res.json();
  },

  async calculateCVaR(data: CVaRRequest) {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_A}/api/v1/risk/cvar`,
      `${FALLBACK_URLS.ENGINE_A}/api/v1/risk/cvar`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      }
    );
    return res.json();
  },

  async calculateSortino(data: { returns: number[]; risk_free_rate?: number }) {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_A}/api/v1/risk/sortino`,
      `${FALLBACK_URLS.ENGINE_A}/api/v1/risk/sortino`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      }
    );
    return res.json();
  },

  async calculateKelly(data: KellyRequest) {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_A}/api/v1/risk/kelly`,
      `${FALLBACK_URLS.ENGINE_A}/api/v1/risk/kelly`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      }
    );
    return res.json();
  },

  async calculatePositionSize(data: PositionSizeRequest) {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_A}/api/v1/risk/position-size`,
      `${FALLBACK_URLS.ENGINE_A}/api/v1/risk/position-size`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      }
    );
    return res.json();
  },

  async getComprehensiveRisk(data: { returns: number[]; risk_free_rate?: number }) {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_A}/api/v1/risk/comprehensive`,
      `${FALLBACK_URLS.ENGINE_A}/api/v1/risk/comprehensive`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      }
    );
    return res.json();
  },

  async startTrade(data: { symbol: string; qty?: number; strategy?: string }) {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_A}/api/v1/trade/start`,
      `${FALLBACK_URLS.ENGINE_A}/api/v1/trade/start`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      }
    );
    return res.json();
  },
};

// Engine B - AI/ML Intelligence
export const engineB = {
  async health(): Promise<EngineHealth> {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_B}/health`,
      `${FALLBACK_URLS.ENGINE_B}/health`
    );
    return res.json();
  },

  async getSignal(data: SignalRequest): Promise<SignalResponse> {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_B}/api/v1/signal`,
      `${FALLBACK_URLS.ENGINE_B}/api/v1/signal`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      }
    );
    return res.json();
  },

  async getGeminiAnalysis(data: { symbol: string; context?: string }) {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_B}/api/v1/gemini/analyze`,
      `${FALLBACK_URLS.ENGINE_B}/api/v1/gemini/analyze`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      }
    );
    return res.json();
  },

  async getBatchSignals(symbols: string[]) {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_B}/api/v1/signals/batch`,
      `${FALLBACK_URLS.ENGINE_B}/api/v1/signals/batch`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbols }),
      }
    );
    return res.json();
  },

  async getModelStatus() {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_B}/api/v1/models/status`,
      `${FALLBACK_URLS.ENGINE_B}/api/v1/models/status`
    );
    return res.json();
  },

  // Analyze portfolio holdings using AI/ML
  async analyzePortfolio(holdings: any[]) {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_B}/api/v1/portfolio/analyze`,
      `${FALLBACK_URLS.ENGINE_B}/api/v1/portfolio/analyze`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ holdings }),
      }
    );
    return res.json();
  },

  // Get AI recommendations for a specific holding
  async getHoldingRecommendation(symbol: string, holding: any) {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_B}/api/v1/holding/recommendation`,
      `${FALLBACK_URLS.ENGINE_B}/api/v1/holding/recommendation`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbol, holding }),
      }
    );
    return res.json();
  },

  // Portfolio Optimization - Get optimal allocation
  async optimizePortfolio(holdings: any[], riskTolerance: 'low' | 'medium' | 'high' = 'medium') {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_B}/api/v1/portfolio/optimize`,
      `${FALLBACK_URLS.ENGINE_B}/api/v1/portfolio/optimize`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ holdings, risk_tolerance: riskTolerance }),
      }
    );
    return res.json();
  },

  // Market Prediction - Next day/week predictions
  async getMarketPrediction(timeframe: 'day' | 'week' | 'month' = 'day') {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_B}/api/v1/market/prediction`,
      `${FALLBACK_URLS.ENGINE_B}/api/v1/market/prediction`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ timeframe }),
      }
    );
    return res.json();
  },

  // Sector Analysis - AI analysis of sectors
  async getSectorAnalysis() {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_B}/api/v1/sector/analysis`,
      `${FALLBACK_URLS.ENGINE_B}/api/v1/sector/analysis`
    );
    return res.json();
  },

  // Stock Screener - AI-powered screening
  async screenStocks(criteria: {
    minMarketCap?: number;
    sector?: string;
    signalType?: 'BUY' | 'SELL' | 'HOLD';
    minConfidence?: number;
  }) {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_B}/api/v1/screener`,
      `${FALLBACK_URLS.ENGINE_B}/api/v1/screener`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(criteria),
      }
    );
    return res.json();
  },

  // Technical Indicators - Get indicators for a symbol
  async getTechnicalIndicators(symbol: string) {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_B}/api/v1/technical/${symbol}`,
      `${FALLBACK_URLS.ENGINE_B}/api/v1/technical/${symbol}`
    );
    return res.json();
  },

  // Sentiment Analysis - News and social media sentiment
  async getSentimentAnalysis(symbol: string) {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_B}/api/v1/sentiment/${symbol}`,
      `${FALLBACK_URLS.ENGINE_B}/api/v1/sentiment/${symbol}`
    );
    return res.json();
  },

  // Correlation Analysis - Find correlated stocks
  async getCorrelationAnalysis(symbols: string[]) {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_B}/api/v1/correlation`,
      `${FALLBACK_URLS.ENGINE_B}/api/v1/correlation`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbols }),
      }
    );
    return res.json();
  },

  // AI Trade Ideas - Get trade recommendations
  async getTradeIdeas(budget?: number, riskLevel?: 'conservative' | 'moderate' | 'aggressive') {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_B}/api/v1/trade-ideas`,
      `${FALLBACK_URLS.ENGINE_B}/api/v1/trade-ideas`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ budget, risk_level: riskLevel }),
      }
    );
    return res.json();
  },
};

// Engine C - Execution
export const engineC = {
  async health(): Promise<EngineHealth> {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_C}/health`,
      `${FALLBACK_URLS.ENGINE_C}/health`
    );
    return res.json();
  },

  async getFunds(): Promise<FundsResponse> {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_C}/api/dhan/funds`,
      `${FALLBACK_URLS.ENGINE_C}/api/dhan/funds`
    );
    return res.json();
  },

  async getPositions() {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_C}/api/dhan/positions`,
      `${FALLBACK_URLS.ENGINE_C}/api/dhan/positions`
    );
    return res.json();
  },

  async getHoldings() {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_C}/api/dhan/holdings`,
      `${FALLBACK_URLS.ENGINE_C}/api/dhan/holdings`
    );
    return res.json();
  },

  async getOrders() {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_C}/api/dhan/orders`,
      `${FALLBACK_URLS.ENGINE_C}/api/dhan/orders`
    );
    return res.json();
  },

  async placeOrder(data: OrderRequest) {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_C}/api/dhan/place-order`,
      `${FALLBACK_URLS.ENGINE_C}/api/dhan/place-order`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      }
    );
    return res.json();
  },

  async cancelOrder(orderId: string) {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_C}/api/dhan/cancel-order`,
      `${FALLBACK_URLS.ENGINE_C}/api/dhan/cancel-order`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ order_id: orderId }),
      }
    );
    return res.json();
  },

  async getExecutionAnalytics() {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_C}/api/v1/execution/analytics`,
      `${FALLBACK_URLS.ENGINE_C}/api/v1/execution/analytics`
    );
    return res.json();
  },
};

// Combined API
export const api = {
  engineA,
  engineB,
  engineC,

  // Utility: Check all engines health
  async checkAllEngines(): Promise<{
    engineA: EngineHealth | null;
    engineB: EngineHealth | null;
    engineC: EngineHealth | null;
  }> {
    const [a, b, c] = await Promise.allSettled([
      engineA.health(),
      engineB.health(),
      engineC.health(),
    ]);

    return {
      engineA: a.status === 'fulfilled' ? a.value : null,
      engineB: b.status === 'fulfilled' ? b.value : null,
      engineC: c.status === 'fulfilled' ? c.value : null,
    };
  },
};

export default api;

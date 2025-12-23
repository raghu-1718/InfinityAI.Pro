// API Client for InfinityAI.Pro 3-Engine Architecture

// Direct Cloud Run URLs (subdomains require Cloud Run domain mapping which isn't set up)
const API_CONFIG = {
  ENGINE_A: process.env.NEXT_PUBLIC_ENGINE_A_URL || 'https://engine-a-429140669077.us-central1.run.app',
  ENGINE_B: process.env.NEXT_PUBLIC_ENGINE_B_URL || 'https://engine-b-429140669077.us-central1.run.app',
  ENGINE_C: process.env.NEXT_PUBLIC_ENGINE_C_URL || 'https://engine-c-429140669077.us-central1.run.app',
};

// Fallback URLs (same as primary since custom domains aren't mapped to Cloud Run)
const FALLBACK_URLS = {
  ENGINE_A: 'https://engine-a-429140669077.us-central1.run.app',
  ENGINE_B: 'https://engine-b-429140669077.us-central1.run.app',
  ENGINE_C: 'https://engine-c-429140669077.us-central1.run.app',
};

async function fetchWithFallback(primaryUrl: string, fallbackUrl: string, options?: RequestInit) {
  try {
    const response = await fetch(primaryUrl, { ...options, signal: AbortSignal.timeout(8000) });
    if (response.ok) return response;
    throw new Error(`HTTP ${response.status}`);
  } catch {
    // Try fallback URL with timeout
    return fetch(fallbackUrl, { ...options, signal: AbortSignal.timeout(15000) });
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

// User Trading Settings Types
export interface TradingSettings {
  stop_loss_percent: number;
  take_profit_percent: number;
  max_trades_per_day: number;
  trading_amount: number;
  min_capital: number;
  max_capital: number;
  risk_level: 'conservative' | 'moderate' | 'aggressive';
  max_risk_per_trade: number;
  min_confidence: number;
  selected_instruments: string[];
  use_ai_signals: boolean;
  auto_rebalance: boolean;
  trailing_stop_loss: boolean;
  position_sizing_method: 'fixed' | 'percentage' | 'kelly';
}

export interface TradingSettingsResponse {
  user_id: string;
  settings: TradingSettings;
  is_default: boolean;
  last_updated?: string;
  status?: string;
  message?: string;
}

export interface TradingSettingsSchema {
  schema: Record<string, {
    type: string;
    description: string;
    min?: number;
    max?: number;
    default: unknown;
    unit?: string;
    options?: string[];
    details?: Record<string, string>;
  }>;
  risk_presets: Record<string, Partial<TradingSettings>>;
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

// Position Analysis Types
export interface PositionAnalysisRequest {
  symbol: string;
  trading_symbol: string;
  security_id: string;
  position_type: 'LONG' | 'SHORT';
  exchange_segment: string;
  product_type: string;
  buy_avg: number;
  cost_price: number;
  buy_qty: number;
  sell_qty?: number;
  net_qty: number;
  realized_profit?: number;
  unrealized_profit?: number;
  expiry_date?: string;
  option_type?: 'CALL' | 'PUT';
  strike_price?: number;
  current_price?: number;
}

export interface PositionGreeks {
  delta: number;
  theta: number;
  gamma: number;
  vega: number;
  moneyness: number;
  moneyness_status: 'ITM' | 'ATM' | 'OTM';
}

export interface PositionRiskMetrics {
  position_value: number;
  unrealized_pnl: number;
  unrealized_pnl_pct: number;
  max_loss: number | string;
  breakeven: number | null;
  days_to_expiry: number | null;
  implied_volatility_estimate: number;
  greeks: PositionGreeks | null;
}

export interface AIRecommendation {
  action: 'HOLD' | 'MONITOR' | 'REVIEW' | 'EXIT_CONSIDERATION';
  confidence: 'HIGH' | 'MEDIUM' | 'LOW';
  summary: string;
  score: number;
  factors: string[];
  suggested_actions: Array<{
    action: string;
    reason: string;
    urgency: 'HIGH' | 'MEDIUM' | 'LOW';
  }>;
}

export interface MarketContext {
  underlying_price: number;
  trend: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
  trend_strength: number;
  volatility: number;
  sma_5: number;
  sma_20: number;
  market_status: string;
  data_source: string;
}

export interface PositionAnalysis {
  position_type: 'OPTION' | 'EQUITY';
  option_type: 'CALL' | 'PUT' | null;
  direction: 'LONG' | 'SHORT';
  quantity: number;
  entry_price: number;
  current_value: number;
  strike_price: number | null;
  expiry_date: string | null;
  is_profitable: boolean;
  risk_reward_status: 'FAVORABLE' | 'UNFAVORABLE';
}

export interface PositionAnalysisResponse {
  symbol: string;
  analysis: PositionAnalysis;
  risk_metrics: PositionRiskMetrics;
  ai_recommendation: AIRecommendation;
  market_context: MarketContext;
  timestamp: string;
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

  // Start instrument-specific auto trading (filters signals by selected instruments)
  async startInstrumentTrade(data: {
    instruments: string[];
    riskLevel?: string;
    stopLoss?: number;
    takeProfit?: number;
    strategy?: string;
    symbol?: string;
    qty?: number;
  }) {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_A}/api/v1/trade/start-instrument`,
      `${FALLBACK_URLS.ENGINE_A}/api/v1/trade/start-instrument`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      }
    );
    return res.json();
  },

  // Start auto trading with specific instrument configuration
  async startAutoTrading(data: {
    instruments: string[];
    tradingAmount: number;
    riskLevel: string;
    stopLossPercent: number;
    takeProfitPercent: number;
    maxTradesPerDay: number;
    useAISignals: boolean;
    user_id?: string;
  }) {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_A}/api/v1/auto-trade/start`,
      `${FALLBACK_URLS.ENGINE_C}/api/auto-trade/start`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      }
    );
    return res.json();
  },

  async stopAutoTrading() {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_A}/api/v1/auto-trade/stop`,
      `${FALLBACK_URLS.ENGINE_C}/api/auto-trade/stop`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      }
    );
    return res.json();
  },

  async getAutoTradingStatus() {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_A}/api/v1/auto-trade/status`,
      `${FALLBACK_URLS.ENGINE_C}/api/auto-trade/status`
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

  async getEnhancedSignal(data: {
    symbol: string;
    timeframe: string;
    user_analysis_type?: string;
    use_pro_model?: boolean;
  }): Promise<SignalResponse> {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_B}/api/v1/signal`,
      `${FALLBACK_URLS.ENGINE_B}/api/v1/signal`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          symbol: data.symbol,
          use_gemini: true,
          _metadata: { timeframe: data.timeframe, type: data.user_analysis_type },
        }),
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

  // Position Analysis - AI-powered analysis of individual positions
  async analyzePosition(position: PositionAnalysisRequest): Promise<PositionAnalysisResponse> {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_B}/api/v1/position/analyze`,
      `${FALLBACK_URLS.ENGINE_B}/api/v1/position/analyze`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(position),
      }
    );
    return res.json();
  },

  // Portfolio Analysis - Analyze entire portfolio with AI
  async analyzePortfolioPositions(positions: PositionAnalysisRequest[]) {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_B}/api/v1/portfolio/analyze`,
      `${FALLBACK_URLS.ENGINE_B}/api/v1/portfolio/analyze`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(positions),
      }
    );
    return res.json();
  },

  // Sentiment Analysis - Analyze text for sentiment
  async analyzeSentiment(symbol: string, text: string) {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_B}/api/v1/sentiment`,
      `${FALLBACK_URLS.ENGINE_B}/api/v1/sentiment`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbol, text }),
      }
    );
    return res.json();
  },

  // Market Status
  async getMarketStatus() {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_B}/api/v1/market/status`,
      `${FALLBACK_URLS.ENGINE_B}/api/v1/market/status`
    );
    return res.json();
  },

  // ============================================================================
  // FINANCE AI MODEL ENDPOINTS (Gemini-powered)
  // ============================================================================

  // Finance AI Status - Check if Finance AI is available
  async getFinanceAIStatus() {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_B}/api/v1/finance-ai/status`,
      `${FALLBACK_URLS.ENGINE_B}/api/v1/finance-ai/status`
    );
    return res.json();
  },

  // Finance AI Signal - Get AI-powered trading signal
  async getFinanceAISignal(data: {
    symbol: string;
    current_price: number;
    technical_indicators?: Record<string, any>;
    news_items?: string[];
    model_type?: 'stock_analyst' | 'options_strategist' | 'technical_analyst' | 'risk_manager' | 'sentiment_analyst';
  }) {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_B}/api/v1/finance-ai/signal`,
      `${FALLBACK_URLS.ENGINE_B}/api/v1/finance-ai/signal`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      }
    );
    return res.json();
  },

  // Finance AI Market Analysis - Get comprehensive market analysis
  async getFinanceAIMarketAnalysis(data: {
    symbol: string;
    current_price: number;
    technical_indicators?: Record<string, any>;
    news_headlines?: string[];
  }) {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_B}/api/v1/finance-ai/market-analysis`,
      `${FALLBACK_URLS.ENGINE_B}/api/v1/finance-ai/market-analysis`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      }
    );
    return res.json();
  },

  // Finance AI Options Strategy - Get AI-powered options strategy
  async getFinanceAIOptionsStrategy(data: {
    index: string;
    spot_price: number;
    outlook: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
    capital: number;
    risk_appetite: 'LOW' | 'MODERATE' | 'HIGH';
  }) {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_B}/api/v1/finance-ai/options-strategy`,
      `${FALLBACK_URLS.ENGINE_B}/api/v1/finance-ai/options-strategy`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      }
    );
    return res.json();
  },

  // Finance AI Risk Analysis - Get AI-powered portfolio risk analysis
  async getFinanceAIRiskAnalysis(data: {
    positions: Array<{
      symbol: string;
      quantity: number;
      entry_price: number;
      current_price: number;
    }>;
    account_value: number;
  }) {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_B}/api/v1/finance-ai/risk-analysis`,
      `${FALLBACK_URLS.ENGINE_B}/api/v1/finance-ai/risk-analysis`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      }
    );
    return res.json();
  },

  // Free-form Gemini Chat for any trading question
  async askGemini(data: { question: string; context?: string }) {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_B}/api/v1/gemini/chat`,
      `${FALLBACK_URLS.ENGINE_B}/api/v1/gemini/chat`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
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

  async getFunds(userId?: string): Promise<FundsResponse> {
    const queryParam = userId ? `?user_id=${userId}` : '';
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_C}/api/dhan/funds${queryParam}`,
      `${FALLBACK_URLS.ENGINE_C}/api/dhan/funds${queryParam}`
    );
    return res.json();
  },

  async getPositions(userId?: string) {
    const queryParam = userId ? `?user_id=${userId}` : '';
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_C}/api/dhan/positions${queryParam}`,
      `${FALLBACK_URLS.ENGINE_C}/api/dhan/positions${queryParam}`
    );
    return res.json();
  },

  async getHoldings(userId?: string) {
    const queryParam = userId ? `?user_id=${userId}` : '';
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_C}/api/dhan/holdings${queryParam}`,
      `${FALLBACK_URLS.ENGINE_C}/api/dhan/holdings${queryParam}`
    );
    return res.json();
  },

  async getOrders(userId?: string) {
    const queryParam = userId ? `?user_id=${userId}` : '';
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_C}/api/dhan/orders${queryParam}`,
      `${FALLBACK_URLS.ENGINE_C}/api/dhan/orders${queryParam}`
    );
    return res.json();
  },

  // Get complete user account with funds, positions, holdings
  async getUserAccount(userId: string) {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_C}/api/v1/user/${userId}/account`,
      `${FALLBACK_URLS.ENGINE_C}/api/v1/user/${userId}/account`
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

  // User Credentials API
  async getUserCredentials(userId: string) {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_C}/api/user/credentials?user_id=${userId}`,
      `${FALLBACK_URLS.ENGINE_C}/api/user/credentials?user_id=${userId}`
    );
    return res.json();
  },

  async saveUserCredentials(data: {
    user_id: string;
    client_id: string;
    access_token: string;
    api_key?: string;
  }) {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_C}/api/user/credentials`,
      `${FALLBACK_URLS.ENGINE_C}/api/user/credentials`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      }
    );
    return res.json();
  },

  async verifyUserCredentials(userId: string) {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_C}/api/user/credentials/verify?user_id=${userId}`,
      `${FALLBACK_URLS.ENGINE_C}/api/user/credentials/verify?user_id=${userId}`
    );
    return res.json();
  },

  async getUserDemat(userId: string) {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_C}/api/user/demat?user_id=${userId}`,
      `${FALLBACK_URLS.ENGINE_C}/api/user/demat?user_id=${userId}`
    );
    return res.json();
  },

  async deleteUserCredentials(userId: string) {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_C}/api/user/credentials?user_id=${userId}`,
      `${FALLBACK_URLS.ENGINE_C}/api/user/credentials?user_id=${userId}`,
      { method: 'DELETE' }
    );
    return res.json();
  },

  // ==================== USER TRADING SETTINGS ====================

  async getTradingSettings(userId: string): Promise<TradingSettingsResponse> {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_C}/api/trading-settings/${userId}`,
      `${FALLBACK_URLS.ENGINE_C}/api/trading-settings/${userId}`
    );
    return res.json();
  },

  async saveTradingSettings(userId: string, settings: Partial<TradingSettings>): Promise<TradingSettingsResponse> {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_C}/api/trading-settings/${userId}`,
      `${FALLBACK_URLS.ENGINE_C}/api/trading-settings/${userId}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings),
      }
    );
    return res.json();
  },

  async resetTradingSettings(userId: string) {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_C}/api/trading-settings/${userId}`,
      `${FALLBACK_URLS.ENGINE_C}/api/trading-settings/${userId}`,
      { method: 'DELETE' }
    );
    return res.json();
  },

  async getTradingSettingsSchema(): Promise<TradingSettingsSchema> {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_C}/api/trading-settings-schema`,
      `${FALLBACK_URLS.ENGINE_C}/api/trading-settings-schema`
    );
    return res.json();
  },

  // ============================================================================
  // BACKGROUND TRADING API - Persistent trading that runs even when browser closed
  // ============================================================================

  async startBackgroundTrading(data: {
    user_id: string;
    min_confidence?: number;
    max_risk_per_trade?: number;
    max_daily_trades?: number;
    trading_amount?: number;
    instruments?: string[];
    strategy?: string;
  }) {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_C}/api/background-trading/start`,
      `${FALLBACK_URLS.ENGINE_C}/api/background-trading/start`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      }
    );
    return res.json();
  },

  async stopBackgroundTrading(userId: string) {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_C}/api/background-trading/stop`,
      `${FALLBACK_URLS.ENGINE_C}/api/background-trading/stop`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId }),
      }
    );
    return res.json();
  },

  async getBackgroundTradingStatus(userId: string) {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_C}/api/background-trading/status/${userId}`,
      `${FALLBACK_URLS.ENGINE_C}/api/background-trading/status/${userId}`
    );
    return res.json();
  },

  // ============================================================================
  // ACTIVITY LOGGING API - Track all user activities in real-time
  // ============================================================================

  async logActivity(data: {
    user_id: string;
    type: string;
    details?: Record<string, any>;
  }) {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_C}/api/activity/log`,
      `${FALLBACK_URLS.ENGINE_C}/api/activity/log`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      }
    );
    return res.json();
  },

  async getActivityLog(userId: string, options?: {
    date?: string;
    activity_type?: string;
    limit?: number;
  }) {
    const params = new URLSearchParams();
    if (options?.date) params.append('date', options.date);
    if (options?.activity_type) params.append('activity_type', options.activity_type);
    if (options?.limit) params.append('limit', options.limit.toString());

    const queryString = params.toString() ? `?${params.toString()}` : '';
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_C}/api/activity/log/${userId}${queryString}`,
      `${FALLBACK_URLS.ENGINE_C}/api/activity/log/${userId}${queryString}`
    );
    return res.json();
  },

  async getActivitySummary(userId: string, date?: string) {
    const queryString = date ? `?date=${date}` : '';
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_C}/api/activity/summary/${userId}${queryString}`,
      `${FALLBACK_URLS.ENGINE_C}/api/activity/summary/${userId}${queryString}`
    );
    return res.json();
  },

  async getTodayActivity(userId: string) {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_C}/api/activity/today/${userId}`,
      `${FALLBACK_URLS.ENGINE_C}/api/activity/today/${userId}`
    );
    return res.json();
  },

  // ============================================================================
  // VERTEX AI AGENT API - Financial Advisor Agent for AI-driven trading
  // ============================================================================

  async getAgentStatus() {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_C}/api/agent/status`,
      `${FALLBACK_URLS.ENGINE_C}/api/agent/status`
    );
    return res.json();
  },

  async chatWithAgent(data: {
    user_id: string;
    message: string;
    context?: Record<string, any>;
  }) {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_C}/api/agent/chat`,
      `${FALLBACK_URLS.ENGINE_C}/api/agent/chat`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      }
    );
    return res.json();
  },

  async analyzeTradeOpportunity(data: {
    user_id: string;
    symbol: string;
    current_price?: number;
    market_data?: Record<string, any>;
    portfolio_context?: Record<string, any>;
  }) {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_C}/api/agent/analyze`,
      `${FALLBACK_URLS.ENGINE_C}/api/agent/analyze`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      }
    );
    return res.json();
  },

  async getRealtimeSignal(userId: string, symbol: string, timeframe: string = 'intraday') {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_C}/api/agent/signal/${userId}/${symbol}?timeframe=${timeframe}`,
      `${FALLBACK_URLS.ENGINE_C}/api/agent/signal/${userId}/${symbol}?timeframe=${timeframe}`
    );
    return res.json();
  },

  async shouldExecuteTrade(data: {
    user_id: string;
    symbol: string;
    signal: Record<string, any>;
    config?: Record<string, any>;
  }) {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_C}/api/agent/should-execute`,
      `${FALLBACK_URLS.ENGINE_C}/api/agent/should-execute`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      }
    );
    return res.json();
  },

  async runAutomatedTrading(data: {
    user_id: string;
    watchlist: string[];
    config?: {
      min_confidence?: number;
      max_risk_per_trade?: number;
      max_daily_trades?: number;
      trading_amount?: number;
    };
  }) {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_C}/api/agent/auto-trade`,
      `${FALLBACK_URLS.ENGINE_C}/api/agent/auto-trade`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      }
    );
    return res.json();
  },

  async createAgentSession(userId: string) {
    const res = await fetchWithFallback(
      `${API_CONFIG.ENGINE_C}/api/agent/session/create/${userId}`,
      `${FALLBACK_URLS.ENGINE_C}/api/agent/session/create/${userId}`,
      { method: 'POST' }
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

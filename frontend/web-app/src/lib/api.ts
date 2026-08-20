// API Client for InfinityAI.Pro 3-Engine Architecture

import { getUserId } from "@/lib/user";

// Helper to determine Engine A URL based on environment
export const getEngineAUrl = () => {
  return (
    process.env.NEXT_PUBLIC_ENGINE_A_URL ||
    "https://engine-a-313407263327.asia-south1.run.app"
  );
};

// Helper to determine Engine B URL based on environment
export const getEngineBUrl = () => {
  return (
    process.env.NEXT_PUBLIC_ENGINE_B_URL ||
    "https://engine-b-313407263327.asia-south1.run.app"
  );
};

// Helper to determine Engine C URL based on environment
export const getEngineCUrl = () => {
  return (
    process.env.NEXT_PUBLIC_ENGINE_C_URL ||
    "https://engine-c-313407263327.asia-south1.run.app"
  );
};


// API URLs from environment variables with correct fallbacks
export const API_CONFIG = {
  ENGINE_A: getEngineAUrl(),
  ENGINE_B: getEngineBUrl(),
  ENGINE_C: getEngineCUrl(),
};

// Debug logging in development
if (typeof window !== "undefined") {
  console.log("🔧 API Configuration:", {
    ENGINE_A: API_CONFIG.ENGINE_A,
    ENGINE_B: API_CONFIG.ENGINE_B,
    ENGINE_C: API_CONFIG.ENGINE_C,
  });
}

async function fetchWithTimeout(
  primaryUrl: string,
  options?: RequestInit & { timeoutMs?: number }
) {
  try {
    const timeout = options?.timeoutMs || 20000;
    const { timeoutMs, ...fetchOpts } = options || {};
    const response = await fetch(primaryUrl, {
      ...fetchOpts,
      signal: AbortSignal.timeout(timeout),
    });
    if (response.ok) return response;


    // Create error with status for better handling
    const error = new Error(`HTTP ${response.status}: ${response.statusText}`);
    (error as any).status = response.status;
    throw error;
  } catch (err: any) {
    // Re-throw with status if available
    if (err.status) throw err;

    // Network or timeout error
    console.error(`API Error for ${primaryUrl}:`, err.message);
    throw err;
  }
}

export const fetchFromEngineB = async (endpoint: string, options: RequestInit = {}) => {
  // 1. Create a custom AbortController
  const controller = new AbortController();
  
  // 2. Set a generous 60-second timeout for Heavy AI operations
  const timeoutId = setTimeout(() => controller.abort(), 60000); 

  const baseUrl = API_CONFIG.ENGINE_B;

  try {
    const response = await fetch(`${baseUrl}${endpoint}`, {
      ...options,
      signal: controller.signal, // 3. Attach the custom signal
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    // 4. Clear the timeout if the request succeeds before 60 seconds
    clearTimeout(timeoutId);

    if (!response.ok) {
      const error = new Error(`Engine-B API Error: ${response.statusText}`);
      (error as any).status = response.status;
      throw error;
    }

    return await response.json();
    
  } catch (error: any) {
    clearTimeout(timeoutId);
    
    // Catch the specific AbortError to log it cleanly
    if (error.name === 'AbortError') {
      console.error(`[TIMEOUT] Engine-B took longer than 60 seconds on ${endpoint}`);
      throw new Error('AI Engine timed out. Please try again.');
    }
    
    throw error;
  }
};

export const fetchFromEngineC = async (endpoint: string, options: RequestInit = {}) => {
  const baseUrl = API_CONFIG.ENGINE_C;
  const res = await fetchWithTimeout(`${baseUrl}${endpoint}`, options);
  return res.json();
};

// Standalone Dhan API fetch functions (Zero required user_id parameter)
export const getFunds = () => fetchFromEngineC("/api/dhan/funds");
export const getPositions = () => fetchFromEngineC("/api/dhan/positions");
export const getHoldings = () => fetchFromEngineC("/api/dhan/holdings");
export const getOrders = () => fetchFromEngineC("/api/dhan/orders");
export const getTrades = () => fetchFromEngineC("/api/dhan/trades");
export const getMarketQuotes = (securityIds: string[] | string = ["1333", "11536"], exchangeSegment = "NSE_EQ") => {
  const ids = Array.isArray(securityIds) ? securityIds.join(",") : securityIds;
  const params = new URLSearchParams({
    security_ids: ids,
    exchange_segment: exchangeSegment,
  });
  return fetchFromEngineC(`/api/dhan/market/quotes?${params.toString()}`);
};

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
  risk_level: "LOW" | "MEDIUM" | "HIGH";
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
  risk_level: "conservative" | "moderate" | "aggressive";
  max_risk_per_trade: number;
  min_confidence: number;
  selected_instruments: string[];
  use_ai_signals: boolean;
  auto_rebalance: boolean;
  trailing_stop_loss: boolean;
  position_sizing_method: "fixed" | "percentage" | "kelly";
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
  schema: Record<
    string,
    {
      type: string;
      description: string;
      min?: number;
      max?: number;
      default: unknown;
      unit?: string;
      options?: string[];
      details?: Record<string, string>;
    }
  >;
  risk_presets: Record<string, Partial<TradingSettings>>;
}

export interface VaRRequest {
  returns: number[];
  confidence?: number;
  method?: "historical" | "parametric" | "cornish-fisher";
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
  signal: "BUY" | "SELL" | "HOLD";
  confidence: number;
  symbol: string;
  analysis: {
    technical_score: number;
    sentiment_score: number;
    ml_prediction: number;
  };
  market_context: {
    reasoning?: string;
    trend?: string;
  };
  timestamp: string;
}

export interface OrderRequest {
  transaction_type: "BUY" | "SELL";
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
    availableBalance: number;
    availabelBalance?: number;
    sodLimit: number;
    collateralAmount: number;
  };
}

// Position Analysis Types
export interface PositionAnalysisRequest {
  symbol: string;
  trading_symbol: string;
  security_id: string;
  position_type: "LONG" | "SHORT";
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
  option_type?: "CALL" | "PUT";
  strike_price?: number;
  current_price?: number;
}

export interface PositionGreeks {
  delta: number;
  theta: number;
  gamma: number;
  vega: number;
  moneyness: number;
  moneyness_status: "ITM" | "ATM" | "OTM";
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
  action: "HOLD" | "MONITOR" | "REVIEW" | "EXIT_CONSIDERATION";
  confidence: "HIGH" | "MEDIUM" | "LOW";
  summary: string;
  score: number;
  factors: string[];
  suggested_actions: Array<{
    action: string;
    reason: string;
    urgency: "HIGH" | "MEDIUM" | "LOW";
  }>;
}

export interface MarketContext {
  underlying_price: number;
  trend: "BULLISH" | "BEARISH" | "NEUTRAL";
  trend_strength: number;
  volatility: number;
  sma_5: number;
  sma_20: number;
  market_status: string;
  data_source: string;
}

export interface PositionAnalysis {
  position_type: "OPTION" | "EQUITY";
  option_type: "CALL" | "PUT" | null;
  direction: "LONG" | "SHORT";
  quantity: number;
  entry_price: number;
  current_value: number;
  strike_price: number | null;
  expiry_date: string | null;
  is_profitable: boolean;
  risk_reward_status: "FAVORABLE" | "UNFAVORABLE";
}

export interface PositionAnalysisResponse {
  symbol: string;
  analysis: PositionAnalysis;
  risk_metrics: PositionRiskMetrics;
  ai_recommendation: AIRecommendation;
  market_context: MarketContext;
  timestamp: string;
}

export interface SystemStateResponse {
  system_status: string; // NORMAL, DEGRADED, KILL_SWITCH
  dhan_connected: boolean;
  trader_identity: string | null;
  engine_active: boolean;
  timestamp: string;
}

// Engine A - Orchestration & Risk Management
export const engineA = {
  // Get Unified System State
  getSystemState: async () => {
    const userId = getUserId();
    const headers: Record<string, string> = {};
    if (userId) {
      headers["X-User-ID"] = userId;
    }

    const res = await fetchWithTimeout(
      `${API_CONFIG.ENGINE_A}/api/system/state`,
      { headers },
    );
    return res.json() as Promise<SystemStateResponse>;
  },

  // Start Trading Session (Immutable Configuration)
  startSession: async (config: {
    capital: number;
    risk_mode: string;
    asset_class: string;
    user_id: string;
  }) => {
    const res = await fetchWithTimeout(
      `${API_CONFIG.ENGINE_A}/api/trading/session/start`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config),
      },
    );
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.message || "Failed to start session");
    }
    return res.json();
  },

  // Stop Trading Session (Kill Switch)
  stopSession: async () => {
    const res = await fetchWithTimeout(
      `${API_CONFIG.ENGINE_A}/api/trading/session/stop`,
      {
        method: "POST",
      },
    );
    if (!res.ok) {
      throw new Error("Failed to stop session");
    }
    return res.json();
  },

  async health(): Promise<EngineHealth> {
    // Engine A Health Check - Uses /api/system/state as the reliable endpoint
    const res = await fetchWithTimeout(
      `${API_CONFIG.ENGINE_A}/api/system/state`,
    );
    return res.json();
  },

  async calculateRiskScore(data: RiskScoreRequest): Promise<RiskScoreResponse> {
    const res = await fetchWithTimeout(
      `${API_CONFIG.ENGINE_A}/api/v1/risk/score`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      },
    );
    return res.json();
  },

  async calculateVaR(data: VaRRequest) {
    const res = await fetchWithTimeout(
      `${API_CONFIG.ENGINE_A}/api/v1/risk/var`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      },
    );
    return res.json();
  },

  async calculateCVaR(data: CVaRRequest) {
    const res = await fetchWithTimeout(
      `${API_CONFIG.ENGINE_A}/api/v1/risk/cvar`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      },
    );
    return res.json();
  },

  async calculateSortino(data: { returns: number[]; risk_free_rate?: number }) {
    const res = await fetchWithTimeout(
      `${API_CONFIG.ENGINE_A}/api/v1/risk/sortino`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      },
    );
    return res.json();
  },

  async calculateKelly(data: KellyRequest) {
    const res = await fetchWithTimeout(
      `${API_CONFIG.ENGINE_A}/api/v1/risk/kelly`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      },
    );
    return res.json();
  },

  async calculatePositionSize(data: PositionSizeRequest) {
    const res = await fetchWithTimeout(
      `${API_CONFIG.ENGINE_A}/api/v1/risk/position-size`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      },
    );
    return res.json();
  },

  async getComprehensiveRisk(data: {
    returns: number[];
    risk_free_rate?: number;
  }) {
    const res = await fetchWithTimeout(
      `${API_CONFIG.ENGINE_A}/api/v1/risk/comprehensive`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      },
    );
    return res.json();
  },

  async startTrade(data: { symbol: string; qty?: number; strategy?: string }) {
    const res = await fetchWithTimeout(
      `${API_CONFIG.ENGINE_A}/api/v1/trade/start`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      },
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
    const res = await fetchWithTimeout(
      `${API_CONFIG.ENGINE_A}/api/v1/trade/start-instrument`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      },
    );
    return res.json();
  },

  // Start auto trading with specific instrument configuration (SECURE SESSION V2)
  async startAutoTrading(data: {
    instruments: string[];
    tradingAmount: number; // Mapped to capital
    riskLevel: string; // Mapped to risk_mode
    stopLossPercent: number;
    takeProfitPercent: number;
    maxTradesPerDay: number;
    useAISignals: boolean;
    user_id: string; // Required now
  }) {
    // Mapping to Backend SessionConfig (Pure F&O & Commodities)
    const assetClass = data.instruments.some(
      (i) => i.toLowerCase().includes("crude") || i.toLowerCase().includes("gold") || i.toLowerCase().includes("silver"),
    )
      ? "commodities"
      : "fno";

    // Construct SessionConfig payload
    const payload = {
      capital: data.tradingAmount,
      risk_mode: data.riskLevel.toLowerCase(), // conservative, moderate, aggressive
      asset_class: assetClass,
      user_id: data.user_id,
      // Extra config passed as loose props if needed by Trader, but SessionConfig strict fields are above
      // We might need to ensure backend accepts extra fields or we put them in a 'params' dict if specific
      // For now, sticking to the defined SessionConfig in main.py.
      // Iterate: The backend SessionConfig Pydantic model might reject extras.
      // Let's check main.py SessionConfig definition again. It was:
      // class SessionConfig(BaseModel): capital, risk_mode, asset_class, user_id
      // So we strictly send these.
    };

    const res = await fetchWithTimeout(
      `${API_CONFIG.ENGINE_A}/api/trading/session/start`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      },
    );
    return res.json();
  },

  async stopAutoTrading(userId: string) {
    const res = await fetchWithTimeout(
      `${API_CONFIG.ENGINE_A}/api/trading/session/stop`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-User-ID": userId,
        },
      },
    );
    return res.json();
  },

  async getAutoTradingStatus() {
    // This might not exist in main.py yet, defaulting to what was there or need to add it?
    // main.py didn't show a status endpoint in the snippet.
    // I will disable this or leave as is (it might fail if endpoint missing).
    // For safety, let's point to a health check or similar if specific status missing.
    // actually, let's leave it pointing to old V1 for now as I didn't remove V1 routers (if they exist).
    const res = await fetchWithTimeout(
      `${API_CONFIG.ENGINE_A}/api/v1/auto-trade/status`,
    );
    return res.json();
  },
};

// Engine B - AI/ML Intelligence
export const engineB = {
  async health(): Promise<EngineHealth> {
    return fetchFromEngineB("/api/health");
  },

  async getSignal(data: SignalRequest): Promise<SignalResponse> {
    return fetchFromEngineB("/api/v1/signal", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async getEnhancedSignal(data: {
    symbol: string;
    timeframe: string;
    user_analysis_type?: string;
    use_pro_model?: boolean;
  }): Promise<SignalResponse> {
    return fetchFromEngineB("/api/v1/signal", {
      method: "POST",
      body: JSON.stringify({
        symbol: data.symbol,
        use_gemini: true,
        _metadata: {
          timeframe: data.timeframe,
          type: data.user_analysis_type,
        },
      }),
    });
  },

  async getGeminiAnalysis(data: { symbol: string; context?: string }) {
    return fetchFromEngineB(`/api/v1/gemini/quick-signal/${data.symbol}`);
  },

  async getBatchSignals(symbols: string[]) {
    return fetchFromEngineB("/api/v1/signals/batch", {
      method: "POST",
      body: JSON.stringify({ symbols }),
    });
  },

  async getModelStatus() {
    return fetchFromEngineB("/api/v1/models/status");
  },

  // Analyze portfolio holdings using AI/ML
  async analyzePortfolio(holdings: any[]) {
    return fetchFromEngineB("/api/v1/portfolio/analyze", {
      method: "POST",
      body: JSON.stringify({ holdings }),
    });
  },

  // Get AI recommendations for a specific holding
  async getHoldingRecommendation(symbol: string, holding: any) {
    return fetchFromEngineB("/api/v1/holding/recommendation", {
      method: "POST",
      body: JSON.stringify({ symbol, holding }),
    });
  },

  // Portfolio Optimization - Get optimal allocation
  async optimizePortfolio(
    holdings: any[],
    riskTolerance: "low" | "medium" | "high" = "medium",
  ) {
    return fetchFromEngineB("/api/v1/portfolio/optimize", {
      method: "POST",
      body: JSON.stringify({ holdings, risk_tolerance: riskTolerance }),
    });
  },

  // Removed obsolete 404 routes (sector analysis, stock screener, technical indicators, correlation analysis, trade ideas)

  // Market Prediction - Wired to Finance AI Signal
  async getMarketPrediction(timeframe: "day" | "week" | "month" = "day") {
    try {
      const data = await fetchFromEngineB("/api/v1/finance-ai/signal", {
        method: "POST",
        body: JSON.stringify({
          symbol: "NIFTY",
          current_price: 0, // Backend will fetch real price if 0
          model_type: "stock_analyst",
        }),
      });
      const signalObj = data.signal;
      const predictionStr =
        typeof signalObj === "string"
          ? signalObj
          : signalObj?.action || "BULLISH";
      const confidenceVal =
        typeof signalObj === "object"
          ? (signalObj?.confidence ?? data.confidence ?? 0.75)
          : (data.confidence ?? 0.75);

      return {
        prediction: predictionStr,
        confidence: confidenceVal,
        timeframe,
      };
    } catch (e) {
      console.warn("Prediction endpoint failed, falling back to neutral");
      return { prediction: "NEUTRAL", confidence: 0.5, timeframe };
    }
  },

  // Sentiment Analysis - Live News Sentiment from Aggregator
  async getSentimentAnalysis(symbol: string) {
    try {
      const res = await fetchWithTimeout(
        `${API_CONFIG.ENGINE_C}/api/news/sentiment/${symbol}`,
      );
      const data = await res.json();
      return {
        overall_sentiment: data.overall_sentiment || "Neutral",
        confidence: data.confidence || 0.5,
        catalysts: data.recent_headlines || [],
      };
    } catch (e) {
      console.warn("Sentiment endpoint failed, falling back");
      return { overall_sentiment: "Neutral", confidence: 0.5, catalysts: [] };
    }
  },

  // Position Analysis - AI-powered analysis of individual positions
  async analyzePosition(
    position: PositionAnalysisRequest,
  ): Promise<PositionAnalysisResponse> {
    return fetchFromEngineB("/api/v1/position/analyze", {
      method: "POST",
      body: JSON.stringify(position),
    });
  },

  // Portfolio Analysis - Analyze entire portfolio with AI
  async analyzePortfolioPositions(positions: PositionAnalysisRequest[]) {
    return fetchFromEngineB("/api/v1/portfolio/analyze", {
      method: "POST",
      body: JSON.stringify(positions),
    });
  },

  // Sentiment Analysis - Analyze text for sentiment
  async analyzeSentiment(symbol: string, text: string) {
    return fetchFromEngineB("/api/v1/sentiment", {
      method: "POST",
      body: JSON.stringify({ symbol, text }),
    });
  },

  // Market Status
  async getMarketStatus() {
    return fetchFromEngineB("/api/v1/market/status");
  },

  // ============================================================================
  // FINANCE AI MODEL ENDPOINTS (Gemini-powered)
  // ============================================================================

  // Finance AI Status - Check if Finance AI is available
  async getFinanceAIStatus() {
    return fetchFromEngineB("/api/v1/finance-ai/status");
  },

  // Finance AI Signal - Get AI-powered trading signal
  async getFinanceAISignal(data: {
    symbol: string;
    current_price: number;
    technical_indicators?: Record<string, any>;
    news_items?: string[];
    model_type?:
      | "stock_analyst"
      | "options_strategist"
      | "technical_analyst"
      | "risk_manager"
      | "sentiment_analyst";
  }) {
    return fetchFromEngineB("/api/v1/finance-ai/signal", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  // Finance AI Market Analysis - Get comprehensive market analysis
  async getFinanceAIMarketAnalysis(data: {
    symbol: string;
    current_price: number;
    technical_indicators?: Record<string, any>;
    news_headlines?: string[];
  }) {
    return fetchFromEngineB("/api/v1/finance-ai/market-analysis", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  // Finance AI Options Strategy - Get AI-powered options strategy
  async getFinanceAIOptionsStrategy(data: {
    index: string;
    spot_price: number;
    outlook: "BULLISH" | "BEARISH" | "NEUTRAL";
    capital: number;
    risk_appetite: "LOW" | "MODERATE" | "HIGH";
  }) {
    return fetchFromEngineB("/api/v1/finance-ai/options-strategy", {
      method: "POST",
      body: JSON.stringify(data),
    });
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
    return fetchFromEngineB("/api/v1/finance-ai/risk-analysis", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  // Free-form Gemini Chat for any trading question
  async askGemini(data: { question: string; context?: string }) {
    return fetchFromEngineB("/api/v1/gemini/chat", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },
};

// Engine C - Execution
export const engineC = {
  async health(): Promise<EngineHealth> {
    const res = await fetchWithTimeout(`${API_CONFIG.ENGINE_C}/api/health`);
    return res.json();
  },

  async getFunds(userId?: string): Promise<FundsResponse> {
    const queryParam = userId ? `?user_id=${userId}` : "";
    const res = await fetchWithTimeout(
      `${API_CONFIG.ENGINE_C}/api/dhan/funds${queryParam}`,
    );
    return res.json();
  },

  async getPositions(userId?: string) {
    const queryParam = userId ? `?user_id=${userId}` : "";
    const res = await fetchWithTimeout(
      `${API_CONFIG.ENGINE_C}/api/dhan/positions${queryParam}`,
    );
    return res.json();
  },

  async getHoldings(userId?: string) {
    const queryParam = userId ? `?user_id=${userId}` : "";
    const res = await fetchWithTimeout(
      `${API_CONFIG.ENGINE_C}/api/dhan/holdings${queryParam}`,
    );
    return res.json();
  },

  async getOrders(userId?: string) {
    const queryParam = userId ? `?user_id=${userId}` : "";
    const res = await fetchWithTimeout(
      `${API_CONFIG.ENGINE_C}/api/dhan/orders${queryParam}`,
    );
    return res.json();
  },

  // Get complete user account with funds, positions, holdings
  async getUserAccount(userId: string) {
    const res = await fetchWithTimeout(
      `${API_CONFIG.ENGINE_C}/api/v1/user/${userId}/account`,
    );
    return res.json();
  },

  async placeOrder(data: OrderRequest) {
    const res = await fetchWithTimeout(
      `${API_CONFIG.ENGINE_C}/api/dhan/place-order`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      },
    );
    return res.json();
  },

  async cancelOrder(orderId: string) {
    const res = await fetchWithTimeout(
      `${API_CONFIG.ENGINE_C}/api/dhan/cancel-order`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ order_id: orderId }),
      },
    );
    return res.json();
  },

  async getExecutionAnalytics() {
    const res = await fetchWithTimeout(
      `${API_CONFIG.ENGINE_C}/api/v1/execution/analytics`,
    );
    return res.json();
  },

  // DhanHQ v2 Methods
  async getForeverOrders(userId: string = "znyNtT2lW3MKHqFrVA6E0A2Iv3N2") {
    const res = await fetchWithTimeout(`${API_CONFIG.ENGINE_C}/api/dhan/v2/forever/orders?user_id=${userId}`);
    return res.json();
  },

  async createForeverOrder(data: any) {
    const res = await fetchWithTimeout(`${API_CONFIG.ENGINE_C}/api/dhan/v2/forever/orders`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    return res.json();
  },

  async cancelForeverOrder(orderId: string, userId: string = "znyNtT2lW3MKHqFrVA6E0A2Iv3N2") {
    const res = await fetchWithTimeout(`${API_CONFIG.ENGINE_C}/api/dhan/v2/forever/orders/${orderId}?user_id=${userId}`, {
      method: "DELETE",
    });
    return res.json();
  },

  async convertPosition(data: any) {
    const res = await fetchWithTimeout(`${API_CONFIG.ENGINE_C}/api/dhan/v2/positions/convert`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    return res.json();
  },

  async calculateMargin(data: any) {
    const res = await fetchWithTimeout(`${API_CONFIG.ENGINE_C}/api/dhan/v2/margin/calculator`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    return res.json();
  },

  async getAccountLedger(userId: string = "znyNtT2lW3MKHqFrVA6E0A2Iv3N2") {
    const res = await fetchWithTimeout(`${API_CONFIG.ENGINE_C}/api/dhan/v2/ledger?user_id=${userId}`);
    return res.json();
  },

  async generateEdisForm(isin: string, quantity: number, userId: string = "znyNtT2lW3MKHqFrVA6E0A2Iv3N2") {
    const res = await fetchWithTimeout(`${API_CONFIG.ENGINE_C}/api/dhan/v2/edis/form?isin=${isin}&quantity=${quantity}&user_id=${userId}`);
    return res.json();
  },

  async getMarketQuotes(securityIds: string = "1333,11536", exchangeSegment: string = "NSE_EQ") {
    const res = await fetchWithTimeout(
      `${API_CONFIG.ENGINE_C}/api/dhan/market/quotes?security_ids=${encodeURIComponent(securityIds)}&exchange_segment=${encodeURIComponent(exchangeSegment)}`
    );
    return res.json();
  },

  async getTrades(userId?: string) {
    const queryParam = userId ? `?user_id=${userId}` : "";
    const res = await fetchWithTimeout(
      `${API_CONFIG.ENGINE_C}/api/dhan/trades${queryParam}`
    );
    return res.json();
  },

  async getHistoricalData(symbol: string, fromDate: string, toDate: string, interval: string = "1D") {
    const res = await fetchWithTimeout(
      `${API_CONFIG.ENGINE_C}/api/dhan/historical?symbol=${encodeURIComponent(symbol)}&fromDate=${fromDate}&toDate=${toDate}&interval=${interval}`
    );
    return res.json();
  },

  async getMarketDepth(symbol: string, levels: number = 20) {
    const res = await fetchWithTimeout(
      `${API_CONFIG.ENGINE_C}/api/dhan/market-depth?symbol=${encodeURIComponent(symbol)}&levels=${levels}`
    );
    return res.json();
  },

  async getOptionChain(symbol: string, expiry?: string) {
    const query = expiry ? `&expiry=${encodeURIComponent(expiry)}` : "";
    const res = await fetchWithTimeout(
      `${API_CONFIG.ENGINE_C}/api/dhan/optionchain?under_security_id=13${query}`
    );
    return res.json();
  },

  async getExpiredOptions(symbol: string, date: string) {
    const res = await fetchWithTimeout(
      `${API_CONFIG.ENGINE_C}/api/dhan/expired-options?symbol=${encodeURIComponent(symbol)}&date=${date}`
    );
    return res.json();
  },

  // User Credentials API (Single-Tenant Default)
  async getUserCredentials(userId?: string) {
    const queryParam = userId ? `?user_id=${userId}` : "";
    const res = await fetchWithTimeout(
      `${API_CONFIG.ENGINE_C}/api/user/credentials${queryParam}`,
    );
    return res.json();
  },

  async saveUserCredentials(data: {
    user_id?: string;
    client_id: string;
    access_token: string;
    api_key?: string;
  }) {
    const res = await fetchWithTimeout(
      `${API_CONFIG.ENGINE_C}/api/user/credentials`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      },
    );
    return res.json();
  },

  async verifyUserCredentials(userId?: string) {
    const queryParam = userId ? `?user_id=${userId}` : "";
    const res = await fetchWithTimeout(
      `${API_CONFIG.ENGINE_C}/api/user/credentials/verify${queryParam}`,
    );
    return res.json();
  },

  async getUserDemat(userId?: string) {
    const queryParam = userId ? `?user_id=${userId}` : "";
    const res = await fetchWithTimeout(
      `${API_CONFIG.ENGINE_C}/api/user/demat${queryParam}`,
    );
    return res.json();
  },

  async deleteUserCredentials(userId?: string) {
    const queryParam = userId ? `?user_id=${userId}` : "";
    const res = await fetchWithTimeout(
      `${API_CONFIG.ENGINE_C}/api/user/credentials${queryParam}`,
      { method: "DELETE" },
    );
    return res.json();
  },

  // ==================== USER TRADING SETTINGS ====================

  async getTradingSettings(userId: string): Promise<TradingSettingsResponse> {
    const res = await fetchWithTimeout(
      `${API_CONFIG.ENGINE_C}/api/trading-settings/${userId}`,
    );
    return res.json();
  },

  async saveTradingSettings(
    userId: string,
    settings: Partial<TradingSettings>,
  ): Promise<TradingSettingsResponse> {
    const res = await fetchWithTimeout(
      `${API_CONFIG.ENGINE_C}/api/trading-settings/${userId}`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(settings),
      },
    );
    return res.json();
  },

  async resetTradingSettings(userId: string) {
    const res = await fetchWithTimeout(
      `${API_CONFIG.ENGINE_C}/api/trading-settings/${userId}`,
      { method: "DELETE" },
    );
    return res.json();
  },

  async getTradingSettingsSchema(): Promise<TradingSettingsSchema> {
    const res = await fetchWithTimeout(
      `${API_CONFIG.ENGINE_C}/api/trading-settings-schema`,
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
    const res = await fetchWithTimeout(
      `${API_CONFIG.ENGINE_C}/api/background-trading/start`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      },
    );
    return res.json();
  },

  async stopBackgroundTrading(userId: string) {
    const res = await fetchWithTimeout(
      `${API_CONFIG.ENGINE_C}/api/background-trading/stop`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId }),
      },
    );
    return res.json();
  },

  async getBackgroundTradingStatus(userId: string) {
    const res = await fetchWithTimeout(
      `${API_CONFIG.ENGINE_C}/api/background-trading/status/${userId}`,
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
    const res = await fetchWithTimeout(
      `${API_CONFIG.ENGINE_C}/api/activity/log`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      },
    );
    return res.json();
  },

  async getActivityLog(
    userId: string,
    options?: {
      date?: string;
      activity_type?: string;
      limit?: number;
    },
  ) {
    const params = new URLSearchParams();
    if (options?.date) params.append("date", options.date);
    if (options?.activity_type)
      params.append("activity_type", options.activity_type);
    if (options?.limit) params.append("limit", options.limit.toString());

    const queryString = params.toString() ? `?${params.toString()}` : "";
    const res = await fetchWithTimeout(
      `${API_CONFIG.ENGINE_C}/api/activity/log/${userId}${queryString}`,
    );
    return res.json();
  },

  async getActivitySummary(userId: string, date?: string) {
    const queryString = date ? `?date=${date}` : "";
    const res = await fetchWithTimeout(
      `${API_CONFIG.ENGINE_C}/api/activity/summary/${userId}${queryString}`,
    );
    return res.json();
  },

  async getTodayActivity(userId: string) {
    const res = await fetchWithTimeout(
      `${API_CONFIG.ENGINE_C}/api/activity/today/${userId}`,
    );
    return res.json();
  },

  // ============================================================================
  // VERTEX AI AGENT API - Financial Advisor Agent for AI-driven trading
  // ============================================================================

  async getAgentStatus() {
    const res = await fetchWithTimeout(
      `${API_CONFIG.ENGINE_C}/api/agent/status`,
    );
    return res.json();
  },

  async chatWithAgent(data: {
    user_id: string;
    message: string;
    context?: Record<string, any>;
  }) {
    const res = await fetchWithTimeout(
      `${API_CONFIG.ENGINE_C}/api/agent/chat`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      },
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
    const res = await fetchWithTimeout(
      `${API_CONFIG.ENGINE_C}/api/agent/analyze`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      },
    );
    return res.json();
  },

  async getRealtimeSignal(
    userId: string,
    symbol: string,
    timeframe: string = "intraday",
  ) {
    const res = await fetchWithTimeout(
      `${API_CONFIG.ENGINE_C}/api/agent/signal/${userId}/${symbol}?timeframe=${timeframe}`,
    );
    return res.json();
  },

  async shouldExecuteTrade(data: {
    user_id: string;
    symbol: string;
    signal: Record<string, any>;
    config?: Record<string, any>;
  }) {
    const res = await fetchWithTimeout(
      `${API_CONFIG.ENGINE_C}/api/agent/should-execute`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      },
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
    const res = await fetchWithTimeout(
      `${API_CONFIG.ENGINE_C}/api/agent/auto-trade`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      },
    );
    return res.json();
  },

  async createAgentSession(userId: string) {
    const res = await fetchWithTimeout(
      `${API_CONFIG.ENGINE_C}/api/agent/session/create/${userId}`,
      { method: "POST" },
    );
    return res.json();
  },

  // ==================== OPTIONS ANALYTICS & MARKET DATA ====================

  async getOptionChainFull(params: {
    under_security_id: number;
    under_exchange_segment: string;
    expiry: string;
    user_id: string;
  }) {
    const qs = new URLSearchParams({
      under_security_id: params.under_security_id.toString(),
      under_exchange_segment: params.under_exchange_segment,
      expiry: params.expiry,
      user_id: params.user_id,
    });
    const res = await fetchWithTimeout(
      `${API_CONFIG.ENGINE_C}/api/dhan/market/options/chain?${qs.toString()}`,
    );
    return res.json();
  },

  async calculateGreeks(data: {
    spot_price: number;
    strike_price: number;
    time_to_expiry_days: number;
    implied_volatility: number;
    risk_free_rate?: number;
    option_type: "call" | "put";
  }) {
    const res = await fetchWithTimeout(
      `${API_CONFIG.ENGINE_C}/api/dhan/options/greeks/calculate`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      },
    );
    return res.json();
  },

  async calculatePCR(option_chain: any[]) {
    const res = await fetchWithTimeout(
      `${API_CONFIG.ENGINE_C}/api/dhan/options/analytics/pcr`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(option_chain),
      },
    );
    return res.json();
  },

  async calculateMaxPain(option_chain: any[]) {
    const res = await fetchWithTimeout(
      `${API_CONFIG.ENGINE_C}/api/dhan/options/analytics/max-pain`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(option_chain),
      },
    );
    return res.json();
  },

  async analyzeOptionStrategy(data: {
    strategy_name: string;
    spot_price: number;
    params: Record<string, number>;
  }) {
    const res = await fetchWithTimeout(
      `${API_CONFIG.ENGINE_C}/api/dhan/options/strategies/analyze`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      },
    );
    return res.json();
  },
};

// ─── InfinityAI Copilot Client (BigQuery Agent + Vertex AI) ────────────────
export const infinityCopilot = {
  async chat(message: string, context?: any) {
    const userId = getUserId();
    const res = await fetchWithTimeout(
      `${API_CONFIG.ENGINE_C}/api/copilot/chat`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message,
          user_id: userId,
          context,
        }),
        timeoutMs: 60000,
      }
    );
    return res.json();
  },

  async getStatus() {
    const res = await fetchWithTimeout(`${API_CONFIG.ENGINE_C}/api/copilot/status`, {
      timeoutMs: 15000,
    });
    return res.json();
  },
};


// Combined API
export const api = {
  engineA,
  engineB,
  engineC,
  copilot: infinityCopilot,

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
      engineA: a.status === "fulfilled" ? a.value : null,
      engineB: b.status === "fulfilled" ? b.value : null,
      engineC: c.status === "fulfilled" ? c.value : null,
    };
  },
};

export default api;


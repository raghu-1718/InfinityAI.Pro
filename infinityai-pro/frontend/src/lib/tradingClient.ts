// frontend/src/lib/tradingClient.ts
// TypeScript client library for InfinityAI.Pro Python backend
// Provides clean interface for trading operations, AI signals, and portfolio management

export interface TradingSignal {
  id: string;
  broker: 'dhan' | 'coinswitch';
  symbol: string;
  side: 'buy' | 'sell';
  quantity: number;
  price?: number;
  order_type?: 'limit' | 'market';
  notes?: string;
  timestamp?: string;
}

export interface OrderResponse {
  order_id: string;
  status: 'pending' | 'completed' | 'rejected';
  message: string;
  broker_order_id?: string;
}

export interface PortfolioPosition {
  symbol: string;
  quantity: number;
  average_price: number;
  current_price: number;
  pnl: number;
  pnl_percentage: number;
}

export interface PortfolioResponse {
  positions: PortfolioPosition[];
  total_value: number;
  total_pnl: number;
  total_pnl_percentage: number;
}

export interface SimulationResult {
  total_pnl: number;
  trades_executed: number;
  equity: number;
  episode_reward: number;
  epsilon: number;
  win_rate: number;
  sharpe_ratio: number;
}

export interface PerformanceData {
  total_return_pct: number;
  final_equity: number;
  total_trades: number;
  avg_reward_per_episode: number;
  best_episode_reward: number;
  worst_episode_reward: number;
  win_rate: number;
  sharpe_ratio: number;
  total_episodes: number;
  final_epsilon: number;
  model_trained: boolean;
}

export class InfinityAIClient {
  private baseUrl: string;
  private apiKey?: string;

  constructor(baseUrl: string = 'https://infinityai.pro', apiKey?: string) {
    this.baseUrl = baseUrl.replace(/\/+$/, '');
    this.apiKey = apiKey;
  }

  private async request<T>(
    method: 'GET' | 'POST' | 'PUT' | 'DELETE',
    endpoint: string,
    data?: any
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (this.apiKey) {
      headers['Authorization'] = `Bearer ${this.apiKey}`;
    }

    const config: RequestInit = {
      method,
      headers,
    };

    if (data && (method === 'POST' || method === 'PUT')) {
      config.body = JSON.stringify(data);
    }

    const response = await fetch(url, config);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
  }

  // AI Trading Simulation
  async runSimulation(days: number = 1, assetType: 'traditional' | 'crypto' = 'traditional', symbol?: string): Promise<SimulationResult> {
    const payload: any = { days };
    if (assetType === 'crypto' && symbol) {
      payload.asset_type = assetType;
      payload.symbol = symbol;
    }
    return this.request<SimulationResult>('POST', '/ai/simulate-day', payload);
  }

  async startContinuousLearning(days: number = 7, assetType: 'traditional' | 'crypto' = 'traditional', symbol?: string): Promise<PerformanceData> {
    const payload: any = { days };
    if (assetType === 'crypto' && symbol) {
      payload.asset_type = assetType;
      payload.symbol = symbol;
    }
    return this.request<PerformanceData>('POST', '/ai/train-model', payload);
  }

  async getPerformance(): Promise<PerformanceData> {
    return this.request<PerformanceData>('GET', '/ai/performance');
  }

  // Trading Operations
  async placeOrder(signal: TradingSignal): Promise<OrderResponse> {
    return this.request<OrderResponse>('POST', '/trading/order', signal);
  }

  async cancelOrder(orderId: string, broker: 'dhan' | 'coinswitch'): Promise<{ success: boolean; message: string }> {
    return this.request<{ success: boolean; message: string }>('DELETE', `/trading/order/${orderId}`, { broker });
  }

  async getOrders(broker: 'dhan' | 'coinswitch'): Promise<any[]> {
    return this.request<any[]>('GET', `/trading/orders/${broker}`);
  }

  async getPortfolio(broker: 'dhan' | 'coinswitch'): Promise<PortfolioResponse> {
    return this.request<PortfolioResponse>('GET', `/trading/portfolio/${broker}`);
  }

  // Market Data
  async getQuotes(symbols: string[], broker: 'dhan' | 'coinswitch'): Promise<Record<string, any>> {
    return this.request<Record<string, any>>('POST', `/trading/quotes/${broker}`, { symbols });
  }

  async getHistoricalData(symbol: string, interval: string, days: number = 30, broker: 'dhan' | 'coinswitch'): Promise<any[]> {
    return this.request<any[]>('GET', `/trading/historical/${broker}/${symbol}`, {
      interval,
      days: days.toString()
    });
  }

  // AI Features
  async getAISuggestions(symbol: string, marketData: any): Promise<{
    action: 'buy' | 'sell' | 'hold';
    confidence: number;
    reasoning: string;
    technical_indicators: Record<string, any>;
  }> {
    return this.request('POST', '/ai/analyze', { symbol, market_data: marketData });
  }

  async generateTradingStrategy(params: {
    risk_tolerance: 'low' | 'medium' | 'high';
    investment_amount: number;
    time_horizon: 'short' | 'medium' | 'long';
    asset_type: 'traditional' | 'crypto';
  }): Promise<{
    strategy: string;
    expected_return: number;
    risk_metrics: Record<string, any>;
    recommendations: string[];
  }> {
    return this.request('POST', '/ai/strategy', params);
  }

  // User Management
  async login(credentials: { username: string; password: string }): Promise<{ token: string; user: any }> {
    return this.request('POST', '/user/login', credentials);
  }

  async getUserProfile(): Promise<any> {
    return this.request('GET', '/user/profile');
  }

  // WebSocket connection for real-time signals (if implemented)
  connectRealTimeSignals(onSignal: (signal: TradingSignal) => void): WebSocket | null {
    try {
      const wsUrl = this.baseUrl.replace(/^http/, 'ws') + '/ws/signals';
      const ws = new WebSocket(wsUrl);

      ws.onmessage = (event) => {
        try {
          const signal: TradingSignal = JSON.parse(event.data);
          onSignal(signal);
        } catch (error) {
          console.error('Failed to parse signal:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      return ws;
    } catch (error) {
      console.error('Failed to connect to WebSocket:', error);
      return null;
    }
  }
}

// Default client instance
export const tradingClient = new InfinityAIClient();

// Helper function to create authenticated client
export function createAuthenticatedClient(apiKey: string, baseUrl?: string): InfinityAIClient {
  return new InfinityAIClient(baseUrl, apiKey);
}
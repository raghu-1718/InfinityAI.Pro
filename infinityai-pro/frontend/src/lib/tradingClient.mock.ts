// frontend/src/lib/tradingClient.mock.ts
// Mock client for offline development and testing
// Provides realistic mock responses without requiring backend

import {
  InfinityAIClient,
  TradingSignal,
  OrderResponse,
  PortfolioResponse,
  SimulationResult,
  PerformanceData
} from './tradingClient';

export class MockInfinityAIClient extends InfinityAIClient {
  private delay: number;
  private shouldFail: boolean;

  constructor(delay: number = 500, shouldFail: boolean = false) {
    super('http://mock-api');
    this.delay = delay;
    this.shouldFail = shouldFail;
  }

  private async mockDelay(): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, this.delay));
  }

  private mockError(message: string): never {
    throw new Error(message);
  }

  async runSimulation(days: number = 1, assetType: 'traditional' | 'crypto' = 'traditional', symbol?: string): Promise<SimulationResult> {
    await this.mockDelay();
    if (this.shouldFail) this.mockError('Simulation failed: Network error');

    const baseResult: SimulationResult = {
      total_pnl: Math.random() * 10000 - 2000, // -2000 to +8000
      trades_executed: Math.floor(Math.random() * 50) + 10,
      equity: 100000 + (Math.random() * 20000 - 10000),
      episode_reward: Math.random() * 1000,
      epsilon: Math.random() * 0.5,
      win_rate: Math.random() * 0.4 + 0.3, // 30-70%
      sharpe_ratio: Math.random() * 2 + 0.5 // 0.5-2.5
    };

    return baseResult;
  }

  async startContinuousLearning(days: number = 7, assetType: 'traditional' | 'crypto' = 'traditional', symbol?: string): Promise<PerformanceData> {
    await this.mockDelay();
    if (this.shouldFail) this.mockError('Training failed: Insufficient data');

    return {
      total_return_pct: Math.random() * 50 - 10, // -10% to +40%
      final_equity: 100000 + (Math.random() * 50000 - 10000),
      total_trades: Math.floor(Math.random() * 200) + 50,
      avg_reward_per_episode: Math.random() * 500,
      best_episode_reward: Math.random() * 2000,
      worst_episode_reward: Math.random() * -1000,
      win_rate: Math.random() * 0.3 + 0.4, // 40-70%
      sharpe_ratio: Math.random() * 1.5 + 0.8, // 0.8-2.3
      total_episodes: days,
      final_epsilon: Math.random() * 0.1,
      model_trained: Math.random() > 0.2 // 80% success rate
    };
  }

  async getPerformance(): Promise<PerformanceData> {
    await this.mockDelay();
    if (this.shouldFail) this.mockError('Failed to fetch performance data');

    return {
      total_return_pct: 15.7,
      final_equity: 115700,
      total_trades: 156,
      avg_reward_per_episode: 234.5,
      best_episode_reward: 1250.0,
      worst_episode_reward: -450.0,
      win_rate: 0.62,
      sharpe_ratio: 1.85,
      total_episodes: 45,
      final_epsilon: 0.05,
      model_trained: true
    };
  }

  async placeOrder(signal: TradingSignal): Promise<OrderResponse> {
    await this.mockDelay();
    if (this.shouldFail) this.mockError('Order placement failed: Insufficient funds');

    const success = Math.random() > 0.1; // 90% success rate
    return {
      order_id: `mock_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      status: success ? 'completed' : 'rejected',
      message: success ? 'Order placed successfully' : 'Order rejected: Market closed',
      broker_order_id: success ? `BRKR_${Math.random().toString(36).substr(2, 8)}` : undefined
    };
  }

  async cancelOrder(orderId: string, broker: 'dhan' | 'coinswitch'): Promise<{ success: boolean; message: string }> {
    await this.mockDelay();
    if (this.shouldFail) this.mockError('Cancel failed: Order already executed');

    return {
      success: Math.random() > 0.2, // 80% success rate
      message: Math.random() > 0.2 ? 'Order cancelled successfully' : 'Failed to cancel: Order not found'
    };
  }

  async getOrders(broker: 'dhan' | 'coinswitch'): Promise<any[]> {
    await this.mockDelay();
    if (this.shouldFail) this.mockError('Failed to fetch orders');

    const mockOrders = [];
    const numOrders = Math.floor(Math.random() * 5) + 1;

    for (let i = 0; i < numOrders; i++) {
      mockOrders.push({
        order_id: `ORD_${Math.random().toString(36).substr(2, 8)}`,
        symbol: broker === 'dhan' ? ['RELIANCE', 'TCS', 'INFY', 'HDFC'][Math.floor(Math.random() * 4)] :
                ['BTCINR', 'ETHINR', 'BNBINR'][Math.floor(Math.random() * 3)],
        side: Math.random() > 0.5 ? 'buy' : 'sell',
        quantity: Math.floor(Math.random() * 100) + 10,
        price: Math.random() * 1000 + 100,
        status: ['pending', 'completed', 'cancelled'][Math.floor(Math.random() * 3)],
        timestamp: new Date(Date.now() - Math.random() * 86400000).toISOString()
      });
    }

    return mockOrders;
  }

  async getPortfolio(broker: 'dhan' | 'coinswitch'): Promise<PortfolioResponse> {
    await this.mockDelay();
    if (this.shouldFail) this.mockError('Failed to fetch portfolio');

    const positions = [];
    const numPositions = Math.floor(Math.random() * 8) + 3;

    for (let i = 0; i < numPositions; i++) {
      const symbol = broker === 'dhan' ?
        ['RELIANCE', 'TCS', 'INFY', 'HDFC', 'ICICIBANK'][Math.floor(Math.random() * 5)] :
        ['BTCINR', 'ETHINR', 'BNBINR', 'ADAINR', 'SOLINR'][Math.floor(Math.random() * 5)];

      const quantity = Math.floor(Math.random() * 100) + 10;
      const avgPrice = Math.random() * 1000 + 100;
      const currentPrice = avgPrice * (0.9 + Math.random() * 0.2); // ±10% from avg
      const pnl = (currentPrice - avgPrice) * quantity;
      const pnlPercentage = ((currentPrice - avgPrice) / avgPrice) * 100;

      positions.push({
        symbol,
        quantity,
        average_price: avgPrice,
        current_price: currentPrice,
        pnl,
        pnl_percentage: pnlPercentage
      });
    }

    const totalValue = positions.reduce((sum, pos) => sum + (pos.current_price * pos.quantity), 0);
    const totalPnl = positions.reduce((sum, pos) => sum + pos.pnl, 0);
    const totalPnlPercentage = (totalPnl / (totalValue - totalPnl)) * 100;

    return {
      positions,
      total_value: totalValue,
      total_pnl: totalPnl,
      total_pnl_percentage: totalPnlPercentage
    };
  }

  async getQuotes(symbols: string[], broker: 'dhan' | 'coinswitch'): Promise<Record<string, any>> {
    await this.mockDelay();
    if (this.shouldFail) this.mockError('Failed to fetch quotes');

    const quotes: Record<string, any> = {};

    symbols.forEach(symbol => {
      const basePrice = Math.random() * 1000 + 100;
      quotes[symbol] = {
        symbol,
        price: basePrice,
        change: (Math.random() - 0.5) * 100,
        change_percent: (Math.random() - 0.5) * 10,
        volume: Math.floor(Math.random() * 1000000),
        high: basePrice * 1.05,
        low: basePrice * 0.95,
        open: basePrice * (0.98 + Math.random() * 0.04),
        timestamp: new Date().toISOString()
      };
    });

    return quotes;
  }

  async getHistoricalData(symbol: string, interval: string, days: number = 30, broker: 'dhan' | 'coinswitch'): Promise<any[]> {
    await this.mockDelay();
    if (this.shouldFail) this.mockError('Failed to fetch historical data');

    const data = [];
    const basePrice = Math.random() * 1000 + 100;
    let currentPrice = basePrice;

    for (let i = days; i >= 0; i--) {
      const change = (Math.random() - 0.5) * 50; // ±25 points
      currentPrice += change;

      data.push({
        timestamp: new Date(Date.now() - i * 24 * 60 * 60 * 1000).toISOString(),
        open: currentPrice - Math.random() * 10,
        high: currentPrice + Math.random() * 20,
        low: currentPrice - Math.random() * 20,
        close: currentPrice,
        volume: Math.floor(Math.random() * 100000) + 10000
      });
    }

    return data.reverse();
  }

  async getAISuggestions(symbol: string, marketData: any): Promise<{
    action: 'buy' | 'sell' | 'hold';
    confidence: number;
    reasoning: string;
    technical_indicators: Record<string, any>;
  }> {
    await this.mockDelay();
    if (this.shouldFail) this.mockError('AI analysis failed');

    const actions: ('buy' | 'sell' | 'hold')[] = ['buy', 'sell', 'hold'];
    const action = actions[Math.floor(Math.random() * actions.length)];

    return {
      action,
      confidence: Math.random() * 0.4 + 0.6, // 60-100%
      reasoning: `Based on technical analysis, ${symbol} shows ${action === 'buy' ? 'bullish' : action === 'sell' ? 'bearish' : 'neutral'} signals with RSI at ${Math.floor(Math.random() * 30) + 35} and MACD showing ${action === 'buy' ? 'positive' : 'negative'} momentum.`,
      technical_indicators: {
        rsi: Math.floor(Math.random() * 30) + 35,
        macd: {
          value: Math.random() * 10 - 5,
          signal: Math.random() * 10 - 5,
          histogram: Math.random() * 5 - 2.5
        },
        moving_averages: {
          sma_20: marketData?.close * (0.95 + Math.random() * 0.1),
          sma_50: marketData?.close * (0.9 + Math.random() * 0.1),
          ema_12: marketData?.close * (0.97 + Math.random() * 0.06)
        },
        bollinger_bands: {
          upper: marketData?.close * 1.05,
          middle: marketData?.close,
          lower: marketData?.close * 0.95
        }
      }
    };
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
    await this.mockDelay();
    if (this.shouldFail) this.mockError('Strategy generation failed');

    const strategies = {
      low: 'Conservative dividend-focused strategy',
      medium: 'Balanced growth strategy',
      high: 'Aggressive momentum strategy'
    };

    const expectedReturns = {
      low: 0.08 + Math.random() * 0.04, // 8-12%
      medium: 0.12 + Math.random() * 0.08, // 12-20%
      high: 0.20 + Math.random() * 0.15 // 20-35%
    };

    return {
      strategy: strategies[params.risk_tolerance],
      expected_return: expectedReturns[params.risk_tolerance],
      risk_metrics: {
        max_drawdown: params.risk_tolerance === 'low' ? 0.15 : params.risk_tolerance === 'medium' ? 0.25 : 0.40,
        volatility: params.risk_tolerance === 'low' ? 0.12 : params.risk_tolerance === 'medium' ? 0.18 : 0.30,
        sharpe_ratio: params.risk_tolerance === 'low' ? 1.2 : params.risk_tolerance === 'medium' ? 1.5 : 1.8,
        win_rate: params.risk_tolerance === 'low' ? 0.55 : params.risk_tolerance === 'medium' ? 0.60 : 0.65
      },
      recommendations: [
        `Allocate ${params.asset_type === 'crypto' ? '20-30%' : '60-70%'} to core holdings`,
        `Maintain ${params.risk_tolerance === 'low' ? 'cash reserves' : 'diversification'} for stability`,
        `Review positions ${params.time_horizon === 'short' ? 'weekly' : params.time_horizon === 'medium' ? 'monthly' : 'quarterly'}`,
        'Use stop-loss orders to protect capital',
        'Consider dollar-cost averaging for new investments'
      ]
    };
  }

  async login(credentials: { username: string; password: string }): Promise<{ token: string; user: any }> {
    await this.mockDelay();
    if (this.shouldFail || credentials.password !== 'demo') {
      this.mockError('Invalid credentials');
    }

    return {
      token: `mock_jwt_${Date.now()}`,
      user: {
        id: 'mock_user_123',
        username: credentials.username,
        email: `${credentials.username}@example.com`,
        role: 'trader',
        preferences: {
          default_broker: 'dhan',
          risk_tolerance: 'medium',
          notifications: true
        }
      }
    };
  }

  async getUserProfile(): Promise<any> {
    await this.mockDelay();
    if (this.shouldFail) this.mockError('Failed to fetch profile');

    return {
      id: 'mock_user_123',
      username: 'demo_user',
      email: 'demo@example.com',
      role: 'trader',
      preferences: {
        default_broker: 'dhan',
        risk_tolerance: 'medium',
        notifications: true,
        theme: 'dark'
      },
      stats: {
        total_trades: 156,
        win_rate: 0.62,
        total_pnl: 15700,
        best_trade: 2500,
        worst_trade: -800
      }
    };
  }
}

// Factory function to create mock client
export function createMockClient(delay: number = 500, shouldFail: boolean = false): MockInfinityAIClient {
  return new MockInfinityAIClient(delay, shouldFail);
}

// Test utilities
export class TradingClientTestUtils {
  static async testAllEndpoints(client: InfinityAIClient): Promise<{
    passed: number;
    failed: number;
    results: Array<{ test: string; success: boolean; error?: string }>;
  }> {
    const results = [];

    // Test simulation
    try {
      await client.runSimulation(1);
      results.push({ test: 'runSimulation', success: true });
    } catch (error) {
      results.push({ test: 'runSimulation', success: false, error: (error as Error).message });
    }

    // Test performance
    try {
      await client.getPerformance();
      results.push({ test: 'getPerformance', success: true });
    } catch (error) {
      results.push({ test: 'getPerformance', success: false, error: (error as Error).message });
    }

    // Test portfolio
    try {
      await client.getPortfolio('dhan');
      results.push({ test: 'getPortfolio', success: true });
    } catch (error) {
      results.push({ test: 'getPortfolio', success: false, error: (error as Error).message });
    }

    // Test orders
    try {
      await client.getOrders('dhan');
      results.push({ test: 'getOrders', success: true });
    } catch (error) {
      results.push({ test: 'getOrders', success: false, error: (error as Error).message });
    }

    // Test quotes
    try {
      await client.getQuotes(['RELIANCE', 'TCS'], 'dhan');
      results.push({ test: 'getQuotes', success: true });
    } catch (error) {
      results.push({ test: 'getQuotes', success: false, error: (error as Error).message });
    }

    const passed = results.filter(r => r.success).length;
    const failed = results.length - passed;

    return { passed, failed, results };
  }

  static async benchmarkClient(client: InfinityAIClient, iterations: number = 10): Promise<{
    averageResponseTime: number;
    minResponseTime: number;
    maxResponseTime: number;
    successRate: number;
  }> {
    const responseTimes = [];
    let successes = 0;

    for (let i = 0; i < iterations; i++) {
      const start = Date.now();
      try {
        await client.getPerformance();
        responseTimes.push(Date.now() - start);
        successes++;
      } catch (error) {
        responseTimes.push(Date.now() - start);
      }
    }

    return {
      averageResponseTime: responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length,
      minResponseTime: Math.min(...responseTimes),
      maxResponseTime: Math.max(...responseTimes),
      successRate: successes / iterations
    };
  }
}
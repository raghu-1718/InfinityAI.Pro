// frontend/src/lib/tradingClient.test.ts
// Example tests and usage of the trading client library

import { InfinityAIClient, createAuthenticatedClient } from './tradingClient';
import { MockInfinityAIClient, createMockClient, TradingClientTestUtils } from './tradingClient.mock';

// Example usage in a React component
export class TradingDemo {
  private client: InfinityAIClient;

  constructor(useMock: boolean = false) {
    if (useMock) {
      // Use mock client for development/testing
      this.client = createMockClient(300); // 300ms delay
    } else {
      // Use real client with authentication
      this.client = createAuthenticatedClient('your_api_token_here');
    }
  }

  async runDemo() {
    try {
      console.log('🚀 Starting InfinityAI.Pro Trading Demo');

      // 1. Run AI simulation
      console.log('📊 Running AI simulation...');
      const simulation = await this.client.runSimulation(1, 'traditional');
      console.log('Simulation result:', simulation);

      // 2. Get AI performance
      console.log('📈 Getting AI performance...');
      const performance = await this.client.getPerformance();
      console.log('Performance:', performance);

      // 3. Get portfolio
      console.log('💼 Getting portfolio...');
      const portfolio = await this.client.getPortfolio('dhan');
      console.log('Portfolio:', portfolio);

      // 4. Get market quotes
      console.log('💰 Getting market quotes...');
      const quotes = await this.client.getQuotes(['RELIANCE', 'TCS'], 'dhan');
      console.log('Quotes:', quotes);

      // 5. Get AI suggestions
      console.log('🤖 Getting AI suggestions...');
      const suggestions = await this.client.getAISuggestions('RELIANCE', { close: 2500 });
      console.log('AI Suggestions:', suggestions);

      // 6. Generate trading strategy
      console.log('📋 Generating trading strategy...');
      const strategy = await this.client.generateTradingStrategy({
        risk_tolerance: 'medium',
        investment_amount: 100000,
        time_horizon: 'medium',
        asset_type: 'traditional'
      });
      console.log('Strategy:', strategy);

      console.log('✅ Demo completed successfully!');

    } catch (error) {
      console.error('❌ Demo failed:', error);
    }
  }

  async testErrorHandling() {
    console.log('🧪 Testing error handling with failing mock client...');

    const failingClient = createMockClient(100, true); // Mock client that always fails

    try {
      await failingClient.runSimulation(1);
    } catch (error) {
      console.log('✅ Expected error caught:', (error as Error).message);
    }

    try {
      await failingClient.getPerformance();
    } catch (error) {
      console.log('✅ Expected error caught:', (error as Error).message);
    }
  }

  async benchmarkPerformance() {
    console.log('⚡ Benchmarking client performance...');

    const mockClient = createMockClient(50); // Fast mock client
    const benchmark = await TradingClientTestUtils.benchmarkClient(mockClient, 20);

    console.log('Benchmark results:');
    console.log(`- Average response time: ${benchmark.averageResponseTime.toFixed(2)}ms`);
    console.log(`- Min response time: ${benchmark.minResponseTime}ms`);
    console.log(`- Max response time: ${benchmark.maxResponseTime}ms`);
    console.log(`- Success rate: ${(benchmark.successRate * 100).toFixed(1)}%`);
  }

  async runComprehensiveTests() {
    console.log('🧪 Running comprehensive endpoint tests...');

    const mockClient = createMockClient(100);
    const testResults = await TradingClientTestUtils.testAllEndpoints(mockClient);

    console.log(`Test Results: ${testResults.passed} passed, ${testResults.failed} failed`);

    testResults.results.forEach(result => {
      const status = result.success ? '✅' : '❌';
      console.log(`${status} ${result.test}: ${result.success ? 'OK' : result.error}`);
    });
  }
}

// Example React hook for using the trading client
export function useTradingClient(apiKey?: string, useMock: boolean = false) {
  const client = useMock ?
    createMockClient() :
    (apiKey ? createAuthenticatedClient(apiKey) : new InfinityAIClient());

  return {
    client,
    // Convenience methods
    runSimulation: (days: number, assetType?: 'traditional' | 'crypto', symbol?: string) =>
      client.runSimulation(days, assetType, symbol),

    getPerformance: () => client.getPerformance(),

    getPortfolio: (broker: 'dhan' | 'coinswitch') => client.getPortfolio(broker),

    placeOrder: (signal: any) => client.placeOrder(signal),

    getQuotes: (symbols: string[], broker: 'dhan' | 'coinswitch') =>
      client.getQuotes(symbols, broker),

    getAISuggestions: (symbol: string, marketData: any) =>
      client.getAISuggestions(symbol, marketData),

    generateStrategy: (params: any) => client.generateTradingStrategy(params)
  };
}

// Example usage in development
export async function runDevelopmentDemo() {
  console.log('🔧 Running development demo with mock client...');

  const demo = new TradingDemo(true); // Use mock client

  await demo.runDemo();
  await demo.testErrorHandling();
  await demo.benchmarkPerformance();
  await demo.runComprehensiveTests();

  console.log('🎉 Development demo completed!');
}

// Auto-run demo in development
if (typeof window !== 'undefined' && (window as any).process?.env?.NODE_ENV === 'development') {
  // Uncomment to run demo automatically in browser console
  // runDevelopmentDemo();
}
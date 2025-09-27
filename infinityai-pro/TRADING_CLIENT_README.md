# InfinityAI.Pro - Unified Trading Client & Broker Abstraction

This package provides a complete TypeScript client library for the InfinityAI.Pro trading platform, along with mock implementations for offline development and a unified broker abstraction layer for the Python backend.

## 🚀 Features

- **TypeScript Client Library**: Clean, type-safe interface to InfinityAI.Pro backend
- **Mock Client**: Realistic mock responses for offline development and testing
- **Broker Abstraction**: Unified interface between Dhan (stocks) and CoinSwitch (crypto)
- **Comprehensive Testing**: Built-in test utilities and performance benchmarking
- **React Integration**: Hooks and components for easy frontend integration

## 📦 Installation

```bash
# Install dependencies (if not already installed)
npm install axios socket.io-client
npm install --save-dev @types/node
```

## 🏗️ Architecture Overview

### Frontend Client Library
```
frontend/src/lib/
├── tradingClient.ts          # Main TypeScript client
├── tradingClient.mock.ts     # Mock client for testing
└── tradingClient.test.ts     # Tests and examples
```

### Backend Broker Abstraction
```
backend/services/
└── broker_abstraction.py     # Unified broker interface
```

## 💻 Usage

### Basic Client Usage

```typescript
import { InfinityAIClient, createAuthenticatedClient } from './lib/tradingClient';

// For production
const client = createAuthenticatedClient('your_api_token');

// For development with mock data
const mockClient = createMockClient(500); // 500ms delay

// Run AI simulation
const result = await client.runSimulation(1, 'traditional');
console.log('P&L:', result.total_pnl);

// Get AI performance
const performance = await client.getPerformance();
console.log('Win Rate:', performance.win_rate);

// Get portfolio
const portfolio = await client.getPortfolio('dhan');
console.log('Positions:', portfolio.positions);

// Place order
const order = await client.placeOrder({
  broker: 'dhan',
  symbol: 'RELIANCE',
  side: 'buy',
  quantity: 10,
  price: 2500,
  order_type: 'limit'
});
```

### React Hook Integration

```typescript
import { useTradingClient } from './lib/tradingClient';

function TradingDashboard() {
  const {
    client,
    runSimulation,
    getPerformance,
    getPortfolio,
    placeOrder
  } = useTradingClient('api_token', false); // false = real client

  const handleSimulation = async () => {
    const result = await runSimulation(1, 'crypto', 'BTCINR');
    console.log('Crypto simulation:', result);
  };

  // ... component logic
}
```

### Mock Client for Development

```typescript
import { createMockClient, TradingClientTestUtils } from './lib/tradingClient.mock';

// Create mock client with custom delay
const mockClient = createMockClient(300);

// Run comprehensive tests
const testResults = await TradingClientTestUtils.testAllEndpoints(mockClient);
console.log(`Tests passed: ${testResults.passed}/${testResults.passed + testResults.failed}`);

// Benchmark performance
const benchmark = await TradingClientTestUtils.benchmarkClient(mockClient, 20);
console.log(`Avg response time: ${benchmark.averageResponseTime}ms`);
```

### Backend Broker Abstraction

```python
from services.broker_abstraction import UnifiedBrokerManager, DhanBrokerAdapter, CoinSwitchBrokerAdapter, BrokerCredentials

# Initialize broker manager
manager = UnifiedBrokerManager()

# Register Dhan for traditional markets
dhan_creds = BrokerCredentials(
    api_key="your_dhan_api_key",
    request_token="user_request_token"
)
manager.register_broker("dhan", DhanBrokerAdapter(dhan_creds))

# Register CoinSwitch for crypto
coinswitch_creds = BrokerCredentials(
    api_key="your_coinswitch_api_key",
    api_secret="your_coinswitch_secret"
)
manager.register_broker("coinswitch", CoinSwitchBrokerAdapter(coinswitch_creds))

# Initialize all brokers
await manager.initialize_all_brokers()

# Place unified orders (auto-selects correct broker)
stock_order = await manager.place_unified_order("traditional", "RELIANCE", "buy", 10, 2500.0)
crypto_order = await manager.place_unified_order("crypto", "BTCINR", "buy", 0.001, 4500000.0)

# Get unified portfolio
portfolio = await manager.get_unified_portfolio()
```

## 🧪 Testing & Development

### Running Tests

```typescript
import { runDevelopmentDemo } from './lib/tradingClient.test';

// Run complete demo with mock client
await runDevelopmentDemo();
```

### Error Testing

```typescript
// Test error handling
const failingClient = createMockClient(100, true); // Always fails

try {
  await failingClient.runSimulation(1);
} catch (error) {
  console.log('Expected error:', error.message);
}
```

### Performance Benchmarking

```typescript
const benchmark = await TradingClientTestUtils.benchmarkClient(client, 50);
console.log(`Average response: ${benchmark.averageResponseTime}ms`);
console.log(`Success rate: ${(benchmark.successRate * 100)}%`);
```

## 🔧 API Reference

### InfinityAIClient Methods

#### AI Trading
- `runSimulation(days, assetType?, symbol?)` - Run AI trading simulation
- `startContinuousLearning(days, assetType?, symbol?)` - Start AI learning
- `getPerformance()` - Get AI performance metrics
- `getAISuggestions(symbol, marketData)` - Get AI trading suggestions
- `generateTradingStrategy(params)` - Generate trading strategy

#### Trading Operations
- `placeOrder(signal)` - Place a trading order
- `cancelOrder(orderId, broker)` - Cancel an order
- `getOrders(broker)` - Get all orders
- `getPortfolio(broker)` - Get portfolio positions

#### Market Data
- `getQuotes(symbols, broker)` - Get market quotes
- `getHistoricalData(symbol, interval, days, broker)` - Get historical data

#### User Management
- `login(credentials)` - User login
- `getUserProfile()` - Get user profile

### Broker Abstraction Classes

#### UnifiedBrokerManager
- `register_broker(name, broker)` - Register a broker adapter
- `get_broker_for_asset(asset_type)` - Get broker for asset type
- `place_unified_order(asset_type, ...)` - Place order with auto-broker selection
- `get_unified_portfolio()` - Get portfolio from all brokers

#### Broker Adapters
- `DhanBrokerAdapter` - Dhan API integration
- `CoinSwitchBrokerAdapter` - CoinSwitch PRO API integration

## 🔒 Security Notes

- **Never store API keys in frontend code**
- **Use short-lived JWT tokens for authentication**
- **Backend validates all trading operations**
- **Implement rate limiting and risk checks**
- **Log all trading activities for compliance**

## 🚀 Deployment

### Environment Variables

```bash
# Backend
PORT=8000
BACKEND_API_KEY=your_secure_api_key
INTERNAL_SECRET=websocket_secret

# Dhan Broker
DHAN_API_KEY=your_dhan_key

# CoinSwitch Broker
COINSWITCH_API_KEY=your_coinswitch_key
COINSWITCH_SECRET=your_coinswitch_secret
```

### Docker Deployment

```yaml
# docker-compose.yml
version: '3.9'
services:
  backend:
    build: ./backend
    env_file: .env
    ports:
      - "8000:8000"

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
```

## 📊 Supported Brokers & Assets

| Broker | Assets | Features |
|--------|--------|----------|
| Dhan | Stocks, Commodities, Crypto | NSE, MCX, Real-time quotes |
| CoinSwitch | Cryptocurrency | BTC, ETH, BNB, ADA, SOL |

## 🤝 Contributing

1. Use mock client for development
2. Run comprehensive tests before committing
3. Follow TypeScript strict mode
4. Add JSDoc comments for new methods
5. Test error handling scenarios

## 📄 License

InfinityAI.Pro - Unified Trading Platform
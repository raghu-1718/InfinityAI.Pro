# InfinityAI Pro Node.js Backend

A production-ready Node.js/TypeScript backend for InfinityAI Pro trading platform with multi-broker support (Dhan + CoinSwitch), real-time trading signals, and comprehensive risk management.

## Features

- **Multi-Broker Support**: Unified interface for Dhan (Indian markets) and CoinSwitch (cryptocurrency)
- **Real-Time Trading**: Socket.IO integration for live signals and auto-execution
- **Risk Management**: Comprehensive safety checks and position limits
- **BTC Options Trading**: AI-powered BTC options strategies with spreads
- **Type Safety**: Full TypeScript implementation with strict typing
- **Production Ready**: Docker containerization, graceful shutdown, and error handling

## Quick Start

### Prerequisites

- Node.js 18+
- npm or yarn
- API credentials for Dhan and CoinSwitch

### Installation

```bash
cd infinityai-pro/node-backend
npm install
```

### Environment Setup

Copy the example environment file and configure your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your actual API credentials:

```env
# Server Configuration
PORT=3001
FRONTEND_URL=http://localhost:3000
BACKEND_API_KEY=your-secure-api-key-here

# Dhan Broker (Indian Markets)
DHAN_CLIENT_ID=your-dhan-client-id
DHAN_ACCESS_TOKEN=your-dhan-access-token
DHAN_DEMO=true

# CoinSwitch Broker (Cryptocurrency)
COINSWITCH_API_KEY=your-coinswitch-api-key
COINSWITCH_API_SECRET=your-coinswitch-api-secret
COINSWITCH_DEMO=true

# Risk Management Limits
MAX_ORDER_VALUE=100000
MAX_DAILY_LOSS=50000
MAX_POSITION_SIZE=10000
MAX_OPEN_POSITIONS=10
ALLOWED_BROKERS=dhan,coinswitch

# BTC Options Trading
BTC_TRADING_CAPITAL=4000
BTC_MAX_RISK_PERCENT=0.08
BTC_TARGET_PROFIT_PERCENT=0.15

# AI Services (Optional)
RUNPOD_URL=https://your-runpod-endpoint
HUGGINGFACE_TOKEN=your-huggingface-token
OLLAMA_URL=http://localhost:11434
```

### Development

```bash
npm run dev
```

### Production Build

```bash
npm run build
npm start
```

### Docker

```bash
docker build -t infinityai-backend .
docker run -p 3001:3001 --env-file .env infinityai-backend
```

## API Endpoints

### Health Check
```http
GET /health
```

### Authentication
All API endpoints require authentication via API key header:
```
x-api-key: your-backend-api-key
```

### Trading Operations

#### Place Order
```http
POST /api/order
Content-Type: application/json

{
  "broker": "dhan",
  "symbol": "RELIANCE",
  "side": "buy",
  "quantity": 10,
  "price": 2500.50,
  "orderType": "limit"
}
```

#### Cancel Order
```http
DELETE /api/order/:orderId?broker=dhan
```

#### Get Orders
```http
GET /api/orders/:broker
```

#### Get Portfolio
```http
GET /api/portfolio/:broker
GET /api/portfolio  # Combined portfolio
```

#### Get Market Quotes
```http
POST /api/quotes/:broker
Content-Type: application/json

{
  "symbols": ["RELIANCE", "TCS"]
}
```

### BTC Options Trading

#### Get BTC Trading Status
```http
GET /api/btc/status
```

#### Generate AI Trading Signal
```http
POST /api/btc/signal
Content-Type: application/json

{
  "btcPrice": 4500000,
  "chartImage": "base64-encoded-chart-image" // optional
}
```

#### Execute BTC Spread Trade
```http
POST /api/btc/trade
Content-Type: application/json

{
  "btcPrice": 4500000,
  "chartImage": "base64-encoded-chart-image", // optional
  "forceExecute": false // optional, override confidence check
}
```

#### Get BTC Positions
```http
GET /api/btc/positions
```

#### Monitor Positions
```http
POST /api/btc/monitor
Content-Type: application/json

{
  "btcPrice": 4500000 // optional, auto-fetch if not provided
}
```

#### Emergency Stop
```http
POST /api/btc/emergency-stop
```

#### Get BTC Market Data
```http
GET /api/btc/market-data
```

### Risk Management

#### Get Risk Limits
```http
GET /api/risk/limits
```

#### Update Risk Limits
```http
PUT /api/risk/limits
Content-Type: application/json

{
  "maxOrderValue": 150000,
  "maxDailyLoss": 75000
}
```

#### Emergency Stop
```http
POST /api/emergency-stop
```

### AI Integration

#### Get AI Suggestions
```http
POST /api/ai/suggestions
Content-Type: application/json

{
  "symbol": "RELIANCE",
  "marketData": {
    "close": 2500.50,
    "volume": 1000000
  }
}
```

## BTC Options Trading Strategy

### Overview
The BTC options trading module implements a risk-managed strategy using spread options for ₹2,000–₹4,000 capital, targeting 10–15% profit while limiting losses to 5–8%.

### Strategy Details

#### Capital Allocation
- **Total Capital**: ₹2,000–₹4,000
- **Risk per Trade**: 5–8% of capital (₹100–₹320)
- **Max Trades**: 1–2 per week
- **Reserve**: 50% capital for hedging/emergencies

#### Option Strategies
1. **Bull Call Spread**: Buy ATM call, Sell OTM call
2. **Bear Put Spread**: Buy ATM put, Sell OTM put

#### Trade Setup
- **Strike Selection**: Buy ATM (current BTC price), Sell OTM (5% away)
- **Expiry**: 1-week options
- **Max Loss**: Premium paid (5–8% of capital)
- **Max Profit**: Strike difference - premium (10–15%+ of capital)

#### AI Signal Integration
Signals combine multiple AI components:
- **YOLO Analysis**: Chart pattern recognition (40% weight)
- **Whisper Sentiment**: News sentiment analysis (30% weight)
- **LLM Analysis**: Market reasoning (30% weight)

#### Risk Management
- **Entry**: Only execute if AI confidence ≥70%
- **Stop Loss**: Close if loss hits 5–8% threshold
- **Profit Target**: Close at 10–15%+ profit
- **Expiry**: Auto-close at option expiry
- **Emergency**: Manual emergency stop available

### Example Trade

```javascript
// Signal Generation
const signal = await fetch('/api/btc/signal', {
  method: 'POST',
  headers: { 'x-api-key': 'your-api-key' },
  body: JSON.stringify({ btcPrice: 4500000 })
});

// Trade Execution
const trade = await fetch('/api/btc/trade', {
  method: 'POST',
  headers: { 'x-api-key': 'your-api-key' },
  body: JSON.stringify({ btcPrice: 4500000 })
});
```

### Performance Tracking
- **Win Rate Target**: 60%+ with AI signals
- **Risk/Reward Ratio**: 1:2–1:3
- **Monthly Target**: 20–30% returns (conservative)

## Socket.IO Real-Time Events

### Connection
```javascript
import io from 'socket.io-client';

const socket = io('http://localhost:3001', {
  auth: {
    key: 'your-backend-api-key',
    userId: 'optional-user-id'
  }
});
```

### Subscribe to Signals
```javascript
socket.emit('subscribe_signals');
socket.on('signal', (signal) => {
  console.log('New trade signal:', signal);
});
```

### Manual Trade Execution
```javascript
socket.emit('execute_trade', {
  id: 'signal-123',
  broker: 'dhan',
  symbol: 'RELIANCE',
  side: 'buy',
  quantity: 10,
  price: 2500.50
});
```

### Auto-Trading
```javascript
// Enable auto-trading
socket.emit('set_auto_trade', true);

// Listen for auto-executions
socket.on('auto_trade_executed', (data) => {
  console.log('Auto-trade executed:', data);
});
```

### Emergency Stop
```javascript
socket.emit('emergency_stop');
socket.on('emergency_stop_result', (result) => {
  console.log('Emergency stop completed:', result);
});
```

## Broker Configuration

### Dhan (Indian Markets)
- **Markets**: NSE Equity, NSE Futures & Options, BSE, MCX Commodities
- **Order Types**: LIMIT, MARKET, SL, SL-M
- **Products**: INTRADAY, DELIVERY, MARGIN, CNC

### CoinSwitch (Cryptocurrency)
- **Markets**: Major cryptocurrencies (BTC, ETH, etc.)
- **Order Types**: LIMIT, MARKET
- **Features**: HMAC-SHA256 authentication, comprehensive crypto trading

## Risk Management

The backend implements comprehensive risk controls:

- **Order Value Limits**: Maximum value per single order
- **Daily Loss Limits**: Maximum portfolio loss per day
- **Position Size Limits**: Maximum exposure per position
- **Open Position Limits**: Maximum concurrent positions
- **Broker Restrictions**: Configurable allowed brokers

## Development

### Project Structure
```
src/
├── clients/           # Broker API clients
│   ├── dhan.ts       # Dhan API integration
│   └── coinswitch.ts # CoinSwitch API integration
├── tradingManager.ts  # Risk management & order validation
├── btcOptionsTrader.ts # BTC options trading logic
├── aiSignalGenerator.ts # AI signal processing
├── socket.ts         # Real-time Socket.IO manager
├── routes.ts         # Express API routes
└── index.ts          # Server entry point
```

### Testing
```bash
npm test
```

### Linting
```bash
npm run lint
```

## Deployment

### Docker Compose (with Frontend)
```yaml
version: "3.8"
services:
  backend:
    build: ./node-backend
    ports:
      - "3001:3001"
    env_file: ./node-backend/.env
    depends_on:
      - redis  # if using Redis for caching

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://localhost:3001
```

### Environment Variables Reference

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Server port | `3001` |
| `FRONTEND_URL` | CORS allowed frontend URL | `http://localhost:3000` |
| `BACKEND_API_KEY` | API authentication key | Required |
| `DHAN_CLIENT_ID` | Dhan client ID | Required |
| `DHAN_ACCESS_TOKEN` | Dhan access token | Required |
| `DHAN_DEMO` | Use Dhan demo environment | `true` |
| `COINSWITCH_API_KEY` | CoinSwitch API key | Required |
| `COINSWITCH_API_SECRET` | CoinSwitch API secret | Required |
| `COINSWITCH_DEMO` | Use CoinSwitch demo environment | `true` |
| `MAX_ORDER_VALUE` | Max order value (₹) | `100000` |
| `MAX_DAILY_LOSS` | Max daily loss (₹) | `50000` |
| `MAX_POSITION_SIZE` | Max position size (₹) | `10000` |
| `MAX_OPEN_POSITIONS` | Max open positions | `10` |
| `ALLOWED_BROKERS` | Comma-separated broker list | `dhan,coinswitch` |
| `BTC_TRADING_CAPITAL` | BTC trading capital (₹) | `4000` |
| `BTC_MAX_RISK_PERCENT` | Max risk per BTC trade | `0.08` |
| `BTC_TARGET_PROFIT_PERCENT` | Target profit per BTC trade | `0.15` |
| `RUNPOD_URL` | RunPod GPU service URL | Optional |
| `HUGGINGFACE_TOKEN` | Hugging Face API token | Optional |
| `OLLAMA_URL` | Ollama LLM service URL | Optional |

## Security

- API key authentication for all endpoints
- Socket.IO authentication with API keys
- Input validation and sanitization
- Rate limiting (recommended to add)
- HTTPS in production
- Environment variable validation

## Monitoring

The backend provides health checks and statistics:

- Health endpoint: `GET /health`
- Socket.IO heartbeat events
- Connection statistics via Socket.IO
- Error logging and graceful shutdown

## Contributing

1. Follow TypeScript strict mode
2. Add comprehensive error handling
3. Update tests for new features
4. Document API changes
5. Use conventional commits

## License

See LICENSE file in the root directory.